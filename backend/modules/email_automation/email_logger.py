import json
import logging
import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from .models import EmailLog

logger = logging.getLogger(__name__)

def log_email_pending(
    db: Session,
    recipient_email: str,
    email_type: str,
    candidate_id: Optional[int] = None
) -> int:
    """
    Inserts a pending email log record in the database.
    """
    log = EmailLog(
        candidate_id=candidate_id,
        email_type=email_type,
        recipient_email=recipient_email,
        status="Pending",
        created_at=datetime.datetime.utcnow()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log.id

def update_email_log(
    db: Session,
    log_id: int,
    status: str,
    subject: Optional[str] = None,
    content_json: Optional[str] = None,
    html: Optional[str] = None,
    error_message: Optional[str] = None
):
    """
    Updates an email log record after sending attempt.
    """
    log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
    if log:
        log.status = status
        if subject is not None:
            log.generated_subject = subject
            log.subject = subject
        if content_json is not None:
            log.generated_content_json = content_json
        if html is not None:
            log.generated_html = html
            log.body = html
        if error_message is not None:
            log.error_message = error_message
        if status == "Sent":
            log.sent_at = datetime.datetime.utcnow()
            log.delivery_status = "Sent"
        else:
            log.delivery_status = "Failed"
            
        db.commit()
        db.refresh(log)
        logger.info(f"Updated EmailLog #{log_id} to status: {status}")

def has_duplicate_email(
    db: Session,
    recipient_email: str,
    email_type: str,
    candidate_id: Optional[int] = None,
    job_id: Optional[int] = None
) -> bool:
    """
    Checks if an email of the same type has already been sent/pending to prevent duplicates.
    """
    # 1. Job-specific candidate events (Application Submitted, Shortlisted, Rejected, Offer Letter, etc.)
    if job_id and candidate_id:
        logs = db.query(EmailLog).filter(
            EmailLog.candidate_id == candidate_id,
            EmailLog.recipient_email == recipient_email,
            EmailLog.email_type == email_type,
            EmailLog.status.in_(["Sent", "Pending"])
        ).all()
        
        for log in logs:
            if log.generated_content_json:
                try:
                    data = json.loads(log.generated_content_json)
                    if data.get("context", {}).get("job_id") == job_id or data.get("job_id") == job_id:
                        return True
                except Exception:
                    pass
        return False
        
    # 2. General candidate events (Registration, Resume Upload, Assessment unlocked/result)
    elif candidate_id:
        exists = db.query(EmailLog).filter(
            EmailLog.candidate_id == candidate_id,
            EmailLog.email_type == email_type,
            EmailLog.status.in_(["Sent", "Pending"])
        ).first()
        return exists is not None

    # 3. Recruiter registration or general email check
    else:
        exists = db.query(EmailLog).filter(
            EmailLog.recipient_email == recipient_email,
            EmailLog.email_type == email_type,
            EmailLog.status.in_(["Sent", "Pending"])
        ).first()
        return exists is not None
