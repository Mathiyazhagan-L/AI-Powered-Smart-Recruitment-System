from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CandidateExperienceCreate(BaseModel):
    user_id: int
    company_name: str = Field(..., max_length=255)
    job_title: str = Field(..., max_length=255)
    employment_type: str = Field(..., max_length=100)
    start_date: date
    end_date: Optional[date] = None
    currently_working: bool = False
    description: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, value, info):
        start_date = info.data.get("start_date")
        if value is not None and start_date and value < start_date:
            raise ValueError("end_date must be the same as or after start_date")
        return value

    model_config = {"from_attributes": True}


class CandidateExperienceUpdate(BaseModel):
    company_name: Optional[str] = Field(None, max_length=255)
    job_title: Optional[str] = Field(None, max_length=255)
    employment_type: Optional[str] = Field(None, max_length=100)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currently_working: Optional[bool] = None
    description: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def validate_dates(cls, value, info):
        start_date = info.data.get("start_date")
        if value is not None and start_date and value < start_date:
            raise ValueError("end_date must be the same as or after start_date")
        return value

    model_config = {"from_attributes": True}


class CandidateExperienceResponse(BaseModel):
    id: int
    user_id: int
    company_name: str
    job_title: str
    employment_type: str
    start_date: date
    end_date: Optional[date]
    currently_working: bool
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
