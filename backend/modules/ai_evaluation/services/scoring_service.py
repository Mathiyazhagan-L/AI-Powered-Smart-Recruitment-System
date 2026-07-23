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

logger = logging.getLogger(__name__)


def calculate_ats_score(candidate_id: int, job_id: int, db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Calculates the ATS Score based on the formula:
    - Skills Match = 40%
    - Experience Match = 30%
    - Education Match = 15%
    - Projects Match = 15%
    """
    if db is None:
        with SessionLocal() as session:
            return _calculate_ats_score_impl(session, candidate_id, job_id)
    return _calculate_ats_score_impl(db, candidate_id, job_id)


def _calculate_ats_score_impl(db: Session, candidate_id: int, job_id: int) -> Dict[str, Any]:
    # 1. Fetch Job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job with ID {job_id} not found for ATS scoring.")
        return {
            "ats_score": 0,
            "integrity_score": 100,
            "score_breakdown": {
                "skills": 0, "experience": 0, "location": 0, "education": 0,
                "aptitude": 0, "coding": 0, "interview": 0
            }
        }

    # Verify Candidate Profile exists
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile:
        logger.warning(f"Candidate profile with ID {candidate_id} not found for ATS scoring.")
        return {
            "ats_score": 0,
            "integrity_score": 100,
            "score_breakdown": {
                "skills": 0, "experience": 0, "location": 0, "education": 0,
                "aptitude": 0, "coding": 0, "interview": 0
            }
        }

    # ==========================================
    # 1. Skills Score (40% Weight)
    # ==========================================
    cand_skills = db.query(CandidateSkill).filter(CandidateSkill.user_id == candidate_id).all()
    cand_skills_lower = {cs.skill_name.lower().strip() for cs in cand_skills if cs.skill_name}

    import json
    req_skills = job.required_skills or []
    if isinstance(req_skills, str):
        try: req_skills = json.loads(req_skills)
        except Exception: req_skills = [req_skills]

    pref_skills = job.preferred_skills or []
    if isinstance(pref_skills, str):
        try: pref_skills = json.loads(pref_skills)
        except Exception: pref_skills = [pref_skills]

    matched_req = [s for s in req_skills if s and s.lower().strip() in cand_skills_lower]
    matched_pref = [s for s in pref_skills if s and s.lower().strip() in cand_skills_lower]

    req_ratio = len(matched_req) / len(req_skills) if req_skills else 1.0
    pref_ratio = len(matched_pref) / len(pref_skills) if pref_skills else 0.0
    
    if pref_skills:
        skills_score = req_ratio * 30 + pref_ratio * 10
    else:
        skills_score = req_ratio * 40

    # ==========================================
    # 2. Experience Score (25% Weight)
    # ==========================================
    cand_exp = db.query(CandidateExperience).filter(CandidateExperience.user_id == candidate_id).all()
    num_exp = len(cand_exp)
    
    if num_exp == 0: experience_score = 0
    elif num_exp == 1: experience_score = 15
    else: experience_score = 25

    # ==========================================
    # 3. Location Match (10% Weight)
    # ==========================================
    job_loc = (job.location or "").lower().strip()
    cand_loc = (profile.location or "").lower().strip()
    location_score = 0.0
    if job_loc and cand_loc:
        if job_loc in cand_loc or cand_loc in job_loc or job_loc == 'remote':
            location_score = 10.0
        else:
            location_score = 5.0  # Partial score for having a location

    # ==========================================
    # 4. Education Score (10% Weight)
    # ==========================================
    cand_edu = db.query(CandidateEducation).filter(CandidateEducation.user_id == candidate_id).all()
    if not cand_edu:
        education_score = 0.0
    else:
        edu = cand_edu[0]
        base_edu = 5.0
        cgpa_score = 3.0
        if edu.cgpa is not None:
            if edu.cgpa > 5.0:
                cgpa_score = (edu.cgpa / 10.0) * 5.0
            else:
                cgpa_score = (edu.cgpa / 4.0) * 5.0
            cgpa_score = min(5.0, max(0.0, cgpa_score))
        education_score = base_edu + cgpa_score

    # ==========================================
    # 5. Aptitude, Coding, Interview Scores (5% each)
    # ==========================================
    apt_score_raw = profile.aptitude_score or 0.0
    int_score_raw = profile.interview_score or 0.0
    
    # Fetch coding score
    from modules.coding_assessment.models import CodingResult
    coding_res = db.query(CodingResult).filter(CodingResult.candidate_id == candidate_id).order_by(CodingResult.id.desc()).first()
    coding_score_raw = coding_res.total_score if coding_res else 0.0

    aptitude_score = (apt_score_raw / 100.0) * 5.0
    coding_score = (coding_score_raw / 100.0) * 5.0
    interview_score = (int_score_raw / 100.0) * 5.0

    # ==========================================
    # Integrity Score Fetching
    # ==========================================
    from modules.proctoring.models import AssessmentIntegrityResult
    integrity_records = db.query(AssessmentIntegrityResult).filter(AssessmentIntegrityResult.candidate_id == candidate_id).all()
    
    if integrity_records:
        avg_integrity = sum([r.integrity_score for r in integrity_records]) / len(integrity_records)
    else:
        avg_integrity = 100.0  # Default perfect integrity if no assessments taken

    # ==========================================
    # Combine and Round
    # ==========================================
    skills_score_rounded = round(skills_score)
    experience_score_rounded = round(experience_score)
    location_score_rounded = round(location_score)
    education_score_rounded = round(education_score)
    aptitude_score_rounded = round(aptitude_score)
    coding_score_rounded = round(coding_score)
    interview_score_rounded = round(interview_score)
    
    total_score = (skills_score_rounded + experience_score_rounded + location_score_rounded + 
                   education_score_rounded + aptitude_score_rounded + coding_score_rounded + 
                   interview_score_rounded)
    
    total_score = min(100, max(0, total_score))

    # ==========================================
    # TF-IDF Similarity Score (supplementary, not part of core ATS)
    # ==========================================
    tfidf_match_percentage = 0.0
    try:
        from modules.ai_evaluation.services.tfidf_matching_service import calculate_tfidf_skill_match
        tfidf_res = calculate_tfidf_skill_match(candidate_id=candidate_id, job_id=job_id, db=db)
        tfidf_match_percentage = tfidf_res.get("tfidf_match_percentage", 0.0)
    except Exception as e:
        logger.warning(f"TF-IDF matching failed during ATS scoring for candidate {candidate_id}: {e}")

    return {
        "ats_score": total_score,
        "integrity_score": round(avg_integrity),
        "tfidf_match_percentage": tfidf_match_percentage,
        "score_breakdown": {
            "skills": skills_score_rounded,
            "experience": experience_score_rounded,
            "location": location_score_rounded,
            "education": education_score_rounded,
            "aptitude": aptitude_score_rounded,
            "coding": coding_score_rounded,
            "interview": interview_score_rounded
        }
    }

