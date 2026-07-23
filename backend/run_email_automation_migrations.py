import sys
import os
from sqlalchemy import text, inspect

# Ensure backend directory is in the Python search path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import engine, SessionLocal

def run_migrations():
    print("Running Email Automation schema migrations on MySQL...")
    
    with SessionLocal() as db:
        inspector = inspect(engine)
        if 'email_logs' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('email_logs')]
            
            # Define new columns to add
            new_cols = {
                'email_type': "VARCHAR(100) NULL",
                'recipient_email': "VARCHAR(255) NULL",
                'generated_subject': "VARCHAR(255) NULL",
                'generated_content_json': "TEXT NULL",
                'generated_html': "LONGTEXT NULL",
                'status': "VARCHAR(20) NOT NULL DEFAULT 'Pending'",
                'sent_at': "DATETIME NULL"
            }
            
            for col_name, col_type in new_cols.items():
                if col_name not in columns:
                    print(f"Adding column '{col_name}' to 'email_logs'...")
                    db.execute(text(f"ALTER TABLE email_logs ADD COLUMN {col_name} {col_type}"))
            
            # Ensure candidate_id is nullable (recruiters don't have candidate_id)
            print("Ensuring 'candidate_id' is nullable...")
            db.execute(text("ALTER TABLE email_logs MODIFY COLUMN candidate_id INT NULL"))
            
            db.commit()
            print("Successfully updated email_logs table schema.")
        else:
            print("Table 'email_logs' not found. It will be created on database initialization.")

if __name__ == "__main__":
    run_migrations()
