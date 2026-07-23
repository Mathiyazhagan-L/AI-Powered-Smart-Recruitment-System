from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from modules.auth.logic import verify_access_token

from .schema import (
    AssessmentSaveAnswerRequest,
    AssessmentSubmitRequest,
    AssessmentStartResponse,
    AssessmentSubmitResponse,
    AssessmentResultResponse
)
from .logic import (
    generate_assessment,
    save_answer,
    submit_assessment,
    get_latest_result,
    reset_assessment
)

router = APIRouter(prefix="/assessment", tags=["Aptitude Assessment"])
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


@router.post("/start", response_model=AssessmentStartResponse, summary="Start or resume an aptitude assessment attempt")
def start_assessment(
    candidate_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # Check Profile Completion Eligibility
    from modules.candidate.profile.model import CandidateProfile
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile or not profile.profile_completion or profile.profile_completion < 70:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your profile must be at least 70% complete to take assessments."
        )
        
    try:
        result = generate_assessment(candidate_id=candidate_id, db=db)
        from modules.proctoring.logic import start_monitoring
        start_monitoring(candidate_id=candidate_id, assessment_type="APTITUDE", db=db)
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize assessment: {exc}"
        )


@router.post("/save-answer", summary="Auto-save an option choice in real-time")
def auto_save_answer(
    payload: AssessmentSaveAnswerRequest,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        save_answer(
            attempt_id=payload.attempt_id,
            question_id=payload.question_id,
            selected_answer=payload.selected_answer,
            integrity_score=payload.integrity_score,
            db=db
        )
        return {"success": True, "message": "Answer saved successfully."}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Auto-save failed: {exc}"
        )


@router.post("/submit", response_model=AssessmentSubmitResponse, summary="Submit assessment and grade results")
def submit_candidate_assessment(
    payload: AssessmentSubmitRequest,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        from .models import AssessmentAttempt
        from modules.proctoring.logic import stop_monitoring
        
        attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == payload.attempt_id).first()
        candidate_id = attempt.candidate_id if attempt else None
        
        res = submit_assessment(
            attempt_id=payload.attempt_id,
            answers_list=payload.answers,
            integrity_score=payload.integrity_score,
            db=db
        )
        
        if candidate_id:
            stop_monitoring(candidate_id=candidate_id, assessment_type="APTITUDE", db=db)
            
        return res
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Submission failed: {exc}"
        )


@router.get("/result/{candidate_id}", response_model=AssessmentResultResponse, summary="Get latest assessment result for candidate")
def fetch_assessment_result(
    candidate_id: int,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    res = get_latest_result(candidate_id=candidate_id, db=db)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment result found for this candidate."
        )
    return res


@router.post("/reset", summary="Reset candidate's assessment attempt and results to allow reattempt")
def reset_candidate_assessment(
    candidate_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return reset_assessment(candidate_id=candidate_id, db=db)

