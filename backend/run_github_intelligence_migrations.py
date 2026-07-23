import sys
import os
from sqlalchemy import text, inspect

# Ensure backend directory is in the Python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import engine, SessionLocal

def run_migrations():
    print("Running GitHub Intelligence schema migrations...")
    
    with SessionLocal() as db:
        inspector = inspect(engine)
        if 'candidate_profiles' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('candidate_profiles')]
            
            # Define new columns
            new_cols = {
                'github_score': "INT NULL",
                'github_summary': "JSON NULL",
                'github_last_updated': "DATETIME NULL",
                'github_repositories': "INT NULL",
                'github_stars': "INT NULL",
                'github_followers': "INT NULL",
                'github_languages': "JSON NULL"
            }
            
            for col_name, col_type in new_cols.items():
                if col_name not in columns:
                    print(f"Adding column '{col_name}' to 'candidate_profiles'...")
                    db.execute(text(f"ALTER TABLE candidate_profiles ADD COLUMN {col_name} {col_type}"))
                    
            db.commit()
            print("Successfully updated candidate_profiles table schema.")
        else:
            print("Table 'candidate_profiles' not found. It will be created on start.")

if __name__ == "__main__":
    run_migrations()
