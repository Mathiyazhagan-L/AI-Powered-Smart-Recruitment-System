from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from core.base import Base


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    skill_category = Column(String(255), nullable=True)
    proficiency_level = Column(String(50), nullable=True)
    years_of_experience = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
