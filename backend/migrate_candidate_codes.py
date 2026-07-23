import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.database import SessionLocal
from modules.candidate.profile.model import CandidateProfile

def run_migration(db: Session = None):
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
        
    try:
        # Find all candidates without a candidate_code
        candidates = db.query(CandidateProfile).filter(CandidateProfile.candidate_code == None).all()
        
        count = 0
        for profile in candidates:
            profile.candidate_code = f"AIH{profile.id:04d}"
            count += 1
            
        if count > 0:
            db.commit()
            print(f"Migrated {count} candidate profiles with new candidate codes.")
        else:
            print("No candidate profiles needed migration (all have candidate codes).")
            
        return count
    except Exception as e:
        print(f"Migration failed: {e}")
        db.rollback()
        raise e
    finally:
        if close_db:
            db.close()

if __name__ == "__main__":
    print("Starting Candidate Code Migration...")
    run_migration()
    print("Migration complete.")
