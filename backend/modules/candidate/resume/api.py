from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from .schema import CandidateResumeCreate, CandidateResumeResponse
from .logic import delete_resume, get_resume_by_id, get_resumes_by_user, upload_resume_metadata

router = APIRouter(prefix="/candidate/resume", tags=["Candidate Resumes"])


@router.post("/upload", response_model=CandidateResumeResponse, status_code=status.HTTP_201_CREATED)
def upload_candidate_resume(
    payload: CandidateResumeCreate,
    db: Session = Depends(get_db),
):
    try:
        return upload_resume_metadata(db=db, data=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{user_id}", response_model=List[CandidateResumeResponse])
def list_candidate_resumes(user_id: int, db: Session = Depends(get_db)):
    return get_resumes_by_user(db=db, user_id=user_id)


@router.get("/status/{candidate_id}", response_model=dict)
def get_resume_status(candidate_id: int, db: Session = Depends(get_db)):
    """
    Get candidate resume upload status.
    """
    from modules.candidate.resume.model import CandidateResume
    from modules.resume_parser.model import ResumeParserResult

    candidate_resume = db.query(CandidateResume).filter(CandidateResume.user_id == candidate_id).order_by(CandidateResume.created_at.desc()).first()
    parser_resume = db.query(ResumeParserResult).filter(
        ResumeParserResult.candidate_id == candidate_id
    ).order_by(ResumeParserResult.created_at.desc()).first()

    uploaded = False
    file_name = "N/A"
    uploaded_at = "N/A"

    cond1 = candidate_resume is not None
    cond2 = (candidate_resume and candidate_resume.resume_path) or (parser_resume and parser_resume.resume_file)
    cond3 = parser_resume and parser_resume.parsing_status == "completed"

    if cond1 or cond2 or cond3:
        uploaded = True
        if candidate_resume:
            file_name = candidate_resume.resume_name or "resume"
            uploaded_at = candidate_resume.created_at.isoformat() if candidate_resume.created_at else "N/A"
        elif parser_resume:
            file_name = parser_resume.original_filename or "resume"
            uploaded_at = parser_resume.created_at.isoformat() if parser_resume.created_at else "N/A"

    return {
        "uploaded": uploaded,
        "file_name": file_name,
        "uploaded_at": uploaded_at
    }


@router.delete("/delete/{resume_id}")
def delete_candidate_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = get_resume_by_id(db=db, resume_id=resume_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    delete_resume(db=db, resume=resume)
    return {"message": "Resume metadata deleted successfully"}
