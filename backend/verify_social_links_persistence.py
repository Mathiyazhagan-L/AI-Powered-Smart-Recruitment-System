import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

os.environ["DB_USER"] = "dummy"
os.environ["DB_PASSWORD"] = "dummy"

from main import app
from core.database import get_db
from core.base import Base

from modules.auth.model import User
from modules.candidate.profile.model import CandidateProfile
from modules.resume_parser.services.autofill_service import autofill_candidate_tables

from sqlalchemy.pool import StaticPool
from modules.auth.logic import create_access_token

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Create Candidate User (id=2)
    cand_user = User(
        id=2,
        email="candidate2@example.com",
        role="candidate",
        password_hash="dummy",
        full_name="Candidate Two"
    )
    db.add(cand_user)
    db.commit()
    db.close()

def run_tests():
    client = TestClient(app)
    token = create_access_token({"sub": "2", "role": "candidate"})
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "=" * 60)
    print("RUNNING SOCIAL LINKS PERSISTENCE VERIFICATION SCENARIOS")
    print("=" * 60)
    
    # -------------------------------------------------------------
    # Test 1: Manual Save via POST API
    # -------------------------------------------------------------
    print("\nTest 1: Manual Save Profile via POST /candidate/profile/create")
    payload = {
        "user_id": 2,
        "full_name": "Candidate Two",
        "email": "candidate2@example.com",
        "phone": "1234567890",
        "location": "NY",
        "headline": "Software Engineer",
        "summary": "Experienced dev",
        "linkedin_url": "https://linkedin.com/in/candidate-two",
        "github_url": "https://github.com/candidate-two",
        "portfolio_url": "https://candidate-two.dev"
    }
    
    res = client.post("/candidate/profile/create", json=payload, headers=headers)
    print(f"  POST Response Status: {res.status_code}")
    assert res.status_code == 201, f"Failed to create profile: {res.text}"
    data = res.json()
    print(f"  Saved LinkedIn: {data['linkedin_url']}")
    print(f"  Saved GitHub: {data['github_url']}")
    assert data["linkedin_url"] == "https://linkedin.com/in/candidate-two"
    assert data["github_url"] == "https://github.com/candidate-two"
    print("✓ Test 1 passed!")

    # -------------------------------------------------------------
    # Test 2: Reload / Fetch Profile via GET API
    # -------------------------------------------------------------
    print("\nTest 2: Reload Profile via GET /candidate/profile/{id}")
    res = client.get("/candidate/profile/2", headers=headers)
    print(f"  GET Response Status: {res.status_code}")
    assert res.status_code == 200, f"Failed to get profile: {res.text}"
    data = res.json()
    print(f"  Retrieved LinkedIn: {data['linkedin_url']}")
    print(f"  Retrieved GitHub: {data['github_url']}")
    assert data["linkedin_url"] == "https://linkedin.com/in/candidate-two"
    assert data["github_url"] == "https://github.com/candidate-two"
    print("✓ Test 2 passed!")

    # -------------------------------------------------------------
    # Test 3: Update Profile via PUT API
    # -------------------------------------------------------------
    print("\nTest 3: Update Profile via PUT /candidate/profile/update/{id}")
    update_payload = {
        "full_name": "Candidate Two Modified",
        "email": "candidate2@example.com",
        "phone": "9876543210",
        "linkedin_url": "https://linkedin.com/in/candidate-two-updated",
        "github_url": "https://github.com/candidate-two-updated"
    }
    res = client.put("/candidate/profile/update/2", json=update_payload, headers=headers)
    print(f"  PUT Response Status: {res.status_code}")
    assert res.status_code == 200, f"Failed to update profile: {res.text}"
    data = res.json()
    print(f"  Updated LinkedIn: {data['linkedin_url']}")
    print(f"  Updated GitHub: {data['github_url']}")
    assert data["linkedin_url"] == "https://linkedin.com/in/candidate-two-updated"
    assert data["github_url"] == "https://github.com/candidate-two-updated"
    print("✓ Test 3 passed!")

    # -------------------------------------------------------------
    # Test 4: Database State Check (Verify SQLite direct query)
    # -------------------------------------------------------------
    print("\nTest 4: Verify directly in the database")
    db = TestingSessionLocal()
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == 2).first()
    print(f"  DB Stored LinkedIn: {profile.linkedin_url}")
    print(f"  DB Stored GitHub: {profile.github_url}")
    assert profile.linkedin_url == "https://linkedin.com/in/candidate-two-updated"
    assert profile.github_url == "https://github.com/candidate-two-updated"
    db.close()
    print("✓ Test 4 passed!")

    # -------------------------------------------------------------
    # Test 5: Resume Parser Autofill Update Check
    # -------------------------------------------------------------
    print("\nTest 5: Resume Parser URL Autofill Update Check")
    mock_parsed_resume = {
        "personal": {
            "full_name": "Candidate Two",
            "email": "candidate2@example.com",
            "phone": "1234567890",
            "location": "NY",
            "linkedin_url": "https://linkedin.com/in/candidate-two-parsed",
            "github_url": "https://github.com/candidate-two-parsed",
            "portfolio_url": "https://candidate-two-parsed.dev"
        },
        "skills": [],
        "education": [],
        "experience": [],
        "projects": []
    }
    
    db = TestingSessionLocal()
    autofill_candidate_tables(db, 2, mock_parsed_resume)
    db.close()
    
    # Verify the values have been updated in the DB
    res = client.get("/candidate/profile/2", headers=headers)
    assert res.status_code == 200
    data = res.json()
    print(f"  Autofilled LinkedIn: {data['linkedin_url']}")
    print(f"  Autofilled GitHub: {data['github_url']}")
    assert data["linkedin_url"] == "https://linkedin.com/in/candidate-two-parsed"
    assert data["github_url"] == "https://github.com/candidate-two-parsed"
    print("✓ Test 5 passed!")

    print("\n" + "=" * 60)
    print("ALL SOCIAL LINKS PERSISTENCE SCENARIOS VERIFIED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    setup_db()
    try:
        run_tests()
    except AssertionError as e:
        print(f"\n❌ Assertion Failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)
