from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class EmailLogResponse(BaseModel):
    id: int
    candidate_id: Optional[int] = None
    email_type: str
    recipient_email: str
    generated_subject: Optional[str] = None
    generated_content_json: Optional[str] = None
    generated_html: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class EmailStatsResponse(BaseModel):
    total_sent: int
    total_failed: int
    total_pending: int

class ResendResponse(BaseModel):
    success: bool
    message: str
    log_id: int
