import os
import sys

# Add backend directory to sys.path
sys.path.append(r"c:\Recruitment\backend")

from core.database import SessionLocal
from modules.auth.model import User
from modules.coding_assessment.models import CodingResult, CodingAttempt
from modules.candidate.profile.model import CandidateProfile

def pass_coding_test(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} not found.")
            return

        print(f"Found user: {user.id}")

        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
        if not profile:
            print(f"Candidate profile for {email} not found.")
            return

        # Create or update Coding Attempt
        attempt = db.query(CodingAttempt).filter(CodingAttempt.candidate_id == user.id).first()
        if not attempt:
            attempt = CodingAttempt(candidate_id=user.id)
            db.add(attempt)
            db.commit()
            db.refresh(attempt)
        
        attempt.status = "COMPLETED"
        attempt.score = 100.0

        # Create or update Coding Result
        result = db.query(CodingResult).filter(CodingResult.candidate_id == user.id).first()
        if not result:
            result = CodingResult(
                candidate_id=user.id,
                attempt_id=attempt.id,
                total_score=100.0,
                easy_score=100.0,
                medium_score=100.0,
                hard_score=100.0,
                questions_solved=3,
                questions_attempted=3,
                status="PASS"
            )
            db.add(result)
        else:
            result.total_score = 100.0
            result.status = "PASS"
            
        # Update CandidateProfile coding score and assessment status if applicable
        if hasattr(profile, 'coding_score'):
            profile.coding_score = 100.0
            
        # If aptitude is PASSED and coding is PASSED, maybe we need to ensure the profile allows moving to interview
        # Usually frontend checks `/coding/result/` endpoint which we just populated in `CodingResult`
            
        db.commit()
        print(f"Successfully marked coding assessment as PASS for {email}.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    pass_coding_test("ml7785792@gmail.com")
