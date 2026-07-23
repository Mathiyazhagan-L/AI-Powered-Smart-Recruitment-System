import sys
import os
from sqlalchemy.orm import Session
from datetime import date, timedelta

# Add current directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from modules.auth.model import User
from modules.job_management.model import Job, Application
from modules.candidate.profile.model import CandidateProfile
from modules.offer_management.model import OfferLetter
from modules.offer_management.logic import OfferManagementLogic
from modules.offer_management.schema import OfferCreate
from modules.email_automation.models import EmailLog

def run_verify():
    print("====================================================")
    print("Verifying Offer Acceptance & Post-Offer Workflow")
    print("====================================================")
    
    db = SessionLocal()
    
    # 1. Clean previous data
    db.query(EmailLog).filter(EmailLog.recipient_email == "cand_accept_test@example.com").delete()
    db.query(OfferLetter).filter(OfferLetter.candidate_id == 9999).delete()
    db.query(Application).filter(Application.candidate_id == 9999).delete()
    db.query(CandidateProfile).filter(CandidateProfile.user_id == 9999).delete()
    db.query(Job).filter(Job.id == 9999).delete()
    db.query(User).filter(User.id.in_([9999, 9998])).delete()
    db.commit()

    try:
        # Create users
        cand_user = User(id=9999, email="cand_accept_test@example.com", role="candidate", password_hash="hash")
        rec_user = User(id=9998, email="rec_accept_test@example.com", role="recruiter", password_hash="hash")
        db.add_all([cand_user, rec_user])
        db.commit()

        # Create Profile
        profile = CandidateProfile(
            user_id=9999,
            candidate_code="AIHACC",
            full_name="Acceptance Test Candidate",
            email="cand_accept_test@example.com",
            interview_status="Selected" # Initial State
        )
        db.add(profile)

        # Create Job
        job = Job(
            id=9999,
            title="Senior Developer",
            description="Engineering lead role.",
            required_skills=["Python"],
            preferred_skills=["Docker"],
            experience="5 years",
            package="24 LPA",
            location="Remote",
            openings=1,
            deadline=date.today(),
            selection_rounds=[],
            salary_rules={},
            eligibility_rules={},
            application_settings={}
        )
        db.add(job)

        # Create Application
        app = Application(
            job_id=9999,
            candidate_id=9999,
            status="Applied"
        )
        db.add(app)
        db.commit()

        # Create Offer Input
        offer_data = OfferCreate(
            candidate_id=9999,
            job_id=9999,
            recruiter_id=9998,
            company_name="Acme Tech Labs",
            position_title="Senior Developer",
            department="Engineering",
            employment_type="Full-time",
            package_amount="24 LPA",
            joining_date=date.today() + date.resolution * 30,
            location="Remote",
            reporting_manager="VP of Engineering",
            offer_expiry_date=date.today() + date.resolution * 7
        )

        print("[Step 1] Creating and Generating Draft...")
        offer = OfferManagementLogic.create_offer_draft(db, offer_data)
        offer = OfferManagementLogic.generate_offer(db, offer.id)
        
        print("[Step 2] Sending Offer (logs attachment and status = Sent)...")
        offer = OfferManagementLogic.send_offer(db, offer.id)
        assert offer.offer_status == "Sent", "Offer status should be Sent."
        
        sent_email = db.query(EmailLog).filter(
            EmailLog.candidate_id == 9999,
            EmailLog.email_type == "OFFER_SENT"
        ).first()
        assert sent_email is not None, "OFFER_SENT email was not logged."
        print(f"-> Offer Sent email log found. Status: {sent_email.status}")

        # Check Application Status updated to 'Offer Released'
        db.refresh(app)
        assert app.status == "Offer Released", f"Application status should be Offer Released (got {app.status})."
        print(f"-> Application status correctly transitioned to: {app.status}")

        print("[Step 3] Simulating Candidate Acceptance (status = Accepted, NOT Hired yet)...")
        offer = OfferManagementLogic.accept_offer(db, offer.id)
        assert offer.offer_status == "Accepted", "Offer status should update to Accepted."
        assert offer.candidate_response == "Accepted", "Candidate response should be Accepted."
        
        db.refresh(app)
        assert app.status == "Offer Accepted", f"Application status should update to Offer Accepted (got {app.status})."
        
        db.refresh(profile)
        assert profile.interview_status == "Selected", f"Candidate profile interview status should NOT be Hired yet (got {profile.interview_status})."
        print("-> Offer accepted and application status updated to Offer Accepted successfully.")

        print("[Step 4] Simulating Recruiter Joined Action (joining_status = Joined)...")
        offer = OfferManagementLogic.mark_joined(db, offer.id)
        assert offer.offer_status == "Joined", "Offer status should update to Joined."
        assert offer.joining_status == "Joined", "Joining status should update to Joined."
        assert offer.joined_date == date.today(), "Joined date should be today."
        
        db.refresh(app)
        assert app.status == "Joined", f"Application status should be Joined (got {app.status})."
        print("-> Candidate marked as Joined successfully.")

        print("[Step 5] Simulating Recruiter Hired Action (final step, candidate status = Hired)...")
        offer = OfferManagementLogic.mark_hired(db, offer.id)
        assert offer.offer_status == "Hired", "Offer status should update to Hired."
        
        db.refresh(app)
        assert app.status == "Hired", f"Application status should be Hired (got {app.status})."
        
        db.refresh(profile)
        assert profile.interview_status == "Hired", f"Candidate profile status should be Hired (got {profile.interview_status})."
        print("-> Candidate marked as Hired successfully. Recruitment lifecycle completed.")

        print("[Step 6] Verifying Expiry Sweep Cron Simulation...")
        # Create an expired offer
        expired_offer = OfferLetter(
            candidate_id=9999,
            candidate_code="AIHEXP",
            job_id=9999,
            recruiter_id=9998,
            offer_reference="AIH-OFFER-AIHEXP-J9999-V1",
            offer_version=1,
            company_name="Acme Labs",
            candidate_name="Expired Candidate",
            position_title="Developer",
            department="Engineering",
            employment_type="Full-time",
            package_amount="10 LPA",
            joining_date=date.today(),
            location="Remote",
            reporting_manager="Lead",
            offer_status="Sent",
            offer_expiry_date=date.today() - timedelta(days=1) # Expired yesterday
        )
        db.add(expired_offer)
        db.commit()

        expired_count = OfferManagementLogic.auto_expire_offers(db)
        print(f"-> Sweep completed. Total expired offers processed: {expired_count}")
        assert expired_count == 1, f"Expected 1 expired offer to be processed (got {expired_count})."
        
        db.refresh(expired_offer)
        assert expired_offer.offer_status == "Expired", f"Offer status should be Expired (got {expired_offer.offer_status})."
        print("-> Sweep successfully expired out-of-date offers.")

        print("[Step 7] Verifying Expiry Reminder Sweep Cron Simulation...")
        # Create an offer expiring in 1 day
        expiring_offer = OfferLetter(
            candidate_id=9999,
            candidate_code="AIHREM",
            job_id=9999,
            recruiter_id=9998,
            offer_reference="AIH-OFFER-AIHREM-J9999-V1",
            offer_version=1,
            company_name="Acme Labs",
            candidate_name="Reminder Candidate",
            position_title="Developer",
            department="Engineering",
            employment_type="Full-time",
            package_amount="10 LPA",
            joining_date=date.today(),
            location="Remote",
            reporting_manager="Lead",
            offer_status="Sent",
            offer_expiry_date=date.today() + timedelta(days=1) # Expires tomorrow
        )
        db.add(expiring_offer)
        db.commit()

        reminder_count = OfferManagementLogic.send_expiry_reminders(db)
        print(f"-> Sweep completed. Expiry reminders sent: {reminder_count}")
        assert reminder_count == 1, f"Expected 1 reminder to be sent (got {reminder_count})."
        
        reminder_email = db.query(EmailLog).filter(
            EmailLog.recipient_email == "cand_accept_test@example.com",
            EmailLog.email_type == "OFFER_EXPIRY_REMINDER"
        ).first()
        assert reminder_email is not None, "Reminder email was not logged."
        print("-> Sweep successfully dispatched reminder alerts.")

        print("[Step 8] Verifying Recruiter Dashboard Analytics...")
        analytics = OfferManagementLogic.get_analytics(db)
        print(f"-> Analytics retrieved: {analytics}")
        assert analytics["total_generated"] >= 3, "Total generated count mismatch."
        assert analytics["accepted_offers"] == 1, "Accepted offers count mismatch."
        assert analytics["expired_offers"] >= 1, "Expired offers count mismatch."
        print("-> Analytics dashboard values successfully validated.")

        print("====================================================")
        print("VERIFICATION SUCCESSFUL: Acceptance & post-offer lifecycle works!")
        print("====================================================")

    except Exception as e:
        print(f"VERIFICATION FAILURE: {e}")
        import traceback
        traceback.print_exc()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run_verify()
