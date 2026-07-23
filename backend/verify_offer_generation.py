import sys
import os
from sqlalchemy.orm import Session
from datetime import date

# Add current directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from core.base import Base
from modules.auth.model import User
from modules.job_management.model import Job, Application
from modules.candidate.profile.model import CandidateProfile
from modules.offer_management.model import OfferLetter
from modules.offer_management.logic import OfferManagementLogic
from modules.offer_management.schema import OfferCreate
from modules.email_automation.models import EmailLog

def run_verify():
    print("====================================================")
    print("Verifying Offer Draft & Generation Workflows")
    print("====================================================")
    
    db = SessionLocal()
    
    # 1. Clean previous data
    db.query(EmailLog).filter(EmailLog.recipient_email == "cand_offer_test@example.com").delete()
    db.query(OfferLetter).filter(OfferLetter.candidate_id == 9999).delete()
    db.query(Application).filter(Application.candidate_id == 9999).delete()
    db.query(CandidateProfile).filter(CandidateProfile.user_id == 9999).delete()
    db.query(Job).filter(Job.id == 9999).delete()
    db.query(User).filter(User.id.in_([9999, 9998])).delete()
    db.commit()

    try:
        # Create users
        cand_user = User(id=9999, email="cand_offer_test@example.com", role="candidate", password_hash="hash")
        rec_user = User(id=9998, email="rec_offer_test@example.com", role="recruiter", password_hash="hash")
        db.add_all([cand_user, rec_user])
        db.commit()

        # Create Profile
        profile = CandidateProfile(
            user_id=9999,
            candidate_code="AIHTEST",
            full_name="Test Candidate Workflow",
            email="cand_offer_test@example.com"
        )
        db.add(profile)

        # Create Job
        job = Job(
            id=9999,
            title="Software Developer",
            description="Technical engineering role.",
            required_skills=["Python"],
            preferred_skills=["FastAPI"],
            experience="2 years",
            package="12 LPA",
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

        # Create Offer Draft Input
        offer_data = OfferCreate(
            candidate_id=9999,
            job_id=9999,
            recruiter_id=9998,
            company_name="AIHire Client Corp",
            position_title="Software Developer",
            department="Engineering",
            employment_type="Full-time",
            package_amount="12 LPA",
            joining_date=date.today() + date.resolution * 30, # 30 days out
            location="Remote",
            reporting_manager="Engineering Director",
            offer_expiry_date=date.today() + date.resolution * 7, # 7 days out
            notes="Initial salary negotiation proposal."
        )

        print("[Step 1] Creating Offer Letter Draft...")
        offer = OfferManagementLogic.create_offer_draft(db, offer_data)
        
        assert offer is not None, "Failed to create draft offer."
        assert offer.offer_status == "Draft", "Offer status should be Draft."
        assert offer.offer_version == 1, "Offer version should be 1."
        assert offer.candidate_code == "AIHTEST", "Candidate code mismatch."
        assert "AIH-OFFER-AIHTEST-J9999-V1" in offer.offer_reference, "Offer reference format mismatch."
        print(f"-> Draft Offer created with Ref: {offer.offer_reference}")

        # Try to create a second draft for the same candidate/job to check version incrementing
        print("[Step 2] Creating second Offer Letter Draft for negotiation...")
        offer_v2 = OfferManagementLogic.create_offer_draft(db, offer_data)
        assert offer_v2.offer_version == 2, "Offer version should increment to 2."
        assert "AIH-OFFER-AIHTEST-J9999-V2" in offer_v2.offer_reference, "Offer version 2 reference format mismatch."
        print(f"-> Second Draft Offer created successfully with Version: {offer_v2.offer_version} Ref: {offer_v2.offer_reference}")

        print("[Step 3] Generating PDF and email notifications for Draft v2...")
        offer_v2 = OfferManagementLogic.generate_offer(db, offer_v2.id)
        assert offer_v2.offer_status == "Generated", "Status should update to Generated."
        assert offer_v2.offer_pdf_path is not None, "PDF Path should be populated."
        print(f"-> PDF path populated: {offer_v2.offer_pdf_path}")

        # Check that OFFER_GENERATED email is logged
        email_log = db.query(EmailLog).filter(
            EmailLog.candidate_id == 9999,
            EmailLog.email_type == "OFFER_GENERATED"
        ).first()
        assert email_log is not None, "OFFER_GENERATED email was not logged."
        print(f"-> Email trigger successfully logged: {email_log.email_type} (Status: {email_log.status})")

        print("====================================================")
        print("VERIFICATION SUCCESSFUL: Offer generation & versioning works!")
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
