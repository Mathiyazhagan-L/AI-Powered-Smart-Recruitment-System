import sys
import os

# Add the backend directory to sys.path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from sqlalchemy.orm import Session
from core.database import SessionLocal
from modules.auth.model import User
from modules.offer_management.model import OfferLetter
from modules.interview_scheduling.model import InterviewSchedule
from modules.candidate.profile.model import CandidateProfile

def delete_mock_data():
    db = SessionLocal()
    try:
        # Find the mock candidate & recruiter users by email or name
        mock_emails = ["cand_offer_test@example.com", "rec_offer_test@example.com"]
        mock_users = db.query(User).filter(
            (User.email.in_(mock_emails)) | (User.full_name == "Test Candidate Workflow")
        ).all()
        
        if not mock_users:
            print("No mock users found.")
        
        for mock_user in mock_users:
            print(f"Deleting mock user {mock_user.id} ({mock_user.email}) and related data...")
            
            # Delete their offers
            deleted_offers = db.query(OfferLetter).filter(
                (OfferLetter.candidate_id == mock_user.id) | 
                (OfferLetter.candidate_name == "Test Candidate Workflow")
            ).delete(synchronize_session=False)
            print(f"Deleted {deleted_offers} offers.")
            
            # Delete their interviews
            deleted_interviews = db.query(InterviewSchedule).filter(
                InterviewSchedule.candidate_id == mock_user.id
            ).delete(synchronize_session=False)
            print(f"Deleted {deleted_interviews} interviews.")
            
            # Delete candidate profile
            deleted_profiles = db.query(CandidateProfile).filter(
                (CandidateProfile.user_id == mock_user.id) |
                (CandidateProfile.email == mock_user.email) |
                (CandidateProfile.full_name == "Test Candidate Workflow")
            ).delete(synchronize_session=False)
            print(f"Deleted {deleted_profiles} candidate profiles.")
            
            # Delete the user
            db.delete(mock_user)
            
        # Delete mock Job 9999 and related applications
        from modules.job_management.model import Job, Application
        db.query(Application).filter(Application.job_id == 9999).delete(synchronize_session=False)
        db.query(Job).filter(Job.id == 9999).delete(synchronize_session=False)
        
        db.commit()
        print("Mock data deleted successfully.")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    delete_mock_data()
