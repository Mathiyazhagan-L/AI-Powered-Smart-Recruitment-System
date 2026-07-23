from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CandidateEducationCreate(BaseModel):
    user_id: int
    degree: str = Field(..., max_length=255)
    institution: str = Field(..., max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    start_year: int = Field(..., ge=1900)
    end_year: Optional[int] = Field(None, ge=1900)
    description: Optional[str] = None

    @field_validator("end_year")
    @classmethod
    def validate_end_year(cls, value, info):
        start_year = info.data.get("start_year")
        if value is not None and start_year is not None and value < start_year:
            raise ValueError("end_year must be equal to or greater than start_year")
        return value

    model_config = {"from_attributes": True}


class CandidateEducationUpdate(BaseModel):
    degree: Optional[str] = Field(None, max_length=255)
    institution: Optional[str] = Field(None, max_length=255)
    department: Optional[str] = Field(None, max_length=255)
    cgpa: Optional[float] = Field(None, ge=0.0, le=10.0)
    start_year: Optional[int] = Field(None, ge=1900)
    end_year: Optional[int] = Field(None, ge=1900)
    description: Optional[str] = None

    @field_validator("end_year")
    @classmethod
    def validate_end_year(cls, value, info):
        start_year = info.data.get("start_year")
        if value is not None and start_year is not None and value < start_year:
            raise ValueError("end_year must be equal to or greater than start_year")
        return value

    model_config = {"from_attributes": True}


class CandidateEducationResponse(BaseModel):
    id: int
    user_id: int
    degree: str
    institution: str
    department: Optional[str]
    cgpa: Optional[float]
    start_year: Optional[int]
    end_year: Optional[int]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
