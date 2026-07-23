from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from core.base import Base

class HRReview(Base):
    __tablename__ = "hr_reviews"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    candidate_code = Column(String(50), nullable=True, index=True)
    job_id = Column(Integer, nullable=False, index=True)
    recruiter_id = Column(Integer, nullable=False, index=True)
    
    # Analytics Snapshots
    aptitude_score = Column(Float, nullable=True)
    coding_score = Column(Float, nullable=True)
    interview_score = Column(Float, nullable=True)
    github_score = Column(Float, nullable=True)
    ats_score = Column(Float, nullable=True)
    overall_score = Column(Float, nullable=True)
    
    # Review Details
    review_status = Column(String(50), nullable=False, default="Pending", index=True) # Pending, Approved, Rejected, Hold
    comments = Column(Text, nullable=True)
    reviewed_by = Column(Integer, nullable=True) # Maps to User ID
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
