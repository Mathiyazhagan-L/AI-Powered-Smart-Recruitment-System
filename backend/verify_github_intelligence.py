import sys
import os
from unittest.mock import patch
import requests
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure backend directory is in the Python search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

os.environ["DB_USER"] = "dummy"
os.environ["DB_PASSWORD"] = "dummy"

from main import app
from core.database import get_db
from core.base import Base
from modules.auth.model import User
from modules.candidate.profile.model import CandidateProfile
from modules.auth.logic import create_access_token
from modules.resume_parser.services.autofill_service import autofill_candidate_tables

# Setup sqlite in-memory database with StaticPool for thread-safe shared connection
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
    
    # Create Candidate User (id=3)
    cand_user = User(
        id=3,
        email="candidate3@example.com",
        role="candidate",
        password_hash="dummy",
        full_name="Candidate Three"
    )
    db.add(cand_user)
    db.commit()
    db.close()

# Mock response class for requests.get
class MockResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self.json_data = json_data
        
    def json(self):
        return self.json_data

# Global request count tracker
request_count = 0

def mock_github_api(url, *args, **kwargs):
    global request_count
    request_count += 1
    
    # Rate limit test case
    if "ratelimited" in url:
        return MockResponse(403, {"message": "API rate limit exceeded"})
        
    # Unavailable test case
    if "unavailable" in url:
        return MockResponse(502, {"message": "Bad Gateway"})
        
    # Timeout test case
    if "timeout" in url:
        raise requests.exceptions.Timeout("Connection timed out")

    # Valid user case
    if "validuser" in url:
        if "/repos" in url:
            return MockResponse(200, [
                {
                    "name": "python-project",
                    "language": "Python",
                    "stargazers_count": 2,
                    "forks_count": 1,
                    "updated_at": "2026-06-15T12:00:00Z"
                },
                {
                    "name": "react-frontend",
                    "language": "JavaScript",
                    "stargazers_count": 3,
                    "forks_count": 0,
                    "updated_at": "2026-05-10T12:00:00Z"
                }
            ])
        else:
            return MockResponse(200, {
                "login": "validuser",
                "followers": 5,
                "following": 3
            })
            
    # Default fallback
    return MockResponse(404, {"message": "Not Found"})

# Mock background evaluation trigger to execute synchronously in tests
def mock_trigger_background_github_evaluation(profile_id: int, github_url: str):
    from modules.github_intelligence.service import run_github_evaluation_task
    run_github_evaluation_task(profile_id, github_url)

# Apply patches so that database writes use SQLite memory DB, requests are mocked, and background tasks run synchronously
@patch("core.database.SessionLocal", TestingSessionLocal)
@patch("modules.github_intelligence.service.trigger_background_github_evaluation", mock_trigger_background_github_evaluation)
@patch("requests.get", side_effect=mock_github_api)
def run_tests(mock_get):
    global request_count
    client = TestClient(app)
    token = create_access_token({"sub": "3", "role": "candidate"})
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "=" * 60)
    print("RUNNING GITHUB INTELLIGENCE ENGINE VERIFICATION")
    print("=" * 60)

    # Setup profile
    print("\nSetting up initial profile with NO GitHub URL...")
    create_payload = {
        "user_id": 3,
        "full_name": "Candidate Three",
        "email": "candidate3@example.com",
        "phone": "555-0199",
        "location": "San Francisco",
        "headline": "Fullstack Lead",
        "summary": "Building modern apps",
        "linkedin_url": "https://linkedin.com/in/candidate3",
        "github_url": None
    }
    res = client.post("/candidate/profile/create", json=create_payload, headers=headers)
    assert res.status_code == 201, f"Failed initial profile creation: {res.text}"
    profile_id = res.json()["id"]
    print(f"✓ Initial profile created with ID: {profile_id}")

    # Verify that github columns are null
    db = TestingSessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    assert p.github_score is None
    assert p.github_summary is None
    assert p.github_repositories is None
    assert p.github_stars is None
    assert p.github_followers is None
    assert p.github_languages is None
    db.close()
    print("✓ GitHub columns are successfully verified to be NULL.")

    # -------------------------------------------------------------
    # Scenario 1: URL Added / Changed (Should trigger evaluation)
    # -------------------------------------------------------------
    print("\n[Scenario 1] Adding github_url (URL Changed)...")
    request_count = 0
    update_payload = {
        "full_name": "Candidate Three",
        "email": "candidate3@example.com",
        "github_url": "https://github.com/validuser"
    }
    
    # Save profile (runs synchronously due to our trigger mock)
    res = client.put(f"/candidate/profile/update/3", json=update_payload, headers=headers)
    assert res.status_code == 200, f"Failed to update profile: {res.text}"

    # Verify results in database
    db = TestingSessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    print(f"  Updated score: {p.github_score}")
    print(f"  Repositories count: {p.github_repositories}")
    print(f"  Stars count: {p.github_stars}")
    print(f"  Followers: {p.github_followers}")
    print(f"  Languages: {p.github_languages}")
    print(f"  Summary: {p.github_summary}")
    
    # Assertions on metrics
    assert p.github_score == 66, f"Expected github score 66, got {p.github_score}"
    assert p.github_repositories == 2, f"Expected repos = 2, got {p.github_repositories}"
    assert p.github_stars == 5, f"Expected stars = 5, got {p.github_stars}"
    assert p.github_followers == 5, f"Expected followers = 5, got {p.github_followers}"
    assert p.github_languages == ["JavaScript", "Python"]
    assert p.github_summary["inferred_skills"] == ["JavaScript", "Python", "React"]
    db.close()
    
    # Ensure requests.get was indeed called
    print(f"  API Calls triggered: {request_count} (expected 2)")
    assert request_count == 2, "Expected 2 API requests (profile & repos) to be triggered."
    print("✓ Scenario 1 passed!")

    # -------------------------------------------------------------
    # Scenario 2: URL Unchanged (Should NOT trigger evaluation)
    # -------------------------------------------------------------
    print("\n[Scenario 2] Updating simple profile edits with UNCHANGED github_url...")
    request_count = 0
    simple_edit_payload = {
        "full_name": "Candidate Three Edited",
        "email": "candidate3@example.com",
        "github_url": "https://github.com/validuser",
        "phone": "555-9999"
    }
    res = client.put(f"/candidate/profile/update/3", json=simple_edit_payload, headers=headers)
    assert res.status_code == 200
    
    print(f"  API Calls triggered: {request_count} (expected 0)")
    assert request_count == 0, "Evaluation was triggered even though github_url didn't change!"
    print("✓ Scenario 2 passed!")

    # -------------------------------------------------------------
    # Scenario 3: Empty URL (Should clear database fields)
    # -------------------------------------------------------------
    print("\n[Scenario 3] Setting github_url to Empty/None...")
    request_count = 0
    empty_url_payload = {
        "full_name": "Candidate Three",
        "email": "candidate3@example.com",
        "github_url": None
    }
    res = client.put(f"/candidate/profile/update/3", json=empty_url_payload, headers=headers)
    assert res.status_code == 200
    
    db = TestingSessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    print(f"  Database score after empty URL: {p.github_score}")
    print(f"  Database summary after empty URL: {p.github_summary}")
    assert p.github_score is None, "Score was not cleared on empty URL"
    assert p.github_summary is None, "Summary was not cleared on empty URL"
    assert p.github_repositories is None
    assert p.github_stars is None
    assert p.github_followers is None
    assert p.github_languages is None
    db.close()
    
    print(f"  API Calls triggered: {request_count} (expected 0)")
    assert request_count == 0, "API calls were triggered on empty URL!"
    print("✓ Scenario 3 passed!")

    # -------------------------------------------------------------
    # Scenario 4: Invalid URL (Should graceful clear and show error)
    # -------------------------------------------------------------
    print("\n[Scenario 4] Setting github_url to an Invalid format...")
    request_count = 0
    invalid_url_payload = {
        "full_name": "Candidate Three",
        "email": "candidate3@example.com",
        "github_url": "https://google.com/not-github"
    }
    res = client.put(f"/candidate/profile/update/3", json=invalid_url_payload, headers=headers)
    assert res.status_code == 200
    
    db = TestingSessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    print(f"  Database score after invalid URL: {p.github_score}")
    print(f"  Database summary after invalid URL: {p.github_summary}")
    assert p.github_score is None, "Score should be None for invalid URL"
    assert p.github_summary is not None
    assert p.github_summary["error"] == "Invalid GitHub URL format."
    assert p.github_repositories is None
    assert p.github_stars is None
    assert p.github_followers is None
    assert p.github_languages is None
    db.close()
    
    print(f"  API Calls triggered: {request_count} (expected 0)")
    assert request_count == 0, "API calls were triggered for an invalid URL format!"
    print("✓ Scenario 4 passed!")

    # -------------------------------------------------------------
    # Scenario 5: GitHub Rate Limit (403 Handling)
    # -------------------------------------------------------------
    print("\n[Scenario 5] Testing GitHub API Rate Limit (403 status)...")
    request_count = 0
    ratelimit_payload = {
        "full_name": "Candidate Three",
        "email": "candidate3@example.com",
        "github_url": "https://github.com/ratelimited"
    }
    res = client.put(f"/candidate/profile/update/3", json=ratelimit_payload, headers=headers)
    assert res.status_code == 200
    
    db = TestingSessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    print(f"  Database score during rate limit: {p.github_score}")
    print(f"  Database summary error: {p.github_summary['error']}")
    
    assert p.github_score == 0
    assert p.github_summary["error"] == "GitHub API rate limit reached. Please try again later."
    assert p.github_repositories == 0
    assert p.github_stars == 0
    assert p.github_followers == 0
    assert p.github_languages == []
    db.close()
    print("✓ Scenario 5 passed!")

    # -------------------------------------------------------------
    # Scenario 6: GitHub Unavailable (502 / Connection error/timeout)
    # -------------------------------------------------------------
    print("\n[Scenario 6] Testing GitHub Service Unavailable/Timeout...")
    request_count = 0
    
    # 6a. Service returns bad status (502)
    unavailable_payload = {
        "full_name": "Candidate Three",
        "email": "candidate3@example.com",
        "github_url": "https://github.com/unavailable"
    }
    res = client.put(f"/candidate/profile/update/3", json=unavailable_payload, headers=headers)
    db = TestingSessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    print(f"  502 Summary error: {p.github_summary['error']}")
    assert p.github_score == 0
    assert "GitHub API returned error status: 502" in p.github_summary["error"]
    db.close()

    # 6b. Service times out
    timeout_payload = {
        "full_name": "Candidate Three",
        "email": "candidate3@example.com",
        "github_url": "https://github.com/timeout"
    }
    res = client.put(f"/candidate/profile/update/3", json=timeout_payload, headers=headers)
    db = TestingSessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    print(f"  Timeout Summary error: {p.github_summary['error']}")
    assert p.github_score == 0
    assert p.github_summary["error"] == "GitHub service connection timed out."
    db.close()
    print("✓ Scenario 6 passed!")

    # -------------------------------------------------------------
    # Scenario 7: Background Refresh / On-demand Endpoint
    # -------------------------------------------------------------
    print("\n[Scenario 7] Testing Manual/On-demand Refresh Endpoint...")
    request_count = 0
    
    # Set valid github url directly in DB first
    db = TestingSessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    p.github_url = "https://github.com/validuser"
    p.github_score = None
    db.commit()
    db.close()
    
    # Trigger refresh
    res = client.post(f"/candidate/profile/3/refresh-github", headers=headers)
    print(f"  Refresh endpoint response status: {res.status_code}")
    assert res.status_code == 200, f"Refresh endpoint failed: {res.text}"
    
    data = res.json()
    print(f"  Returned Score in JSON: {data['github_score']}")
    print(f"  API Calls triggered during refresh: {request_count}")
    
    assert data["github_score"] == 66
    assert request_count == 2, "Expected 2 API requests to be triggered during refresh."
    print("✓ Scenario 7 passed!")

    # -------------------------------------------------------------
    # Scenario 8: Resume Parser Autofill Trigger
    # -------------------------------------------------------------
    print("\n[Scenario 8] Testing Resume Parser Autofill Trigger...")
    request_count = 0
    
    # Setup initial profile with NO github url
    empty_payload = {
        "full_name": "Candidate Three",
        "email": "candidate3@example.com",
        "github_url": None
    }
    client.put(f"/candidate/profile/update/3", json=empty_payload, headers=headers)
    
    mock_parsed_resume = {
        "personal": {
            "full_name": "Candidate Three Parsed",
            "email": "candidate3@example.com",
            "github_url": "https://github.com/validuser"
        },
        "skills": [],
        "education": [],
        "experience": [],
        "projects": []
    }
    
    db = TestingSessionLocal()
    autofill_candidate_tables(db, 3, mock_parsed_resume)
    db.close()
    
    db = TestingSessionLocal()
    p = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
    print(f"  Database score after resume parser autofill: {p.github_score}")
    assert p.github_score == 66
    db.close()
    print("✓ Scenario 8 passed!")

    print("\n" + "=" * 60)
    print("ALL GITHUB INTELLIGENCE ENGINE SCENARIOS VERIFIED SUCCESSFULLY!")
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
