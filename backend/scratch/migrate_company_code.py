import sys
import os
from sqlalchemy import text

# Add parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal, engine
from modules.auth.model import User
from modules.candidate.profile.model import CandidateProfile
from modules.company_profile.model import CompanyProfile

def run_migration():
    print("Connecting to the database...")
    db = SessionLocal()
    
    try:
        # Step 1: Alter table schema for company_profiles (make website nullable and add company_code)
        print("Checking/Updating database schema for company_profiles...")
        with engine.begin() as conn:
            # 1.1 Check if company_code column exists
            columns_query = conn.execute(text("SHOW COLUMNS FROM company_profiles LIKE 'company_code'"))
            column_exists = columns_query.fetchone() is not None
            
            if not column_exists:
                print("Adding 'company_code' column to 'company_profiles' table...")
                conn.execute(text("ALTER TABLE company_profiles ADD COLUMN company_code VARCHAR(50) UNIQUE NULL;"))
                print("'company_code' column added successfully.")
            else:
                print("'company_code' column already exists.")
                
            # 1.2 Modify website to be nullable
            print("Ensuring 'website' column is nullable in 'company_profiles' table...")
            conn.execute(text("ALTER TABLE company_profiles MODIFY COLUMN website VARCHAR(255) NULL;"))
            print("'website' column modified successfully.")
            
        # Step 2: Generate company codes for existing company profiles
        print("Migrating company profiles (generating company codes)...")
        companies = db.query(CompanyProfile).filter(
            (CompanyProfile.company_code == None) | (CompanyProfile.company_code == "")
        ).all()
        
        company_count = 0
        for comp in companies:
            comp.company_code = f"AIHR{comp.id:04d}"
            company_count += 1
            
        if company_count > 0:
            db.commit()
            print(f"Generated company codes for {company_count} company profiles.")
        else:
            print("No company profiles needed migration.")

        # Step 3: Generate candidate profiles for users who registered as candidate but don't have a profile
        print("Checking for candidate users without profiles...")
        candidate_users = db.query(User).filter(User.role == "candidate").all()
        candidate_created_count = 0
        for u in candidate_users:
            profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == u.id).first()
            if not profile:
                print(f"Creating missing CandidateProfile for user: {u.email} (ID: {u.id})...")
                profile = CandidateProfile(
                    user_id=u.id,
                    full_name=u.full_name or "Candidate Name",
                    email=u.email,
                    phone=u.phone,
                    candidate_status="NEW",
                    profile_completion=0
                )
                db.add(profile)
                db.commit()
                db.refresh(profile)
                profile.candidate_code = f"AIH{profile.id:04d}"
                db.commit()
                db.refresh(profile)
                print(f"Created profile with code: {profile.candidate_code}")
                candidate_created_count += 1
                
        print(f"Auto-created {candidate_created_count} missing candidate profiles.")

        # Step 4: Generate company profiles for users who registered as recruiter/company but don't have a profile
        print("Checking for recruiter/company users without profiles...")
        recruiter_users = db.query(User).filter(User.role.in_(["company", "recruiter", "RECRUITER"])).all()
        recruiter_created_count = 0
        for u in recruiter_users:
            company = db.query(CompanyProfile).filter(CompanyProfile.user_id == u.id).first()
            if not company:
                print(f"Creating missing CompanyProfile for user: {u.email} (ID: {u.id})...")
                company = CompanyProfile(
                    user_id=u.id,
                    company_name=u.full_name or "Company Name",
                    company_email=u.email,
                    company_phone=u.phone,
                    website="",
                    is_email_verified=False,
                    verification_status="Pending"
                )
                db.add(company)
                db.commit()
                db.refresh(company)
                company.company_code = f"AIHR{company.id:04d}"
                db.commit()
                db.refresh(company)
                print(f"Created company profile with code: {company.company_code}")
                recruiter_created_count += 1
                
        print(f"Auto-created {recruiter_created_count} missing company profiles.")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    run_migration()
