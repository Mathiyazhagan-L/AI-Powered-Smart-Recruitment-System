from datetime import date, time, datetime
from typing import Optional
from pydantic import BaseModel, Field

class InterviewScheduleCreate(BaseModel):
    candidate_id: int
    job_id: int
    recruiter_id: int
    hr_id: Optional[int] = None
    interview_title: str = Field(..., max_length=255)
    interviewer_name: Optional[str] = Field(None, max_length=255)
    interviewer_email: Optional[str] = Field(None, max_length=255)
    duration_minutes: int = Field(60, description="Duration in minutes")
    interview_date: date
    interview_time: time
    interview_mode: str = Field("Online", description="Online, Offline, Hybrid")
    meeting_link: Optional[str] = Field(None, max_length=500)
    interview_notes: Optional[str] = None

class InterviewScheduleUpdate(BaseModel):
    interview_title: Optional[str] = None
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[str] = None
    duration_minutes: Optional[int] = None
    interview_date: Optional[date] = None
    interview_time: Optional[time] = None
    interview_mode: Optional[str] = None
    meeting_link: Optional[str] = None
    interview_notes: Optional[str] = None
    status: Optional[str] = None

class InterviewStatusUpdate(BaseModel):
    status: str = Field(..., description="Scheduled, Confirmed, Completed, Cancelled, Rescheduled, Selected, Waiting, Rejected")
    notes: Optional[str] = None

class InterviewScheduleResponse(BaseModel):
    id: int
    candidate_id: int
    candidate_code: Optional[str] = None
    job_id: int
    recruiter_id: int
    hr_id: Optional[int] = None
    
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    
    interview_title: str
    interviewer_name: Optional[str] = None
    interviewer_email: Optional[str] = None
    duration_minutes: int
    
    interview_date: date
    interview_time: time
    interview_mode: str
    meeting_link: Optional[str] = None
    interview_notes: Optional[str] = None
    
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
