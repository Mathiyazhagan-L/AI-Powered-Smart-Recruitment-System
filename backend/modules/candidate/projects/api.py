from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from .schema import (
    CandidateProjectCreate,
    CandidateProjectResponse,
    CandidateProjectUpdate,
)
from .logic import (
    add_project,
    delete_project,
    get_project_by_id,
    get_projects_by_user,
    update_project,
)

router = APIRouter(prefix="/candidate/projects", tags=["Candidate Projects"])


@router.post("/create", response_model=CandidateProjectResponse, status_code=status.HTTP_201_CREATED)
def create_candidate_project(
    payload: CandidateProjectCreate,
    db: Session = Depends(get_db),
):
    try:
        return add_project(db=db, data=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{user_id}", response_model=List[CandidateProjectResponse])
def list_candidate_projects(user_id: int, db: Session = Depends(get_db)):
    return get_projects_by_user(db=db, user_id=user_id)


@router.put("/update/{project_id}", response_model=CandidateProjectResponse)
def update_candidate_project(
    project_id: int,
    payload: CandidateProjectUpdate,
    db: Session = Depends(get_db),
):
    project = get_project_by_id(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return update_project(db=db, project=project, data=payload)


@router.delete("/delete/{project_id}")
def delete_candidate_project(project_id: int, db: Session = Depends(get_db)):
    project = get_project_by_id(db=db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    delete_project(db=db, project=project)
    return {"message": "Project deleted successfully"}
