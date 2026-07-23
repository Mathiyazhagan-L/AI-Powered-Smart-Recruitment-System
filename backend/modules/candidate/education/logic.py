
from modules.candidate.profile.logic import trigger_profile_completion_update
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from .model import CandidateEducation
from .schema import (
    CandidateEducationCreate,
    CandidateEducationUpdate,
)


def add_education(db: Session, data: CandidateEducationCreate) -> CandidateEducation:
    existing = (
        db.query(CandidateEducation)
        .filter(
            CandidateEducation.user_id == data.user_id,
            CandidateEducation.degree == data.degree,
            CandidateEducation.institution == data.institution,
        )
        .first()
    )
    if existing:
        raise ValueError("Education record already exists for this candidate")

    education = CandidateEducation(
        user_id=data.user_id,
        degree=data.degree,
        institution=data.institution,
        department=data.department,
        cgpa=data.cgpa,
        start_year=data.start_year,
        end_year=data.end_year,
        description=data.description,
    )
    db.add(education)
    db.commit()
    db.refresh(education)
    trigger_profile_completion_update(db, education.user_id)
    return education


def get_education_by_user(db: Session, user_id: int) -> List[CandidateEducation]:
    return (
        db.query(CandidateEducation)
        .filter(CandidateEducation.user_id == user_id)
        .order_by(CandidateEducation.start_year.desc())
        .all()
    )


def get_education_by_id(db: Session, education_id: int) -> Optional[CandidateEducation]:
    return db.query(CandidateEducation).filter(CandidateEducation.id == education_id).first()


def update_education(
    db: Session,
    education: CandidateEducation,
    data: CandidateEducationUpdate,
) -> CandidateEducation:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(education, key, value)

    education.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(education)
    trigger_profile_completion_update(db, education.user_id)
    return education


def delete_education(db: Session, education: CandidateEducation) -> bool:
    user_id = education.user_id
    db.delete(education)
    db.commit()
    trigger_profile_completion_update(db, user_id)
    return True
