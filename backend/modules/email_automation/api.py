import json
import logging
import threading
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from .models import EmailLog
from .schemas import EmailLogResponse, EmailStatsResponse, ResendResponse
from .service import process_email_generation_and_send

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-automation", tags=["Email Automation Engine"])

@router.get("/candidate/{candidate_id}/logs", response_model=List[EmailLogResponse])
def get_candidate_logs(candidate_id: int, db: Session = Depends(get_db)):
    """
    Fetch email communication log history for a specific candidate.
    """
    logs = db.query(EmailLog).filter(EmailLog.candidate_id == candidate_id).order_by(EmailLog.created_at.desc()).all()
    return logs

@router.get("/recruiter/logs", response_model=List[EmailLogResponse])
def get_recruiter_logs(db: Session = Depends(get_db)):
    """
    Fetch all sent/pending/failed email logs for recruiter dashboard.
    """
    logs = db.query(EmailLog).order_by(EmailLog.created_at.desc()).all()
    return logs

@router.get("/recruiter/stats", response_model=EmailStatsResponse)
def get_email_stats(db: Session = Depends(get_db)):
    """
    Retrieve counts of sent, failed, and pending emails.
    """
    sent = db.query(EmailLog).filter(EmailLog.status == "Sent").count()
    failed = db.query(EmailLog).filter(EmailLog.status == "Failed").count()
    pending = db.query(EmailLog).filter(EmailLog.status == "Pending").count()
    return EmailStatsResponse(total_sent=sent, total_failed=failed, total_pending=pending)

@router.post("/logs/{log_id}/resend", response_model=ResendResponse)
def resend_email(log_id: int, db: Session = Depends(get_db)):
    """
    Resets the email status to Pending and triggers a background resend.
    """
    log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Email log record not found.")

    # Rebuild context for LLM if we need to regenerate
    context = {
        "candidate_name": "",
        "candidate_code": "",
        "job_title": "",
        "company_name": "AIHire",
        "recruiter_name": "",
        "aptitude_score": None,
        "coding_score": None,
        "interview_score": None,
        "interview_status": None,
        "workflow_stage": log.email_type,
        "company_logo": "https://cdn-icons-png.flaticon.com/512/3850/3850285.png",
        "candidate_id": log.candidate_id
    }

    if log.candidate_id:
        from modules.candidate.profile.model import CandidateProfile
        from modules.coding_assessment.models import CodingResult
        
        cand_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == log.candidate_id).first()
        if cand_profile:
            context["candidate_name"] = cand_profile.full_name
            context["candidate_code"] = cand_profile.candidate_code or f"AIH{cand_profile.id:04d}"
            context["aptitude_score"] = cand_profile.aptitude_score
            context["interview_score"] = cand_profile.interview_score
            context["interview_status"] = cand_profile.interview_status
            
            try:
                coding_res = db.query(CodingResult).filter(CodingResult.candidate_id == log.candidate_id).order_by(CodingResult.created_at.desc()).first()
                if coding_res:
                    context["coding_score"] = int(coding_res.total_score)
            except Exception:
                pass
                
        # Try getting last application to find job title
        from modules.job_management.model import Application
        app = db.query(Application).filter(Application.candidate_id == log.candidate_id).order_by(Application.created_at.desc()).first()
        if app:
            from modules.job_management.model import Job
            job = db.query(Job).filter(Job.id == app.job_id).first()
            if job:
                context["job_title"] = job.title
                context["job_id"] = job.id

    # Reset log state
    log.status = "Pending"
    log.error_message = None
    db.commit()

    # Dispatch to background thread
    thread = threading.Thread(
        target=process_email_generation_and_send,
        args=(log.id, context)
    )
    thread.start()

    return ResendResponse(
        success=True,
        message="Email resend task dispatched successfully in the background.",
        log_id=log_id
    )
