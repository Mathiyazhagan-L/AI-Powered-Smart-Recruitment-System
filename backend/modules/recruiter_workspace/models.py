from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float, JSON
from sqlalchemy.orm import relationship
import datetime
from core.base import Base

class RecruiterNote(Base):
    __tablename__ = "recruiter_notes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recruiter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=True)
    note_type = Column(String(100), default="General") # General, Interview Feedback, HR Feedback, Recommendation
    content = Column(Text, nullable=False)
    visibility = Column(String(50), default="Team") # Private, Team
    rating = Column(Integer, nullable=True) # 1-5
    tags = Column(String(255), nullable=True) # Comma separated
    attachments = Column(JSON, nullable=True) # List of file URLs
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class CandidateTimelineEvent(Base):
    __tablename__ = "candidate_timeline"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    event_type = Column(String(100), nullable=False) # e.g. "Registration", "Job Applied", "Interview Passed"
    description = Column(Text, nullable=False)
    triggered_by = Column(String(100), nullable=False) # Candidate, Recruiter, System, AI
    related_entity_id = Column(Integer, nullable=True) # e.g. Job ID, Assessment ID
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RecruiterAuditLog(Base):
    __tablename__ = "recruiter_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False) # "Job Created", "Candidate Moved", "Note Added", etc.
    description = Column(Text, nullable=False)
    target_entity_type = Column(String(100), nullable=False) # "Job", "Candidate", "Offer"
    target_entity_id = Column(Integer, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
