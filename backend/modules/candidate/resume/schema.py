from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class CandidateResumeCreate(BaseModel):
    user_id: int
    resume_name: str = Field(..., max_length=255)
    resume_path: str = Field(..., max_length=1000)
    file_type: str = Field(..., max_length=50)
    file_size: int = Field(..., ge=0)
    ats_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    parsed_status: bool = False

    @field_validator("resume_path")
    @classmethod
    def normalize_path(cls, value):
        return value.strip()

    model_config = {"from_attributes": True}


class CandidateResumeResponse(BaseModel):
    id: int
    user_id: int
    resume_name: str
    resume_path: str
    file_type: str
    file_size: int
    ats_score: Optional[float]
    parsed_status: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
