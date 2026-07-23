from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class CandidateSkillCreate(BaseModel):
    user_id: int
    skill_name: str = Field(..., max_length=255)
    skill_category: Optional[str] = Field(None, max_length=255)
    proficiency_level: str = Field(..., max_length=50)
    years_of_experience: int = Field(..., ge=0)

    @field_validator("proficiency_level")
    @classmethod
    def validate_proficiency(cls, value):
        known_levels = {"beginner", "intermediate", "advanced", "expert"}
        normalized = value.strip().lower()
        if normalized not in known_levels:
            raise ValueError(f"proficiency_level must be one of {sorted(known_levels)}")
        return normalized

    model_config = {"from_attributes": True}


class CandidateSkillUpdate(BaseModel):
    skill_name: Optional[str] = Field(None, max_length=255)
    skill_category: Optional[str] = Field(None, max_length=255)
    proficiency_level: Optional[str] = Field(None, max_length=50)
    years_of_experience: Optional[int] = Field(None, ge=0)

    @field_validator("proficiency_level")
    @classmethod
    def validate_proficiency(cls, value):
        if value is None:
            return value
        known_levels = {"beginner", "intermediate", "advanced", "expert"}
        normalized = value.strip().lower()
        if normalized not in known_levels:
            raise ValueError(f"proficiency_level must be one of {sorted(known_levels)}")
        return normalized

    model_config = {"from_attributes": True}


class CandidateSkillResponse(BaseModel):
    id: int
    user_id: int
    skill_name: str
    skill_category: Optional[str]
    proficiency_level: Optional[str]
    years_of_experience: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
