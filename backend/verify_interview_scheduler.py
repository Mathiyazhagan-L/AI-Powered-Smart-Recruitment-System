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
from modules.interview_scheduling.logic import InterviewSchedulingLogic
from modules.interview_scheduling.model import InterviewSchedule
from modules.interview_scheduling.schema import InterviewScheduleCreate, InterviewScheduleUpdate, InterviewStatusUpdate
from modules.email_automation.models import EmailLog

def run_verify():
    print("====================================================")
    print("Verifying Interview Scheduling & Final Decision logic")
    print("====================================================")
    
    db = SessionLocal()
    
    # 1. Clean previous data
    db.query(EmailLog).filter(EmailLog.recipient_email.in_(["cand_sched_test@example.com", "rec_sched_test@example.com"])).delete()
    db.query(InterviewSchedule).filter(InterviewSchedule.candidate_id == 9991).delete()
    db.query(Application).filter(Application.candidate_id == 9991).delete()
    db.query(CandidateProfile).filter(CandidateProfile.user_id == 9991).delete()
    db.query(Job).filter(Job.id == 9991).delete()
    db.query(User).filter(User.id.in_([9991, 9990])).delete()
    db.commit()

    try:
        # Create users
        cand_user = User(id=9991, email="cand_sched_test@example.com", role="candidate", password_hash="hash")
        rec_user = User(id=9990, email="rec_sched_test@example.com", role="recruiter", password_hash="hash")
        db.add_all([cand_user, rec_user])
        db.commit()

        # Create Job
        job = Job(
            id=9991,
            title="DevOps Lead",
            description="Docker, K8s, AWS",
            required_skills=["AWS"],
            preferred_skills=[],
            experience="6 years",
            package="150,000 USD",
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
        
        # Create Application
        app = Application(candidate_id=9991, job_id=9991, status="HR Approved", ats_score=90)
        db.add(app)
        db.commit()

        # Create Profile
        profile = CandidateProfile(
            id=9991,
            user_id=9991,
            full_name="Schedule Tester",
            email="cand_sched_test@example.com",
            profile_completion=100,
            candidate_code="AIH9991"
        )
        db.add(profile)
        db.commit()

        # 2. Test Create Interview
        print("Scheduling interview...")
        create_data = InterviewScheduleCreate(
            candidate_id=9991,
            job_id=9991,
            recruiter_id=9990,
            interview_title="Technical Architecture Round",
            interviewer_name="Alice (Lead Architect)",
            interviewer_email="alice@company.com",
            duration_minutes=60,
            interview_date=datetime.date(2026, 7, 10),
            interview_time=datetime.time(14, 30),
            interview_mode="Online"
        )

        interview = InterviewSchedulingLogic.create_interview(db, create_data)
        assert interview.status == "Scheduled"
        assert interview.meeting_link == "https://meet.google.com/abc-defg-hij" # fallback link
        print("[OK] Interview successfully scheduled with fallback meeting link.")

        # 3. Test Candidate Confirm
        print("Confirming interview attendance...")
        update_data = InterviewScheduleUpdate(status="Confirmed")
        interview = InterviewSchedulingLogic.update_interview(db, interview.id, update_data)
        assert interview.status == "Confirmed"
        print("[OK] Interview attendance confirmed.")

        # 4. Test Recruiter Reschedule
        print("Rescheduling interview...")
        resched_data = InterviewScheduleUpdate(
            interview_date=datetime.date(2026, 7, 12),
            interview_time=datetime.time(16, 0)
        )
        interview = InterviewSchedulingLogic.update_interview(db, interview.id, resched_data)
        assert interview.status == "Rescheduled"
        assert interview.interview_date == datetime.date(2026, 7, 12)
        assert interview.interview_time == datetime.time(16, 0)
        print("[OK] Interview successfully rescheduled.")

        # 5. Test Final Decision: Selection
        print("Executing final decision: Selection...")
        interview = InterviewSchedulingLogic.execute_final_decision(db, interview.id, "Selection", "Excellent coding skills and alignment.")
        assert interview.status == "Completed"
        
        db.refresh(app)
        assert app.status == "Selected"
        print("[OK] Candidate successfully marked as Selected.")

        # 6. Test Final Decision: Rejection
        print("Executing final decision: Rejection...")
        interview = InterviewSchedulingLogic.execute_final_decision(db, interview.id, "Rejection", "Did not meet requirements.")
        db.refresh(app)
        assert app.status == "Rejected"
        print("[OK] Candidate successfully marked as Rejected.")

        # 7. Test Final Decision: OfferReleased
        print("Executing final decision: OfferReleased...")
        interview = InterviewSchedulingLogic.execute_final_decision(db, interview.id, "OfferReleased", "Released standard offer package.")
        db.refresh(app)
        assert app.status == "Offer Released"
        print("[OK] Candidate successfully marked as Offer Released.")

        print("\n==============================================")
        print("INTERVIEW SCHEDULER & HIRING DECISIONS PASSED")
        print("==============================================")

    finally:
        # Clean up database records
        db.query(EmailLog).filter(EmailLog.recipient_email.in_(["cand_sched_test@example.com", "rec_sched_test@example.com"])).delete()
        db.query(InterviewSchedule).filter(InterviewSchedule.candidate_id == 9991).delete()
        db.query(Application).filter(Application.candidate_id == 9991).delete()
        db.query(CandidateProfile).filter(CandidateProfile.user_id == 9991).delete()
        db.query(Job).filter(Job.id == 9991).delete()
        db.query(User).filter(User.id.in_([9991, 9990])).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    run_verify()
