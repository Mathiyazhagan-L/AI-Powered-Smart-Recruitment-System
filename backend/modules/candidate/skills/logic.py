
from modules.candidate.profile.logic import trigger_profile_completion_update
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from .model import CandidateSkill
from .schema import CandidateSkillCreate, CandidateSkillUpdate


def add_skill(db: Session, data: CandidateSkillCreate) -> CandidateSkill:
    skill = CandidateSkill(
        user_id=data.user_id,
        skill_name=data.skill_name,
        skill_category=data.skill_category,
        proficiency_level=data.proficiency_level,
        years_of_experience=data.years_of_experience,
    )
    db.add(skill)
    db.commit()
    db.refresh(skill)
    trigger_profile_completion_update(db, skill.user_id)
    return skill


def get_skills_by_user(db: Session, user_id: int) -> List[CandidateSkill]:
    return (
        db.query(CandidateSkill)
        .filter(CandidateSkill.user_id == user_id)
        .order_by(CandidateSkill.skill_name.asc())
        .all()
    )


def get_skill_by_id(db: Session, skill_id: int) -> Optional[CandidateSkill]:
    return db.query(CandidateSkill).filter(CandidateSkill.id == skill_id).first()


def update_skill(db: Session, skill: CandidateSkill, data: CandidateSkillUpdate) -> CandidateSkill:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(skill, key, value)

    skill.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(skill)
    trigger_profile_completion_update(db, skill.user_id)
    return skill


def delete_skill(db: Session, skill: CandidateSkill) -> bool:
    user_id = skill.user_id
    db.delete(skill)
    db.commit()
    trigger_profile_completion_update(db, user_id)
    return True
