import sys
import os
import datetime
from sqlalchemy.orm import Session

# Add current directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.base import Base
from modules.auth.model import User
from modules.job_management.model import Job, Application
from modules.candidate.profile.model import CandidateProfile
from modules.candidate.resume.model import CandidateResume
from modules.assessment.models import AssessmentResult
from modules.coding_assessment.models import CodingResult
from modules.interview_assessment.models import InterviewResult
from modules.hr_review.logic import HRReviewLogic
from modules.hr_review.model import HRReview
from modules.hr_review.schema import HRReviewCreate, HRReviewUpdate
from modules.email_automation.models import EmailLog

def run_verify():
    print("====================================================")
    print("Verifying HR Review Business Logic & Auto Eligibility")
    print("====================================================")
    
    db = SessionLocal()
    
    # 1. Clean previous verification data to ensure reproducibility
    db.query(EmailLog).filter(EmailLog.recipient_email.in_(["cand_test_workflow@example.com", "rec_test_workflow@example.com"])).delete()
    db.query(HRReview).filter(HRReview.candidate_id == 9999).delete()
    db.query(Application).filter(Application.candidate_id == 9999).delete()
    db.query(InterviewResult).filter(InterviewResult.candidate_id == 9999).delete()
    db.query(CodingResult).filter(CodingResult.candidate_id == 9999).delete()
    db.query(AssessmentResult).filter(AssessmentResult.candidate_id == 9999).delete()
    db.query(CandidateResume).filter(CandidateResume.user_id == 9999).delete()
    db.query(CandidateProfile).filter(CandidateProfile.user_id == 9999).delete()
    db.query(Job).filter(Job.id == 9999).delete()
    db.query(User).filter(User.id.in_([9999, 9998])).delete()
    db.commit()

    try:
        # Create users
        cand_user = User(id=9999, email="cand_test_workflow@example.com", role="candidate", password_hash="hash")
        rec_user = User(id=9998, email="rec_test_workflow@example.com", role="recruiter", password_hash="hash")
        db.add_all([cand_user, rec_user])
        db.commit()

        # Create Job
        job = Job(
            id=9999,
            title="Senior Verification Engineer",
            description="Details",
            required_skills=["Python"],
            preferred_skills=[],
            experience="5 years",
            package="120,000 USD",
            location="Remote",
            criteria="None",
            openings=1,
            deadline=datetime.datetime.utcnow() + datetime.timedelta(days=30),
            status="published",
            selection_rounds=[],
            salary_rules={},
            eligibility_rules={},
            application_settings={}
        )
        db.add(job)
        db.commit()

        # Create Profile (incomplete initially)
        profile = CandidateProfile(
            id=9999,
            user_id=9999,
            full_name="Workflow Tester",
            email="cand_test_workflow@example.com",
            profile_completion=50, # Incomplete
            github_score=80
        )
        db.add(profile)
        db.commit()

        review_data = HRReviewCreate(candidate_id=9999, job_id=9999, recruiter_id=9998)

        # Assert Auto Eligibility Check 1: Incomplete profile (must fail)
        print("Testing eligibility validation - Incomplete Profile...")
        try:
            HRReviewLogic.request_hr_review(db, review_data)
            assert False, "Should have raised 403 for incomplete profile."
        except Exception as e:
            print(f"[OK] Correctly raised error: {e.detail}")
            assert e.status_code == 403

        # Update profile to complete
        profile.profile_completion = 100
        db.commit()

        # Assert Auto Eligibility Check 2: Missing Resume
        print("Testing eligibility validation - Missing Resume...")
        try:
            HRReviewLogic.request_hr_review(db, review_data)
            assert False, "Should have raised 403 for missing resume."
        except Exception as e:
            print(f"[OK] Correctly raised error: {e.detail}")
            assert e.status_code == 403

        # Add Resume
        resume = CandidateResume(user_id=9999, resume_name="test.pdf", resume_path="/path/test.pdf", file_type="pdf", file_size=500, parsed_status=True)
        db.add(resume)
        db.commit()

        # Assert Auto Eligibility Check 3: Missing Aptitude
        print("Testing eligibility validation - Missing Aptitude...")
        try:
            HRReviewLogic.request_hr_review(db, review_data)
            assert False, "Should have raised 403 for missing aptitude."
        except Exception as e:
            print(f"[OK] Correctly raised error: {e.detail}")
            assert e.status_code == 403

        # Add Aptitude Result
        apt = AssessmentResult(
            candidate_id=9999,
            attempt_id=1,
            total_correct=10,
            total_wrong=0,
            aptitude_score=90.0,
            quantitative_score=90.0,
            logical_score=90.0,
            verbal_score=90.0,
            analytical_reasoning_score=90.0,
            computer_fundamentals_score=90.0,
            status="PASSED"
        )
        db.add(apt)
        db.commit()

        # Assert Auto Eligibility Check 4: Missing Coding
        print("Testing eligibility validation - Missing Coding...")
        try:
            HRReviewLogic.request_hr_review(db, review_data)
            assert False, "Should have raised 403 for missing coding."
        except Exception as e:
            print(f"[OK] Correctly raised error: {e.detail}")
            assert e.status_code == 403

        # Add Coding Result
        coding = CodingResult(
            candidate_id=9999,
            attempt_id=1,
            total_score=85.0,
            easy_score=90.0,
            medium_score=80.0,
            hard_score=85.0,
            questions_solved=4,
            questions_attempted=5,
            status="PASS"
        )
        db.add(coding)
        db.commit()

        # Assert Auto Eligibility Check 5: Missing Interview
        print("Testing eligibility validation - Missing Interview Assessment...")
        try:
            HRReviewLogic.request_hr_review(db, review_data)
            assert False, "Should have raised 403 for missing interview."
        except Exception as e:
            print(f"[OK] Correctly raised error: {e.detail}")
            assert e.status_code == 403

        # Add Interview Result
        intv = InterviewResult(candidate_id=9999, session_id=1, communication_score=20, technical_score=30, confidence_score=15, professionalism_score=15, total_score=80.0, grade="A", hiring_recommendation="Hire")
        db.add(intv)
        db.commit()

        # Assert Auto Eligibility Check 6: Missing Job Application
        print("Testing eligibility validation - Missing Job Application...")
        try:
            HRReviewLogic.request_hr_review(db, review_data)
            assert False, "Should have raised 403 for missing job application."
        except Exception as e:
            print(f"[OK] Correctly raised error: {e.detail}")
            assert e.status_code == 403

        # Add Application
        app = Application(candidate_id=9999, job_id=9999, status="Applied", ats_score=95)
        db.add(app)
        db.commit()

        # Now all requirements met! Request HR review
        print("Submitting candidate to HR review queue...")
        review = HRReviewLogic.request_hr_review(db, review_data)
        
        # Verify Snapshots & Score calculations
        print("Verifying metrics snapshots...")
        assert review.review_status == "Pending"
        assert review.github_score == 80.0
        assert review.ats_score == 95.0
        assert review.aptitude_score == 90.0
        assert review.coding_score == 85.0
        assert review.interview_score == 80.0
        
        # Calculate expected overall weighted score:
        # ATS 15%, GitHub 15%, Aptitude 20%, Coding 25%, Interview 25%
        # 95*0.15 + 80*0.15 + 90*0.20 + 85*0.25 + 80*0.25 = 14.25 + 12 + 18 + 21.25 + 20 = 85.5
        expected_overall = round((95*0.15) + (80*0.15) + (90*0.20) + (85*0.25) + (80*0.25), 2)
        assert review.overall_score == expected_overall
        print(f"[OK] Overall score calculated correctly: {review.overall_score}% (expected {expected_overall}%)")

        # Verify HR review listed in queue
        queue = HRReviewLogic.get_hr_queue(db, "Pending")
        assert any(q.candidate_id == 9999 for q in queue)
        print("[OK] Candidate correctly listed in pending HR queue.")

        # Update Review Status to Approved
        print("Approving candidate review status...")
        update_data = HRReviewUpdate(review_status="Approved", comments="Highly qualified candidate.", reviewed_by=100)
        approved_review = HRReviewLogic.update_hr_review_status(db, review.id, update_data)
        
        assert approved_review.review_status == "Approved"
        assert approved_review.comments == "Highly qualified candidate."
        assert approved_review.reviewed_by == 100
        
        # Verify application status was updated
        db.refresh(app)
        assert app.status == "HR Approved"
        print("[OK] Application status updated to HR Approved successfully.")
        
        print("\n==============================================")
        print("HR REVIEW & AUTO ELIGIBILITY VERIFICATION PASSED")
        print("==============================================")

    finally:
        # Clean up database records
        db.query(EmailLog).filter(EmailLog.recipient_email.in_(["cand_test_workflow@example.com", "rec_test_workflow@example.com"])).delete()
        db.query(HRReview).filter(HRReview.candidate_id == 9999).delete()
        db.query(Application).filter(Application.candidate_id == 9999).delete()
        db.query(InterviewResult).filter(InterviewResult.candidate_id == 9999).delete()
        db.query(CodingResult).filter(CodingResult.candidate_id == 9999).delete()
        db.query(AssessmentResult).filter(AssessmentResult.candidate_id == 9999).delete()
        db.query(CandidateResume).filter(CandidateResume.user_id == 9999).delete()
        db.query(CandidateProfile).filter(CandidateProfile.user_id == 9999).delete()
        db.query(Job).filter(Job.id == 9999).delete()
        db.query(User).filter(User.id.in_([9999, 9998])).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    run_verify()
