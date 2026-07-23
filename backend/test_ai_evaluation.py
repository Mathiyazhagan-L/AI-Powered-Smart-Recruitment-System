import json
from fastapi.testclient import TestClient
from sqlalchemy import text
from core.database import SessionLocal
from main import app

# Services
from modules.ai_evaluation.services.matching_service import calculate_skill_match
from modules.ai_evaluation.services.scoring_service import calculate_ats_score
from modules.ai_evaluation.services.ranking_service import rank_candidates
from modules.ai_evaluation.services.recommendation_service import generate_recommendations

candidate_id = 11
job_id = 1

def run_python_services():
    print("=" * 60)
    # 1. Verify candidate profile and job
    with SessionLocal() as db:
        candidate_exists = db.execute(
            text("SELECT COUNT(*) FROM candidate_profiles WHERE user_id = :cid"),
            {"cid": candidate_id}
        ).scalar() > 0
        
        job_exists = db.execute(
            text("SELECT COUNT(*) FROM jobs WHERE id = :jid"),
            {"jid": job_id}
        ).scalar() > 0
        
        print(f"Candidate {candidate_id} exists in candidate_profiles: {candidate_exists}")
        print(f"Job {job_id} exists in jobs: {job_exists}")
        
    print("=" * 60)
    print("RUNNING PYTHON SERVICES DIRECTLY")
    print("=" * 60)
    
    # 2. Skill matching
    print("1. Skill Matching Engine Output:")
    match_res = calculate_skill_match(candidate_id=candidate_id, job_id=job_id)
    print(json.dumps(match_res, indent=2))
    print("-" * 60)
    
    # 3. ATS scoring
    print("2. ATS Score Engine Output:")
    score_res = calculate_ats_score(candidate_id=candidate_id, job_id=job_id)
    print(json.dumps(score_res, indent=2))
    print("-" * 60)
    
    # 4. Candidate ranking
    print("3. Candidate Ranking Engine Output:")
    ranking_res = rank_candidates(job_id=job_id)
    print(json.dumps(ranking_res, indent=2))
    print("-" * 60)
    
    # 5. Recommendation engine
    print("4. Recommendation Engine Output:")
    recommend_res = generate_recommendations(candidate_id=candidate_id, job_id=job_id)
    print(json.dumps(recommend_res, indent=2))
    print("=" * 60)


def run_api_endpoints():
    print("\n" + "=" * 60)
    print("RUNNING API ENDPOINTS VIA TESTCLIENT")
    print("=" * 60)
    client = TestClient(app)
    
    # 1. Skill matching
    print("POST /matching/job/{job_id}/candidate/{candidate_id}:")
    response = client.post(f"/matching/job/{job_id}/candidate/{candidate_id}")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("-" * 60)
    
    # 2. ATS scoring
    print("POST /ats-score/job/{job_id}/candidate/{candidate_id}:")
    response = client.post(f"/ats-score/job/{job_id}/candidate/{candidate_id}")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("-" * 60)
    
    # 3. Candidate ranking
    print("GET /ranking/job/{job_id}:")
    response = client.get(f"/ranking/job/{job_id}")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("-" * 60)
    
    # 4. Recommendation
    print("GET /recommendation/job/{job_id}/candidate/{candidate_id}:")
    response = client.get(f"/recommendation/job/{job_id}/candidate/{candidate_id}")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("=" * 60)


def run_sql_proof():
    print("\n" + "=" * 60)
    print("SQL PROOFS")
    print("=" * 60)
    with SessionLocal() as db:
        # 1. candidate_profiles where user_id=11
        print("SELECT * FROM candidate_profiles WHERE user_id=11;")
        res = db.execute(text("SELECT id, user_id, full_name, email, headline FROM candidate_profiles WHERE user_id = 11")).all()
        for r in res:
            print(dict(r._mapping))
        print("-" * 60)
        
        # 2. candidate_skills where user_id=11
        print("SELECT * FROM candidate_skills WHERE user_id=11;")
        res = db.execute(text("SELECT id, user_id, skill_name, skill_category, years_of_experience FROM candidate_skills WHERE user_id = 11")).all()
        print(f"Total skills: {len(res)}")
        for r in res[:5]:
            print(dict(r._mapping))
        print("... (truncated list)")
        print("-" * 60)
        
        # 3. jobs where id=1
        print("SELECT * FROM jobs WHERE id=1;")
        res = db.execute(text("SELECT id, title, required_skills, preferred_skills, experience FROM jobs WHERE id = 1")).all()
        for r in res:
            print(dict(r._mapping))
        print("-" * 60)
        
        # 4. candidate_rankings
        print("SELECT * FROM candidate_rankings;")
        res = db.execute(text("SELECT * FROM candidate_rankings")).all()
        for r in res:
            print(dict(r._mapping))
        print("=" * 60)


if __name__ == "__main__":
    run_python_services()
    run_api_endpoints()
    run_sql_proof()
