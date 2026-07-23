from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, JSON
from core.base import Base


class CandidateProject(Base):
    __tablename__ = "candidate_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    project_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(JSON, nullable=False)
    github_url = Column(String(500), nullable=True)
    live_url = Column(String(500), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
