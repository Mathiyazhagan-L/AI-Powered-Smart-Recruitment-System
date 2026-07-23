from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Time
from core.base import Base

class InterviewSchedule(Base):
    __tablename__ = "interview_schedules"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    candidate_code = Column(String(50), nullable=True, index=True)
    job_id = Column(Integer, nullable=False, index=True)
    recruiter_id = Column(Integer, nullable=False, index=True)
    hr_id = Column(Integer, nullable=True, index=True) # Optional, HR who approved
    
    interview_title = Column(String(255), nullable=False)
    interviewer_name = Column(String(255), nullable=True)
    interviewer_email = Column(String(255), nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=60)
    
    interview_date = Column(Date, nullable=False)
    interview_time = Column(Time, nullable=False)
    interview_mode = Column(String(50), nullable=False, default="Online") # Online, Offline, Hybrid
    meeting_link = Column(String(500), nullable=True)
    interview_notes = Column(Text, nullable=True)
    
    status = Column(String(50), nullable=False, default="Scheduled", index=True) # Scheduled, Confirmed, Completed, Cancelled, Rescheduled
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
