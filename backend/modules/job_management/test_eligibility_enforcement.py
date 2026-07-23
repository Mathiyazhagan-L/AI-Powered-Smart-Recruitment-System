import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Set dummy database environment variables for configuration initialization
os.environ["DB_USER"] = "dummy"
os.environ["DB_PASSWORD"] = "dummy"

from main import app
from core.database import get_db
from core.base import Base

from modules.auth.model import User
from modules.job_management.model import Job
from modules.candidate.profile.model import CandidateProfile
from modules.candidate.resume.model import CandidateResume
from modules.assessment.models import AssessmentResult
from modules.coding_assessment.models import CodingResult
from modules.interview_assessment.models import InterviewResult

from sqlalchemy.pool import StaticPool

# In-memory SQLite for testing with StaticPool to share connection across threads
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
    
    # 1. Create a Candidate User (id=1)
    cand_user = User(
        id=1,
        email="candidate1@example.com",
        role="candidate",
        password_hash="dummy_password_hash",
        full_name="Candidate One"
    )
    db.add(cand_user)
    # 2. Create a Job (id=1)
    import datetime
    future_deadline = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    job = Job(
        id=1,
        title="AI Engineer",
        description="FastAPI, Machine Learning, Python",
        required_skills=["Python", "FastAPI"],
        preferred_skills=["Machine Learning"],
        experience="2 years",
        package="100,000 USD",
        location="Remote",
        criteria="None",
        openings=2,
        deadline=future_deadline,
        status="published",
        selection_rounds=[],
        salary_rules={},
        eligibility_rules={},
        application_settings={}
    )
    db.add(job)
    
    # 3. Create CandidateProfile with incomplete profile (profile_completion = 50)
    profile = CandidateProfile(
        id=1,
        user_id=1,
        full_name="Candidate One",
        email="candidate1@example.com",
        phone="1234567890",
        location="Chennai",
        profile_completion=50
    )
    db.add(profile)
    
    db.commit()
    db.close()

def clear_profile_relations(db):
    # Clear resume, aptitude, coding, interview results
    db.query(CandidateResume).filter(CandidateResume.user_id == 1).delete()
    db.query(AssessmentResult).filter(AssessmentResult.candidate_id == 1).delete()
    db.query(CodingResult).filter(CodingResult.candidate_id == 1).delete()
    db.query(InterviewResult).filter(InterviewResult.candidate_id == 1).delete()
    db.commit()

def test_scenarios():
    client = TestClient(app)
    db = TestingSessionLocal()
    
    print("\n=============================================")
    print("RUNNING RECRUITMENT WORKFLOW ELIGIBILITY TESTS")
    print("=============================================")

    # ---------------------------------------------
    # Scenario 1: Profile incomplete (completion < 100)
    # ---------------------------------------------
    print("\nScenario 1: Profile incomplete (completion = 50)")
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == 1).first()
    profile.profile_completion = 50
    db.commit()
    clear_profile_relations(db)
    
    res = client.post("/jobs/1/apply?candidate_id=1")
    print(f"Result Status Code: {res.status_code}")
    print(f"Result JSON: {res.json()}")
    assert res.status_code == 403
    assert res.json()["detail"] == "Complete profile before applying."
    print("✓ Scenario 1 passed successfully!")

    # ---------------------------------------------
    # Scenario 2: Resume missing (profile complete but no resume)
    # ---------------------------------------------
    print("\nScenario 2: Resume missing (profile completion = 100)")
    profile.profile_completion = 100
    db.commit()
    
    # Verify GET /candidate/resume/status/1
    status_res = client.get("/candidate/resume/status/1")
    print(f"Resume Status JSON (Scenario 2): {status_res.json()}")
    assert status_res.status_code == 200
    assert status_res.json()["uploaded"] is False

    res = client.post("/jobs/1/apply?candidate_id=1")
    print(f"Result Status Code: {res.status_code}")
    print(f"Result JSON: {res.json()}")
    assert res.status_code == 403
    assert res.json()["detail"] == "Upload resume before applying."
    print("✓ Scenario 2 passed successfully!")

    # ---------------------------------------------
    # Scenario 3: Only aptitude completed (resume present, aptitude PASSED)
    # ---------------------------------------------
    print("\nScenario 3: Only aptitude completed")
    # Add resume
    resume = CandidateResume(
        id=1,
        user_id=1,
        resume_name="resume.pdf",
        resume_path="/path/to/resume.pdf",
        file_type="pdf",
        file_size=1024,
        parsed_status=True
    )
    db.add(resume)
    db.commit()

    # Verify GET /candidate/resume/status/1
    status_res = client.get("/candidate/resume/status/1")
    print(f"Resume Status JSON (Scenario 3): {status_res.json()}")
    assert status_res.status_code == 200
    assert status_res.json()["uploaded"] is True
    assert status_res.json()["file_name"] == "resume.pdf"
    
    # Add aptitude result
    apt_res = AssessmentResult(
        id=1,
        candidate_id=1,
        attempt_id=1,
        aptitude_score=80.0,
        quantitative_score=80.0,
        logical_score=80.0,
        verbal_score=80.0,
        analytical_reasoning_score=80.0,
        computer_fundamentals_score=80.0,
        total_correct=20,
        total_wrong=5,
        status="PASSED"
    )
    db.add(apt_res)
    db.commit()
    
    res = client.post("/jobs/1/apply?candidate_id=1")
    print(f"Result Status Code: {res.status_code}")
    print(f"Result JSON: {res.json()}")
    assert res.status_code == 403
    assert res.json()["detail"] == "Complete coding assessment before applying."
    print("✓ Scenario 3 passed successfully!")

    # ---------------------------------------------
    # Scenario 4: Aptitude + Coding completed (no interview)
    # ---------------------------------------------
    print("\nScenario 4: Aptitude + Coding completed")
    # Add coding result
    coding_res = CodingResult(
        id=1,
        candidate_id=1,
        attempt_id=1,
        total_score=85.0,
        easy_score=90.0,
        medium_score=80.0,
        hard_score=85.0,
        questions_solved=4,
        questions_attempted=5,
        status="PASS"
    )
    db.add(coding_res)
    db.commit()
    
    res = client.post("/jobs/1/apply?candidate_id=1")
    print(f"Result Status Code: {res.status_code}")
    print(f"Result JSON: {res.json()}")
    assert res.status_code == 403
    assert res.json()["detail"] == "Complete interview assessment before applying."
    print("✓ Scenario 4 passed successfully!")

    # ---------------------------------------------
    # Scenario 5: All assessments completed (Aptitude + Coding + Interview)
    # ---------------------------------------------
    print("\nScenario 5: All assessments completed")
    # Add interview result
    interview_res = InterviewResult(
        id=1,
        candidate_id=1,
        session_id=1,
        communication_score=20.0,
        technical_score=35.0,
        confidence_score=18.0,
        professionalism_score=13.0,
        total_score=86.0,
        grade="A",
        hiring_recommendation="Recommended"
    )
    db.add(interview_res)
    db.commit()
    
    res = client.post("/jobs/1/apply?candidate_id=1")
    print(f"Result Status Code: {res.status_code}")
    print(f"Result JSON: {res.json()}")
    assert res.status_code == 201
    assert res.json()["status"] == "Applied"
    print("✓ Scenario 5 passed successfully!")

    # ---------------------------------------------
    # Scenario 6: Direct API call bypass attempt (unauthorized or ineligible candidate)
    # ---------------------------------------------
    print("\nScenario 6: Direct API call bypass attempt (Candidate 2, profile incomplete)")
    cand2_user = User(
        id=2,
        email="candidate2@example.com",
        role="candidate",
        password_hash="dummy_password_hash",
        full_name="Candidate Two"
    )
    db.add(cand2_user)
    db.commit()
    
    res = client.post("/jobs/1/apply?candidate_id=2")
    print(f"Result Status Code: {res.status_code}")
    print(f"Result JSON: {res.json()}")
    assert res.status_code == 404 or res.status_code == 403
    print("✓ Scenario 6 passed successfully!")

    print("\n=============================================")
    print("ALL ELIGIBILITY ENFORCEMENT SCENARIOS PASSED!")
    print("=============================================")
    db.close()

if __name__ == "__main__":
    setup_db()
    try:
        test_scenarios()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
