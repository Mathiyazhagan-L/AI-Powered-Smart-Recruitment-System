import os
import random
import logging
import json
import joblib
import pandas as pd
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.database import SessionLocal
from modules.candidate.profile.model import CandidateProfile
from modules.candidate.skills.model import CandidateSkill
from modules.candidate.education.model import CandidateEducation
from modules.candidate.experience.model import CandidateExperience
from modules.candidate.projects.model import CandidateProject
from modules.ai_evaluation.model import CandidateRanking
from modules.ai_evaluation.services.matching_service import calculate_skill_match
from modules.ai_evaluation.services.scoring_service import calculate_ats_score

# Sklearn imports
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

logger = logging.getLogger(__name__)

# Feature List
FEATURES = [
    "skill_match_percentage",
    "ats_score",
    "cgpa",
    "total_skills",
    "total_projects",
    "total_experience_entries"
]


def check_candidate_exists(candidate_id: int, db: Session) -> bool:
    """Checks if a candidate profile exists in the database."""
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    return profile is not None


def generate_ats_features(candidate_id: int, job_id: int, db: Session) -> Dict[str, Any]:
    """Fetches candidate and job details and constructs the feature vector."""
    # 1. Skill Match Percentage
    match_res = calculate_skill_match(candidate_id=candidate_id, job_id=job_id, db=db)
    skill_match_percentage = match_res.get("match_percentage", 0)

    # 2. ATS Score (From rankings table if exists, else calculate)
    ats_score = 0
    ranking_entry = db.query(CandidateRanking).filter(
        CandidateRanking.candidate_id == candidate_id,
        CandidateRanking.job_id == job_id
    ).first()
    if ranking_entry:
        ats_score = ranking_entry.score
    else:
        score_res = calculate_ats_score(candidate_id=candidate_id, job_id=job_id, db=db)
        ats_score = score_res.get("ats_score", 0)

    # 3. CGPA
    cgpa = 0.0
    edu = db.query(CandidateEducation).filter(CandidateEducation.user_id == candidate_id).first()
    if edu and edu.cgpa is not None:
        cgpa = edu.cgpa
        # If cgpa is on 4.0 scale, normalize to 10.0 scale
        if cgpa <= 5.0 and cgpa > 0.0:
            cgpa = cgpa * 2.5

    # 4. Total Skills
    total_skills = db.query(CandidateSkill).filter(CandidateSkill.user_id == candidate_id).count()

    # 5. Total Projects
    total_projects = db.query(CandidateProject).filter(CandidateProject.user_id == candidate_id).count()

    # 6. Total Experience Entries
    total_experience_entries = db.query(CandidateExperience).filter(CandidateExperience.user_id == candidate_id).count()

    return {
        "skill_match_percentage": skill_match_percentage,
        "ats_score": ats_score,
        "cgpa": cgpa,
        "total_skills": total_skills,
        "total_projects": total_projects,
        "total_experience_entries": total_experience_entries
    }


def map_label(ats_score: int) -> str:
    """Maps ATS Score to suitability label based on rules."""
    if ats_score >= 80:
        return "Selected"
    elif ats_score >= 60:
        return "High Potential"
    elif ats_score >= 40:
        return "Medium Potential"
    else:
        return "Rejected"


def train_and_save_model() -> Dict[str, Any]:
    """
    Generates dataset, trains a RandomForestClassifier, 
    saves model & metrics, and returns metrics summary.
    """
    db = SessionLocal()
    try:
        # Verify candidate_id=11 exists before training
        target_candidate_id = 11
        if not check_candidate_exists(target_candidate_id, db):
            logger.warning(f"Candidate {target_candidate_id} does not exist before training.")

        # 1. Build dataset from existing DB
        real_data = []
        # Get all candidates
        profiles = db.query(CandidateProfile).all()
        # Get job_id = 1 (and other jobs if exist)
        jobs = db.execute(text("SELECT id FROM jobs")).fetchall()
        job_ids = [j[0] for j in jobs]
        if not job_ids:
            job_ids = [1] # fallback

        for profile in profiles:
            for j_id in job_ids:
                feats = generate_ats_features(profile.user_id, j_id, db)
                feats["suitability_label"] = map_label(feats["ats_score"])
                real_data.append(feats)

        # 2. Augment with synthetic dataset to achieve a robust balanced dataset (e.g. 250 samples)
        synthetic_samples = []
        target_dataset_size = 250
        num_synthetic_needed = max(50, target_dataset_size - len(real_data))

        for _ in range(num_synthetic_needed):
            # Synthesize realistic profiles across classes
            # Classes: Selected (score >= 80), High Potential (60-79), Medium (40-59), Rejected (<40)
            score = random.randint(10, 100)
            skill_pct = min(100, max(0, score + random.randint(-15, 15)))
            
            # CGPA correlates loosely with performance
            cgpa = round(random.uniform(5.5, 10.0), 2) if score >= 50 else round(random.uniform(4.5, 8.0), 2)
            # Skills count
            skills_count = random.randint(10, 30) if score >= 60 else random.randint(2, 15)
            # Projects count
            projects_count = random.randint(2, 5) if score >= 60 else random.randint(0, 2)
            # Experience count
            exp_count = random.randint(1, 4) if score >= 50 else random.randint(0, 1)

            feats = {
                "skill_match_percentage": skill_pct,
                "ats_score": score,
                "cgpa": cgpa,
                "total_skills": skills_count,
                "total_projects": projects_count,
                "total_experience_entries": exp_count,
                "suitability_label": map_label(score)
            }
            synthetic_samples.append(feats)

        # Combine
        all_data = real_data + synthetic_samples
        df = pd.DataFrame(all_data)

        # Ensure models directory exists
        os.makedirs("models", exist_ok=True)
        # Save training data to CSV for visibility
        csv_path = os.path.join("models", "training_dataset.csv")
        df.to_csv(csv_path, index=False)

        # 3. Train RandomForest model
        X = df[FEATURES]
        y = df["suitability_label"]

        # Ensure we have enough samples to do a split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        
        accuracy = float(accuracy_score(y_test, y_pred))
        precision = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
        recall = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

        # Get feature importance
        importances = model.feature_importances_
        feature_importance_map = {feat: float(imp) for feat, imp in zip(FEATURES, importances)}

        # Save metrics
        metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "total_samples": len(all_data),
            "real_samples": len(real_data),
            "synthetic_samples": len(synthetic_samples),
            "feature_importance": feature_importance_map
        }

        # Store metrics as attributes on the estimator object so they're saved together
        model.metrics_ = metrics

        # Ensure models directory exists
        os.makedirs("models", exist_ok=True)
        model_path = os.path.join("models", "candidate_suitability.pkl")
        joblib.dump(model, model_path)

        # Also write metrics to JSON for ease of inspectability
        metrics_path = os.path.join("models", "candidate_suitability_metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        logger.info(f"Model trained and saved to {model_path}. Accuracy: {accuracy:.4f}")
        return metrics

    finally:
        db.close()
