from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Float, JSON
from core.base import Base


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    candidate_code = Column(String(50), unique=True, index=True, nullable=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    headline = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    leetcode_url = Column(String(500), nullable=True)
    hackerrank_url = Column(String(500), nullable=True)
    profile_image = Column(String(500), nullable=True)

    # Educational Details
    school_name = Column(String(255), nullable=True)
    twelfth_percentage = Column(Float, nullable=True)
    college_name = Column(String(255), nullable=True)
    cgpa = Column(Float, nullable=True)
    profile_completion = Column(Integer, default=0, nullable=False)
    candidate_status = Column(String(50), default="NEW", nullable=False)
    aptitude_score = Column(Integer, nullable=True)
    assessment_date = Column(DateTime, nullable=True)
    assessment_status = Column(String(20), nullable=True)
    interview_score = Column(Float, nullable=True)
    interview_date = Column(DateTime, nullable=True)
    interview_status = Column(String(50), nullable=True)
    
    # GitHub Intelligence Engine Columns
    github_score = Column(Integer, nullable=True)
    github_summary = Column(JSON, nullable=True)
    github_last_updated = Column(DateTime, nullable=True)
    github_repositories = Column(Integer, nullable=True)
    github_stars = Column(Integer, nullable=True)
    github_followers = Column(Integer, nullable=True)
    github_languages = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
