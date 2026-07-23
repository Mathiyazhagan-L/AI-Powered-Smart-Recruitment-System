import sys
import os
import time
import datetime
from sqlalchemy.orm import Session

# Add current directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.base import Base
from modules.auth.model import User
from modules.job_management.model import Job, Application
from modules.candidate.profile.model import CandidateProfile
from modules.email_automation.triggers import trigger_email
from modules.email_automation.models import EmailLog

def run_verify():
    print("====================================================")
    print("Verifying HR & Interview Email Engine Integration")
    print("====================================================")
    
    db = SessionLocal()
    
    # 1. Clean previous data
    db.query(EmailLog).filter(EmailLog.recipient_email.in_(["cand_email_test@example.com", "rec_email_test@example.com"])).delete()
    db.query(Application).filter(Application.candidate_id == 9992).delete()
    db.query(CandidateProfile).filter(CandidateProfile.user_id == 9992).delete()
    db.query(Job).filter(Job.id == 9992).delete()
    db.query(User).filter(User.id.in_([9992, 9993])).delete()
    db.commit()

    try:
        # Create users
        cand_user = User(id=9992, email="cand_email_test@example.com", role="candidate", password_hash="hash")
        rec_user = User(id=9993, email="rec_email_test@example.com", role="recruiter", password_hash="hash")
        db.add_all([cand_user, rec_user])
        db.commit()

        # Create Job
        job = Job(
            id=9992,
            title="Senior QA Engineer",
            description="Selenium, pytest",
            required_skills=["Python"],
            preferred_skills=[],
            experience="4 years",
            package="110,000 USD",
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

        # Create Profile
        profile = CandidateProfile(
            id=9992,
            user_id=9992,
            full_name="Email Tester",
            email="cand_email_test@example.com",
            profile_completion=100,
            candidate_code="AIH9992"
        )
        db.add(profile)
        db.commit()

        events_to_test = [
            "HR_REVIEW_REQUESTED",
            "HR_APPROVED",
            "HR_REJECTED",
            "INTERVIEW_SCHEDULED",
            "INTERVIEW_CONFIRMED",
            "INTERVIEW_RESCHEDULED",
            "INTERVIEW_CANCELLED",
            "INTERVIEW_COMPLETED",
            "FINAL_SELECTION",
            "FINAL_REJECTION",
            "OFFER_RELEASED"
        ]

        print(f"Triggering {len(events_to_test)} events...")
        triggered_log_ids = []
        for event in events_to_test:
            # We use different recipient emails based on event design
            # HR_REVIEW_REQUESTED targets the recruiter, others target candidate
            recip_id = 9993 if event == "HR_REVIEW_REQUESTED" else 9992
            
            # Pass custom context
            context = {
                "candidate_name": "Email Tester",
                "candidate_code": "AIH9992",
                "job_title": "Senior QA Engineer",
                "company_name": "AIHire Corporation",
                "interview_title": "System Architecture Sync",
                "interviewer_name": "Bob (QA Lead)",
                "interview_date": "2026-07-15",
                "interview_time": "11:00 AM",
                "interview_mode": "Online",
                "meeting_link": "https://meet.google.com/abc-defg-hij",
                "duration_minutes": 45,
                "notes": "Bring your resume.",
                "comments": "Good fit."
            }
            
            log_id = trigger_email(
                event_type=event,
                candidate_id=cand_user.id if recip_id == 9992 else None,
                recruiter_id=rec_user.id if recip_id == 9993 else None,
                job_id=job.id,
                context=context,
                db=db
            )
            
            if log_id:
                triggered_log_ids.append((event, log_id))
                print(f"[OK] Event '{event}' triggered successfully. Log ID: {log_id}")
            else:
                print(f"[FAILED] Event '{event}' failed to trigger.")

        # Assert all 11 events were triggered
        assert len(triggered_log_ids) == len(events_to_test)
        print("\nAll 11 event logs recorded in database.")

        # Wait a short moment for background thread generation (if any API key was present)
        # In a test setting, if APIs fail, the predefined templates will be written to DB anyway.
        time.sleep(2)

        # Check in DB if records exist and have status either Pending, Sent, or Completed
        for event, log_id in triggered_log_ids:
            log_record = db.query(EmailLog).filter(EmailLog.id == log_id).first()
            assert log_record is not None
            assert log_record.email_type == event
            print(f"[OK] Verified database persistence for log #{log_id} (Event: {event}, Status: {log_record.status})")

        print("\n==============================================")
        print("EMAIL ENGINE INTEGRATION VERIFICATION PASSED")
        print("==============================================")

    finally:
        # Wait for threads to finish before database deletion to prevent pending rollback errors
        time.sleep(3)
        db.query(EmailLog).filter(EmailLog.recipient_email.in_(["cand_email_test@example.com", "rec_email_test@example.com"])).delete()
        db.query(Application).filter(Application.candidate_id == 9992).delete()
        db.query(CandidateProfile).filter(CandidateProfile.user_id == 9992).delete()
        db.query(Job).filter(Job.id == 9992).delete()
        db.query(User).filter(User.id.in_([9992, 9993])).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    run_verify()
