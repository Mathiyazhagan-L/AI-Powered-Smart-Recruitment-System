from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session

from .model import CandidateResume
from .schema import CandidateResumeCreate


def upload_resume_metadata(db: Session, data: CandidateResumeCreate) -> CandidateResume:
    resume = CandidateResume(
        user_id=data.user_id,
        resume_name=data.resume_name,
        resume_path=data.resume_path,
        file_type=data.file_type,
        file_size=data.file_size,
        ats_score=data.ats_score,
        parsed_status=data.parsed_status,
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Trigger Resume Upload Email
    try:
            from modules.email_automation.triggers import trigger_email
            trigger_email(
                event_type="Resume Successfully Uploaded",
                candidate_id=data.user_id,
                context={
                    "extra_details": f"Your resume '{data.resume_name}' was uploaded successfully and is being processed by our AI."
                },
                db=db
            )
    except Exception as e:
        print(f"Failed to send resume upload email: {e}")

    return resume


def get_resumes_by_user(db: Session, user_id: int) -> List[CandidateResume]:
    return (
        db.query(CandidateResume)
        .filter(CandidateResume.user_id == user_id)
        .order_by(CandidateResume.created_at.desc())
        .all()
    )


def get_resume_by_id(db: Session, resume_id: int) -> Optional[CandidateResume]:
    return db.query(CandidateResume).filter(CandidateResume.id == resume_id).first()


def delete_resume(db: Session, resume: CandidateResume) -> bool:
    db.delete(resume)
    db.commit()
    return True
