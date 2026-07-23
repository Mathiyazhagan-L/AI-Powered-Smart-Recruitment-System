import os
import json
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from core.database import SessionLocal
from modules.job_management.model import Job
from modules.candidate.profile.model import CandidateProfile
from modules.candidate.skills.model import CandidateSkill
from modules.candidate.education.model import CandidateEducation
from modules.candidate.experience.model import CandidateExperience
from modules.candidate.projects.model import CandidateProject
from modules.ai_evaluation.services.matching_service import calculate_skill_match
from modules.ai_evaluation.services.scoring_service import calculate_ats_score

logger = logging.getLogger(__name__)


def generate_recommendations(candidate_id: int, job_id: int, db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Generates candidate recommendations.
    Uses LLM recommendations if GEMINI_API_KEY or OPENAI_API_KEY exists.
    Otherwise, uses rule-based recommendations.
    """
    if db is None:
        with SessionLocal() as session:
            return _generate_recommendations_impl(session, candidate_id, job_id)
    return _generate_recommendations_impl(db, candidate_id, job_id)


def _generate_recommendations_impl(db: Session, candidate_id: int, job_id: int) -> Dict[str, Any]:
    # 1. Check database cache
    from modules.job_management.model import AIRecommendation
    
    cached = db.query(AIRecommendation).filter(
        AIRecommendation.job_id == job_id,
        AIRecommendation.candidate_id == candidate_id
    ).first()
    
    if cached:
        logger.info(f"Returning cached recommendations for candidate {candidate_id}, job {job_id}")
        strengths = cached.strengths
        weaknesses = cached.weaknesses
        skill_gaps = cached.skill_gaps
        if isinstance(strengths, str):
            try: strengths = json.loads(strengths)
            except: pass
        if isinstance(weaknesses, str):
            try: weaknesses = json.loads(weaknesses)
            except: pass
        if isinstance(skill_gaps, str):
            try: skill_gaps = json.loads(skill_gaps)
            except: pass
            
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "skill_gaps": skill_gaps,
            "recommendation": cached.recommendation,
            "career_recommendation": cached.career_recommendation,
            "recommendation_report": f"Hiring Recommendation:\n{cached.recommendation}\n\nCareer Recommendation:\n{cached.career_recommendation}"
        }

    # 2. Fetch Job & Candidate Details
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job with ID {job_id} not found for recommendations.")
        return {
            "strengths": [],
            "weaknesses": ["Job profile not found."],
            "skill_gaps": [],
            "recommendation": "Not Recommended",
            "career_recommendation": "Job profile not found."
        }

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile:
        logger.warning(f"Candidate profile with ID {candidate_id} not found for recommendations.")
        return {
            "strengths": [],
            "weaknesses": ["Candidate profile not found."],
            "skill_gaps": [],
            "recommendation": "Not Recommended",
            "career_recommendation": "Candidate profile not found."
        }

    skills = db.query(CandidateSkill).filter(CandidateSkill.user_id == candidate_id).all()
    education = db.query(CandidateEducation).filter(CandidateEducation.user_id == candidate_id).all()
    experience = db.query(CandidateExperience).filter(CandidateExperience.user_id == candidate_id).all()
    projects = db.query(CandidateProject).filter(CandidateProject.user_id == candidate_id).all()

    # 3. Call AI Service with Retries
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    result = None
    if gemini_key:
        logger.info("Using Gemini for recommendation generation...")
        for attempt in range(1, 4):
            try:
                result = _generate_gemini_recommendations(profile, skills, education, experience, projects, job, gemini_key)
                if result and "hiring_recommendation" in result:
                    break
            except Exception as ex:
                logger.error(f"Gemini generation attempt {attempt} failed: {ex}")
        
        if not result or "hiring_recommendation" not in result:
            logger.warning("Gemini failed after 3 attempts. Falling back to rule-based recommendations.")
            result = None
            
    elif openai_key:
        logger.info("Using OpenAI for recommendation generation...")
        try:
            result = _generate_openai_recommendations(profile, skills, education, experience, projects, job, openai_key)
        except Exception as ex:
            logger.error(f"OpenAI generation failed: {ex}")
            result = None

    # 4. Rule-Based Fallback
    if not result:
        logger.info("No LLM result available. Using rule-based recommendation engine...")
        rule_res = _generate_rule_based_recommendations(profile, skills, education, experience, projects, job, db)
        result = {
            "strengths": rule_res["strengths"],
            "weaknesses": rule_res["weaknesses"],
            "skill_gaps": rule_res["skill_gaps"],
            "hiring_recommendation": rule_res["recommendation"],
            "career_recommendation": f"Focus on acquiring these missing skills: {', '.join(rule_res['skill_gaps'])}" if rule_res["skill_gaps"] else "Keep refining your technical profile and projects."
        }

    # 5. Save/Cache in Database
    try:
        new_rec = AIRecommendation(
            job_id=job_id,
            candidate_id=candidate_id,
            strengths=result.get("strengths", []),
            weaknesses=result.get("weaknesses", []),
            skill_gaps=result.get("skill_gaps", []),
            recommendation=result.get("hiring_recommendation", "Not Recommended"),
            career_recommendation=result.get("career_recommendation", "No career advice generated.")
        )
        db.add(new_rec)
        db.commit()
        logger.info(f"Saved recommendations to db for candidate {candidate_id}, job {job_id}")

        # Trigger Recruiter Email for Final Hiring Recommendation
        from modules.email_automation.triggers import trigger_email
        from modules.auth.model import User
        recruiters = db.query(User).filter(User.role.in_(["recruiter", "admin"])).all()
        for rec in recruiters:
            trigger_email(
                event_type="HR_REVIEW_REQUESTED",
                candidate_id=candidate_id,
                recruiter_id=rec.id,
                job_id=job_id,
                context={
                    "extra_details": f"A new recommendation has been generated for candidate #{candidate_id}: {result.get('hiring_recommendation')}"
                },
                db=db
            )

        # Auto-request HR Review if recommendation is favorable
        hiring_rec = result.get("hiring_recommendation", "Review")
        if hiring_rec in ["Strong Hire", "Hire", "Review"]:
            try:
                from modules.hr_review.logic import HRReviewLogic
                from modules.hr_review.schema import HRReviewCreate
                
                # Assign to a default recruiter if needed, here we use the first recruiter or ID 1
                rec_user = recruiters[0] if recruiters else None
                rec_id = rec_user.id if rec_user else 1
                
                review_data = HRReviewCreate(
                    candidate_id=candidate_id,
                    job_id=job_id,
                    recruiter_id=rec_id,
                    comments=f"Auto-requested by AI Recommendation: {hiring_rec}"
                )
                HRReviewLogic.request_hr_review(db, review_data)
                logger.info(f"Auto-submitted candidate {candidate_id} to HR review queue.")
            except Exception as hr_ex:
                logger.error(f"Failed to auto-request HR review: {hr_ex}")

    except Exception as db_ex:
        db.rollback()
        logger.error(f"Failed to cache recommendations in database: {db_ex}")

    return {
        "strengths": result.get("strengths", []),
        "weaknesses": result.get("weaknesses", []),
        "skill_gaps": result.get("skill_gaps", []),
        "recommendation": result.get("hiring_recommendation", "Not Recommended"),
        "career_recommendation": result.get("career_recommendation", "No career advice generated."),
        "recommendation_report": f"Hiring Recommendation:\n{result.get('hiring_recommendation', '')}\n\nCareer Recommendation:\n{result.get('career_recommendation', '')}"
    }


def _generate_rule_based_recommendations(
    profile: CandidateProfile,
    skills: list,
    education: list,
    experience: list,
    projects: list,
    job: Job,
    db: Session
) -> Dict[str, Any]:
    match_res = calculate_skill_match(candidate_id=profile.user_id, job_id=job.id, db=db)
    score_res = calculate_ats_score(candidate_id=profile.user_id, job_id=job.id, db=db)
    
    ats_score = score_res["ats_score"]
    skill_gaps = match_res["missing_skills"]

    strengths = []
    if match_res["match_percentage"] >= 75:
        strengths.append(f"Strong match for job required skills ({match_res['match_percentage']}% matched).")
    elif len(match_res["matched_skills"]) > 0:
        strengths.append(f"Possesses core required skills: {', '.join(match_res['matched_skills'][:4])}.")

    if education:
        edu = education[0]
        if edu.cgpa and edu.cgpa >= 8.0:
            strengths.append(f"Excellent academic performance with CGPA of {edu.cgpa}/10 at {edu.institution}.")
        elif edu.degree:
            strengths.append(f"Holds relevant degree: {edu.degree}.")

    if experience:
        first_exp = experience[0]
        strengths.append(f"Practical internship/work experience as a {first_exp.job_title} at {first_exp.company_name}.")

    if projects:
        strengths.append(f"Demonstrates hands-on capability with {len(projects)} technical projects (e.g. {projects[0].project_name}).")

    if not strengths:
        strengths.append("Basic candidate profile exists.")

    weaknesses = []
    if skill_gaps:
        weaknesses.append(f"Lacks key required skills: {', '.join(skill_gaps)}.")
    
    job_pref = job.preferred_skills or []
    if isinstance(job_pref, str):
        try:
            job_pref = json.loads(job_pref)
        except Exception:
            job_pref = [job_pref]

    cand_skills_lower = {s.skill_name.lower().strip() for s in skills if s.skill_name}
    missing_pref = [s for s in job_pref if s and s.lower().strip() not in cand_skills_lower]
    if missing_pref:
        weaknesses.append(f"Lacks preferred skills: {', '.join(missing_pref)}.")

    if not experience:
        weaknesses.append("Lacks formal professional experience or internships.")
    elif len(experience) == 1:
        weaknesses.append("Has limited industry exposure (only 1 experience entry).")

    if not weaknesses:
        weaknesses.append("No major weaknesses identified.")

    if ats_score >= 80:
        rec_text = "Strong Hire"
    elif ats_score >= 60:
        rec_text = "Hire"
    elif ats_score >= 40:
        rec_text = "Review"
    elif ats_score >= 20:
        rec_text = "Weak Match"
    else:
        rec_text = "Reject Recommendation"

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "skill_gaps": skill_gaps,
        "recommendation": rec_text
    }


def _build_llm_prompt(
    profile: CandidateProfile,
    skills: list,
    education: list,
    experience: list,
    projects: list,
    job: Job
) -> str:
    candidate_info = {
        "full_name": profile.full_name,
        "headline": profile.headline,
        "summary": profile.summary,
        "skills": [s.skill_name for s in skills if s.skill_name],
        "education": [
            {
                "degree": e.degree,
                "institution": e.institution,
                "department": e.department,
                "cgpa": e.cgpa,
                "end_year": e.end_year
            }
            for e in education
        ],
        "experience": [
            {
                "company_name": exp.company_name,
                "job_title": exp.job_title,
                "employment_type": exp.employment_type,
                "description": exp.description
            }
            for exp in experience
        ],
        "projects": [
            {
                "project_name": p.project_name,
                "description": p.description,
                "technologies": p.technologies
            }
            for p in projects
        ]
    }

    job_info = {
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
        "criteria": job.criteria
    }

    prompt = f"""
You are an expert ATS (Applicant Tracking System) recruiter. Review the candidate details against the job requirements and generate a recommendation report.

Job Requirements:
{json.dumps(job_info, indent=2)}

Candidate Details:
{json.dumps(candidate_info, indent=2)}

You MUST respond with a valid JSON object ONLY. Do not include markdown code block formatting (such as ```json) or any conversational text. The JSON object must match this schema:
{{
  "strengths": ["string", ...],
  "weaknesses": ["string", ...],
  "skill_gaps": ["string", ...],
  "hiring_recommendation": "string",
  "career_recommendation": "string"
}}

Where:
- "strengths": A list of candidate's technical or professional strengths relative to the job.
- "weaknesses": A list of areas for improvement or limitations relative to the job.
- "skill_gaps": A list of job required skills that the candidate is missing.
- "hiring_recommendation": A short summary recommendation. It MUST be EXACTLY ONE of the following options: "Strong Hire", "Hire", "Review", "Weak Match", or "Reject Recommendation".
- "career_recommendation": Detailed career coaching feedback for the candidate, e.g. "Candidate demonstrates strong Machine Learning and NLP skills through project work and technical experience. Additional exposure to backend deployment technologies such as Docker and FastAPI would strengthen suitability for production AI roles."
"""
    return prompt


def _parse_llm_json(raw_text: str) -> Dict[str, Any]:
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    
    try:
        data = json.loads(text)
        return {
            "strengths": data.get("strengths", []),
            "weaknesses": data.get("weaknesses", []),
            "skill_gaps": data.get("skill_gaps", []),
            "hiring_recommendation": data.get("hiring_recommendation") or data.get("recommendation") or "Review",
            "career_recommendation": data.get("career_recommendation") or "Keep updating your profile to receive better recommendations."
        }
    except Exception as e:
        logger.error(f"Failed to parse LLM JSON: {e}. Raw text: {raw_text}")
        return {
            "strengths": ["Failed to parse LLM recommendations."],
            "weaknesses": [],
            "skill_gaps": [],
            "hiring_recommendation": "Review",
            "career_recommendation": "Try updating your profile details to obtain better recommendations."
        }


def _generate_gemini_recommendations(
    profile: CandidateProfile,
    skills: list,
    education: list,
    experience: list,
    projects: list,
    job: Job,
    api_key: str
) -> Dict[str, Any]:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = _build_llm_prompt(profile, skills, education, experience, projects, job)
    logger.info(f"Generating recommendations via Gemini for candidate {profile.user_id}")
    response = model.generate_content(prompt)
    logger.info(f"Gemini API Response text: {response.text}")
    return _parse_llm_json(response.text)


def _generate_openai_recommendations(
    profile: CandidateProfile,
    skills: list,
    education: list,
    experience: list,
    projects: list,
    job: Job,
    api_key: str
) -> Dict[str, Any]:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    prompt = _build_llm_prompt(profile, skills, education, experience, projects, job)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )
    return _parse_llm_json(response.choices[0].message.content)
