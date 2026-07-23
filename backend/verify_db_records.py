import sys
import os

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.database import SessionLocal
from modules.assessment.models import AssessmentAttempt

def verify():
    db = SessionLocal()
    attempts = db.query(AssessmentAttempt).filter(AssessmentAttempt.candidate_id == 1).all()
    for a in attempts:
        print(a.id, a.status, a.start_time)
    db.close()

if __name__ == "__main__":
    verify()
