import logging
from datetime import datetime, date, time
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .model import InterviewSchedule
from .schema import InterviewScheduleCreate, InterviewScheduleUpdate

from modules.auth.model import User
from modules.job_management.model import Job, Application
from modules.candidate.profile.model import CandidateProfile
from modules.email_automation.triggers import trigger_email

logger = logging.getLogger(__name__)

class InterviewSchedulingLogic:
    @staticmethod
    def create_interview(db: Session, create_data: InterviewScheduleCreate) -> InterviewSchedule:
        # Retrieve candidate profile
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == create_data.candidate_id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate profile with User ID {create_data.candidate_id} not found."
            )

        # Retrieve job details
        job = db.query(Job).filter(Job.id == create_data.job_id).first()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {create_data.job_id} not found."
            )

        candidate_code = profile.candidate_code or f"AIH{create_data.candidate_id:04d}"

        # Validate meeting link
        if create_data.interview_mode in ["Online", "Hybrid"] and not create_data.meeting_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting link is required for Online and Hybrid interviews."
            )
        meeting_link = create_data.meeting_link

        interview = InterviewSchedule(
            candidate_id=create_data.candidate_id,
            candidate_code=candidate_code,
            job_id=create_data.job_id,
            recruiter_id=create_data.recruiter_id,
            hr_id=create_data.hr_id,
            interview_title=create_data.interview_title,
            interviewer_name=create_data.interviewer_name,
            interviewer_email=create_data.interviewer_email,
            duration_minutes=create_data.duration_minutes,
            interview_date=create_data.interview_date,
            interview_time=create_data.interview_time,
            interview_mode=create_data.interview_mode,
            meeting_link=meeting_link,
            interview_notes=create_data.interview_notes,
            status="Scheduled"
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)

        # Update application status
        application = db.query(Application).filter(
            Application.candidate_id == create_data.candidate_id,
            Application.job_id == create_data.job_id
        ).first()
        if application:
            application.status = "Interview Scheduled"
            db.commit()

        # Trigger INTERVIEW_SCHEDULED email
        trigger_email(
            event_type="INTERVIEW_SCHEDULED",
            candidate_id=interview.candidate_id,
            recruiter_id=interview.recruiter_id,
            job_id=interview.job_id,
            context={
                "candidate_name": profile.full_name,
                "candidate_code": candidate_code,
                "job_title": job.title,
                "interview_title": interview.interview_title,
                "interviewer_name": interview.interviewer_name,
                "interview_date": str(interview.interview_date),
                "interview_time": str(interview.interview_time),
                "interview_mode": interview.interview_mode,
                "meeting_link": interview.meeting_link,
                "google_meet_link": interview.meeting_link,
                "duration_minutes": interview.duration_minutes,
                "interview_notes": interview.interview_notes,
                "additional_notes": interview.interview_notes
            },
            db=db
        )

        # Trigger INTERVIEW_SCHEDULED email to HR
        trigger_email(
            event_type="INTERVIEW_SCHEDULED",
            candidate_id=None,
            recruiter_id=interview.recruiter_id,
            job_id=interview.job_id,
            context={
                "candidate_name": profile.full_name,
                "candidate_code": candidate_code,
                "job_title": job.title,
                "interview_title": interview.interview_title,
                "interviewer_name": interview.interviewer_name,
                "interview_date": str(interview.interview_date),
                "interview_time": str(interview.interview_time),
                "interview_mode": interview.interview_mode,
                "meeting_link": interview.meeting_link,
                "google_meet_link": interview.meeting_link,
                "duration_minutes": interview.duration_minutes,
                "interview_notes": interview.interview_notes,
                "additional_notes": interview.interview_notes
            },
            db=db
        )

        return interview

    @staticmethod
    def get_interviews_by_candidate(db: Session, candidate_id: int) -> List[InterviewSchedule]:
        interviews = db.query(InterviewSchedule).filter(InterviewSchedule.candidate_id == candidate_id).order_by(InterviewSchedule.interview_date.asc(), InterviewSchedule.interview_time.asc()).all()
        from modules.company_profile.model import CompanyProfile
        for interview in interviews:
            company = db.query(CompanyProfile).filter(CompanyProfile.user_id == interview.recruiter_id).first()
            if company:
                interview.company_name = company.company_name
            job = db.query(Job).filter(Job.id == interview.job_id).first()
            if job:
                interview.job_title = job.title
        return interviews

    @staticmethod
    def get_interviews_by_recruiter(db: Session, recruiter_id: int) -> List[InterviewSchedule]:
        interviews = db.query(InterviewSchedule).filter(InterviewSchedule.recruiter_id == recruiter_id).order_by(InterviewSchedule.interview_date.asc(), InterviewSchedule.interview_time.asc()).all()
        from modules.company_profile.model import CompanyProfile
        for interview in interviews:
            profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == interview.candidate_id).first()
            job = db.query(Job).filter(Job.id == interview.job_id).first()
            company = db.query(CompanyProfile).filter(CompanyProfile.user_id == interview.recruiter_id).first()
            if profile:
                interview.candidate_name = profile.full_name
            if job:
                interview.job_title = job.title
            if company:
                interview.company_name = company.company_name
        return interviews

    @staticmethod
    def update_interview(db: Session, interview_id: int, update_data: InterviewScheduleUpdate) -> InterviewSchedule:
        interview = db.query(InterviewSchedule).filter(InterviewSchedule.id == interview_id).first()
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview Schedule with ID {interview_id} not found."
            )

        original_status = interview.status
        original_date = interview.interview_date
        original_time = interview.interview_time

        # Validate meeting link
        final_mode = update_data.interview_mode if update_data.interview_mode is not None else interview.interview_mode
        final_link = update_data.meeting_link if update_data.meeting_link is not None else interview.meeting_link
        if final_mode in ["Online", "Hybrid"] and not final_link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Meeting link is required for Online and Hybrid interviews."
            )

        # Update fields if provided
        for field, val in update_data.model_dump(exclude_unset=True).items():
            setattr(interview, field, val)

        # Auto transition to Rescheduled if date/time changed and not explicitly updating status
        if (interview.interview_date != original_date or interview.interview_time != original_time) and update_data.status is None:
            interview.status = "Rescheduled"

        db.commit()
        db.refresh(interview)

        # Retrieve job and candidate details for email context
        job = db.query(Job).filter(Job.id == interview.job_id).first()
        job_title = job.title if job else "Position"

        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == interview.candidate_id).first()
        cand_name = profile.full_name if profile else "Candidate"
        candidate_code = interview.candidate_code or (profile.candidate_code if profile else f"AIH{interview.candidate_id:04d}")

        # Send email notifications based on status updates
        if interview.status != original_status or interview.status == "Rescheduled":
            event_type = f"INTERVIEW_{interview.status.upper()}"
            # Support event types: INTERVIEW_CONFIRMED, INTERVIEW_RESCHEDULED, INTERVIEW_CANCELLED, INTERVIEW_COMPLETED
            if event_type in ["INTERVIEW_CONFIRMED", "INTERVIEW_RESCHEDULED", "INTERVIEW_CANCELLED", "INTERVIEW_COMPLETED"]:
                trigger_email(
                    event_type=event_type,
                    candidate_id=interview.candidate_id,
                    recruiter_id=interview.recruiter_id,
                    job_id=interview.job_id,
                    context={
                        "candidate_name": cand_name,
                        "candidate_code": candidate_code,
                        "job_title": job_title,
                        "interview_title": interview.interview_title,
                        "interviewer_name": interview.interviewer_name,
                        "interview_date": str(interview.interview_date),
                        "interview_time": str(interview.interview_time),
                        "interview_mode": interview.interview_mode,
                        "meeting_link": interview.meeting_link,
                        "google_meet_link": interview.meeting_link,
                        "duration_minutes": interview.duration_minutes,
                        "interview_notes": interview.interview_notes,
                        "additional_notes": interview.interview_notes
                    },
                    db=db
                )

        return interview

    @staticmethod
    def execute_final_decision(db: Session, interview_id: int, decision: str, notes: Optional[str] = None) -> InterviewSchedule:
        """
        Executes final selection, final rejection, or offer letter release.
        decision parameter must be one of: Selection, Rejection, OfferReleased
        """
        interview = db.query(InterviewSchedule).filter(InterviewSchedule.id == interview_id).first()
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Interview with ID {interview_id} not found."
            )

        # Update application status
        application = db.query(Application).filter(
            Application.candidate_id == interview.candidate_id,
            Application.job_id == interview.job_id
        ).first()

        job = db.query(Job).filter(Job.id == interview.job_id).first()
        job_title = job.title if job else "Position"

        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == interview.candidate_id).first()
        cand_name = profile.full_name if profile else "Candidate"
        candidate_code = interview.candidate_code or (profile.candidate_code if profile else f"AIH{interview.candidate_id:04d}")

        if decision == "Selection":
            if application:
                application.status = "Selected"
            interview.status = "Completed"
            event_type = "FINAL_SELECTION"
        elif decision == "Rejection":
            if application:
                application.status = "Rejected"
            interview.status = "Completed"
            event_type = "FINAL_REJECTION"
        elif decision == "OfferReleased":
            if application:
                application.status = "Offer Released"
            interview.status = "Completed"
            event_type = "OFFER_RELEASED"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid decision. Must be one of: Selection, Rejection, OfferReleased"
            )

        db.commit()

        # Trigger final workflow emails
        trigger_email(
            event_type=event_type,
            candidate_id=interview.candidate_id,
            recruiter_id=interview.recruiter_id,
            job_id=interview.job_id,
            context={
                "candidate_name": cand_name,
                "candidate_code": candidate_code,
                "job_title": job_title,
                "notes": notes,
                "comments": notes
            },
            db=db
        )

        return interview
