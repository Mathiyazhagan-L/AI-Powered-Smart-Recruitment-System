from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from modules.auth.logic import verify_access_token

from .repository import ResumeParserRepository
from .schema import ParseOnlyResponse, ResumeParserResultResponse, ResumeParserResultSummary
from .service import ResumeParsingService

router = APIRouter(
    prefix="/resume-parser",
    tags=["Resume Parser"],
)

security = HTTPBearer()
repo = ResumeParserRepository()
service = ResumeParsingService()


# ------------------------------------------------------------------
# Auth dependency  (reuses ATS JWT from modules/auth/logic.py)
# ------------------------------------------------------------------

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> int:
    """Extract and validate the candidate's user_id from the Bearer JWT."""
    try:
        payload = verify_access_token(credentials.credentials)
        user_id = int(payload.get("sub"))
        return user_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )


# ------------------------------------------------------------------
# POST /resume-parser/upload
# Parse AND persist to resume_parser_results
# ------------------------------------------------------------------

@router.post(
    "/upload",
    response_model=ResumeParserResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a resume, storing results in the database",
)
async def upload_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, DOC, TXT, JPG, PNG)"),
    candidate_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Full pipeline:
        Upload → Local Storage → Text Extraction → Cleaning
        → Parsing → JSON Generation → Store in resume_parser_results
    """
    try:
        record = await service.upload_and_parse(
            db=db,
            file=file,
            candidate_id=candidate_id,
        )
        return record
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume parsing failed: {exc}",
        )


# ------------------------------------------------------------------
# POST /resume-parser/parse
# Parse only — returns JSON, does NOT write to database
# ------------------------------------------------------------------

@router.post(
    "/parse",
    response_model=ParseOnlyResponse,
    summary="Parse a resume and return structured JSON without storing",
)
async def parse_resume(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, DOC, TXT, JPG, PNG)"),
    _: int = Depends(get_current_user_id),   # require auth even for parse-only
):
    """
    Stateless parse — no database record created.
    Returns raw_text, cleaned_text, and parsed_json.
    """
    try:
        result = await service.parse_only(file=file)
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume parsing failed: {exc}",
        )


# ------------------------------------------------------------------
# GET /resume-parser
# List resume parser results (filtered by authenticated user)
# ------------------------------------------------------------------

@router.get(
    "/",
    response_model=List[ResumeParserResultSummary],
    summary="List all parsed resumes for the authenticated user",
)
def list_resumes(
    parsing_status: str | None = Query(
        None, description="Filter by status: pending | processing | completed | failed"
    ),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit"),
    candidate_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Returns a summary list (without raw/cleaned text) for the authenticated user."""
    records = repo.list_resume_records(
        db=db,
        candidate_id=candidate_id,
        parsing_status=parsing_status,
        skip=skip,
        limit=limit,
    )
    return records


# ------------------------------------------------------------------
# GET /resume-parser/{id}
# Fetch a single result by ID
# ------------------------------------------------------------------

@router.get(
    "/{record_id}",
    response_model=ResumeParserResultResponse,
    summary="Get a full resume parser result by ID",
)
def get_resume(
    record_id: int,
    candidate_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Returns the full record including raw_text, cleaned_text, and parsed_json."""
    record = repo.get_resume_record(db=db, record_id=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume parser result {record_id} not found.",
        )
    # Enforce ownership — candidates can only read their own records
    if record.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )
    return record


# ------------------------------------------------------------------
# DELETE /resume-parser/{id}
# ------------------------------------------------------------------

@router.delete(
    "/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a resume parser result by ID",
)
def delete_resume(
    record_id: int,
    candidate_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Deletes the record. Returns 404 if not found, 403 if not owned by caller."""
    record = repo.get_resume_record(db=db, record_id=record_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume parser result {record_id} not found.",
        )
    if record.candidate_id != candidate_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied.",
        )
    repo.delete_resume_record(db=db, record_id=record_id)
    return {"detail": "Resume parser result deleted.", "id": record_id}
