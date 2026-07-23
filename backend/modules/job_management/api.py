from typing import List, Optional
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .model import (
    JobResponse, JobCreate, JobUpdate, Job,
    Application, ApplicationResponse, ApplicationStatusUpdate
)
from . import logic
from core.database import get_db
from modules.auth.model import User
from modules.candidate.profile.model import CandidateProfile
from .model import SavedJob, SavedJobResponse
from modules.ai_evaluation.services.scoring_service import calculate_ats_score
from modules.ml_prediction.service import predict_candidate_suitability
from modules.ai_evaluation.services.recommendation_service import generate_recommendations
from modules.job_management.email_logic import send_automated_email
from modules.company_profile.api import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["Job Management"])


# ==========================================
# Endpoints
# ==========================================

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """
    Create a new job post in 'draft' status by default.
    Performs field validations and rule checks.
    Requires complete company profile.
    """
    from modules.company_profile.model import CompanyProfile
    from modules.company_profile.logic import is_company_profile_complete

    profile = db.query(CompanyProfile).filter(CompanyProfile.user_id == user_id).first()
    if not profile or not is_company_profile_complete(profile):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complete Company Profile before posting jobs."
        )

    try:
        return logic.create_job(db=db, job_data=job_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/analytics", response_model=dict)
def get_job_analytics(db: Session = Depends(get_db)):
    """
    Retrieve statistics and analytics for all job postings:
    - Status counts (draft, published, closed)
    - Total job openings
    - Location counts
    - Average salary metrics
    """
    return logic.get_job_analytics(db=db)


@router.get("/", response_model=List[JobResponse])
def search_and_filter_jobs(
    search_query: Optional[str] = Query(None, description="Search term for job title/description"),
    status: Optional[str] = Query(None, description="Filter by job status (draft, published, closed)"),
    location: Optional[str] = Query(None, description="Filter by job location"),
    experience: Optional[str] = Query(None, description="Filter by experience text"),
    min_salary: Optional[float] = Query(None, description="Filter by minimum salary value"),
    skills: Optional[List[str]] = Query(None, description="Filter by one or more required skills"),
    db: Session = Depends(get_db)
):
    """
    Search and filter job postings. Supports searching text, status, location, minimum salary, and skills.
    """
    return logic.search_and_filter_jobs(
        db=db,
        search_query=search_query,
        status=status,
        location=location,
        experience=experience,
        min_salary=min_salary,
        skills=skills
    )


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    """
    Get detailed information for a single job post by its ID.
    """
    db_job = logic.get_job_by_id(db=db, job_id=job_id)
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )
    return db_job


@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, job_data: JobUpdate, db: Session = Depends(get_db)):
    """
    Update details of a job post. Partial updates are supported.
    Re-runs validation if active/published status is affected.
    """
    try:
        db_job = logic.update_job(db=db, job_id=job_id, job_data=job_data)
        if not db_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found."
            )
        return db_job
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{job_id}", status_code=status.HTTP_200_OK)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """
    Delete a job post.
    """
    success = logic.delete_job(db=db, job_id=job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )
    return {"detail": "Job successfully deleted.", "job_id": job_id}


@router.post("/{job_id}/publish", response_model=JobResponse)
def publish_job(job_id: int, db: Session = Depends(get_db)):
    """
    Publish a draft job post. Performs final validation.
    """
    try:
        db_job = logic.publish_job(db=db, job_id=job_id)
        if not db_job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID {job_id} not found."
            )
        return db_job
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{job_id}/close", response_model=JobResponse)
def close_job(job_id: int, db: Session = Depends(get_db)):
    """
    Close a job post. Applications will no longer be accepted.
    """
    db_job = logic.close_job(db=db, job_id=job_id)
    if not db_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )
    return db_job


# ==========================================
# 4. Job Applications Endpoints
# ==========================================

@router.get("/candidate/{candidate_id}/eligibility", response_model=dict)
def check_candidate_eligibility(candidate_id: int, db: Session = Depends(get_db)):
    """
    Check if the candidate meets all recruitment workflow eligibility rules.
    Returns eligibility details and reasons.
    """
    user = db.query(User).filter(User.id == candidate_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate user with ID {candidate_id} not found.")

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    
    profile_complete = (profile is not None) and (profile.profile_completion == 100)

    # Resume Check (multiple conditions)
    from modules.candidate.resume.model import CandidateResume
    from modules.resume_parser.model import ResumeParserResult
    candidate_resume = db.query(CandidateResume).filter(CandidateResume.user_id == candidate_id).first()
    parser_resume = db.query(ResumeParserResult).filter(
        ResumeParserResult.candidate_id == candidate_id
    ).order_by(ResumeParserResult.created_at.desc()).first()

    cond1 = candidate_resume is not None
    cond2 = bool((candidate_resume and candidate_resume.resume_path) or (parser_resume and parser_resume.resume_file))
    cond3 = bool(parser_resume and parser_resume.parsing_status == "completed")
    resume_uploaded = bool(cond1 or cond2 or cond3)

    # Aptitude Check
    from modules.assessment.models import AssessmentResult
    aptitude_res = db.query(AssessmentResult).filter(
        AssessmentResult.candidate_id == candidate_id,
        AssessmentResult.status == "PASSED"
    ).first()
    aptitude_completed = aptitude_res is not None

    # Coding Check
    from modules.coding_assessment.models import CodingResult
    coding_res = db.query(CodingResult).filter(
        CodingResult.candidate_id == candidate_id
    ).first()
    coding_completed = (coding_res is not None) and (coding_res.status in ["PASS", "FAIL", "COMPLETED"])

    # Interview Check
    from modules.interview_assessment.models import InterviewResult
    interview_res = db.query(InterviewResult).filter(
        InterviewResult.candidate_id == candidate_id
    ).first()
    interview_completed = (interview_res is not None) and (interview_res.status == "COMPLETED")

    eligible = profile_complete and resume_uploaded and aptitude_completed and coding_completed and interview_completed
    
    # Determine reason
    reason = ""
    if not profile_complete:
        reason = "Complete profile before applying."
    elif not resume_uploaded:
        reason = "Upload resume before applying."
    elif not aptitude_completed:
        reason = "Complete aptitude assessment before applying."
    elif not coding_completed:
        reason = "Complete coding assessment before applying."
    elif not interview_completed:
        reason = "Complete interview assessment before applying."

    return {
        "eligible": eligible,
        "reason": reason,
        "profile_complete": profile_complete,
        "resume_uploaded": resume_uploaded,
        "aptitude_completed": aptitude_completed,
        "coding_completed": coding_completed,
        "interview_completed": interview_completed
    }


@router.post("/{job_id}/apply", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_job(job_id: int, candidate_id: int = Query(..., description="ID of the candidate applying"), db: Session = Depends(get_db)):
    """
    Candidate applies to a job. Calculates ATS & ML suitability prediction, 
    caches recommendations, ranks candidates, sends verification email, and persists the application.
    """
    # 1. Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID {job_id} not found.")

    # 2. Verify candidate user exists
    user = db.query(User).filter(User.id == candidate_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Candidate user with ID {candidate_id} not found.")

    # 3. Verify candidate profile exists
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Please complete your personal profile details first before applying.")

    # 3B. Single Eligibility Gateway
    from modules.candidate.resume.model import CandidateResume
    from modules.resume_parser.model import ResumeParserResult
    from modules.assessment.models import AssessmentResult
    from modules.coding_assessment.models import CodingResult
    from modules.interview_assessment.models import InterviewResult

    # 1. Profile Completion Check
    if not profile.profile_completion or profile.profile_completion < 70:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your profile must be at least 70% complete to apply."
        )

    # 2. Candidate Status Check
    if profile.candidate_status != "VERIFIED":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your candidate status must be VERIFIED to apply."
        )

    # 3. Resume Uploaded & Parsed Check
    candidate_resume = db.query(CandidateResume).filter(CandidateResume.user_id == candidate_id).first()
    parser_resume = db.query(ResumeParserResult).filter(
        ResumeParserResult.candidate_id == candidate_id
    ).order_by(ResumeParserResult.created_at.desc()).first()
    
    has_resume = candidate_resume and candidate_resume.resume_path
    is_parsed = parser_resume and parser_resume.parsing_status == "completed"
    
    if not (has_resume and is_parsed):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must upload a resume and wait for it to be successfully parsed before applying."
        )

    # 4. Assessment checks removed per new workflow - AI screening happens post-application.

    # 4. Check duplicate application
    existing_app = db.query(Application).filter(
        Application.job_id == job_id,
        Application.candidate_id == candidate_id
    ).first()
    if existing_app:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You have already applied to this job.")

    # 5. Run Skill Match and ATS Score calculation
    try:
        from modules.ai_evaluation.services.matching_service import calculate_skill_match
        skill_match_res = calculate_skill_match(candidate_id=candidate_id, job_id=job_id, db=db)
        skill_match_pct = skill_match_res.get("match_percentage", 0)
    except Exception as e:
        logger.error(f"Skill match calculation failed during application: {e}")
        skill_match_pct = 0

    try:
        ats_result = calculate_ats_score(candidate_id=candidate_id, job_id=job_id, db=db)
        ats_score = ats_result.get("ats_score", 0)
    except Exception as e:
        logger.error(f"ATS Score computation failed during application: {e}")
        ats_score = 0

    # 6. Run ML suitability prediction
    try:
        ml_result = predict_candidate_suitability(candidate_id=candidate_id, job_id=job_id, db=db)
        suitability_pred = ml_result.get("prediction", "Average")
    except Exception as e:
        logger.error(f"ML Suitability prediction failed during application: {e}")
        suitability_pred = "Average"

    # 6B. Calculate Overall AI Score based on weights:
    # Component Weights:
    # ATS Score: 30%, Skill Match: 15%, Experience Match: 10%, Aptitude: 10%,
    # Coding: 15%, Professional Assessment: 10%, Integrity Score: 5%, GitHub Score: 5%
    try:
        from modules.candidate.experience.model import CandidateExperience
        from datetime import date
        import re
        
        experiences = db.query(CandidateExperience).filter(CandidateExperience.user_id == candidate_id).all()
        total_months = 0
        for exp in experiences:
            start = exp.start_date
            end = exp.end_date or date.today()
            if start:
                total_months += (end.year - start.year) * 12 + (end.month - start.month)
        exp_years = total_months / 12.0
        
        required_years = 2
        if job and job.experience:
            nums = re.findall(r'\d+', job.experience)
            if nums:
                required_years = int(nums[0])
                
        experience_match = 100.0 if required_years == 0 else min(100.0, (exp_years / required_years) * 100)
        
        # Other scores (Aptitude Assessment)
        from modules.assessment.models import AssessmentResult
        apt_res = db.query(AssessmentResult).filter(AssessmentResult.candidate_id == candidate_id).order_by(AssessmentResult.id.desc()).first()
        if apt_res and apt_res.aptitude_score is not None:
            aptitude_score = apt_res.aptitude_score
        else:
            aptitude_score = profile.aptitude_score if (profile and profile.aptitude_score is not None) else 80.0
        
        # Coding Score
        from modules.coding_assessment.models import CodingResult
        coding_res = db.query(CodingResult).filter(CodingResult.candidate_id == candidate_id).order_by(CodingResult.id.desc()).first()
        coding_score = coding_res.total_score if (coding_res and coding_res.total_score is not None) else 85.0
        
        # Professional Assessment (AI Interview)
        from modules.interview_assessment.models import InterviewResult
        interview_res = db.query(InterviewResult).filter(InterviewResult.candidate_id == candidate_id).order_by(InterviewResult.id.desc()).first()
        if interview_res and interview_res.total_score is not None:
            interview_score = interview_res.total_score
        else:
            interview_score = profile.interview_score if (profile and profile.interview_score is not None) else 80.0
        
        # Proctoring Integrity Score
        from modules.proctoring.models import AssessmentIntegrityResult
        integrity_records = db.query(AssessmentIntegrityResult).filter(AssessmentIntegrityResult.candidate_id == candidate_id).all()
        integrity_score = sum([r.integrity_score for r in integrity_records]) / len(integrity_records) if integrity_records else 95.0
        
        # GitHub Score
        github_score = profile.github_score if (profile and profile.github_score is not None) else 80.0
        
        overall_score = (
            ats_score * 0.30 +
            skill_match_pct * 0.15 +
            experience_match * 0.10 +
            aptitude_score * 0.10 +
            coding_score * 0.15 +
            interview_score * 0.10 +
            integrity_score * 0.05 +
            github_score * 0.05
        )
        overall_score = round(overall_score)
    except Exception as e:
        logger.error(f"Overall AI suitability calculation failed: {e}")
        overall_score = ats_score

    # 7. Auto-Reject and Auto-Progression Logic
    if skill_match_pct < 30:
        initial_status = "Rejected"
        suitability_pred = "Not Recommended"
    else:
        # Auto-update status to next stages based on overall score
        if overall_score >= 90:
            initial_status = "AI Recommendation"
            suitability_pred = "Highly Recommended"
        elif overall_score >= 80:
            initial_status = "AI Recommendation"
            suitability_pred = "Recommended"
        elif overall_score >= 70:
            initial_status = "Recruiter Review"
            suitability_pred = "Consider"
        elif overall_score >= 60:
            initial_status = "AI Screening"
            suitability_pred = "Needs Review"
        else:
            initial_status = "Rejected"
            suitability_pred = "Not Recommended"

    new_app = Application(
        job_id=job_id,
        candidate_id=candidate_id,
        status=initial_status,
        ats_score=overall_score,
        suitability_prediction=suitability_pred,
        ranking=None
    )
    db.add(new_app)
    db.commit()
    db.refresh(new_app)

    # 8. Re-run Ranking to update rank numbers
    try:
        from modules.ai_evaluation.services.ranking_service import rank_candidates
        rank_candidates(job_id=job_id, db=db)
        
        from modules.ai_evaluation.model import CandidateRanking
        cand_rank = db.query(CandidateRanking).filter(
            CandidateRanking.job_id == job_id,
            CandidateRanking.candidate_id == candidate_id
        ).first()
        if cand_rank:
            new_app.ranking = cand_rank.rank
            db.commit()
            db.refresh(new_app)
    except Exception as e:
        logger.error(f"Ranking computation failed during application: {e}")

    # 9. Generate and cache Gemini recommendations
    try:
        generate_recommendations(candidate_id=candidate_id, job_id=job_id, db=db)
    except Exception as e:
        logger.error(f"AI Recommendations generation failed during application: {e}")

    # 10. Send personalized Application Submitted or Rejection email to Candidate
    try:
        from modules.email_automation.triggers import trigger_email
        if initial_status == "Rejected":
            trigger_email(
                event_type="Rejection Notification",
                candidate_id=candidate_id,
                job_id=job_id,
                context={
                    "extra_details": f"Your compatibility score ({overall_score}%) did not meet the role requirements."
                },
                db=db
            )
        else:
            trigger_email(
                event_type="Job Application Submitted",
                candidate_id=candidate_id,
                job_id=job_id,
                db=db
            )
    except Exception as e:
        logger.error(f"Application email failed to send: {e}")

    # 11. Send Application Received email to Recruiters
    try:
        from modules.email_automation.triggers import trigger_email
        recruiters = db.query(User).filter(User.role.in_(["recruiter", "admin"])).all()
        for rec in recruiters:
            trigger_email(
                event_type="HR_REVIEW_REQUESTED",
                candidate_id=candidate_id,
                recruiter_id=rec.id,
                job_id=job_id,
                context={
                    "extra_details": f"A new application was submitted by {user.full_name or 'Candidate'} for the job '{job.title}'. Application ATS Score: {ats_score}."
                },
                db=db
            )
    except Exception as e:
        logger.error(f"Application Received email to recruiters failed to send: {e}")

    return new_app


@router.get("/all-applications/list", response_model=List[ApplicationResponse])
def get_all_applications(db: Session = Depends(get_db)):
    """
    Get all applications submitted for all jobs.
    """
    apps = db.query(Application).order_by(Application.created_at.desc()).all()
    return apps


@router.get("/{job_id}/applications", response_model=List[ApplicationResponse])
def get_job_applications(job_id: int, db: Session = Depends(get_db)):
    """
    Get all applications submitted for a specific job post.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with ID {job_id} not found.")

    apps = db.query(Application).filter(Application.job_id == job_id).all()
    return apps


@router.get("/candidate/{candidate_id}/applications", response_model=List[ApplicationResponse])
def get_candidate_applications(candidate_id: int, db: Session = Depends(get_db)):
    """
    Get all applications submitted by a candidate.
    """
    apps = db.query(Application).filter(Application.candidate_id == candidate_id).all()
    return apps


@router.put("/applications/{application_id}/status", response_model=ApplicationResponse)
def update_application_status(
    application_id: int,
    status_data: ApplicationStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update application status (Applied, Screening, Shortlisted, Selected, Rejected, Assessment, Interview)
    and send the corresponding AI/Gemini automated email notification.
    """
    app_record = db.query(Application).filter(Application.id == application_id).first()
    if not app_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application record not found.")

    valid_statuses = ["Applied", "AI Screening", "AI Recommendation", "Recruiter Review", "HR Interview", "Offer Generated", "Offer Accepted", "Background Verification", "Joined", "Shortlisted", "Rejected", "Assessment", "Interview", "Selected"]
    new_status = status_data.status
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{new_status}'. Allowed values are: {', '.join(valid_statuses)}"
        )

    old_status = app_record.status
    app_record.status = new_status
    db.commit()
    db.refresh(app_record)

    if old_status != new_status:
        # Auto-request HR review if status is updated to HR Interview
        if new_status == "HR Interview":
            try:
                from modules.hr_review.logic import HRReviewLogic
                from modules.hr_review.schema import HRReviewCreate
                from modules.auth.model import User
                
                # Use a default recruiter ID
                rec_user = db.query(User).filter(User.role == "recruiter").first()
                rec_id = rec_user.id if rec_user else 1
                
                review_data = HRReviewCreate(
                    candidate_id=app_record.candidate_id,
                    job_id=app_record.job_id,
                    recruiter_id=rec_id,
                    comments="Auto-requested on status transition to HR Interview."
                )
                HRReviewLogic.request_hr_review(db, review_data)
                logger.info(f"Auto-submitted candidate {app_record.candidate_id} to HR review queue on status change to HR Interview.")
            except Exception as hr_ex:
                logger.error(f"Failed to auto-request HR review on status change: {hr_ex}")
        elif new_status == "Rejected":
            try:
                from modules.hr_review.model import HRReview
                db.query(HRReview).filter(
                    HRReview.candidate_id == app_record.candidate_id,
                    HRReview.job_id == app_record.job_id
                ).delete(synchronize_session=False)
                db.commit()
                logger.info(f"Deleted candidate {app_record.candidate_id} from HR review queue on rejection status.")
            except Exception as hr_ex:
                logger.error(f"Failed to delete candidate from HR queue on rejection status: {hr_ex}")

        try:
            job = db.query(Job).filter(Job.id == app_record.job_id).first()
            user = db.query(User).filter(User.id == app_record.candidate_id).first()
            if job and user:
                event_map = {
                    "Shortlisted": "Shortlisted Notification",
                    "Rejected": "Rejection Notification",
                    "Assessment": "Aptitude Assessment Invitation",
                    "Interview": "Interview Invitation",
                    "Selected": "Offer Letter Release"
                }
                event_type = event_map.get(new_status)
                if event_type:
                    extra_details = None
                    if new_status == "Assessment":
                        extra_details = "/candidate page.html"
                    elif new_status == "Interview":
                        extra_details = "/candidate page.html"
                    elif new_status == "Selected":
                        extra_details = "CTC: Competitive package details enclosed."
                    elif new_status == "Rejected":
                        extra_details = status_data.reason or "Profile match did not meet the role requirements."

                    from modules.email_automation.triggers import trigger_email
                    trigger_email(
                        event_type=event_type,
                        candidate_id=app_record.candidate_id,
                        job_id=app_record.job_id,
                        context={
                            "extra_details": extra_details
                        },
                        db=db
                    )
        except Exception as e:
            logger.error(f"Failed to send status transition email: {e}")

    return app_record


# ==========================================
# 5. Saved Jobs Endpoints
# ==========================================

@router.post("/{job_id}/save", response_model=SavedJobResponse, status_code=status.HTTP_201_CREATED)
def save_job(job_id: int, candidate_id: int = Query(...), db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    existing = db.query(SavedJob).filter(SavedJob.job_id == job_id, SavedJob.candidate_id == candidate_id).first()
    if existing:
        return existing
        
    saved = SavedJob(job_id=job_id, candidate_id=candidate_id)
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return saved


@router.delete("/{job_id}/save", status_code=status.HTTP_200_OK)
def unsave_job(job_id: int, candidate_id: int = Query(...), db: Session = Depends(get_db)):
    saved = db.query(SavedJob).filter(SavedJob.job_id == job_id, SavedJob.candidate_id == candidate_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Saved job not found")
        
    db.delete(saved)
    db.commit()
    return {"detail": "Job unsaved successfully"}


@router.get("/candidate/{candidate_id}/saved", response_model=List[dict])
def get_saved_jobs(candidate_id: int, db: Session = Depends(get_db)):
    saved_jobs = db.query(SavedJob).filter(SavedJob.candidate_id == candidate_id).all()
    results = []
    for saved in saved_jobs:
        job = db.query(Job).filter(Job.id == saved.job_id).first()
        if job:
            job_dict = JobResponse.model_validate(job).model_dump()
            job_dict["saved_at"] = saved.created_at
            results.append(job_dict)
    return results


# ==========================================
# 6. Candidate Discovery Feed
# ==========================================

@router.get("/candidate/{candidate_id}/feed", response_model=List[dict])
def get_candidate_job_feed(
    candidate_id: int,
    search_query: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    job_type: Optional[str] = Query(None),
    experience: Optional[str] = Query(None),
    min_salary: Optional[float] = Query(None),
    skills: Optional[List[str]] = Query(None),
    department: Optional[str] = Query(None),
    work_mode: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Returns jobs with dynamic Match Score calculated for the candidate.
    Extends standard filtering with department, job_type, and work_mode.
    """
    # Base search
    jobs = logic.search_and_filter_jobs(
        db=db,
        search_query=search_query,
        status="published",  # Candidates only see published jobs
        location=location,
        experience=experience,
        min_salary=min_salary,
        skills=skills
    )
    
    # Additional filters mapped manually since Job model doesn't explicitly have them
    if job_type:
        jobs = [j for j in jobs if job_type.lower() in j.title.lower() or job_type.lower() in j.description.lower()]
    
    if department:
        jobs = [j for j in jobs if department.lower() in j.title.lower() or department.lower() in j.description.lower()]
        
    if work_mode:
        # e.g., Remote, Hybrid, Onsite
        jobs = [j for j in jobs if work_mode.lower() in j.location.lower() or work_mode.lower() in j.title.lower() or work_mode.lower() in j.description.lower()]

    results = []
    for job in jobs:
        # Calculate dynamic match score
        score = logic.calculate_match_score(db, job, candidate_id)
        job_dict = JobResponse.model_validate(job).model_dump()
        job_dict["match_score"] = score
        results.append(job_dict)
        
    # Sort by match score descending
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results
