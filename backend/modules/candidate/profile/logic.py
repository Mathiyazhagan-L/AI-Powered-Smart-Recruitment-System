from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from .model import CandidateProfile
from .schema import CandidateProfileCreate, CandidateProfileUpdate
from modules.candidate.skills.model import CandidateSkill
from modules.candidate.education.model import CandidateEducation
from modules.candidate.experience.model import CandidateExperience
from modules.resume_parser.model import ResumeParserResult


def calculate_profile_completion(db: Session, user_id: int, data) -> int:
    score = 0
    
    # 1. Basic Details (20% total)
    if getattr(data, "full_name", None) and str(data.full_name).strip() and (getattr(data, "location", None) or getattr(data, "headline", None)):
        score += 20

    # 2. Resume Uploaded (20%)
    resume = db.query(ResumeParserResult).filter(ResumeParserResult.candidate_id == user_id).first()
    if resume:
        score += 20

    # 3. Education (15%)
    edu_count = db.query(CandidateEducation).filter(CandidateEducation.user_id == user_id).count()
    if edu_count > 0:
        score += 15

    # 4. Experience (15%)
    exp_count = db.query(CandidateExperience).filter(CandidateExperience.user_id == user_id).count()
    if exp_count > 0:
        score += 15

    # 5. Skills (15%)
    skill_count = db.query(CandidateSkill).filter(CandidateSkill.user_id == user_id).count()
    if skill_count > 0:
        score += 15

    # 6. Projects (15%)
    from modules.candidate.projects.model import CandidateProject
    proj_count = db.query(CandidateProject).filter(CandidateProject.user_id == user_id).count()
    if proj_count > 0:
        score += 15

    # Cap at 100%
    return min(100, score)


def create_profile(db: Session, data: CandidateProfileCreate) -> CandidateProfile:
    existing_profile = (
        db.query(CandidateProfile)
        .filter((CandidateProfile.email == data.email) | (CandidateProfile.user_id == data.user_id))
        .first()
    )
    if existing_profile:
        github_changed = existing_profile.github_url != data.github_url
        
        for key, value in data.model_dump().items():
            setattr(existing_profile, key, value)
        existing_profile.profile_completion = calculate_profile_completion(db, data.user_id, existing_profile)
        existing_profile.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_profile)
        
        if github_changed and existing_profile.github_url:
            from modules.github_intelligence.service import trigger_background_github_evaluation
            trigger_background_github_evaluation(existing_profile.id, existing_profile.github_url)
        elif github_changed and not existing_profile.github_url:
            existing_profile.github_score = None
            existing_profile.github_summary = None
            existing_profile.github_last_updated = None
            existing_profile.github_repositories = None
            existing_profile.github_stars = None
            existing_profile.github_followers = None
            existing_profile.github_languages = None
            db.commit()
            db.refresh(existing_profile)
            
        return existing_profile

    profile = CandidateProfile(
        user_id=data.user_id,
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
        date_of_birth=data.date_of_birth,
        gender=data.gender,
        location=data.location,
        headline=data.headline,
        summary=data.summary,
        linkedin_url=data.linkedin_url,
        github_url=data.github_url,
        portfolio_url=data.portfolio_url,
        profile_image=data.profile_image,
        profile_completion=calculate_profile_completion(db, data.user_id, data),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    # Auto-generate candidate code based on id
    profile.candidate_code = f"AIH{profile.id:04d}"
    db.commit()
    db.refresh(profile)
    
    if profile.github_url:
        from modules.github_intelligence.service import trigger_background_github_evaluation
        trigger_background_github_evaluation(profile.id, profile.github_url)
        
    return profile


def get_profile(db: Session, profile_id: int) -> Optional[CandidateProfile]:
    return db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()


def get_profile_by_user(db: Session, user_id: int) -> Optional[CandidateProfile]:
    return db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()


def update_profile(db: Session, profile: CandidateProfile, data: CandidateProfileUpdate) -> CandidateProfile:
    update_data = data.model_dump(exclude_unset=True)
    
    github_changed = False
    if "github_url" in update_data:
        github_changed = profile.github_url != update_data["github_url"]

    if "email" in update_data:
        existing_profile = (
            db.query(CandidateProfile)
            .filter(CandidateProfile.email == update_data["email"], CandidateProfile.id != profile.id)
            .first()
        )
        if existing_profile:
            raise ValueError("A different candidate profile already uses this email.")

    for key, value in update_data.items():
        setattr(profile, key, value)

    old_completion = profile.profile_completion
    profile.profile_completion = calculate_profile_completion(db, profile.user_id, profile)
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)

    if github_changed and profile.github_url:
        from modules.github_intelligence.service import trigger_background_github_evaluation
        trigger_background_github_evaluation(profile.id, profile.github_url)
    elif github_changed and not profile.github_url:
        profile.github_score = None
        profile.github_summary = None
        profile.github_last_updated = None
        profile.github_repositories = None
        profile.github_stars = None
        profile.github_followers = None
        profile.github_languages = None
        db.commit()
        db.refresh(profile)

    # Trigger Profile Completion Email if hitting 100% for the first time
    if old_completion < 100 and profile.profile_completion == 100:
        try:
            from modules.email_automation.triggers import trigger_email
            trigger_email(
                event_type="Candidate Registration",
                candidate_id=profile.user_id,
                context={
                    "extra_details": "Congratulations! Your profile is now 100% complete. You are ready to apply for jobs and get recommended to top recruiters."
                },
                db=db
            )
        except Exception as e:
            print(f"Failed to send profile completion email: {e}")

    return profile


def delete_profile(db: Session, profile: CandidateProfile) -> bool:
    db.delete(profile)
    db.commit()
    return True

def trigger_profile_completion_update(db: Session, user_id: int):
    """Utility to recalculate profile completion when child entities are modified."""
    profile = get_profile_by_user(db, user_id)
    if profile:
        old_completion = profile.profile_completion
        profile.profile_completion = calculate_profile_completion(db, user_id, profile)
        db.commit()
        db.refresh(profile)
        
        # Trigger Profile Completion Email if hitting 100% for the first time
        if old_completion < 100 and profile.profile_completion == 100:
            try:
                from modules.email_automation.triggers import trigger_email
                trigger_email(
                    event_type="Candidate Registration",
                    candidate_id=user_id,
                    context={
                        "extra_details": "Congratulations! Your profile is now 100% complete. You are ready to apply for jobs and get recommended to top recruiters."
                    },
                    db=db
                )
            except Exception as e:
                print(f"Failed to send profile completion email: {e}")
                
        return profile.profile_completion
    return 0
