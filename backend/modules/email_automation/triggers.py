import os
import threading
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from core.database import SessionLocal

from .models import EmailLog
from .email_logger import log_email_pending, has_duplicate_email
from .service import process_email_generation_and_send
from modules.candidate.profile.model import CandidateProfile
from modules.company_profile.model import CompanyProfile
from modules.job_management.model import Job
from modules.coding_assessment.models import CodingResult
from modules.interview_assessment.models import InterviewResult
from modules.auth.model import User

logger = logging.getLogger(__name__)

def trigger_email(
    event_type: str,
    candidate_id: Optional[int],
    recruiter_id: Optional[int] = None,
    job_id: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None,
    background_tasks: Optional[Any] = None
) -> Optional[int]:
    """
    Centralized email trigger service. Inserts a Pending record, gathers context,
    and runs email generation and delivery in the background (Thread or BackgroundTasks).
    """
    logger.info(f"Triggering email for Event: {event_type}, Candidate: {candidate_id}, Job: {job_id}")
    
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # 1. Resolve Recipient Email
        recipient_email = None
        
        # Define recruiter-facing events that should go to the recruiter/HR
        recruiter_events = {
            "OFFER_GENERATED",
            "OFFER_ACCEPTED",
            "OFFER_REJECTED",
            "OFFER_JOINED",
            "OFFER_HIRED",
            "HR_REVIEW_REQUESTED"
        }
        
        if recruiter_id and event_type in recruiter_events:
            user = db.query(User).filter(User.id == recruiter_id).first()
            if user:
                company = db.query(CompanyProfile).filter(CompanyProfile.user_id == recruiter_id).first()
                if company and company.company_email:
                    recipient_email = company.company_email
                else:
                    recipient_email = user.email
                    
        if not recipient_email:
            if candidate_id:
                # Query candidate user
                user = db.query(User).filter(User.id == candidate_id).first()
                if user:
                    recipient_email = user.email
            elif recruiter_id:
                user = db.query(User).filter(User.id == recruiter_id).first()
                if user:
                    # Prioritize company email for recruiter notifications
                    company = db.query(CompanyProfile).filter(CompanyProfile.user_id == recruiter_id).first()
                    if company and company.company_email:
                        recipient_email = company.company_email
                    else:
                        recipient_email = user.email
                
        if not recipient_email and context:
            recipient_email = context.get("recipient_email") or context.get("email_to")
            
        if not recipient_email:
            logger.error(f"Cannot trigger email for {event_type}: recipient email could not be resolved.")
            return None

        # 2. Duplicate Prevention
        if has_duplicate_email(db, recipient_email, event_type, candidate_id, job_id):
            logger.info(f"Duplicate email prevented for {recipient_email} - {event_type}")
            return None

        # 3. Create Pending Log Record
        log_id = log_email_pending(db, recipient_email, event_type, candidate_id)

        # 4. Gather/Resolve Context Variables
        resolved_context = {
            "candidate_name": "",
            "candidate_code": "",
            "job_title": "",
            "company_name": "AIHire",
            "recruiter_name": "",
            "aptitude_score": None,
            "coding_score": None,
            "interview_score": None,
            "interview_status": None,
            "workflow_stage": event_type,
            "company_logo": "https://cdn-icons-png.flaticon.com/512/3850/3850285.png",
            "job_id": job_id,
            "candidate_id": candidate_id
        }

        # Apply user context overrides
        if context:
            resolved_context.update(context)

        # Query Candidate Data
        if candidate_id:
            cand_profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
            if cand_profile:
                if not resolved_context["candidate_name"]:
                    resolved_context["candidate_name"] = cand_profile.full_name
                if not resolved_context["candidate_code"]:
                    resolved_context["candidate_code"] = cand_profile.candidate_code or f"AIH{cand_profile.id:04d}"
                if resolved_context["aptitude_score"] is None:
                    resolved_context["aptitude_score"] = cand_profile.aptitude_score
                if resolved_context["interview_score"] is None:
                    resolved_context["interview_score"] = cand_profile.interview_score
                if resolved_context["interview_status"] is None:
                    resolved_context["interview_status"] = cand_profile.interview_status

                # Fetch Coding Score
                try:
                    coding_res = db.query(CodingResult).filter(CodingResult.candidate_id == candidate_id).order_by(CodingResult.created_at.desc()).first()
                    if coding_res and resolved_context["coding_score"] is None:
                        resolved_context["coding_score"] = int(coding_res.total_score)
                except Exception:
                    pass

        # Query Job & Company Data
        if job_id:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                if not resolved_context["job_title"]:
                    resolved_context["job_title"] = job.title

        # Query Company Profile (from Recruiter / Workspace profile)
        company_profile = None
        if recruiter_id:
            company_profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == recruiter_id).first()
        if not company_profile:
            # Fallback: get first company profile
            company_profile = db.query(CompanyProfile).first()
            
        if company_profile:
            if not resolved_context.get("company_name") or resolved_context["company_name"] == "AIHire":
                resolved_context["company_name"] = company_profile.company_name
            if not resolved_context.get("company_logo") or "flaticon" in resolved_context["company_logo"]:
                resolved_context["company_logo"] = company_profile.logo_url or resolved_context["company_logo"]
            if recruiter_id and not resolved_context.get("recruiter_name"):
                rec_user = db.query(User).filter(User.id == recruiter_id).first()
                if rec_user:
                    resolved_context["recruiter_name"] = rec_user.full_name or "Hiring Manager"

        # 5. Dispatch Async Task (No Business Workflow Blocking)
        if background_tasks:
            logger.info(f"Dispatching email task #{log_id} to FastAPI BackgroundTasks.")
            background_tasks.add_task(process_email_generation_and_send, log_id, resolved_context)
        else:
            logger.info(f"Spawning background Thread for email task #{log_id}.")
            thread = threading.Thread(
                target=process_email_generation_and_send,
                args=(log_id, resolved_context)
            )
            thread.start()

        return log_id
    except Exception as e:
        logger.error(f"Failed to trigger email notification flow: {e}")
        return None
    finally:
        if close_db:
            db.close()
