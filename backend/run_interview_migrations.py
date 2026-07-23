import sys
import os
from sqlalchemy import text, inspect

# Ensure backend directory is in the Python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import engine, SessionLocal

def run_migrations():
    print("Running interview assessment migrations...")
    
    with SessionLocal() as db:
        inspector = inspect(engine)
        if 'candidate_profiles' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('candidate_profiles')]
            
            # Add interview_score column if missing
            if 'interview_score' not in columns:
                print("Adding column 'interview_score' to 'candidate_profiles'...")
                db.execute(text("ALTER TABLE candidate_profiles ADD COLUMN interview_score FLOAT NULL"))
                
            # Add interview_date column if missing
            if 'interview_date' not in columns:
                print("Adding column 'interview_date' to 'candidate_profiles'...")
                db.execute(text("ALTER TABLE candidate_profiles ADD COLUMN interview_date DATETIME NULL"))

            # Add interview_status column if missing
            if 'interview_status' not in columns:
                print("Adding column 'interview_status' to 'candidate_profiles'...")
                db.execute(text("ALTER TABLE candidate_profiles ADD COLUMN interview_status VARCHAR(50) NULL"))
                
            db.commit()
            print("Successfully updated candidate_profiles table schema.")
        else:
            print("Table 'candidate_profiles' not found. It will be created on start.")

if __name__ == "__main__":
    run_migrations()
