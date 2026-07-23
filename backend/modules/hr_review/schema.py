from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class HRReviewCreate(BaseModel):
    candidate_id: int
    job_id: int
    recruiter_id: int
    comments: Optional[str] = None

class HRReviewUpdate(BaseModel):
    review_status: Optional[str] = Field(None, description="Approved, Rejected, Hold")
    status: Optional[str] = None
    comments: Optional[str] = None
    notes: Optional[str] = None
    reviewed_by: Optional[int] = None

class HRReviewResponse(BaseModel):
    id: int
    candidate_id: int
    candidate_code: Optional[str] = None
    job_id: int
    recruiter_id: int
    
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    ats: Optional[float] = None
    tech: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    
    aptitude_score: Optional[float] = None
    coding_score: Optional[float] = None
    interview_score: Optional[float] = None
    github_score: Optional[float] = None
    ats_score: Optional[float] = None
    overall_score: Optional[float] = None
    
    review_status: str
    comments: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}
