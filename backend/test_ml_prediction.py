import json
from fastapi.testclient import TestClient
from sqlalchemy import text
from core.database import SessionLocal
from main import app

# Services
from modules.ml_prediction.trainer import train_and_save_model, check_candidate_exists
from modules.ml_prediction.service import predict_candidate_suitability

candidate_id = 11
job_id = 1

def run_ml_pipeline():
    db = SessionLocal()
    print("=" * 60)
    print("VERIFYING DATA EXISTENCE")
    print("=" * 60)
    
    # 1. Verify candidate profile exists
    candidate_exists = check_candidate_exists(candidate_id, db)
    # 2. Verify job exists
    job_exists = db.execute(
        text("SELECT COUNT(*) FROM jobs WHERE id = :jid"),
        {"jid": job_id}
    ).scalar() > 0
    
    print(f"Candidate {candidate_id} exists in candidate_profiles: {candidate_exists}")
    print(f"Job {job_id} exists in jobs: {job_exists}")
    db.close()
    
    print("=" * 60)
    print("TRAINING MODEL")
    print("=" * 60)
    # 3. Train model
    metrics = train_and_save_model()
    
    print("Training Metrics:")
    print(f"  - Total training samples: {metrics['total_samples']}")
    print(f"  - Real samples: {metrics['real_samples']}")
    print(f"  - Synthetic samples: {metrics['synthetic_samples']}")
    print(f"  - Model accuracy: {metrics['accuracy'] * 100:.2f}%")
    print(f"  - Weighted Precision: {metrics['precision'] * 100:.2f}%")
    print(f"  - Weighted Recall: {metrics['recall'] * 100:.2f}%")
    print(f"  - Weighted F1 Score: {metrics['f1_score'] * 100:.2f}%")
    print("\nFeature Importances:")
    for feat, imp in metrics["feature_importance"].items():
        print(f"  - {feat}: {imp:.4f}")
    
    print("=" * 60)
    print("RUNNING PREDICTION SERVICE DIRECTLY")
    print("=" * 60)
    
    # 4. Predict suitability
    pred_res = predict_candidate_suitability(candidate_id=candidate_id, job_id=job_id)
    print(json.dumps(pred_res, indent=2))
    
    print("=" * 60)
    print("TESTING API ENDPOINT VIA TESTCLIENT")
    print("=" * 60)
    
    client = TestClient(app)
    response = client.post(f"/ml-prediction/job/{job_id}/candidate/{candidate_id}")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print("=" * 60)


def run_sql_proofs():
    print("\n" + "=" * 60)
    print("SQL PROOFS")
    print("=" * 60)
    db = SessionLocal()
    try:
        # candidate_profiles
        print("SELECT * FROM candidate_profiles WHERE user_id=11;")
        res = db.execute(text("SELECT id, user_id, full_name, email, headline FROM candidate_profiles WHERE user_id = 11")).all()
        for r in res:
            print(dict(r._mapping))
        print("-" * 60)
        
        # candidate_skills
        print("SELECT * FROM candidate_skills WHERE user_id=11;")
        res = db.execute(text("SELECT id, user_id, skill_name, skill_category, years_of_experience FROM candidate_skills WHERE user_id = 11")).all()
        print(f"Total skills: {len(res)}")
        for r in res[:5]:
            print(dict(r._mapping))
        print("... (truncated list)")
        print("-" * 60)
        
        # candidate_education
        print("SELECT * FROM candidate_education WHERE user_id=11;")
        res = db.execute(text("SELECT id, user_id, degree, institution, cgpa, end_year FROM candidate_education WHERE user_id = 11")).all()
        for r in res:
            print(dict(r._mapping))
        print("-" * 60)
        
        # candidate_experience
        print("SELECT * FROM candidate_experience WHERE user_id=11;")
        res = db.execute(text("SELECT id, user_id, company_name, job_title, employment_type FROM candidate_experience WHERE user_id = 11")).all()
        for r in res:
            print(dict(r._mapping))
        print("-" * 60)
        
        # candidate_projects
        print("SELECT * FROM candidate_projects WHERE user_id=11;")
        res = db.execute(text("SELECT id, user_id, project_name, technologies FROM candidate_projects WHERE user_id = 11")).all()
        for r in res:
            print(dict(r._mapping))
        print("-" * 60)
        
        # jobs where id=1
        print("SELECT * FROM jobs WHERE id=1;")
        res = db.execute(text("SELECT id, title, required_skills, preferred_skills, experience FROM jobs WHERE id = 1")).all()
        for r in res:
            print(dict(r._mapping))
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    run_ml_pipeline()
    run_sql_proofs()
