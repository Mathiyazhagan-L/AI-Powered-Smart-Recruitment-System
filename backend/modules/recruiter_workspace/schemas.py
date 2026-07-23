from pydantic import BaseModel, Field
from typing import Optional, List, Any
import datetime

# --- Recruiter Notes ---
class RecruiterNoteBase(BaseModel):
    title: Optional[str] = None
    note_type: str = "General"
    content: str
    visibility: str = "Team"
    rating: Optional[int] = Field(None, ge=1, le=5)
    tags: Optional[str] = None
    attachments: Optional[Any] = None

class RecruiterNoteCreate(RecruiterNoteBase):
    candidate_id: int

class RecruiterNoteUpdate(RecruiterNoteBase):
    pass

class RecruiterNoteResponse(RecruiterNoteBase):
    id: int
    candidate_id: int
    recruiter_id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Candidate Timeline ---
class CandidateTimelineEventBase(BaseModel):
    event_type: str
    description: str
    triggered_by: str
    related_entity_id: Optional[int] = None
    metadata_json: Optional[Any] = None

class CandidateTimelineEventCreate(CandidateTimelineEventBase):
    candidate_id: int

class CandidateTimelineEventResponse(CandidateTimelineEventBase):
    id: int
    candidate_id: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- Recruiter Audit Log ---
class RecruiterAuditLogBase(BaseModel):
    action_type: str
    description: str
    target_entity_type: str
    target_entity_id: int
    metadata_json: Optional[Any] = None

class RecruiterAuditLogCreate(RecruiterAuditLogBase):
    pass

class RecruiterAuditLogResponse(RecruiterAuditLogBase):
    id: int
    recruiter_id: Optional[int] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True
