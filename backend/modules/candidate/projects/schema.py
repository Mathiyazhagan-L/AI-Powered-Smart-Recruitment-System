from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CandidateProjectCreate(BaseModel):
    user_id: int
    project_name: str = Field(..., max_length=255)
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    github_url: Optional[str] = Field(None, max_length=500)
    live_url: Optional[str] = Field(None, max_length=500)
    start_date: date
    end_date: Optional[date] = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, value, info):
        start_date = info.data.get("start_date")
        if value is not None and start_date and value < start_date:
            raise ValueError("end_date must be the same as or after start_date")
        return value

    model_config = {"from_attributes": True}


class CandidateProjectUpdate(BaseModel):
    project_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    technologies: Optional[List[str]] = None
    github_url: Optional[str] = Field(None, max_length=500)
    live_url: Optional[str] = Field(None, max_length=500)
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, value, info):
        start_date = info.data.get("start_date")
        if value is not None and start_date and value < start_date:
            raise ValueError("end_date must be the same as or after start_date")
        return value

    model_config = {"from_attributes": True}


class CandidateProjectResponse(BaseModel):
    id: int
    user_id: int
    project_name: str
    description: Optional[str]
    technologies: List[str]
    github_url: Optional[str]
    live_url: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
