
from modules.candidate.profile.logic import trigger_profile_completion_update
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from .model import CandidateProject
from .schema import CandidateProjectCreate, CandidateProjectUpdate


def add_project(db: Session, data: CandidateProjectCreate) -> CandidateProject:
    project = CandidateProject(
        user_id=data.user_id,
        project_name=data.project_name,
        description=data.description,
        technologies=data.technologies,
        github_url=data.github_url,
        live_url=data.live_url,
        start_date=data.start_date,
        end_date=data.end_date,
    )

    db.add(project)
    db.commit()
    db.refresh(project)
    trigger_profile_completion_update(db, project.user_id)
    return project


def get_projects_by_user(db: Session, user_id: int) -> List[CandidateProject]:
    return (
        db.query(CandidateProject)
        .filter(CandidateProject.user_id == user_id)
        .order_by(CandidateProject.start_date.desc())
        .all()
    )


def get_project_by_id(db: Session, project_id: int) -> Optional[CandidateProject]:
    return db.query(CandidateProject).filter(CandidateProject.id == project_id).first()


def update_project(
    db: Session,
    project: CandidateProject,
    data: CandidateProjectUpdate,
) -> CandidateProject:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    trigger_profile_completion_update(db, project.user_id)
    return project


def delete_project(db: Session, project: CandidateProject) -> bool:
    user_id = project.user_id
    db.delete(project)
    db.commit()
    trigger_profile_completion_update(db, user_id)
    return True
