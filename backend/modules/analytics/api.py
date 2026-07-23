from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Dict

from core.database import get_db
from modules.auth.logic import verify_access_token
from modules.auth.model import User

# Response schemas
from modules.analytics.schema import (
    DashboardOverviewResponse,
    SkillCountResponse,
    SkillGapItem,
    CandidateRankingAnalyticsItem,
    PredictionDistributionResponse,
    HiringFunnelResponse
)

# Service layer
from modules.analytics import service

router = APIRouter(prefix="/analytics", tags=["Recruitment Analytics"])

security = HTTPBearer()


def get_current_company_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency that extracts and validates the JWT, ensuring the user exists and has the 'company' role.
    Raises 401 for invalid/expired tokens, and 403 Forbidden for candidates.
    """
    try:
        token = credentials.credentials
        payload = verify_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or Expired Token"
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing subject ID."
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token."
        )

    # Fetch user from DB to verify status and role
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive."
        )

    # Strict role verification: only 'company' and 'recruiter' users are authorized
    if user.role.lower() not in ["company", "recruiter", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Candidate users do not have access to analytics."
        )

    return {"user_id": user_id, "role": user.role}


@router.get("/overview", response_model=DashboardOverviewResponse)
def get_overview(
    current_user: dict = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """
    Returns high-level recruiting metrics (jobs, candidates, applications, and suitability counts).
    """
    company_id = current_user["user_id"]
    return service.get_dashboard_overview(company_id=company_id, db=db)


@router.get("/ats-distribution", response_model=Dict[str, int])
def get_ats_distribution(
    current_user: dict = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """
    Returns score counts bucketed by 20-point ranges.
    """
    company_id = current_user["user_id"]
    return service.get_ats_score_distribution(company_id=company_id, db=db)


@router.get("/top-skills", response_model=List[SkillCountResponse])
def get_top_skills(
    current_user: dict = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """
    Returns the top 20 candidate skills across all registered candidates.
    """
    return service.get_top_skills(db=db)


@router.get("/skill-gap/{job_id}", response_model=List[SkillGapItem])
def get_skill_gap(
    job_id: int,
    current_user: dict = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """
    Returns a sorted list of required job skills with count of candidates who do not possess them.
    """
    # Verify job exists
    from modules.job_management.model import Job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    return service.get_skill_gap_analysis(job_id=job_id, db=db)


@router.get("/rankings/{job_id}", response_model=List[CandidateRankingAnalyticsItem])
def get_rankings_analytics(
    job_id: int,
    current_user: dict = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """
    Returns job candidates rankings coupled with their ML predicted suitability labels.
    """
    # Verify job exists
    from modules.job_management.model import Job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    return service.get_candidate_rankings_analytics(job_id=job_id, db=db)


@router.get("/prediction-distribution", response_model=PredictionDistributionResponse)
def get_prediction_distribution(
    current_user: dict = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """
    Returns count distribution of suitability predictions.
    """
    dist = service.get_prediction_distribution(db=db)
    # Map dictionary keys containing spaces to response fields with underscores
    return PredictionDistributionResponse(
        Selected=dist["Selected"],
        High_Potential=dist["High Potential"],
        Medium_Potential=dist["Medium Potential"],
        Rejected=dist["Rejected"]
    )


@router.get("/hiring-funnel", response_model=HiringFunnelResponse)
def get_hiring_funnel(
    current_user: dict = Depends(get_current_company_user),
    db: Session = Depends(get_db)
):
    """
    Returns hiring funnel analytics stages.
    """
    return service.get_hiring_funnel_analytics(db=db)
