from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from modules.auth.logic import verify_access_token
from modules.coding_assessment.schema import (
    CodingStartResponse,
    CodeRunRequest,
    CodeRunResponse,
    CodeSubmitRequest,
    CodeSubmitResponse,
    CodingResultResponse
)
from modules.coding_assessment.logic import CodingAssessmentLogic

router = APIRouter(prefix="/coding", tags=["Coding Assessment"])
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

@router.post("/start", response_model=CodingStartResponse, summary="Start or resume a coding assessment attempt")
def start_coding_assessment(
    candidate_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        result = CodingAssessmentLogic.start_attempt(candidate_id=candidate_id, db=db)
        from modules.proctoring.logic import start_monitoring
        start_monitoring(candidate_id=candidate_id, assessment_type="CODING", db=db)
        return result
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start coding assessment: {exc}"
        )

@router.post("/run", response_model=CodeRunResponse, summary="Run candidate code against sample test cases")
def run_coding_code(
    payload: CodeRunRequest,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        result = CodingAssessmentLogic.run_candidate_code(
            attempt_id=payload.attempt_id,
            question_id=payload.question_id,
            source_code=payload.source_code,
            language=payload.language,
            db=db
        )
        return result
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run code: {exc}"
        )

@router.post("/submit", response_model=CodeSubmitResponse, summary="Submit candidate solution and run all test cases")
def submit_coding_solution(
    payload: CodeSubmitRequest,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        result = CodingAssessmentLogic.submit_candidate_solution(
            attempt_id=payload.attempt_id,
            question_id=payload.question_id,
            source_code=payload.source_code,
            language=payload.language,
            db=db
        )
        return result
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit solution: {exc}"
        )

@router.post("/finish", response_model=CodingResultResponse, summary="Finalize coding assessment and generate report")
def finish_coding_assessment(
    attempt_id: int,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        from modules.coding_assessment.models import CodingAttempt
        from modules.proctoring.logic import stop_monitoring
        
        attempt = db.query(CodingAttempt).filter(CodingAttempt.id == attempt_id).first()
        candidate_id = attempt.candidate_id if attempt else None
        
        result = CodingAssessmentLogic.finish_attempt(attempt_id=attempt_id, db=db)
        
        if candidate_id:
            stop_monitoring(candidate_id=candidate_id, assessment_type="CODING", db=db)
            
        return result
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to finish assessment: {exc}"
        )

@router.get("/result/{candidate_id}", response_model=CodingResultResponse, summary="Get latest coding assessment results")
def fetch_coding_result(
    candidate_id: int,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    try:
        result = CodingAssessmentLogic.get_latest_result(candidate_id=candidate_id, db=db)
        return result
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch results: {exc}"
        )
