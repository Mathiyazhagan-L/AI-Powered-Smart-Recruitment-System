import sys
import os
from sqlalchemy import text, inspect

# Ensure backend directory is in the Python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import engine, SessionLocal
from core.base import Base

# Import all models to register with the metadata Base
import modules.auth.model
import modules.company_profile.model
import modules.candidate.profile.model
import modules.candidate.education.model
import modules.candidate.experience.model
import modules.candidate.projects.model
import modules.candidate.skills.model
import modules.candidate.resume.model
import modules.job_management.model
import modules.resume_parser.model
import modules.ai_evaluation.model

# Import assessment models
import modules.assessment.models


def run_migrations():
    print("Connecting to the database and running migrations...")
    
    with SessionLocal() as db:
        inspector = inspect(engine)
        if 'candidate_profiles' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('candidate_profiles')]
            
            # Add aptitude_score column if missing
            if 'aptitude_score' not in columns:
                print("Adding column 'aptitude_score' to 'candidate_profiles'...")
                db.execute(text("ALTER TABLE candidate_profiles ADD COLUMN aptitude_score INT NULL"))
                
            # Add assessment_date column if missing
            if 'assessment_date' not in columns:
                print("Adding column 'assessment_date' to 'candidate_profiles'...")
                db.execute(text("ALTER TABLE candidate_profiles ADD COLUMN assessment_date DATETIME NULL"))

            # Add assessment_status column if missing
            if 'assessment_status' not in columns:
                print("Adding column 'assessment_status' to 'candidate_profiles'...")
                db.execute(text("ALTER TABLE candidate_profiles ADD COLUMN assessment_status VARCHAR(20) NULL"))
                
            db.commit()
            print("Checked and verified candidate_profiles schema columns.")
        else:
            print("Table 'candidate_profiles' does not exist yet. It will be created via create_all().")

    print("Dropping old assessment tables to apply new schema...")
    with SessionLocal() as db:
        db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        db.execute(text("DROP TABLE IF EXISTS assessment_results"))
        db.execute(text("DROP TABLE IF EXISTS assessment_answers"))
        db.execute(text("DROP TABLE IF EXISTS assessment_question_map"))
        db.execute(text("DROP TABLE IF EXISTS assessment_attempts"))
        db.execute(text("DROP TABLE IF EXISTS assessment_questions"))
        db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        db.commit()

    # Create all new tables registered with Base
    Base.metadata.create_all(bind=engine)
    print("All assessment tables created or verified successfully!")


if __name__ == "__main__":
    run_migrations()
