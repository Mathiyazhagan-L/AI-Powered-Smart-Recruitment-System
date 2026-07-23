import os
import sys
import json
import time
import logging

# Set up path to import backend modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from modules.email_automation.triggers import trigger_email
from modules.email_automation.models import EmailLog
from modules.auth.model import User
from modules.candidate.profile.model import CandidateProfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VerifyEmailAutomation")

def run_verification():
    db = SessionLocal()
    cand_user = None
    try:
        print("="*60)
        print("STARTING EMAIL AUTOMATION ENGINE VERIFICATION")
        print("="*60)

        # 1. Setup a test candidate user if not exists
        candidate_email = "test_candidate_email_automation@example.com"
        cand_user = db.query(User).filter(User.email == candidate_email).first()
        if not cand_user:
            print("Creating temporary test candidate user...")
            cand_user = User(
                email=candidate_email,
                role="candidate",
                full_name="Alex Email Automation Tester",
                password_hash="hashed_dummy_password",
                is_active=True
            )
            db.add(cand_user)
            db.commit()
            db.refresh(cand_user)
            print(f"Created candidate user ID: {cand_user.id}")

        # Ensure CandidateProfile exists for user
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == cand_user.id).first()
        if not profile:
            print("Creating temporary candidate profile...")
            profile = CandidateProfile(
                user_id=cand_user.id,
                email=candidate_email,
                full_name="Alex Email Automation Tester",
                candidate_code="AIH9999",
                aptitude_score=85,
                interview_score=90,
                interview_status="Completed"
            )
            db.add(profile)
            db.commit()
            print("Profile created.")

        # Clean existing logs for test candidate to run clean tests
        print("Cleaning prior email logs for test candidate...")
        db.query(EmailLog).filter(EmailLog.candidate_id == cand_user.id).delete()
        db.commit()

        # 2. Trigger Registration Email
        print("\n--- Test 1: Triggering candidate registration email (Async Thread) ---")
        log_id = trigger_email(
            event_type="CANDIDATE_REGISTRATION",
            candidate_id=cand_user.id,
            db=db
        )
        print(f"Trigger returned log ID: {log_id}")
        assert log_id is not None, "Failed to create EmailLog record"

        # Poll database up to 45 seconds for background thread processing
        print("Waiting for background generator and SMTP sender thread (polling up to 45s)...")
        max_attempts = 23
        log = None
        for attempt in range(max_attempts):
            db.rollback()
            log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
            if log and log.status != "Pending":
                break
            time.sleep(2)
        
        print(f"Email Log ID: {log.id}")
        print(f"Status: {log.status}")
        print(f"Recipient: {log.recipient_email}")
        print(f"Subject: {log.generated_subject}")
        print(f"Error Message: {log.error_message}")
        print(f"Created At: {log.created_at}")
        print(f"Sent At: {log.sent_at}")
        
        # Verify schema extension fields
        assert log.generated_subject is not None, "generated_subject was not updated"
        assert log.generated_html is not None, "generated_html was not updated"
        assert log.status in ["Sent", "Failed"], f"Unexpected log status: {log.status}"
        print("Test 1 passed: Extended email_logs fields correctly updated in database.")

        # 3. Duplicate Prevention Checking
        print("\n--- Test 2: Triggering duplicate registration email ---")
        # Force status to Sent to ensure duplicate check triggers (in case SMTP is not configured and Test 1 set it to Failed)
        log.status = "Sent"
        db.commit()
        
        dup_log_id = trigger_email(
            event_type="CANDIDATE_REGISTRATION",
            candidate_id=cand_user.id,
            db=db
        )
        print(f"Trigger returned duplicate log ID: {dup_log_id}")
        assert dup_log_id is None, "Duplicate email was not prevented!"
        print("Test 2 passed: Duplicate email triggered for same candidate event was successfully prevented.")

        # 4. Future Workflow Events Triggering
        print("\n--- Test 3: Triggering future workflow event HR_APPROVED ---")
        hr_app_log_id = trigger_email(
            event_type="HR_APPROVED",
            candidate_id=cand_user.id,
            db=db
        )
        print(f"Trigger returned HR_APPROVED log ID: {hr_app_log_id}")
        assert hr_app_log_id is not None, "Failed to trigger HR_APPROVED event"
        print("Waiting for HR_APPROVED event email to process...")
        hr_log = None
        for attempt in range(max_attempts):
            db.rollback()
            hr_log = db.query(EmailLog).filter(EmailLog.id == hr_app_log_id).first()
            if hr_log and hr_log.status != "Pending":
                break
            time.sleep(2)
        
        print(f"HR_APPROVED Log Status: {hr_log.status}")
        print(f"HR_APPROVED Subject: {hr_log.generated_subject}")
        assert hr_log.generated_subject is not None, "Subject line not populated for HR_APPROVED"
        print("Test 3 passed: Future workflow event HR_APPROVED successfully triggered and generated.")

        # 5. Endpoint Simulation Checks
        print("\n--- Test 4: Testing Candidate Logs Fetch Endpoint ---")
        from modules.email_automation.api import get_candidate_logs
        cand_logs = get_candidate_logs(candidate_id=cand_user.id, db=db)
        print(f"Fetched {len(cand_logs)} logs for candidate ID {cand_user.id}")
        assert len(cand_logs) >= 2, "Candidate logs list should contain at least 2 entries"
        for cl in cand_logs:
            print(f" - Log #{cl.id}: Type={cl.email_type}, Subject={cl.generated_subject}, Status={cl.status}")
        print("Test 4 passed: Candidate log history retrieval matches db state.")

        print("\n--- Test 5: Testing Recruiter Stats & Logs Endpoint ---")
        from modules.email_automation.api import get_email_stats, get_recruiter_logs
        stats = get_email_stats(db=db)
        print(f"Recruiter Email Stats: Sent={stats.total_sent}, Failed={stats.total_failed}, Pending={stats.total_pending}")
        
        all_recruiter_logs = get_recruiter_logs(db=db)
        print(f"Fetched {len(all_recruiter_logs)} total logs for recruiter view.")
        assert len(all_recruiter_logs) >= 2, "Recruiter logs list should retrieve logs"
        print("Test 5 passed: Recruiter dashboard API endpoints return statistics and log items successfully.")

        print("\n--- Test 6: Testing Resend Trigger API ---")
        from modules.email_automation.api import resend_email
        # Resend the first log (registration)
        resend_resp = resend_email(log_id=log_id, db=db)
        print(f"Resend Response: success={resend_resp.success}, msg='{resend_resp.message}'")
        assert resend_resp.success is True, "Resend action failed to trigger"
        
        # Verify log state is reset to Pending
        db.rollback()
        reset_log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        print(f"Reset Log Status after resend API: {reset_log.status}")
        assert reset_log.status == "Pending", "Log status was not reset to Pending"
        
        print("Waiting for resent email to process...")
        reprocessed_log = None
        for attempt in range(max_attempts):
            db.rollback()
            reprocessed_log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
            if reprocessed_log and reprocessed_log.status != "Pending":
                break
            time.sleep(2)
            
        print(f"Reprocessed Log Status: {reprocessed_log.status}")
        assert reprocessed_log.status in ["Sent", "Failed"], "Reprocessing failed to execute"
        print("Test 6 passed: Resend API resets logs and triggers async delivery pipeline.")

        print("\n"+"="*60)
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("="*60)

    except Exception as e:
        print(f"\nVERIFICATION FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up temporary test data
        print("Performing teardown of temporary test candidate and logs...")
        db.rollback() # Clear any active transaction or pending rollbacks
        if cand_user:
            try:
                db.query(EmailLog).filter(EmailLog.candidate_id == cand_user.id).delete()
                db.query(CandidateProfile).filter(CandidateProfile.user_id == cand_user.id).delete()
                db.query(User).filter(User.id == cand_user.id).delete()
                db.commit()
                print("Teardown complete.")
            except Exception as teardown_ex:
                print(f"Warning during teardown: {teardown_ex}")
        db.close()

if __name__ == "__main__":
    run_verification()
