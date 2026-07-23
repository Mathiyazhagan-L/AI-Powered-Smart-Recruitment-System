import logging
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .model import HRReview
from .schema import HRReviewCreate, HRReviewUpdate

from modules.auth.model import User
from modules.job_management.model import Job, Application
from modules.candidate.profile.model import CandidateProfile
from modules.candidate.resume.model import CandidateResume
from modules.assessment.models import AssessmentResult
from modules.coding_assessment.models import CodingResult
from modules.interview_assessment.models import InterviewResult
from modules.email_automation.triggers import trigger_email

logger = logging.getLogger(__name__)

class HRReviewLogic:
    @staticmethod
    def get_candidate_code(db: Session, candidate_id: int) -> str:
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
        if profile and profile.candidate_code:
            return profile.candidate_code
        return f"AIH{candidate_id:04d}"

    @staticmethod
    def request_hr_review(db: Session, review_data: HRReviewCreate) -> HRReview:
        # 1. Profile Complete Verification
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == review_data.candidate_id).first()
        if not profile or not profile.profile_completion or profile.profile_completion != 100:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Candidate must complete Profile before HR Review"
            )

        # 2. Resume Uploaded Verification
        resume = db.query(CandidateResume).filter(CandidateResume.user_id == review_data.candidate_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Candidate must upload Resume before HR Review"
            )

        # 3. Aptitude Completed Verification
        apt_res = db.query(AssessmentResult).filter(AssessmentResult.candidate_id == review_data.candidate_id).first()
        if not apt_res or apt_res.status != "PASSED":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Candidate must complete Aptitude Assessment before HR Review"
            )

        # 4. Coding Completed Verification
        coding_res = db.query(CodingResult).filter(CodingResult.candidate_id == review_data.candidate_id).first()
        if not coding_res or coding_res.status != "PASS":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Candidate must complete Coding Assessment before HR Review"
            )

        # 5. Interview Assessment Completed Verification
        interview_res = db.query(InterviewResult).filter(InterviewResult.candidate_id == review_data.candidate_id).first()
        if not interview_res:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Candidate must complete Interview Assessment before HR Review"
            )

        # 6. Candidate Applied For Job Verification
        application = db.query(Application).filter(
            Application.candidate_id == review_data.candidate_id,
            Application.job_id == review_data.job_id
        ).first()
        if not application:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Candidate must apply for Job before HR Review"
            )

        # Retrieve scores for snapshot
        github_score = float(profile.github_score) if profile.github_score is not None else 0.0
        ats_score = float(application.ats_score) if application.ats_score is not None else 0.0
        aptitude_score = float(apt_res.aptitude_score) if apt_res.aptitude_score is not None else 0.0
        coding_score = float(coding_res.total_score) if coding_res.total_score is not None else 0.0
        interview_score = float(interview_res.total_score) if interview_res.total_score is not None else 0.0

        # Calculate weighted overall score
        # 15% ATS, 15% GitHub, 20% Aptitude, 25% Coding, 25% Interview
        overall_score = round(
            (ats_score * 0.15) +
            (github_score * 0.15) +
            (aptitude_score * 0.20) +
            (coding_score * 0.25) +
            (interview_score * 0.25),
            2
        )

        candidate_code = HRReviewLogic.get_candidate_code(db, review_data.candidate_id)

        # Check if review already exists
        existing_review = db.query(HRReview).filter(
            HRReview.candidate_id == review_data.candidate_id,
            HRReview.job_id == review_data.job_id
        ).first()

        if existing_review:
            # Update fields and set back to Pending
            existing_review.recruiter_id = review_data.recruiter_id
            existing_review.comments = review_data.comments
            existing_review.review_status = "Pending"
            existing_review.aptitude_score = aptitude_score
            existing_review.coding_score = coding_score
            existing_review.interview_score = interview_score
            existing_review.github_score = github_score
            existing_review.ats_score = ats_score
            existing_review.overall_score = overall_score
            existing_review.candidate_code = candidate_code
            review = existing_review
        else:
            review = HRReview(
                candidate_id=review_data.candidate_id,
                candidate_code=candidate_code,
                job_id=review_data.job_id,
                recruiter_id=review_data.recruiter_id,
                aptitude_score=aptitude_score,
                coding_score=coding_score,
                interview_score=interview_score,
                github_score=github_score,
                ats_score=ats_score,
                overall_score=overall_score,
                review_status="Pending",
                comments=review_data.comments
            )
            db.add(review)

        db.commit()
        db.refresh(review)

        # Populate dynamic properties for HRReviewResponse serialization
        review.candidate_name = profile.full_name if profile else f"Candidate #{review.candidate_id}"
        job = db.query(Job).filter(Job.id == review.job_id).first()
        review.job_title = job.title if job else f"Job #{review.job_id}"
        review.ats = review.ats_score
        review.tech = review.coding_score
        review.status = review.review_status
        review.notes = review.comments

        # Trigger HR_REVIEW_REQUESTED email to recruiter/HR manager
        trigger_email(
            event_type="HR_REVIEW_REQUESTED",
            candidate_id=review.candidate_id,
            recruiter_id=review.recruiter_id,
            job_id=review.job_id,
            context={
                "candidate_name": profile.full_name,
                "candidate_code": candidate_code,
                "overall_score": overall_score,
                "comments": review.comments
            },
            db=db
        )

        return review

    @staticmethod
    def get_hr_queue(db: Session, status_filter: Optional[str] = None) -> List[HRReview]:
        # Sync applications in HR-relevant statuses to ensure they have an HRReview record
        try:
            from modules.job_management.model import Application
            from modules.hr_review.schema import HRReviewCreate
            
            # Find all applications with relevant statuses
            hr_apps = db.query(Application).filter(
                Application.status.in_(["AI Recommendation", "Recruiter Review", "HR Interview"])
            ).all()
            for app in hr_apps:
                # Check if HRReview record already exists
                existing = db.query(HRReview).filter(
                    HRReview.candidate_id == app.candidate_id,
                    HRReview.job_id == app.job_id
                ).first()
                if not existing:
                    from modules.auth.model import User
                    rec_user = db.query(User).filter(User.role == "recruiter").first()
                    rec_id = rec_user.id if rec_user else 1
                    
                    review_data = HRReviewCreate(
                        candidate_id=app.candidate_id,
                        job_id=app.job_id,
                        recruiter_id=rec_id,
                        comments="Auto-synced on loading HR queue."
                    )
                    try:
                        HRReviewLogic.request_hr_review(db, review_data)
                        logger.info(f"Auto-synced candidate {app.candidate_id} to HR review queue.")
                    except Exception:
                        pass
        except Exception as sync_ex:
            logger.error(f"Error during HR queue sync: {sync_ex}")

        # Clean up any HRReview records where the candidate's application is rejected
        try:
            from modules.job_management.model import Application
            rejected_apps = db.query(Application).filter(
                (Application.status == "Rejected") | (Application.status.like("%Rejected%")) | (Application.status.like("%rejected%"))
            ).all()
            for app in rejected_apps:
                db.query(HRReview).filter(
                    HRReview.candidate_id == app.candidate_id,
                    HRReview.job_id == app.job_id
                ).delete(synchronize_session=False)
            db.commit()
        except Exception as del_ex:
            logger.error(f"Error cleaning up rejected applications from HR review queue: {del_ex}")

        query = db.query(HRReview)
        if status_filter:
            query = query.filter(HRReview.review_status == status_filter)
        reviews = query.order_by(HRReview.created_at.desc()).all()
        for r in reviews:
            profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == r.candidate_id).first()
            job = db.query(Job).filter(Job.id == r.job_id).first()
            r.candidate_name = profile.full_name if profile else f"Candidate #{r.candidate_id}"
            r.job_title = job.title if job else f"Job #{r.job_id}"
            r.ats = r.ats_score
            r.tech = r.coding_score
            r.status = r.review_status
            r.notes = r.comments
        return reviews

    @staticmethod
    def update_hr_review_status(db: Session, review_id: int, update_data: HRReviewUpdate) -> HRReview:
        review = db.query(HRReview).filter(HRReview.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"HR Review with ID {review_id} not found."
            )

        review_status = update_data.status or update_data.review_status or "Pending"
        comments = update_data.notes or update_data.comments

        review.review_status = review_status
        review.comments = comments
        review.reviewed_by = update_data.reviewed_by or review.recruiter_id or 1
        review.reviewed_at = datetime.utcnow()

        # Update candidate application status
        application = db.query(Application).filter(
            Application.candidate_id == review.candidate_id,
            Application.job_id == review.job_id
        ).first()
        if application:
            application.status = f"HR {review.review_status}"
            db.commit()

        db.commit()
        db.refresh(review)

        # Retrieve candidate profile for name
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == review.candidate_id).first()
        cand_name = profile.full_name if profile else "Candidate"
        job = db.query(Job).filter(Job.id == review.job_id).first()

        # Populate dynamic properties for response
        review.candidate_name = cand_name
        review.job_title = job.title if job else f"Job #{review.job_id}"
        review.ats = review.ats_score
        review.tech = review.coding_score
        review.status = review.review_status
        review.notes = review.comments

        # Trigger email based on new status
        if review.review_status == "Approved":
            trigger_email(
                event_type="HR_APPROVED",
                candidate_id=review.candidate_id,
                recruiter_id=review.recruiter_id,
                job_id=review.job_id,
                context={
                    "candidate_name": cand_name,
                    "comments": review.comments
                },
                db=db
            )
        elif review.review_status == "Rejected":
            trigger_email(
                event_type="HR_REJECTED",
                candidate_id=review.candidate_id,
                recruiter_id=review.recruiter_id,
                job_id=review.job_id,
                context={
                    "candidate_name": cand_name,
                    "comments": review.comments
                },
                db=db
            )

        return review
