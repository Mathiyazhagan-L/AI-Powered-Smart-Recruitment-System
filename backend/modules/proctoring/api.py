from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from core.database import get_db
from modules.auth.logic import verify_access_token
from modules.proctoring.models import AssessmentViolation, AssessmentIntegrityResult
from modules.proctoring.logic import (
    start_monitoring,
    stop_monitoring,
    report_browser_violation,
    report_frame,
    get_proctoring_status
)

router = APIRouter(prefix="/proctoring", tags=["AI Proctoring"])
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


class StartMonitoringRequest(BaseModel):
    candidate_id: int
    assessment_type: str  # APTITUDE, CODING, INTERVIEW


class StopMonitoringRequest(BaseModel):
    candidate_id: int
    assessment_type: str


class ReportViolationRequest(BaseModel):
    candidate_id: int
    assessment_type: str
    violation_type: str


class ReportFrameRequest(BaseModel):
    candidate_id: int
    assessment_type: str
    frame: str  # base64 string


@router.post("/start", summary="Start or resume monitoring session")
def start_session(
    payload: StartMonitoringRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # Enforce basic candidate matching or allow admin/recruiter
    try:
        res = start_monitoring(payload.candidate_id, payload.assessment_type, db)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring session: {e}"
        )


@router.post("/stop", summary="Stop and finalize monitoring session")
def stop_session(
    payload: StopMonitoringRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        res = stop_monitoring(payload.candidate_id, payload.assessment_type, db)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring session: {e}"
        )


@router.post("/violation", summary="Report a browser violation")
def report_browser(
    payload: ReportViolationRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        res = report_browser_violation(
            payload.candidate_id,
            payload.assessment_type,
            payload.violation_type,
            db
        )
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to report browser violation: {e}"
        )


@router.post("/frame", summary="Submit base64 webcam frame for face/object checks")
def submit_webcam_frame(
    payload: ReportFrameRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        res = report_frame(
            payload.candidate_id,
            payload.assessment_type,
            payload.frame,
            db
        )
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process frame violation: {e}"
        )


@router.get("/status", summary="Get current monitoring status")
def fetch_status(
    candidate_id: int,
    assessment_type: str,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        res = get_proctoring_status(candidate_id, assessment_type)
        return res
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch proctoring status: {e}"
        )


@router.get("/history/{candidate_id}", summary="Get candidate proctoring history for recruiter dashboard")
def fetch_history(
    candidate_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        violations = db.query(AssessmentViolation).filter(
            AssessmentViolation.candidate_id == candidate_id
        ).order_by(AssessmentViolation.timestamp.asc()).all()
        
        integrity_results = db.query(AssessmentIntegrityResult).filter(
            AssessmentIntegrityResult.candidate_id == candidate_id
        ).order_by(AssessmentIntegrityResult.completed_at.asc()).all()
        
        return {
            "candidate_id": candidate_id,
            "violations": [
                {
                    "id": v.id,
                    "assessment_type": v.assessment_type,
                    "violation_type": v.violation_type,
                    "warning_level": v.warning_level,
                    "integrity_score": v.integrity_score,
                    "timestamp": v.timestamp
                } for v in violations
            ],
            "integrity_results": [
                {
                    "id": r.id,
                    "assessment_type": r.assessment_type,
                    "assessment_score": r.assessment_score,
                    "integrity_score": r.integrity_score,
                    "violation_count": r.violation_count,
                    "status": r.status,
                    "completed_at": r.completed_at
                } for r in integrity_results
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch proctoring history: {e}"
        )
