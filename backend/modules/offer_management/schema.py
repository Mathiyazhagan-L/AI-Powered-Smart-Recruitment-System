from datetime import datetime, date
from pydantic import BaseModel
from typing import Optional

class OfferCreate(BaseModel):
    candidate_id: int
    job_id: int
    recruiter_id: int
    hr_id: Optional[int] = None
    company_name: str
    position_title: str
    department: str
    employment_type: str
    package_amount: str
    joining_date: date
    location: str
    reporting_manager: str
    offer_expiry_date: Optional[date] = None
    notes: Optional[str] = None

class OfferUpdate(BaseModel):
    company_name: Optional[str] = None
    position_title: Optional[str] = None
    department: Optional[str] = None
    employment_type: Optional[str] = None
    package_amount: Optional[str] = None
    joining_date: Optional[date] = None
    location: Optional[str] = None
    reporting_manager: Optional[str] = None
    offer_expiry_date: Optional[date] = None
    notes: Optional[str] = None

class OfferResponse(BaseModel):
    id: int
    candidate_id: int
    candidate_code: Optional[str] = None
    job_id: int
    recruiter_id: int
    hr_id: Optional[int] = None
    offer_reference: str
    offer_version: int
    company_name: str
    candidate_name: str
    position_title: str
    department: str
    employment_type: str
    package_amount: str
    joining_date: date
    joined_date: Optional[date] = None
    location: str
    reporting_manager: str
    offer_status: str
    candidate_response: str
    joining_status: str
    response_date: Optional[datetime] = None
    offer_pdf_path: Optional[str] = None
    offer_expiry_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
