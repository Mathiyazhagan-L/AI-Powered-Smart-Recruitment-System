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
from modules.company_profile.model import CompanyProfile
from modules.job_management.model import Job
from modules.candidate.profile.model import CandidateProfile
from modules.job_management.model import Application

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
    
    # 1. Create a Recruiter User (id=1)
    rec_user = User(
        id=1,
        email="recruiter1@example.com",
        role="company",
        password_hash="dummy",
        full_name="Recruiter One"
    )
    db.add(rec_user)
    
    db.commit()
    db.close()

def test_scenarios():
    setup_db()
    client = TestClient(app)
    db = TestingSessionLocal()
    
    print("\n=============================================")
    print("RUNNING RECRUITER ENFORCEMENT SCENARIOS")
    print("=============================================")

    # Generate token
    token = create_access_token({"sub": "1", "role": "company"})
    headers = {"Authorization": f"Bearer {token}"}

    # ---------------------------------------------
    # Scenario 1: Incomplete profile
    # ---------------------------------------------
    print("\nScenario 1: Incomplete profile")
    res = client.get("/company/status/1", headers=headers)
    print(f"Status: {res.status_code}, JSON: {res.json()}")
    assert res.json()["complete"] is False
    print("✓ Scenario 1 passed!")

    # ---------------------------------------------
    # Scenario 2: API bypass attempt (post job with incomplete profile)
    # ---------------------------------------------
    print("\nScenario 2: API bypass attempt")
    import datetime
    job_payload = {
        "title": "Software Engineer",
        "description": "Develop software.",
        "required_skills": ["Python"],
        "preferred_skills": [],
        "experience": "1 year",
        "package": "$100k",
        "location": "Remote",
        "openings": 1,
        "deadline": (datetime.datetime.utcnow() + datetime.timedelta(days=10)).isoformat(),
        "status": "draft",
        "selection_rounds": ["Aptitude"],
        "salary_rules": {},
        "eligibility_rules": {},
        "application_settings": {}
    }
    res = client.post("/jobs/", json=job_payload, headers=headers)
    print(f"Status: {res.status_code}, JSON: {res.json()}")
    assert res.status_code == 403
    assert "Complete Company Profile" in res.json()["detail"]
    print("✓ Scenario 2 passed!")

    # ---------------------------------------------
    # Scenario 3: Complete profile
    # ---------------------------------------------
    print("\nScenario 3: Complete profile")
    # Add profile
    profile = CompanyProfile(
        id=1,
        user_id=1,
        company_name="Tech Corp",
        company_email="contact@techcorp.com",
        website="https://techcorp.com",
        industry="Tech",
        location="NY",
        description="A tech company."
    )
    db.add(profile)
    db.commit()

    res = client.get("/company/status/1", headers=headers)
    print(f"Status: {res.status_code}, JSON: {res.json()}")
    assert res.json()["complete"] is True
    
    # Now try to post job
    res = client.post("/jobs/", json=job_payload, headers=headers)
    print(f"Job Post Status: {res.status_code}, JSON: {res.json()}")
    assert res.status_code == 201
    print("✓ Scenario 3 passed!")

    # ---------------------------------------------
    # Scenario 4: Dashboard percentage validation
    # ---------------------------------------------
    print("\nScenario 4: Dashboard percentage validation metrics")
    # We check if jobs endpoint returns jobs (which we just posted)
    res_jobs = client.get("/jobs/", headers=headers)
    jobs_count = len(res_jobs.json())
    
    # Add a candidate to test "Candidate Reviewed" condition (length of /candidate/profile/)
    cand_user = User(
        id=2,
        email="cand@example.com",
        role="candidate",
        password_hash="dummy"
    )
    db.add(cand_user)
    cand_profile = CandidateProfile(
        id=1,
        user_id=2,
        full_name="Cand",
        email="cand@example.com",
        profile_completion=100
    )
    db.add(cand_profile)
    
    # Add application
    app_record = Application(
        job_id=1,
        candidate_id=2,
        status="Applied"
    )
    db.add(app_record)
    db.commit()
    
    res_cands = client.get("/candidate/profile/", headers=headers)
    cands_count = len(res_cands.json())
    
    res_stats = client.get("/analytics/overview", headers=headers)
    stats_data = res_stats.json()
    print(f"Stats Data: {stats_data}")
    apps_count = stats_data.get("total_applications", 0)
    
    # Profile Complete (1) + Job Posted (1) + Cand Reviewed (1) + Apps Received (1) = 4 steps -> 100%
    steps_completed = 1  # Profile is complete
    if jobs_count > 0: steps_completed += 1
    if cands_count > 0: steps_completed += 1
    if apps_count > 0: steps_completed += 1
    
    percentage = (steps_completed / 4) * 100
    print(f"Dashboard Percentage Calculated: {percentage}%")
    assert percentage == 100.0
    print("✓ Scenario 4 passed!")

    print("\n=============================================")
    print("ALL RECRUITER ENFORCEMENT SCENARIOS PASSED!")
    print("=============================================")
    db.close()

if __name__ == "__main__":
    setup_db()
    test_scenarios()
