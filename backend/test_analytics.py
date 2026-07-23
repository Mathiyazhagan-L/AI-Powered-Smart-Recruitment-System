import json
from fastapi.testclient import TestClient
from sqlalchemy import text
from core.database import SessionLocal
from main import app

# Auth imports
from modules.auth.model import User
from modules.auth.logic import create_access_token
from modules.company_profile.model import CompanyProfile

# Test data IDs
candidate_id = 11
job_id = 1

def ensure_users_exist():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("SETTING UP TEST USERS")
        print("=" * 60)
        
        # 1. Verify candidate user (id = 11) exists
        cand_user = db.query(User).filter(User.id == candidate_id).first()
        if not cand_user:
            print(f"Creating missing candidate user with ID {candidate_id}")
            cand_user = User(
                id=candidate_id,
                email="test@example.com",
                role="candidate",
                is_active=True
            )
            db.add(cand_user)
            db.commit()
        else:
            print(f"Candidate user with ID {candidate_id} already exists.")

        # 2. Verify company user exists
        comp_user = db.query(User).filter(User.role == "company").first()
        if not comp_user:
            print("Creating test company user...")
            comp_user = User(
                email="company@example.com",
                role="company",
                full_name="AI Corp Admin",
                is_active=True
            )
            db.add(comp_user)
            db.commit()
            db.refresh(comp_user)
            
            # Create company profile
            comp_profile = CompanyProfile(
                user_id=comp_user.id,
                company_name="AI Corp",
                company_email="company@example.com",
                website="https://aicorp.example.com",
                verification_status="Verified"
            )
            db.add(comp_profile)
            db.commit()
            print(f"Created company user with ID {comp_user.id} and profile.")
        else:
            print(f"Company user already exists with ID {comp_user.id}.")

        # Generate JWT tokens
        cand_token = create_access_token({"sub": str(candidate_id), "role": "candidate"})
        comp_token = create_access_token({"sub": str(comp_user.id), "role": "company"})

        return cand_token, comp_token
        
    finally:
        db.close()


def run_security_tests(cand_token, comp_token):
    print("\n" + "=" * 60)
    print("PHASE 13 — SECURITY ACCESS TESTING")
    print("=" * 60)
    client = TestClient(app)
    
    # 1. Candidate access check (Expect 403)
    headers_cand = {"Authorization": f"Bearer {cand_token}"}
    response_cand = client.get("/analytics/overview", headers=headers_cand)
    print(f"Candidate Access test: GET /analytics/overview")
    print(f"  - Status Code: {response_cand.status_code} (Expected: 403)")
    print(f"  - Response: {response_cand.json()}")
    assert response_cand.status_code == 403, "Security check failed: Candidate was NOT blocked!"
    
    # 2. Company access check (Expect 200)
    headers_comp = {"Authorization": f"Bearer {comp_token}"}
    response_comp = client.get("/analytics/overview", headers=headers_comp)
    print(f"Company Access test: GET /analytics/overview")
    print(f"  - Status Code: {response_comp.status_code} (Expected: 200)")
    print(f"  - Response: {list(response_comp.json().keys())} (truncated keys)")
    assert response_comp.status_code == 200, "Security check failed: Company access was denied!"
    
    print("\nSecurity tests passed successfully!")


def run_functional_tests(comp_token):
    print("\n" + "=" * 60)
    print("PHASE 14 — FUNCTIONAL TESTING (COMPANY AUTHENTICATED)")
    print("=" * 60)
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {comp_token}"}

    endpoints = [
        "/analytics/overview",
        "/analytics/ats-distribution",
        "/analytics/top-skills",
        f"/analytics/skill-gap/{job_id}",
        f"/analytics/rankings/{job_id}",
        "/analytics/prediction-distribution",
        "/analytics/hiring-funnel"
    ]

    for ep in endpoints:
        print(f"GET {ep}:")
        response = client.get(ep, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        print("-" * 60)


def run_sql_proofs():
    print("\n" + "=" * 60)
    print("PHASE 15 — SQL PROOFS")
    print("=" * 60)
    db = SessionLocal()
    try:
        # SELECT COUNT(*) FROM jobs;
        jobs_count = db.execute(text("SELECT COUNT(*) FROM jobs")).scalar()
        print(f"SELECT COUNT(*) FROM jobs; -> {jobs_count}")

        # SELECT COUNT(*) FROM candidate_profiles;
        profiles_count = db.execute(text("SELECT COUNT(*) FROM candidate_profiles")).scalar()
        print(f"SELECT COUNT(*) FROM candidate_profiles; -> {profiles_count}")

        # SELECT COUNT(*) FROM candidate_skills;
        skills_count = db.execute(text("SELECT COUNT(*) FROM candidate_skills")).scalar()
        print(f"SELECT COUNT(*) FROM candidate_skills; -> {skills_count}")

        # SELECT COUNT(*) FROM candidate_rankings;
        rankings_count = db.execute(text("SELECT COUNT(*) FROM candidate_rankings")).scalar()
        print(f"SELECT COUNT(*) FROM candidate_rankings; -> {rankings_count}")

        # SELECT * FROM jobs WHERE id=1;
        print("\nSELECT * FROM jobs WHERE id=1;")
        res_job = db.execute(text("SELECT id, title, required_skills, experience FROM jobs WHERE id = 1")).all()
        for r in res_job:
            print(dict(r._mapping))
            
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    cand_tok, comp_tok = ensure_users_exist()
    run_security_tests(cand_tok, comp_tok)
    run_functional_tests(comp_tok)
    run_sql_proofs()
