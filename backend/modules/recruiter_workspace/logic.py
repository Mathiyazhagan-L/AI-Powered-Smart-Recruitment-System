from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from modules.recruiter_workspace.models import RecruiterNote, CandidateTimelineEvent, RecruiterAuditLog
from modules.recruiter_workspace import schemas

class RecruiterWorkspaceLogic:
    
    # --- Notes ---
    @staticmethod
    def create_note(db: Session, recruiter_id: int, note_data: schemas.RecruiterNoteCreate) -> RecruiterNote:
        db_note = RecruiterNote(**note_data.dict(), recruiter_id=recruiter_id)
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note
        
    @staticmethod
    def get_notes_for_candidate(db: Session, candidate_id: int, recruiter_id: int) -> list[RecruiterNote]:
        # Return public notes + private notes owned by recruiter
        notes = db.query(RecruiterNote).filter(RecruiterNote.candidate_id == candidate_id).all()
        filtered = [n for n in notes if n.visibility != "Private" or n.recruiter_id == recruiter_id]
        return filtered
        
    @staticmethod
    def update_note(db: Session, note_id: int, recruiter_id: int, note_data: schemas.RecruiterNoteUpdate) -> RecruiterNote:
        note = db.query(RecruiterNote).filter(RecruiterNote.id == note_id).first()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        if note.recruiter_id != recruiter_id:
            raise HTTPException(status_code=403, detail="You can only edit your own notes")
            
        update_data = note_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(note, key, value)
            
        db.commit()
        db.refresh(note)
        return note
        
    @staticmethod
    def delete_note(db: Session, note_id: int, recruiter_id: int):
        note = db.query(RecruiterNote).filter(RecruiterNote.id == note_id).first()
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        if note.recruiter_id != recruiter_id:
            raise HTTPException(status_code=403, detail="You can only delete your own notes")
            
        db.delete(note)
        db.commit()
        
    # --- Timeline ---
    @staticmethod
    def add_timeline_event(db: Session, event_data: schemas.CandidateTimelineEventCreate) -> CandidateTimelineEvent:
        db_event = CandidateTimelineEvent(**event_data.dict())
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        return db_event
        
    @staticmethod
    def get_candidate_timeline(db: Session, candidate_id: int) -> list[CandidateTimelineEvent]:
        return db.query(CandidateTimelineEvent).filter(CandidateTimelineEvent.candidate_id == candidate_id).order_by(CandidateTimelineEvent.created_at.desc()).all()
        
    # --- Audit Log ---
    @staticmethod
    def add_audit_log(db: Session, recruiter_id: int, log_data: schemas.RecruiterAuditLogCreate) -> RecruiterAuditLog:
        db_log = RecruiterAuditLog(**log_data.dict(), recruiter_id=recruiter_id)
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log
        
    @staticmethod
    def get_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> list[RecruiterAuditLog]:
        return db.query(RecruiterAuditLog).order_by(RecruiterAuditLog.created_at.desc()).offset(skip).limit(limit).all()
