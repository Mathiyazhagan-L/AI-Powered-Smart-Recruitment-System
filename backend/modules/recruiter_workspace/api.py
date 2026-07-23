from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from modules.auth.api import get_current_user
from modules.auth.model import User
from modules.recruiter_workspace import schemas, logic

router = APIRouter(prefix="/recruiter-workspace", tags=["Recruiter Workspace"])

# --- Notes ---
@router.post("/notes", response_model=schemas.RecruiterNoteResponse)
def create_note(note: schemas.RecruiterNoteCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "RECRUITER":
        raise HTTPException(status_code=403, detail="Only recruiters can create notes")
    
    # Audit log
    logic.RecruiterWorkspaceLogic.add_audit_log(db, current_user.get("id"), schemas.RecruiterAuditLogCreate(
        action_type="Note Added",
        description=f"Added a {note.note_type} note for candidate {note.candidate_id}",
        target_entity_type="Candidate",
        target_entity_id=note.candidate_id
    ))
    return logic.RecruiterWorkspaceLogic.create_note(db, current_user.get("id"), note)

@router.get("/notes/candidate/{candidate_id}", response_model=List[schemas.RecruiterNoteResponse])
def get_notes(candidate_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "RECRUITER":
        raise HTTPException(status_code=403, detail="Only recruiters can view notes")
    return logic.RecruiterWorkspaceLogic.get_notes_for_candidate(db, candidate_id, current_user.get("id"))

@router.put("/notes/{note_id}", response_model=schemas.RecruiterNoteResponse)
def update_note(note_id: int, note: schemas.RecruiterNoteUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "RECRUITER":
        raise HTTPException(status_code=403, detail="Only recruiters can edit notes")
    return logic.RecruiterWorkspaceLogic.update_note(db, note_id, current_user.get("id"), note)

@router.delete("/notes/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "RECRUITER":
        raise HTTPException(status_code=403, detail="Only recruiters can delete notes")
    logic.RecruiterWorkspaceLogic.delete_note(db, note_id, current_user.get("id"))
    return {"status": "deleted"}

# --- Timeline ---
@router.post("/timeline", response_model=schemas.CandidateTimelineEventResponse)
def add_timeline_event(event: schemas.CandidateTimelineEventCreate, db: Session = Depends(get_db)):
    # Can be called by internal systems or directly
    return logic.RecruiterWorkspaceLogic.add_timeline_event(db, event)

@router.get("/timeline/candidate/{candidate_id}", response_model=List[schemas.CandidateTimelineEventResponse])
def get_timeline(candidate_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return logic.RecruiterWorkspaceLogic.get_candidate_timeline(db, candidate_id)

# --- Audit Logs ---
@router.post("/audit", response_model=schemas.RecruiterAuditLogResponse)
def add_audit_log(log: schemas.RecruiterAuditLogCreate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "RECRUITER":
        raise HTTPException(status_code=403, detail="Only recruiters can add audit logs")
    return logic.RecruiterWorkspaceLogic.add_audit_log(db, current_user.get("id"), log)

@router.get("/audit", response_model=List[schemas.RecruiterAuditLogResponse])
def get_audit_logs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "RECRUITER":
        raise HTTPException(status_code=403, detail="Only recruiters can view audit logs")
    return logic.RecruiterWorkspaceLogic.get_audit_logs(db, skip, limit)

# --- Pipeline ---
from pydantic import BaseModel
class PipelineStageUpdate(BaseModel):
    stage: str

@router.put("/pipeline/job/{job_id}/candidate/{candidate_id}/stage")
def update_pipeline_stage(job_id: int, candidate_id: int, update: PipelineStageUpdate, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "RECRUITER":
        raise HTTPException(status_code=403, detail="Only recruiters can update pipeline stages")
        
    from modules.job_management.model import Application
    app = db.query(Application).filter(Application.job_id == job_id, Application.candidate_id == candidate_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
        
    old_stage = app.status
    app.status = update.stage
    db.commit()
    
    # 1. Add Timeline Event
    logic.RecruiterWorkspaceLogic.add_timeline_event(db, schemas.CandidateTimelineEventCreate(
        candidate_id=candidate_id,
        event_type="Stage Updated",
        description=f"Moved candidate from {old_stage} to {update.stage}",
        triggered_by="Recruiter",
        related_entity_id=job_id
    ))
    
    # 2. Add Audit Log
    logic.RecruiterWorkspaceLogic.add_audit_log(db, current_user.get("id"), schemas.RecruiterAuditLogCreate(
        action_type="Candidate Moved",
        description=f"Moved candidate {candidate_id} to {update.stage} for job {job_id}",
        target_entity_type="Candidate",
        target_entity_id=candidate_id
    ))
    
    return {"status": "success", "new_stage": update.stage}

# --- Resume Access for Recruiters ---
@router.get("/resume/{candidate_id}")
def get_candidate_resume(candidate_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != "RECRUITER":
        raise HTTPException(status_code=403, detail="Only recruiters can view resumes")
        
    from modules.resume_parser.model import ResumeParserResult
    # Get the most recent successfully parsed resume
    resume = db.query(ResumeParserResult).filter(
        ResumeParserResult.candidate_id == candidate_id,
        ResumeParserResult.parsing_status == 'completed'
    ).order_by(ResumeParserResult.created_at.desc()).first()
    
    if not resume:
        raise HTTPException(status_code=404, detail="No parsed resume found for this candidate")
        
    return resume
