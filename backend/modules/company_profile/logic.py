from sqlalchemy.orm import Session
from urllib.parse import urlparse
import datetime

from .model import CompanyProfile


# ==========================================
# EXTRACT DOMAIN
# ==========================================

def extract_domain(url: str):

    parsed = urlparse(url)

    domain = parsed.netloc.lower()

    if domain.startswith("www."):
        domain = domain.replace(
            "www.",
            ""
        )

    return domain


# ==========================================
# EMAIL DOMAIN
# ==========================================

def get_email_domain(email: str):

    return email.split("@")[1].lower()


# ==========================================
# VERIFY COMPANY DOMAIN
# ==========================================

def verify_company_domain(
    company_email: str,
    website: str
):

    email_domain = get_email_domain(
        company_email
    )

    website_domain = extract_domain(
        website
    )

    return email_domain == website_domain


# ==========================================
# CREATE COMPANY
# ==========================================

def create_company(
    db: Session,
    user_id: int,
    data
):

    is_verified = verify_company_domain(
        data.company_email,
        data.website
    )

    company = CompanyProfile(

        user_id=user_id,

        company_name=data.company_name,

        company_email=data.company_email,

        company_phone=data.company_phone,

        website=data.website,

        industry=data.industry,

        company_size=data.company_size,

        location=data.location,

        description=data.description,

        linkedin_url=data.linkedin_url,

        logo_url=data.logo_url,

        gst_number=data.gst_number,

        is_email_verified=is_verified,

        verification_status=(
            "Verified"
            if is_verified
            else "Pending"
        )
    )

    db.add(company)

    db.commit()

    db.refresh(company)

    return company


# ==========================================
# GET COMPANY
# ==========================================

def get_company(
    db: Session,
    company_id: int
):

    return (
        db.query(
            CompanyProfile
        )
        .filter(
            CompanyProfile.id == company_id
        )
        .first()
    )


# ==========================================
# UPDATE COMPANY
# ==========================================

def update_company(
    db: Session,
    company,
    data
):

    update_data = data.model_dump(
        exclude_unset=True
    )

    for key, value in update_data.items():

        setattr(
            company,
            key,
            value
        )

    company.updated_at = (
        datetime.datetime.utcnow()
    )

    db.commit()

    db.refresh(company)

    return company


def is_company_profile_complete(profile):
    required_fields = [
        profile.company_name,
        profile.company_email,
        profile.website_url,
        profile.industry,
        profile.location,
        profile.company_description
    ]

    return all(
        value is not None and str(value).strip()
        for value in required_fields
    )