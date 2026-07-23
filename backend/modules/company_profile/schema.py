from pydantic import BaseModel, EmailStr
from typing import Optional


# ==========================================
# CREATE COMPANY
# ==========================================

class CompanyCreate(BaseModel):

    company_name: str

    company_email: EmailStr

    company_phone: Optional[str] = None

    website: str

    industry: Optional[str] = None

    company_size: Optional[str] = None

    location: Optional[str] = None

    description: Optional[str] = None

    linkedin_url: Optional[str] = None

    logo_url: Optional[str] = None

    gst_number: Optional[str] = None


# ==========================================
# UPDATE COMPANY
# ==========================================

class CompanyUpdate(BaseModel):

    company_name: Optional[str] = None

    company_email: Optional[EmailStr] = None

    company_phone: Optional[str] = None

    website: Optional[str] = None

    industry: Optional[str] = None

    company_size: Optional[str] = None

    location: Optional[str] = None

    description: Optional[str] = None

    linkedin_url: Optional[str] = None

    logo_url: Optional[str] = None

    gst_number: Optional[str] = None


# ==========================================
# RESPONSE
# ==========================================

class CompanyResponse(BaseModel):

    id: int

    user_id: int

    company_name: str

    company_email: str

    website: Optional[str] = None

    verification_status: str

    is_email_verified: bool

    company_code: Optional[str] = None

    model_config = {
        "from_attributes": True,
    }