
from modules.candidate.profile.logic import trigger_profile_completion_update
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from .model import CandidateExperience
from .schema import (
    CandidateExperienceCreate,
    CandidateExperienceUpdate,
)


def add_experience(db: Session, data: CandidateExperienceCreate) -> CandidateExperience:
    experience = CandidateExperience(
        user_id=data.user_id,
        company_name=data.company_name,
        job_title=data.job_title,
        employment_type=data.employment_type,
        start_date=data.start_date,
        end_date=data.end_date,
        currently_working=data.currently_working,
        description=data.description,
    )
    db.add(experience)
    db.commit()
    db.refresh(experience)
    trigger_profile_completion_update(db, experience.user_id)
    return experience


def get_experience_by_user(db: Session, user_id: int) -> List[CandidateExperience]:
    return (
        db.query(CandidateExperience)
        .filter(CandidateExperience.user_id == user_id)
        .order_by(CandidateExperience.start_date.desc())
        .all()
    )


def get_experience_by_id(db: Session, experience_id: int) -> Optional[CandidateExperience]:
    return db.query(CandidateExperience).filter(CandidateExperience.id == experience_id).first()


def update_experience(
    db: Session,
    experience: CandidateExperience,
    data: CandidateExperienceUpdate,
) -> CandidateExperience:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(experience, key, value)

    experience.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(experience)
    trigger_profile_completion_update(db, experience.user_id)
    return experience


def delete_experience(db: Session, experience: CandidateExperience) -> bool:
    user_id = experience.user_id
    db.delete(experience)
    db.commit()
    trigger_profile_completion_update(db, user_id)
    return True
