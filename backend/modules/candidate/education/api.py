from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from .schema import (
    CandidateEducationCreate,
    CandidateEducationResponse,
    CandidateEducationUpdate,
)
from .logic import (
    add_education,
    delete_education,
    get_education_by_id,
    get_education_by_user,
    update_education,
)

router = APIRouter(prefix="/candidate/education", tags=["Candidate Education"])


@router.post("/create", response_model=CandidateEducationResponse, status_code=status.HTTP_201_CREATED)
def create_candidate_education(
    payload: CandidateEducationCreate,
    db: Session = Depends(get_db),
):
    try:
        return add_education(db=db, data=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{user_id}", response_model=List[CandidateEducationResponse])
def list_candidate_education(user_id: int, db: Session = Depends(get_db)):
    return get_education_by_user(db=db, user_id=user_id)


@router.put("/update/{education_id}", response_model=CandidateEducationResponse)
def update_candidate_education(
    education_id: int,
    payload: CandidateEducationUpdate,
    db: Session = Depends(get_db),
):
    education = get_education_by_id(db=db, education_id=education_id)
    if not education:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education record not found")
    return update_education(db=db, education=education, data=payload)


@router.delete("/delete/{education_id}")
def delete_candidate_education(education_id: int, db: Session = Depends(get_db)):
    education = get_education_by_id(db=db, education_id=education_id)
    if not education:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Education record not found")
    delete_education(db=db, education=education)
    return {"message": "Education record deleted successfully"}
