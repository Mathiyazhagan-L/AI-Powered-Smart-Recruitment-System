from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from .schema import (
    CandidateSkillCreate,
    CandidateSkillResponse,
    CandidateSkillUpdate,
)
from .logic import (
    add_skill,
    delete_skill,
    get_skill_by_id,
    get_skills_by_user,
    update_skill,
)

router = APIRouter(prefix="/candidate/skills", tags=["Candidate Skills"])


@router.post("/create", response_model=CandidateSkillResponse, status_code=status.HTTP_201_CREATED)
def create_candidate_skill(
    payload: CandidateSkillCreate,
    db: Session = Depends(get_db),
):
    try:
        return add_skill(db=db, data=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{user_id}", response_model=List[CandidateSkillResponse])
def list_candidate_skills(user_id: int, db: Session = Depends(get_db)):
    return get_skills_by_user(db=db, user_id=user_id)


@router.put("/update/{skill_id}", response_model=CandidateSkillResponse)
def update_candidate_skill(
    skill_id: int,
    payload: CandidateSkillUpdate,
    db: Session = Depends(get_db),
):
    skill = get_skill_by_id(db=db, skill_id=skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return update_skill(db=db, skill=skill, data=payload)


@router.delete("/delete/{skill_id}")
def delete_candidate_skill(skill_id: int, db: Session = Depends(get_db)):
    skill = get_skill_by_id(db=db, skill_id=skill_id)
    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    delete_skill(db=db, skill=skill)
    return {"message": "Skill deleted successfully"}
