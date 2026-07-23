import os
import json
import logging
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from sqlalchemy.orm import Session

from modules.job_management.model import EmailLog

logger = logging.getLogger(__name__)

# Fallback email templates
FALLBACK_TEMPLATES = {
    "Application Submitted": {
        "subject": "Application Received: {job_title} at {company_name}",
        "body": "Dear {candidate_name},\n\nThank you for applying for the position of {job_title} at {company_name}. We have received your application and will review your profile shortly.\n\nBest regards,\n{company_name} Recruitment Team"
    },
    "Shortlisted": {
        "subject": "Application Status Update: {job_title} at {company_name}",
        "body": "Dear {candidate_name},\n\nWe are pleased to inform you that your application for the {job_title} position at {company_name} has been shortlisted. Our recruiting team will contact you soon to arrange the next steps.\n\nBest regards,\n{company_name} Recruitment Team"
    },
    "Rejected": {
        "subject": "Update on your application: {job_title} at {company_name}",
        "body": "Dear {candidate_name},\n\nThank you for your interest in the {job_title} position at {company_name}. After careful consideration, we regret to inform you that we will not be moving forward with your application at this time.\n\nReason for rejection: {extra_details}\n\nWe wish you the best in your career pursuits.\n\nBest regards,\n{company_name} Recruitment Team"
    },
    "Assessment Invitation": {
        "subject": "Assessment Invitation: {job_title} at {company_name}",
        "body": "Dear {candidate_name},\n\nYou are invited to complete the online assessment for the {job_title} role at {company_name}.\n\nDetails / Link: {extra_details}\n\nPlease complete this at your earliest convenience.\n\nBest regards,\n{company_name} Recruitment Team"
    },
    "Assessment Reminder": {
        "subject": "Reminder: Online Assessment for {job_title} at {company_name}",
        "body": "Dear {candidate_name},\n\nThis is a reminder to complete your online assessment for the {job_title} role at {company_name}.\n\nDetails / Link: {extra_details}\n\nBest regards,\n{company_name} Recruitment Team"
    },
    "Assessment Result": {
        "subject": "Assessment Results Reviewed: {job_title} at {company_name}",
        "body": "Dear {candidate_name},\n\nThank you for completing the assessment for the {job_title} role at {company_name}. We have received your results and are currently reviewing them.\n\nDetails: {extra_details}\n\nBest regards,\n{company_name} Recruitment Team"
    },
    "Interview Invitation": {
        "subject": "Interview Invitation: {job_title} at {company_name}",
        "body": "Dear {candidate_name},\n\nWe would like to schedule an interview with you for the {job_title} position at {company_name}.\n\nInterview Details: {extra_details}\n\nOur team will send a calendar invite shortly.\n\nBest regards,\n{company_name} Recruitment Team"
    },
    "Interview Reminder": {
        "subject": "Reminder: Upcoming Interview for {job_title} at {company_name}",
        "body": "Dear {candidate_name},\n\nThis is a friendly reminder of your upcoming interview for the {job_title} position at {company_name}.\n\nDetails: {extra_details}\n\nBest regards,\n{company_name} Recruitment Team"
    },
    "Offer Letter": {
        "subject": "Job Offer: {job_title} at {company_name}",
        "body": "Dear {candidate_name},\n\nWe are excited to offer you the position of {job_title} at {company_name}!\n\nOffer Details: {extra_details}\n\nWe look forward to welcoming you to the team. Please review the offer and let us know your decision.\n\nBest regards,\n{company_name} Recruitment Team"
    }
}


def send_automated_email(
    db: Session,
    user_id: int,
    event_type: str,
    job_title: str,
    company_name: str,
    recipient_name: str,
    email_to: str,
    extra_details: Optional[str] = None
) -> bool:
    """
    Compatibility wrapper forwarding to the new centralized Email Trigger Service.
    """
    from modules.email_automation.triggers import trigger_email
    
    # Map event_type to supported new event types
    event_mapping = {
        "Registration Successful": "Candidate Registration",
        "Profile Completed": "Candidate Registration",
        "Resume Uploaded": "Resume Successfully Uploaded",
        "Job Posted": "Job Posted",
        "Application Submitted": "Job Application Submitted",
        "Application Received": "HR_REVIEW_REQUESTED",
        "Assessment Invitation": "Aptitude Assessment Invitation",
        "Assessment Reminder": "Aptitude Assessment Invitation",
        "Assessment Result": "Aptitude Assessment Result",
        "Interview Invitation": "Interview Invitation",
        "Interview Reminder": "Interview Invitation",
        "Offer Letter": "Offer Letter Release",
        "Shortlisted": "Shortlisted Notification",
        "Rejected": "Rejection Notification",
        "Hiring Recommendation Generated": "HR_REVIEW_REQUESTED"
    }
    
    mapped_event = event_mapping.get(event_type, event_type)
    
    # Resolve candidate or recruiter ID from user_id
    from modules.auth.model import User
    user = db.query(User).filter(User.id == user_id).first()
    candidate_id = None
    recruiter_id = None
    if user:
        if user.role == "candidate":
            candidate_id = user.id
        else:
            recruiter_id = user.id
            
    # Try finding job by title
    job_id = None
    if job_title:
        from modules.job_management.model import Job
        job = db.query(Job).filter(Job.title == job_title).first()
        if job:
            job_id = job.id
            
    # Run trigger service
    trigger_email(
        event_type=mapped_event,
        candidate_id=candidate_id,
        recruiter_id=recruiter_id,
        job_id=job_id,
        context={
            "recipient_email": email_to,
            "recipient_name": recipient_name,
            "job_title": job_title,
            "company_name": company_name,
            "extra_details": extra_details
        },
        db=db
    )
    return True
