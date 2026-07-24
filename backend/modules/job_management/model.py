import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, UniqueConstraint
from core.base import Base

from pydantic import BaseModel, Field, field_validator


# ==========================================
# 1. Pydantic Sub-Schemas
# ==========================================

class SelectionRoundSchema(BaseModel):
    round_number: int = Field(..., description="Order of the round")
    name: str = Field(..., description="Name of the selection round (e.g. Technical Interview)")
    type: str = Field(..., description="Type of the round (e.g. aptitude, coding, hr)")
    description: Optional[str] = Field(None, description="Brief description of round criteria")


class SalaryRulesSchema(BaseModel):
    min_salary: Optional[float] = Field(None, description="Minimum salary range")
    max_salary: Optional[float] = Field(None, description="Maximum salary range")
    currency: str = Field("USD", description="Currency (e.g., USD, INR, EUR)")
    is_negotiable: bool = Field(True, description="Whether the package is negotiable")
    benefits: Optional[List[str]] = Field(default_factory=list, description="List of perks/benefits")


class EligibilityRulesSchema(BaseModel):
    min_cgpa: Optional[float] = Field(None, description="Minimum CGPA/GPA required")
    allowed_degrees: Optional[List[str]] = Field(default_factory=list, description="Degrees eligible (e.g. B.Tech, MCA)")
    max_backlogs: int = Field(0, description="Maximum active backlogs allowed")
    min_experience_years: int = Field(0, description="Minimum years of work experience required")


class ApplicationSettingsSchema(BaseModel):
    allow_late_submissions: bool = Field(False, description="Whether applicants can apply after the deadline")
    max_applications: Optional[int] = Field(None, description="Cap on total applications received")
    ask_cover_letter: bool = Field(False, description="Whether cover letter is mandatory")
    custom_questions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Custom application questions")


# ==========================================
# 2. Main Pydantic Job Schemas
# ==========================================

def get_default_selection_rounds() -> List[Dict[str, Any]]:
    return [
        {
            "round_number": 1,
            "name": "HR Round",
            "type": "hr",
            "description": "HR Interview & Culture Fitment Round"
        }
    ]


def coerce_selection_rounds(v: Any) -> Any:
    if v is None or (isinstance(v, list) and len(v) == 0):
        return get_default_selection_rounds()
    if not isinstance(v, list):
        return v
    new_rounds = []
    for i, item in enumerate(v):
        if isinstance(item, str):
            round_name = item
            r_lower = round_name.lower()
            if "resume" in r_lower or "screening" in r_lower:
                r_type = "screening"
            elif "hr" in r_lower:
                r_type = "hr"
            elif "coding" in r_lower or "technical" in r_lower:
                r_type = "coding"
            else:
                r_type = "aptitude"
            
            new_rounds.append({
                "round_number": i + 1,
                "name": round_name,
                "type": r_type,
                "description": f"{round_name} stage"
            })
        elif isinstance(item, dict):
            if "round_number" not in item:
                item["round_number"] = i + 1
            if "type" not in item:
                r_name = item.get("name", "")
                r_lower = r_name.lower()
                if "resume" in r_lower or "screening" in r_lower:
                    r_type = "screening"
                elif "hr" in r_lower:
                    r_type = "hr"
                elif "coding" in r_lower or "technical" in r_lower:
                    r_type = "coding"
                else:
                    r_type = "aptitude"
                item["type"] = r_type
            new_rounds.append(item)
        else:
            new_rounds.append(item)
    return new_rounds


class JobBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=150, description="Job title")
    description: str = Field(..., min_length=10, description="Detailed job description")
    required_skills: List[str] = Field(default_factory=list, description="List of required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="List of preferred skills")
    experience: str = Field(..., description="Experience level description (e.g. 2-4 years)")
    package: str = Field(..., description="Overall compensation package package description")
    location: str = Field(..., description="Job location (e.g. Remote, New York)")
    criteria: Optional[str] = Field(None, description="Eligibility criteria text")
    openings: int = Field(..., ge=1, description="Number of openings")
    deadline: datetime.datetime = Field(..., description="Application deadline")
    status: str = Field("draft", description="Status (draft, published, closed)")
    
    # Nested configurations
    selection_rounds: List[SelectionRoundSchema] = Field(default_factory=get_default_selection_rounds)
    salary_rules: SalaryRulesSchema = Field(default_factory=SalaryRulesSchema)
    eligibility_rules: EligibilityRulesSchema = Field(default_factory=EligibilityRulesSchema)
    application_settings: ApplicationSettingsSchema = Field(default_factory=ApplicationSettingsSchema)

    @field_validator("selection_rounds", mode="before")
    @classmethod
    def validate_selection_rounds(cls, v: Any) -> Any:
        return coerce_selection_rounds(v)

    @field_validator("deadline")
    @classmethod
    def validate_deadline_future(cls, v: datetime.datetime) -> datetime.datetime:
        # We check validation logic. Usually deadline should be in the future when creating/publishing
        # But we'll make a soft check or handle it in logic validation.
        return v


class JobCreate(JobBase):
    pass


class JobUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    description: Optional[str] = Field(None, min_length=10)
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    experience: Optional[str] = None
    package: Optional[str] = None
    location: Optional[str] = None
    criteria: Optional[str] = None
    openings: Optional[int] = Field(None, ge=1)
    deadline: Optional[datetime.datetime] = None
    status: Optional[str] = None
    
    selection_rounds: Optional[List[SelectionRoundSchema]] = None
    salary_rules: Optional[SalaryRulesSchema] = None
    eligibility_rules: Optional[EligibilityRulesSchema] = None
    application_settings: Optional[ApplicationSettingsSchema] = None

    @field_validator("selection_rounds", mode="before")
    @classmethod
    def validate_selection_rounds(cls, v: Any) -> Any:
        return coerce_selection_rounds(v)


class JobResponse(JobBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {
        "from_attributes": True,
    }


# ==========================================
# 2B. Pydantic Application & Rec Schemas
# ==========================================

class ApplicationBase(BaseModel):
    job_id: int
    candidate_id: int
    status: str = "Applied"
    ats_score: Optional[int] = None
    suitability_prediction: Optional[str] = None
    ranking: Optional[int] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationResponse(ApplicationBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = {
        "from_attributes": True,
    }

class ApplicationStatusUpdate(BaseModel):
    status: str
    reason: Optional[str] = None


class AIRecommendationBase(BaseModel):
    job_id: int
    candidate_id: int
    strengths: List[str]
    weaknesses: List[str]
    skill_gaps: List[str]
    recommendation: str
    career_recommendation: str

class AIRecommendationResponse(AIRecommendationBase):
    id: int
    created_at: datetime.datetime

    model_config = {
        "from_attributes": True,
    }


# ==========================================
# 3. SQLAlchemy Database Model
# ==========================================

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False, index=True)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=False)  # List of strings
    preferred_skills = Column(JSON, nullable=False)  # List of strings
    experience = Column(String(100), nullable=False)
    package = Column(String(200), nullable=False)
    location = Column(String(100), nullable=False, index=True)
    criteria = Column(Text, nullable=True)
    openings = Column(Integer, nullable=False, default=1)
    deadline = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False, default="draft", index=True)
    
    # Store settings/rules as structured JSON
    selection_rounds = Column(JSON, nullable=False)
    salary_rules = Column(JSON, nullable=False)
    eligibility_rules = Column(JSON, nullable=False)
    application_settings = Column(JSON, nullable=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_job_candidate"),)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    status = Column(String(50), nullable=False, default="Applied", index=True)
    ats_score = Column(Integer, nullable=True)
    suitability_prediction = Column(String(50), nullable=True)
    ranking = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_rec_job_candidate"),)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    strengths = Column(JSON, nullable=False)  # List of strings
    weaknesses = Column(JSON, nullable=False)  # List of strings
    skill_gaps = Column(JSON, nullable=False)  # List of strings
    recommendation = Column(Text, nullable=False)  # Hiring recommendation
    career_recommendation = Column(Text, nullable=False)  # Career coaching
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


from modules.email_automation.models import EmailLog


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False)  # email_sent, job_match, system_alert, etc.
    is_read = Column(Integer, default=0) # 0 for False, 1 for True for sqlite compat
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime.datetime

    model_config = {
        "from_attributes": True,
    }


class SavedJob(Base):
    __tablename__ = "saved_jobs"
    __table_args__ = (UniqueConstraint("job_id", "candidate_id", name="uq_savedjob_candidate"),)

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, nullable=False, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class SavedJobResponse(BaseModel):
    id: int
    job_id: int
    candidate_id: int
    created_at: datetime.datetime

    model_config = {
        "from_attributes": True,
    }
