import sys
import os
from datetime import datetime, timedelta, date, time

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from core.database import SessionLocal
from modules.auth.model import User
from modules.candidate.profile.model import CandidateProfile
from modules.company_profile.model import CompanyProfile
from modules.job_management.model import Job, Application
from modules.interview_scheduling.model import InterviewSchedule
from modules.email_automation.models import EmailLog

client = TestClient(app)

def create_test_data(db):
    # 1. Create candidate user and profile
    cand_email = "test_candidate_meet@test.com"
    cand_user = db.query(User).filter(User.email == cand_email).first()
    if cand_user:
        db.query(CandidateProfile).filter(CandidateProfile.user_id == cand_user.id).delete()
        db.delete(cand_user)
        db.commit()
        
    cand_user = User(email=cand_email, password_hash="test", full_name="Meet Candidate", role="candidate")
    db.add(cand_user)
    db.commit()
    db.refresh(cand_user)
    
    cand_profile = CandidateProfile(
        user_id=cand_user.id,
        full_name="Meet Candidate",
        email=cand_email,
        candidate_code="AIH9999",
        profile_completion=100
    )
    db.add(cand_profile)
    
    # 2. Create recruiter user and company profile
    rec_email = "test_recruiter_meet@test.com"
    rec_user = db.query(User).filter(User.email == rec_email).first()
    if rec_user:
        db.query(CompanyProfile).filter(CompanyProfile.user_id == rec_user.id).delete()
        db.delete(rec_user)
        db.commit()
        
    rec_user = User(email=rec_email, password_hash="test", full_name="Meet Recruiter", role="recruiter")
    db.add(rec_user)
    db.commit()
    db.refresh(rec_user)
    
    comp_profile = CompanyProfile(
        user_id=rec_user.id,
        company_name="Meet Test Company",
        company_email="meet_comp@test.com",
        website="https://meettest.com"
    )
    db.add(comp_profile)
    
    # 3. Create job
    job = Job(
        title="Test AI Engineer",
        description="Detailed job description for Test AI Engineer position.",
        required_skills=["Python", "SQL"],
        preferred_skills=["Docker"],
        experience="2-4 years",
        package="$120k",
        location="Remote",
        openings=1,
        deadline=datetime.utcnow() + timedelta(days=30),
        status="published",
        selection_rounds=[],
        salary_rules={},
        eligibility_rules={},
        application_settings={}
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # 4. Create job application
    app_record = Application(
        job_id=job.id,
        candidate_id=cand_user.id,
        status="Applied"
    )
    db.add(app_record)
    db.commit()
    
    return cand_user, rec_user, job

def run_tests():
    print("--- Starting Manual Google Meet Interview Workflow Verification ---")
    db = SessionLocal()
    
    cand_user, rec_user, job = create_test_data(db)
    print(f"Test data created: Candidate ID {cand_user.id}, Recruiter ID {rec_user.id}, Job ID {job.id}")
    
    interview_id = None
    try:
        # Phase 1: Test validation rules (Online/Hybrid require meeting link)
        print("\n[Phase 1] Verifying scheduling validation rules...")
        
        # Test 1A: Online without meeting link -> expect 400
        payload_invalid = {
            "candidate_id": cand_user.id,
            "job_id": job.id,
            "recruiter_id": rec_user.id,
            "interview_title": "AI Engineer Final Interview",
            "interviewer_name": "Senior AI Architect",
            "interviewer_email": "architect@test.com",
            "duration_minutes": 45,
            "interview_date": str(date.today() + timedelta(days=2)),
            "interview_time": "14:30:00",
            "interview_mode": "Online",
            "meeting_link": "",
            "interview_notes": "Please join 5 mins before."
        }
        res_invalid = client.post("/interviews/schedule", json=payload_invalid)
        print(f"Test 1A (Online, no link): Status Code {res_invalid.status_code}, Response: {res_invalid.text}")
        assert res_invalid.status_code == 400, f"Expected 400 for Online interview without meeting link, got {res_invalid.status_code}"
        
        # Test 1B: Hybrid without meeting link -> expect 400
        payload_invalid["interview_mode"] = "Hybrid"
        res_invalid_hybrid = client.post("/interviews/schedule", json=payload_invalid)
        print(f"Test 1B (Hybrid, no link): Status Code {res_invalid_hybrid.status_code}")
        assert res_invalid_hybrid.status_code == 400, f"Expected 400 for Hybrid interview without meeting link, got {res_invalid_hybrid.status_code}"
        
        # Test 1C: Offline without meeting link -> expect 201 (optional)
        payload_valid_offline = payload_invalid.copy()
        payload_valid_offline["interview_mode"] = "Offline"
        res_offline = client.post("/interviews/schedule", json=payload_valid_offline)
        print(f"Test 1C (Offline, no link): Status Code {res_offline.status_code}")
        assert res_offline.status_code == 201, f"Expected 201 for Offline interview without meeting link, got {res_offline.status_code}"
        offline_id = res_offline.json()["id"]
        
        # Test 1D: Online with meeting link -> expect 201
        payload_valid = payload_invalid.copy()
        payload_valid["interview_mode"] = "Online"
        payload_valid["meeting_link"] = "https://meet.google.com/abc-defg-hij"
        res_valid = client.post("/interviews/schedule", json=payload_valid)
        print(f"Test 1D (Online, with link): Status Code {res_valid.status_code}")
        assert res_valid.status_code == 201, f"Expected 201 for Online interview with meeting link, got {res_valid.status_code}"
        
        interview_data = res_valid.json()
        interview_id = interview_data["id"]
        assert interview_data["meeting_link"] == "https://meet.google.com/abc-defg-hij", "Meeting link not saved correctly"
        assert interview_data["status"] == "Scheduled", "Default status should be Scheduled"
        
        # Cleanup offline test interview
        db.query(InterviewSchedule).filter(InterviewSchedule.id == offline_id).delete()
        db.commit()

        # Phase 3: Candidate can view interview details
        print("\n[Phase 3] Verifying Candidate view and details...")
        res_cand_view = client.get(f"/interviews/candidate/{cand_user.id}")
        assert res_cand_view.status_code == 200
        cand_interviews = res_cand_view.json()
        assert len(cand_interviews) > 0, "No interviews found for candidate"
        cand_item = next(i for i in cand_interviews if i["id"] == interview_id)
        assert cand_item["meeting_link"] == "https://meet.google.com/abc-defg-hij", "Candidate view has incorrect meeting link"
        assert cand_item["interview_mode"] == "Online", "Candidate view has incorrect mode"
        print("Candidate view check passed.")

        # Phase 5: Candidate confirm attendance
        print("\n[Phase 5] Verifying Candidate confirm attendance...")
        res_confirm = client.put(f"/interviews/{interview_id}/status", json={"status": "Confirmed", "notes": "I will attend."})
        print(f"Confirm Attendance Status Code: {res_confirm.status_code}")
        assert res_confirm.status_code == 200
        assert res_confirm.json()["status"] == "Confirmed", "Expected status to be Confirmed"
        
        # Check Candidate request reschedule
        print("Verifying Candidate request reschedule...")
        res_req_resched = client.put(f"/interviews/{interview_id}/status", json={"status": "Rescheduled", "notes": "Can we move it?"})
        print(f"Request Reschedule Status Code: {res_req_resched.status_code}")
        assert res_req_resched.status_code == 200
        assert res_req_resched.json()["status"] == "Rescheduled", "Expected status to be Rescheduled"

        # Phase 5: Recruiter rescheduling
        print("\nVerifying Recruiter rescheduling updates...")
        new_date = str(date.today() + timedelta(days=3))
        res_resched = client.put(f"/interviews/{interview_id}", json={
            "interview_date": new_date,
            "interview_time": "16:00:00",
            "meeting_link": "https://meet.google.com/xyz-pdq-rst"
        })
        print(f"Recruiter Reschedule Status Code: {res_resched.status_code}")
        assert res_resched.status_code == 200
        resched_data = res_resched.json()
        assert resched_data["interview_date"] == new_date, "Interview date not updated"
        assert resched_data["status"] == "Rescheduled", "Recruiter date update should auto-transition status to Rescheduled"
        assert resched_data["meeting_link"] == "https://meet.google.com/xyz-pdq-rst", "Recruiter update should change meeting link"

        # Recruiter Cancels
        print("Verifying Recruiter cancellation...")
        res_cancel = client.put(f"/interviews/{interview_id}/status", json={"status": "Cancelled", "notes": "Positions closed."})
        print(f"Recruiter Cancel Status Code: {res_cancel.status_code}")
        assert res_cancel.status_code == 200
        assert res_cancel.json()["status"] == "Cancelled", "Expected status to be Cancelled"

        # Recruiter Completes
        print("Verifying Recruiter completion...")
        res_complete = client.put(f"/interviews/{interview_id}/status", json={"status": "Completed", "notes": "Interview was successful."})
        print(f"Recruiter Complete Status Code: {res_complete.status_code}")
        assert res_complete.status_code == 200
        assert res_complete.json()["status"] == "Completed", "Expected status to be Completed"

        # Phase 4 & Email Automation Check
        print("\n[Phase 4] Verifying Email Automation logs...")
        logs = db.query(EmailLog).filter(EmailLog.candidate_id == cand_user.id).all()
        print(f"Total email logs generated for candidate: {len(logs)}")
        for l in logs:
            print(f"- Type: {l.email_type}, Status: {l.status}")
        assert len(logs) > 0, "No email logs generated during workflow events"
        
        # Verify future-proof architecture provider placeholder
        print("\n[Phase 7] Verifying Future-Proof Architecture Meeting Provider...")
        from modules.interview_scheduling.meeting_provider import get_meeting_provider_info
        provider_info = get_meeting_provider_info()
        print(f"Provider info: {provider_info}")
        assert provider_info["provider"] == "MANUAL_GOOGLE_MEET"
        assert provider_info["meeting_provider"] == "Google Meet"
        
        print("\nAll End-to-End Manual Google Meet Workflows Verified Successfully!")
        
    except AssertionError as e:
        print(f"\nVerification Failed: {e}")
        sys.exit(1)
    finally:
        # DB Cleanup
        print("\nCleaning up test data...")
        if interview_id:
            db.query(InterviewSchedule).filter(InterviewSchedule.id == interview_id).delete()
        db.query(Application).filter(Application.candidate_id == cand_user.id).delete()
        db.query(Job).filter(Job.id == job.id).delete()
        db.query(CandidateProfile).filter(CandidateProfile.user_id == cand_user.id).delete()
        db.query(CompanyProfile).filter(CompanyProfile.user_id == rec_user.id).delete()
        db.query(User).filter(User.id.in_([cand_user.id, rec_user.id])).delete()
        db.query(EmailLog).filter(EmailLog.candidate_id == cand_user.id).delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    run_tests()
