import logging
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from modules.candidate.profile.model import CandidateProfile
from modules.candidate.skills.model import CandidateSkill
from modules.candidate.education.model import CandidateEducation
from modules.candidate.experience.model import CandidateExperience
from modules.candidate.projects.model import CandidateProject

logger = logging.getLogger(__name__)

def parse_month_year(date_str: str) -> date | None:
    if not date_str:
        return None
    try:
        # Tries to parse "Jul 2025"
        dt = datetime.strptime(date_str.strip(), "%b %Y")
        return dt.date()
    except ValueError:
        pass
    try:
        # Tries "July 2025"
        dt = datetime.strptime(date_str.strip(), "%B %Y")
        return dt.date()
    except ValueError:
        pass
    try:
        # Tries "2025"
        dt = datetime.strptime(date_str.strip(), "%Y")
        return dt.date()
    except ValueError:
        pass
    return None

def autofill_candidate_tables(db: Session, candidate_id: int, parsed_json: dict) -> dict:
    """Populates ATS tables from the parsed resume JSON."""
    counts = {
        "profile": 0,
        "skills": 0,
        "education": 0,
        "experience": 0,
        "projects": 0
    }
    
    try:
        # 1. CandidateProfile
        personal = parsed_json.get("personal", {})
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
        
        # Determine email: prioritize actual account email from users table to prevent duplicate emails
        from modules.auth.model import User
        user = db.query(User).filter(User.id == candidate_id).first()
        email = user.email if user else personal.get("email")
        if not email:
            email = f"candidate_{candidate_id}_noemail@system.local"

        if profile:
            profile.full_name = personal.get("full_name", profile.full_name or "")
            profile.phone = personal.get("phone", profile.phone)
            profile.location = personal.get("location", profile.location)
            profile.linkedin_url = personal.get("linkedin_url", profile.linkedin_url)
            profile.github_url = personal.get("github_url", profile.github_url)
            profile.portfolio_url = personal.get("portfolio_url", profile.portfolio_url)
            profile.summary = parsed_json.get("summary", profile.summary)
        else:
            profile = CandidateProfile(
                user_id=candidate_id,
                full_name=personal.get("full_name", ""),
                email=email,
                phone=personal.get("phone"),
                location=personal.get("location"),
                linkedin_url=personal.get("linkedin_url"),
                github_url=personal.get("github_url"),
                portfolio_url=personal.get("portfolio_url"),
                summary=parsed_json.get("summary")
            )
            db.add(profile)
        counts["profile"] = 1
        
        # 2. CandidateSkill
        existing_skills = {s.skill_name.lower() for s in db.query(CandidateSkill).filter(CandidateSkill.user_id == candidate_id).all()}
        skills_data = parsed_json.get("skills", [])
        for skill_group in skills_data:
            category = skill_group.get("category")
            for skill_name in skill_group.get("skills", []):
                if skill_name.lower() not in existing_skills:
                    db.add(CandidateSkill(
                        user_id=candidate_id,
                        skill_name=skill_name,
                        skill_category=category,
                        proficiency_level=None,  # Nullable now
                        years_of_experience=0
                    ))
                    existing_skills.add(skill_name.lower())
                    counts["skills"] += 1
                    
        # 3. CandidateEducation
        # Wipe and replace to avoid dupes on re-upload
        db.query(CandidateEducation).filter(CandidateEducation.user_id == candidate_id).delete()
        for edu in parsed_json.get("education", []):
            end_year_val = edu.get("graduation_year")
            try:
                end_year = int(end_year_val) if end_year_val else None
            except ValueError:
                end_year = None
                
            cgpa_val = edu.get("cgpa")
            try:
                cgpa = float(cgpa_val) if cgpa_val else None
            except ValueError:
                cgpa = None

            db.add(CandidateEducation(
                user_id=candidate_id,
                degree=edu.get("degree", ""),
                institution=edu.get("college", ""),
                department=edu.get("branch"),
                cgpa=cgpa,
                start_year=None, # Nullable now
                end_year=end_year
            ))
            counts["education"] += 1
            
        # 4. CandidateExperience
        db.query(CandidateExperience).filter(CandidateExperience.user_id == candidate_id).delete()
        for exp in parsed_json.get("experience", []):
            is_intern = exp.get("internship", False)
            emp_type = "Internship" if is_intern else "Professional"
            
            start_date_val = exp.get("start_date")
            start_d = parse_month_year(start_date_val)
            if not start_d:
                # Required field: if not parsed, use 1970 to avoid DB crash
                start_d = date(1970, 1, 1)
                
            end_date_val = exp.get("end_date")
            end_d = parse_month_year(end_date_val)
            
            resp = exp.get("responsibilities", [])
            desc = "\n".join(resp) if resp else None
            
            db.add(CandidateExperience(
                user_id=candidate_id,
                company_name=exp.get("company_name", ""),
                job_title=exp.get("job_title", ""),
                employment_type=emp_type,
                start_date=start_d,
                end_date=end_d,
                currently_working=True if not end_d else False,
                description=desc
            ))
            counts["experience"] += 1
            
        # 5. CandidateProject
        db.query(CandidateProject).filter(CandidateProject.user_id == candidate_id).delete()
        for proj in parsed_json.get("projects", []):
            db.add(CandidateProject(
                user_id=candidate_id,
                project_name=proj.get("project_title", ""),
                description=proj.get("description"),
                technologies=proj.get("technologies_used", []),
                github_url=proj.get("github_link"),
                live_url=proj.get("live_demo_link"),
                start_date=None # Nullable now
            ))
            counts["projects"] += 1
            
        # 6. Recalculate Profile Completion
        db.commit() # commit the related tables first so they can be counted
        
        from modules.candidate.profile.logic import calculate_profile_completion
        if profile:
            profile.profile_completion = calculate_profile_completion(db, candidate_id, profile)
            db.commit()
            db.refresh(profile)
            
            parsed_github_url = personal.get("github_url")
            if parsed_github_url:
                try:
                    from modules.github_intelligence.service import trigger_background_github_evaluation
                    trigger_background_github_evaluation(profile.id, parsed_github_url)
                except Exception as e:
                    logger.error(f"Failed to trigger background GitHub evaluation on autofill for candidate {candidate_id}: {e}")
            
        logger.info(f"AutoFill completed for candidate {candidate_id}: {counts}")
        return counts
        
    except Exception as e:
        db.rollback()
        logger.error(f"AutoFill failed for candidate {candidate_id}: {e}")
        raise e
