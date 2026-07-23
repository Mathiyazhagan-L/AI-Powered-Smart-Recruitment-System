import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from core.database import SessionLocal
from modules.candidate.profile.model import CandidateProfile

def check():
    db = SessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.user_id == 1).first()
    if p:
        print(f"Completion: {p.profile_completion}")
    else:
        print("No profile")
    db.close()

if __name__ == "__main__":
    check()
