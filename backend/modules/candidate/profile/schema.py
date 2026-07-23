from datetime import date, datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, EmailStr, Field, field_validator


class CandidateProfileCreate(BaseModel):
    user_id: int
    full_name: str = Field(..., max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    headline: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    portfolio_url: Optional[str] = Field(None, max_length=500)
    leetcode_url: Optional[str] = Field(None, max_length=500)
    hackerrank_url: Optional[str] = Field(None, max_length=500)
    profile_image: Optional[str] = Field(None, max_length=500)
    school_name: Optional[str] = Field(None, max_length=255)
    twelfth_percentage: Optional[float] = None
    college_name: Optional[str] = Field(None, max_length=255)
    cgpa: Optional[float] = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value):
        if value is not None and value > date.today():
            raise ValueError("date_of_birth must be in the past")
        return value

    model_config = {"from_attributes": True}


class CandidateProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    headline: Optional[str] = Field(None, max_length=500)
    summary: Optional[str] = None
    linkedin_url: Optional[str] = Field(None, max_length=500)
    github_url: Optional[str] = Field(None, max_length=500)
    portfolio_url: Optional[str] = Field(None, max_length=500)
    leetcode_url: Optional[str] = Field(None, max_length=500)
    hackerrank_url: Optional[str] = Field(None, max_length=500)
    profile_image: Optional[str] = Field(None, max_length=500)
    school_name: Optional[str] = Field(None, max_length=255)
    twelfth_percentage: Optional[float] = None
    college_name: Optional[str] = Field(None, max_length=255)
    cgpa: Optional[float] = None

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value):
        if value is not None and value > date.today():
            raise ValueError("date_of_birth must be in the past")
        return value

    model_config = {"from_attributes": True}


class CandidateProfileResponse(BaseModel):
    id: int
    user_id: int
    candidate_code: Optional[str] = None
    full_name: str
    email: str
    phone: Optional[str]
    date_of_birth: Optional[date]
    gender: Optional[str]
    location: Optional[str]
    headline: Optional[str]
    summary: Optional[str]
    linkedin_url: Optional[str]
    github_url: Optional[str]
    portfolio_url: Optional[str]
    leetcode_url: Optional[str] = None
    hackerrank_url: Optional[str] = None
    profile_image: Optional[str] = None
    school_name: Optional[str] = None
    twelfth_percentage: Optional[float] = None
    college_name: Optional[str] = None
    cgpa: Optional[float] = None
    profile_completion: int
    candidate_status: str
    aptitude_score: Optional[int] = None
    assessment_date: Optional[datetime] = None
    assessment_status: Optional[str] = None
    
    # GitHub Intelligence Response Fields
    github_score: Optional[int] = None
    github_summary: Optional[Dict[str, Any]] = None
    github_last_updated: Optional[datetime] = None
    github_repositories: Optional[int] = None
    github_stars: Optional[int] = None
    github_followers: Optional[int] = None
    github_languages: Optional[List[str]] = None
    
    ats_score: Optional[int] = None
    technical_score: Optional[int] = None
    status: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
