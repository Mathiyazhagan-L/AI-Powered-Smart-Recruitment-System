import sys
import os
from sqlalchemy.orm import Session
from datetime import date

# Add current directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.database import SessionLocal
from modules.auth.model import User
from modules.job_management.model import Job, Application
from modules.candidate.profile.model import CandidateProfile
from modules.offer_management.model import OfferLetter
from modules.offer_management.logic import OfferManagementLogic
from modules.offer_management.schema import OfferCreate

def run_verify():
    print("====================================================")
    print("Verifying Offer PDF Generation & Storage")
    print("====================================================")
    
    db = SessionLocal()
    
    # 1. Clean previous data
    db.query(OfferLetter).filter(OfferLetter.candidate_id == 9999).delete()
    db.query(Application).filter(Application.candidate_id == 9999).delete()
    db.query(CandidateProfile).filter(CandidateProfile.user_id == 9999).delete()
    db.query(Job).filter(Job.id == 9999).delete()
    db.query(User).filter(User.id.in_([9999, 9998])).delete()
    db.commit()

    try:
        # Create users
        cand_user = User(id=9999, email="cand_pdf_test@example.com", role="candidate", password_hash="hash")
        rec_user = User(id=9998, email="rec_pdf_test@example.com", role="recruiter", password_hash="hash")
        db.add_all([cand_user, rec_user])
        db.commit()

        # Create Profile
        profile = CandidateProfile(
            user_id=9999,
            candidate_code="AIHPDF",
            full_name="PDF Test Candidate",
            email="cand_pdf_test@example.com"
        )
        db.add(profile)

        # Create Job
        job = Job(
            id=9999,
            title="PDF Designer",
            description="Visual content role.",
            required_skills=["Design"],
            preferred_skills=["PDFs"],
            experience="1 year",
            package="8 LPA",
            location="Remote",
            openings=1,
            deadline=date.today(),
            selection_rounds=[],
            salary_rules={},
            eligibility_rules={},
            application_settings={}
        )
        db.add(job)
        db.commit()

        # Create Offer Draft Input
        offer_data = OfferCreate(
            candidate_id=9999,
            job_id=9999,
            recruiter_id=9998,
            company_name="Acme Design Labs",
            position_title="PDF Designer",
            department="Creative",
            employment_type="Full-time",
            package_amount="8 LPA",
            joining_date=date.today() + date.resolution * 30,
            location="Remote",
            reporting_manager="Creative Lead",
            offer_expiry_date=date.today() + date.resolution * 7
        )

        print("[Step 1] Creating Draft...")
        offer = OfferManagementLogic.create_offer_draft(db, offer_data)
        
        print("[Step 2] Generating PDF...")
        offer = OfferManagementLogic.generate_offer(db, offer.id)
        
        # Verify PDF path and file existence
        assert offer.offer_pdf_path is not None, "PDF Path is null."
        
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        absolute_pdf_path = os.path.join(backend_dir, offer.offer_pdf_path)
        
        print(f"-> Verifying PDF file exists at absolute path: {absolute_pdf_path}")
        assert os.path.exists(absolute_pdf_path), f"PDF file does not exist on disk: {absolute_pdf_path}"
        
        file_size = os.path.getsize(absolute_pdf_path)
        print(f"-> PDF File successfully created. Size: {file_size} bytes")
        assert file_size > 0, "PDF file is empty (0 bytes)."

        print("====================================================")
        print("VERIFICATION SUCCESSFUL: PDF generated and stored successfully!")
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
