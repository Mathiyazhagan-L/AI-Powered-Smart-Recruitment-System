from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from .schema import (
    CandidateExperienceCreate,
    CandidateExperienceResponse,
    CandidateExperienceUpdate,
)
from .logic import (
    add_experience,
    delete_experience,
    get_experience_by_id,
    get_experience_by_user,
    update_experience,
)

router = APIRouter(prefix="/candidate/experience", tags=["Candidate Experience"])


@router.post("/create", response_model=CandidateExperienceResponse, status_code=status.HTTP_201_CREATED)
def create_candidate_experience(
    payload: CandidateExperienceCreate,
    db: Session = Depends(get_db),
):
    try:
        return add_experience(db=db, data=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{user_id}", response_model=List[CandidateExperienceResponse])
def list_candidate_experience(user_id: int, db: Session = Depends(get_db)):
    return get_experience_by_user(db=db, user_id=user_id)


@router.put("/update/{experience_id}", response_model=CandidateExperienceResponse)
def update_candidate_experience(
    experience_id: int,
    payload: CandidateExperienceUpdate,
    db: Session = Depends(get_db),
):
    experience = get_experience_by_id(db=db, experience_id=experience_id)
    if not experience:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experience record not found")
    return update_experience(db=db, experience=experience, data=payload)


@router.delete("/delete/{experience_id}")
def delete_candidate_experience(experience_id: int, db: Session = Depends(get_db)):
    experience = get_experience_by_id(db=db, experience_id=experience_id)
    if not experience:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experience record not found")
    delete_experience(db=db, experience=experience)
    return {"message": "Experience record deleted successfully"}
