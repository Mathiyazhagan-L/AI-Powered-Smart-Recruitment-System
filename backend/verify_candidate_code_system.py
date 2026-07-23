import sys
import os

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app
from core.database import SessionLocal
from modules.candidate.profile.model import CandidateProfile
from modules.auth.model import User

client = TestClient(app)

def create_test_candidate(db, email_prefix):
    email = f"{email_prefix}@test.com"
    # Create user first to get user_id
    user = User(email=email, password_hash="test", full_name="Test User", role="candidate")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create profile
    from modules.candidate.profile.logic import create_profile
    from modules.candidate.profile.schema import CandidateProfileCreate
    profile_data = CandidateProfileCreate(
        user_id=user.id,
        full_name="Test User",
        email=email
    )
    profile = create_profile(db, profile_data)
    return user, profile

def verify_system():
    print("--- Starting Candidate Code System Verification ---")
    db = SessionLocal()
    
    try:
        # Verify 1 & 7: Migration is safe and existing candidates receive codes
        print("\nTesting Migration Script...")
        import migrate_candidate_codes
        
        # Strip code from one candidate if exists to test migration
        cand = db.query(CandidateProfile).first()
        if cand:
            old_code = cand.candidate_code
            cand.candidate_code = None
            db.commit()
            print(f"Temporarily removed code from Candidate {cand.id} for testing.")
            
            migrated_count = migrate_candidate_codes.run_migration(db)
            print(f"Migrated {migrated_count} candidates.")
            assert migrated_count > 0, "Migration should have affected at least one candidate"
            
            # Verify re-run is safe
            migrated_count_2 = migrate_candidate_codes.run_migration(db)
            assert migrated_count_2 == 0, "Second migration run should do nothing"
            print("Migration is idempotent.")
            
        else:
            print("No candidates in DB to test migration. Skipping...")

        # Verify 2: New candidates receive codes automatically
        print("\nTesting New Candidate Code Generation...")
        user1, prof1 = create_test_candidate(db, "cand_code_test_1")
        print(f"Created new candidate profile ID: {prof1.id}, Code: {prof1.candidate_code}")
        assert prof1.candidate_code == f"AIH{prof1.id:04d}", f"Expected code AIH{prof1.id:04d}, got {prof1.candidate_code}"
        
        user2, prof2 = create_test_candidate(db, "cand_code_test_2")
        print(f"Created new candidate profile ID: {prof2.id}, Code: {prof2.candidate_code}")
        assert prof2.candidate_code == f"AIH{prof2.id:04d}", f"Expected code AIH{prof2.id:04d}, got {prof2.candidate_code}"

        # Verify 3: No duplicate candidate codes
        print("\nVerifying uniqueness constraint...")
        codes = db.query(CandidateProfile.candidate_code).filter(CandidateProfile.candidate_code != None).all()
        code_list = [c[0] for c in codes]
        assert len(code_list) == len(set(code_list)), "Duplicate candidate codes found in DB!"
        print("No duplicates found.")

        # Verify 4: APIs expose candidate_code
        print("\nVerifying API Response Schema...")
        response = client.get(f"/candidate/profile/{prof1.user_id}")
        assert response.status_code == 200, f"API Error: {response.text}"
        data = response.json()
        assert "candidate_code" in data, "candidate_code missing from API response"
        assert data["candidate_code"] == prof1.candidate_code, f"API returned wrong code: {data['candidate_code']}"
        print("API successfully exposes candidate_code.")

        # Print success
        print("\nAll System Verifications Passed Successfully!")
        
    except AssertionError as e:
        print(f"\nVerification Failed: {e}")
    finally:
        # Cleanup
        db.query(CandidateProfile).filter(CandidateProfile.email.like("cand_code_test_%")).delete(synchronize_session=False)
        db.query(User).filter(User.email.like("cand_code_test_%")).delete(synchronize_session=False)
        db.commit()
        db.close()

if __name__ == "__main__":
    verify_system()
