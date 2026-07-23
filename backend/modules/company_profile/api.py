from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from modules.auth.logic import verify_access_token

from .schema import CompanyCreate, CompanyUpdate
from .logic import create_company, get_company, update_company

router = APIRouter(
    prefix="/company",
    tags=["Company Profile"]
)

security = HTTPBearer()


def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    """Extract and validate user ID from Bearer Token."""
    try:
        payload = verify_access_token(credentials.credentials)
        return int(payload.get("sub"))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token."
        )


# ==========================================
# CREATE COMPANY
# ==========================================

@router.post("/create")
def create_company_profile(
    payload: CompanyCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    from .model import CompanyProfile
    existing = db.query(CompanyProfile).filter(CompanyProfile.user_id == user_id).first()
    if existing:
        # If it exists, update it using the payload
        update_payload = CompanyUpdate(**payload.model_dump())
        company = update_company(db=db, company=existing, data=update_payload)
        return {
            "message": "Company updated successfully",
            "company_id": company.id,
            "verification_status": company.verification_status
        }

    company = create_company(
        db=db,
        user_id=user_id,
        data=payload
    )

    return {
        "message": "Company created successfully",
        "company_id": company.id,
        "verification_status": company.verification_status
    }


# ==========================================
# GET COMPANY
# ==========================================

@router.get("/{company_id}")
def get_company_profile(
    company_id: int,
    db: Session = Depends(get_db)
):
    company = get_company(
        db=db,
        company_id=company_id
    )
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )
    return company


# ==========================================
# UPDATE COMPANY
# ==========================================

@router.put("/update/{company_id}")
def update_company_profile(
    company_id: int,
    payload: CompanyUpdate,
    db: Session = Depends(get_db)
):
    company = get_company(
        db=db,
        company_id=company_id
    )
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found"
        )
    company = update_company(
        db=db,
        company=company,
        data=payload
    )
    return {
        "message": "Company updated successfully"
    }


# ==========================================
# GET COMPANY BY USER ID
# ==========================================

@router.get("/user/{user_id}")
def get_company_profile_by_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    from .model import CompanyProfile
    company = db.query(CompanyProfile).filter(CompanyProfile.user_id == user_id).first()
    if not company:
        from modules.auth.model import User
        from modules.auth.logic import auto_create_profile_for_user
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.role.lower() in ("company", "recruiter"):
            try:
                auto_create_profile_for_user(db=db, user=user)
                company = db.query(CompanyProfile).filter(CompanyProfile.user_id == user_id).first()
            except Exception as e:
                print(f"Failed to auto-create company profile on-the-fly: {e}")
    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company profile not found for this user."
        )
    return company


# ==========================================
# GET COMPANY PROFILE STATUS
# ==========================================

@router.get("/status/{user_id}")
def get_company_profile_status(
    user_id: int,
    db: Session = Depends(get_db)
):
    from .model import CompanyProfile
    from .logic import is_company_profile_complete
    
    profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == user_id).first()
    
    missing_fields = []
    if not profile:
        missing_fields = [
            "company_name",
            "company_email",
            "website_url",
            "industry",
            "location",
            "company_description"
        ]
    else:
        if not (profile.company_name and str(profile.company_name).strip()):
            missing_fields.append("company_name")
        if not (profile.company_email and str(profile.company_email).strip()):
            missing_fields.append("company_email")
        if not (profile.website_url and str(profile.website_url).strip()):
            missing_fields.append("website_url")
        if not (profile.industry and str(profile.industry).strip()):
            missing_fields.append("industry")
        if not (profile.location and str(profile.location).strip()):
            missing_fields.append("location")
        if not (profile.company_description and str(profile.company_description).strip()):
            missing_fields.append("company_description")
            
    complete = is_company_profile_complete(profile) if profile else False
    return {
        "complete": complete,
        "missing_fields": missing_fields
    }


# ==========================================
# HEALTH CHECK
# ==========================================

@router.get("/")
def health():
    return {
        "module": "Company Profile",
        "status": "Running"
    }