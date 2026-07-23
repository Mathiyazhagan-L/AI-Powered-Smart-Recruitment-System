from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from core.base import Base


class CandidateEducation(Base):
    __tablename__ = "candidate_education"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    degree = Column(String(255), nullable=False)
    institution = Column(String(255), nullable=False)
    department = Column(String(255), nullable=True)
    cgpa = Column(Float, nullable=True)
    start_year = Column(Integer, nullable=True)
    end_year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
