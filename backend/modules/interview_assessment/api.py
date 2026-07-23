import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from typing import Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from core.database import get_db
from modules.auth.logic import verify_access_token
from modules.interview_assessment.schema import (
    InterviewStartResponse,
    InterviewQuestionResponse,
    InterviewAnswerResponse,
    InterviewEvaluateResponse,
    InterviewResultResponse,
    BulkSubmitRequest,
    ProfessionalAssessmentResult
)
from modules.interview_assessment.logic import InterviewAssessmentLogic

router = APIRouter(prefix="/interview", tags=["AI Interview Assessment"])
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


class EvaluateRequest(BaseModel):
    session_id: int
    question_id: int


@router.post("/start", response_model=InterviewStartResponse, summary="Start or resume AI interview session")
def start_interview(
    candidate_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # Check Profile Completion Eligibility
    from modules.candidate.profile.model import CandidateProfile
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile or not profile.profile_completion or profile.profile_completion < 80:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your profile must be at least 80% complete to attend interviews."
        )

    res = InterviewAssessmentLogic.start_interview(candidate_id=candidate_id, db=db)
    from modules.proctoring.logic import start_monitoring
    start_monitoring(candidate_id=candidate_id, assessment_type="INTERVIEW", db=db)
    return res


@router.get("/question", response_model=InterviewQuestionResponse, summary="Get details of a specific question")
def get_question(
    session_id: int,
    question_id: int,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return InterviewAssessmentLogic.get_question_details(session_id=session_id, question_id=question_id, db=db)


@router.post("/answer", response_model=InterviewAnswerResponse, summary="Submit voice answer audio file")
def submit_answer(
    session_id: int = Form(...),
    question_id: int = Form(...),
    file: UploadFile = File(...),
    speech_text: Optional[str] = Form(None),
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    # Ensure uploads folder exists
    upload_dir = os.path.join("uploads", "interviews", str(session_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file locally
    file_ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".wav"
    if not file_ext:
        file_ext = ".wav"
    file_path = os.path.join(upload_dir, f"q_{question_id}{file_ext}")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save audio file: {e}"
        )

    return InterviewAssessmentLogic.submit_answer(
        session_id=session_id,
        question_id=question_id,
        audio_file_path=file_path,
        speech_text=speech_text,
        db=db
    )


@router.post("/evaluate", response_model=InterviewEvaluateResponse, summary="Evaluate the submitted answer transcript")
def evaluate_answer(
    payload: EvaluateRequest,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return InterviewAssessmentLogic.evaluate_answer(
        session_id=payload.session_id,
        question_id=payload.question_id,
        db=db
    )


@router.post("/finish", response_model=InterviewResultResponse, summary="Finalize the interview session and compile report")
def finish_interview(
    session_id: int,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    from modules.interview_assessment.models import InterviewSession
    from modules.proctoring.logic import stop_monitoring
    
    sess = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
    candidate_id = sess.candidate_id if sess else None
    
    res = InterviewAssessmentLogic.finalize_interview(session_id=session_id, db=db)
    
    if candidate_id:
        stop_monitoring(candidate_id=candidate_id, assessment_type="INTERVIEW", db=db)
        
    return res


@router.get("/result/{candidate_id}", response_model=InterviewResultResponse, summary="Get final interview assessment scorecard")
def get_result(
    candidate_id: int,
    _: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return InterviewAssessmentLogic.get_latest_result(candidate_id=candidate_id, db=db)


@router.post("/reset", summary="Reset candidate's interview session and result to allow reattempt")
def reset_interview(
    candidate_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return InterviewAssessmentLogic.reset_interview(candidate_id=candidate_id, db=db)


@router.post("/submit_bulk", response_model=ProfessionalAssessmentResult, summary="Submit professional assessment")
def submit_bulk_assessment(
    request: BulkSubmitRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    return InterviewAssessmentLogic.submit_professional_assessment(user_id, request.answers, db)
