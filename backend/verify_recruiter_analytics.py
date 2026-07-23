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
from modules.job_management.model import Job, Application
from modules.candidate.profile.model import CandidateProfile
from modules.candidate.skills.model import CandidateSkill

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
    
    # Create Recruiter User (id=1)
    rec_user = User(
        id=1,
        email="recruiter1@example.com",
        role="company",
        password_hash="dummy",
        full_name="Recruiter One"
    )
    db.add(rec_user)
    
    # Create Recruiter Profile
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
    
    # Create Job 1 (id=1) and Job 2 (id=2)
    import datetime
    job1 = Job(
        id=1,
        title="Software Engineer",
        description="Develop software.",
        required_skills=["Python", "SQL"],
        preferred_skills=[],
        experience="1 year",
        package="$100k",
        location="Remote",
        openings=1,
        deadline=datetime.datetime.utcnow() + datetime.timedelta(days=10),
        status="published",
        selection_rounds=["Aptitude"],
        salary_rules={},
        eligibility_rules={},
        application_settings={}
    )
    job2 = Job(
        id=2,
        title="Data Scientist",
        description="Analyze data.",
        required_skills=["Python", "Machine Learning"],
        preferred_skills=[],
        experience="2 years",
        package="$120k",
        location="Remote",
        openings=1,
        deadline=datetime.datetime.utcnow() + datetime.timedelta(days=10),
        status="published",
        selection_rounds=["Aptitude"],
        salary_rules={},
        eligibility_rules={},
        application_settings={}
    )
    db.add(job1)
    db.add(job2)
    
    db.commit()
    db.close()

def clear_data_for_scenarios():
    db = TestingSessionLocal()
    db.query(Application).delete()
    db.query(CandidateProfile).delete()
    db.query(CandidateSkill).delete()
    db.query(User).filter(User.id != 1).delete()
    db.commit()
    db.close()

def verify_validation_rules(data_overview, data_ats, data_prediction, data_funnel, total_candidates):
    print("  -> Validating rules:")
    
    # Rule 1: ATS bucket totals equal total candidate count
    ats_total = sum(data_ats.values())
    print(f"     Rule 1: ATS Total = {ats_total} (Expected: {total_candidates})")
    assert ats_total == total_candidates, f"ATS total {ats_total} does not match total candidates {total_candidates}!"
    
    # Rule 2: Suitability category totals equal total candidate count
    suitability_total = (data_prediction["Selected"] + data_prediction["High_Potential"] + 
                         data_prediction["Medium_Potential"] + data_prediction["Rejected"])
    print(f"     Rule 2: Suitability Total = {suitability_total} (Expected: {total_candidates})")
    assert suitability_total == total_candidates, f"Suitability total {suitability_total} does not match total candidates {total_candidates}!"
    
    # Overview counts validation
    overview_suitability_total = (data_overview["selected_candidates"] + data_overview["high_potential_candidates"] + 
                                  data_overview["medium_potential_candidates"] + data_overview["rejected_candidates"])
    assert overview_suitability_total == total_candidates, f"Overview suitability total {overview_suitability_total} does not match total candidates {total_candidates}!"
    assert data_overview["total_candidates"] == total_candidates, f"Overview total candidates {data_overview['total_candidates']} does not match {total_candidates}!"

    # Rule 3: Funnel stages satisfy: Selected <= Interviewed <= Shortlisted <= Screened <= Applied
    sel = data_funnel["Selected"]
    intv = data_funnel["Interviewed"]
    shor = data_funnel["Shortlisted"]
    scr = data_funnel["Screened"]
    app = data_funnel["Applied"]
    print(f"     Rule 3: Funnel ordering check: {sel} <= {intv} <= {shor} <= {scr} <= {app}")
    assert sel <= intv <= shor <= scr <= app, f"Funnel ordering violation! Selected: {sel}, Interviewed: {intv}, Shortlisted: {shor}, Screened: {scr}, Applied: {app}"
    
    # Rule 4: No negative values
    print("     Rule 4: Checking for negative values...")
    for val in list(data_ats.values()) + list(data_prediction.values()) + list(data_funnel.values()):
        assert val >= 0, f"Value {val} is negative!"
    for key in ["total_jobs", "total_candidates", "total_applications", "selected_candidates", "high_potential_candidates", "medium_potential_candidates", "rejected_candidates"]:
        assert data_overview[key] >= 0, f"Overview key {key} value {data_overview[key]} is negative!"
        
    print("     ✓ All validation rules passed successfully!")

def run_tests():
    client = TestClient(app)
    token = create_access_token({"sub": "1", "role": "company"})
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n" + "=" * 60)
    print("RUNNING RECRUITER ANALYTICS VERIFICATION SCENARIOS")
    print("=" * 60)
    
    # -------------------------------------------------------------
    # Scenario 1: No Candidates
    # -------------------------------------------------------------
    print("\nScenario 1: No candidates")
    clear_data_for_scenarios()
    
    overview = client.get("/analytics/overview", headers=headers).json()
    ats_dist = client.get("/analytics/ats-distribution", headers=headers).json()
    pred_dist = client.get("/analytics/prediction-distribution", headers=headers).json()
    funnel = client.get("/analytics/hiring-funnel", headers=headers).json()
    
    print(f"  Overview: {overview}")
    print(f"  ATS Distribution: {ats_dist}")
    print(f"  ML Suitability: {pred_dist}")
    print(f"  Hiring Funnel: {funnel}")
    
    assert overview["total_candidates"] == 0
    assert overview["total_applications"] == 0
    assert sum(ats_dist.values()) == 0
    assert sum([pred_dist["Selected"], pred_dist["High_Potential"], pred_dist["Medium_Potential"], pred_dist["Rejected"]]) == 0
    assert sum(funnel.values()) == 0
    
    verify_validation_rules(overview, ats_dist, pred_dist, funnel, 0)
    print("✓ Scenario 1 passed!")
    
    # -------------------------------------------------------------
    # Scenario 2: Single Candidate
    # -------------------------------------------------------------
    print("\nScenario 2: Single Candidate (Without and With application)")
    clear_data_for_scenarios()
    db = TestingSessionLocal()
    
    # Add Candidate 2 (user_id = 2)
    c2 = User(id=2, email="candidate2@example.com", role="candidate", password_hash="dummy")
    db.add(c2)
    cp2 = CandidateProfile(id=1, user_id=2, full_name="Candidate Two", email="candidate2@example.com", profile_completion=100)
    db.add(cp2)
    db.commit()
    db.close()
    
    # Step A: Without application (defaults to 0 score, Rejected suitability, and 0 in funnel)
    overview = client.get("/analytics/overview", headers=headers).json()
    ats_dist = client.get("/analytics/ats-distribution", headers=headers).json()
    pred_dist = client.get("/analytics/prediction-distribution", headers=headers).json()
    funnel = client.get("/analytics/hiring-funnel", headers=headers).json()
    
    print(f"  [Without App] Overview: {overview}")
    print(f"  [Without App] ATS Distribution: {ats_dist}")
    print(f"  [Without App] ML Suitability: {pred_dist}")
    print(f"  [Without App] Hiring Funnel: {funnel}")
    
    assert overview["total_candidates"] == 1
    assert overview["total_applications"] == 0
    assert ats_dist["0-20"] == 1
    assert pred_dist["Rejected"] == 1
    assert funnel["Applied"] == 0
    
    verify_validation_rules(overview, ats_dist, pred_dist, funnel, 1)
    
    # Step B: With Application (ATS = 85, Prediction = Selected, Status = Applied)
    db = TestingSessionLocal()
    app1 = Application(
        job_id=1,
        candidate_id=2,
        ats_score=85,
        suitability_prediction="Selected",
        status="Applied"
    )
    db.add(app1)
    db.commit()
    db.close()
    
    overview = client.get("/analytics/overview", headers=headers).json()
    ats_dist = client.get("/analytics/ats-distribution", headers=headers).json()
    pred_dist = client.get("/analytics/prediction-distribution", headers=headers).json()
    funnel = client.get("/analytics/hiring-funnel", headers=headers).json()
    
    print(f"  [With App] Overview: {overview}")
    print(f"  [With App] ATS Distribution: {ats_dist}")
    print(f"  [With App] ML Suitability: {pred_dist}")
    print(f"  [With App] Hiring Funnel: {funnel}")
    
    assert overview["total_candidates"] == 1
    assert overview["total_applications"] == 1
    assert ats_dist["81-100"] == 1
    assert pred_dist["Selected"] == 1
    assert funnel["Applied"] == 1
    assert funnel["Selected"] == 0  # not selected yet in application status
    
    verify_validation_rules(overview, ats_dist, pred_dist, funnel, 1)
    print("✓ Scenario 2 passed!")
    
    # -------------------------------------------------------------
    # Scenario 3: Multiple Candidates
    # -------------------------------------------------------------
    print("\nScenario 3: Multiple Candidates")
    clear_data_for_scenarios()
    db = TestingSessionLocal()
    
    # Add 3 candidates
    for uid, name, email in [(2, "Cand Two", "c2@example.com"), (3, "Cand Three", "c3@example.com"), (4, "Cand Four", "c4@example.com")]:
        db.add(User(id=uid, email=email, role="candidate", password_hash="dummy"))
        db.add(CandidateProfile(id=uid-1, user_id=uid, full_name=name, email=email, profile_completion=100))
    
    # Add application for Cand Two: ATS = 90, Pred = Selected, Status = Selected
    db.add(Application(job_id=1, candidate_id=2, ats_score=90, suitability_prediction="Selected", status="Selected"))
    # Add application for Cand Three: ATS = 65, Pred = High Potential, Status = Shortlisted
    db.add(Application(job_id=1, candidate_id=3, ats_score=65, suitability_prediction="High Potential", status="Shortlisted"))
    # Cand Four has no applications (defaults to 0, Rejected, 0 funnel)
    
    db.commit()
    db.close()
    
    overview = client.get("/analytics/overview", headers=headers).json()
    ats_dist = client.get("/analytics/ats-distribution", headers=headers).json()
    pred_dist = client.get("/analytics/prediction-distribution", headers=headers).json()
    funnel = client.get("/analytics/hiring-funnel", headers=headers).json()
    
    print(f"  Overview: {overview}")
    print(f"  ATS Distribution: {ats_dist}")
    print(f"  ML Suitability: {pred_dist}")
    print(f"  Hiring Funnel: {funnel}")
    
    assert overview["total_candidates"] == 3
    assert overview["total_applications"] == 2
    assert ats_dist["81-100"] == 1  # Cand Two (90)
    assert ats_dist["61-80"] == 1   # Cand Three (65)
    assert ats_dist["0-20"] == 1    # Cand Four (0)
    
    assert pred_dist["Selected"] == 1
    assert pred_dist["High_Potential"] == 1
    assert pred_dist["Rejected"] == 1
    
    verify_validation_rules(overview, ats_dist, pred_dist, funnel, 3)
    print("✓ Scenario 3 passed!")
    
    # -------------------------------------------------------------
    # Scenario 4: Multiple Jobs / Multiple Applications (Independent Logic)
    # -------------------------------------------------------------
    print("\nScenario 4: Multiple Jobs (Multiple Applications per candidate)")
    clear_data_for_scenarios()
    db = TestingSessionLocal()
    
    # Candidate Two (user_id = 2)
    db.add(User(id=2, email="c2@example.com", role="candidate", password_hash="dummy"))
    db.add(CandidateProfile(id=1, user_id=2, full_name="Cand Two", email="c2@example.com", profile_completion=100))
    
    # Application 1 on Job 1: ATS = 95, Pred = Rejected, Status = Applied
    db.add(Application(job_id=1, candidate_id=2, ats_score=95, suitability_prediction="Rejected", status="Applied"))
    # Application 2 on Job 2: ATS = 70, Pred = Selected, Status = Interview
    db.add(Application(job_id=2, candidate_id=2, ats_score=70, suitability_prediction="Selected", status="Interview"))
    
    db.commit()
    db.close()
    
    overview = client.get("/analytics/overview", headers=headers).json()
    ats_dist = client.get("/analytics/ats-distribution", headers=headers).json()
    pred_dist = client.get("/analytics/prediction-distribution", headers=headers).json()
    funnel = client.get("/analytics/hiring-funnel", headers=headers).json()
    
    print(f"  Overview: {overview}")
    print(f"  ATS Distribution: {ats_dist}")
    print(f"  ML Suitability: {pred_dist}")
    print(f"  Hiring Funnel: {funnel}")
    
    # Expect:
    # - ATS Score: 95 (highest) -> 81-100 bucket
    # - ML Prediction: Selected (highest) -> Selected category
    # - Hiring Funnel: Interview (max level 4) -> Applied, Screened, Shortlisted, Interviewed
    assert ats_dist["81-100"] == 1
    assert ats_dist["61-80"] == 0
    assert pred_dist["Selected"] == 1
    assert pred_dist["Rejected"] == 0
    
    assert funnel["Applied"] == 1
    assert funnel["Screened"] == 1
    assert funnel["Shortlisted"] == 1
    assert funnel["Interviewed"] == 1
    assert funnel["Selected"] == 0  # not selected status
    
    verify_validation_rules(overview, ats_dist, pred_dist, funnel, 1)
    print("✓ Scenario 4 passed!")
    
    # -------------------------------------------------------------
    # Scenario 5: Hiring Funnel Consistency (Stress Test)
    # -------------------------------------------------------------
    print("\nScenario 5: Hiring Funnel Consistency Stress Test")
    clear_data_for_scenarios()
    db = TestingSessionLocal()
    
    # 5 Candidates
    for uid in range(2, 7):
        email = f"c{uid}@example.com"
        db.add(User(id=uid, email=email, role="candidate", password_hash="dummy"))
        db.add(CandidateProfile(id=uid-1, user_id=uid, full_name=f"Cand {uid}", email=email, profile_completion=100))
        
    # Cand 2: Applied only
    db.add(Application(job_id=1, candidate_id=2, ats_score=45, suitability_prediction="Medium Potential", status="Applied"))
    
    # Cand 3: Shortlisted
    db.add(Application(job_id=1, candidate_id=3, ats_score=68, suitability_prediction="High Potential", status="Shortlisted"))
    
    # Cand 4: Interview
    db.add(Application(job_id=1, candidate_id=4, ats_score=75, suitability_prediction="High Potential", status="Interview"))
    
    # Cand 5: Selected on job 1, Screening on job 2
    db.add(Application(job_id=1, candidate_id=5, ats_score=88, suitability_prediction="Selected", status="Selected"))
    db.add(Application(job_id=2, candidate_id=5, ats_score=50, suitability_prediction="Medium Potential", status="Screening"))
    
    # Cand 6: Rejected
    db.add(Application(job_id=1, candidate_id=6, ats_score=35, suitability_prediction="Rejected", status="Rejected"))
    
    db.commit()
    db.close()
    
    overview = client.get("/analytics/overview", headers=headers).json()
    ats_dist = client.get("/analytics/ats-distribution", headers=headers).json()
    pred_dist = client.get("/analytics/prediction-distribution", headers=headers).json()
    funnel = client.get("/analytics/hiring-funnel", headers=headers).json()
    
    print(f"  Overview: {overview}")
    print(f"  ATS Distribution: {ats_dist}")
    print(f"  ML Suitability: {pred_dist}")
    print(f"  Hiring Funnel: {funnel}")
    
    # Total candidates = 5.
    # Total applications = 6.
    # Funnel counts checking:
    # Cand 2: max status = Applied -> level 1
    # Cand 3: max status = Shortlisted -> level 3
    # Cand 4: max status = Interview -> level 4
    # Cand 5: max status = Selected -> level 5
    # Cand 6: max status = Rejected -> level 1
    # Progression:
    # Level >= 1: Cand 2, 3, 4, 5, 6 -> Applied = 5
    # Level >= 2: Cand 3, 4, 5 -> Screened = 3 (since Shortlisted, Interview, Selected all imply Screened)
    # Level >= 3: Cand 3, 4, 5 -> Shortlisted = 3
    # Level >= 4: Cand 4, 5 -> Interviewed = 2
    # Level >= 5: Cand 5 -> Selected = 1
    assert funnel["Applied"] == 5
    assert funnel["Screened"] == 3
    assert funnel["Shortlisted"] == 3
    assert funnel["Interviewed"] == 2
    assert funnel["Selected"] == 1
    
    verify_validation_rules(overview, ats_dist, pred_dist, funnel, 5)
    print("✓ Scenario 5 passed!")
    
    print("\n" + "=" * 60)
    print("ALL RECRUITER ANALYTICS VERIFICATION SCENARIOS PASSED SUCCESSFULLY!")
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
