import os
import joblib
import logging
import pandas as pd
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from core.database import SessionLocal

from modules.job_management.model import Job
from modules.candidate.profile.model import CandidateProfile
from modules.ml_prediction.trainer import generate_ats_features, train_and_save_model, FEATURES

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join("models", "candidate_suitability.pkl")


def predict_candidate_suitability(
    candidate_id: int,
    job_id: int,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Predicts candidate suitability for a job using the trained ML model.
    Checks model existence and auto-trains if not present.
    """
    if db is None:
        with SessionLocal() as session:
            return _predict_candidate_suitability_impl(session, candidate_id, job_id)
    return _predict_candidate_suitability_impl(db, candidate_id, job_id)


def _predict_candidate_suitability_impl(db: Session, candidate_id: int, job_id: int) -> Dict[str, Any]:
    # 1. Verify job exists
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise ValueError(f"Job with ID {job_id} not found.")

    # 2. Verify candidate profile exists
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile:
        raise ValueError(f"Candidate profile with ID {candidate_id} not found.")

    # 3. Load or Auto-train model
    if not os.path.exists(MODEL_PATH):
        logger.info(f"Model file {MODEL_PATH} not found. Running auto-training...")
        train_and_save_model()

    try:
        model = joblib.load(MODEL_PATH)
    except Exception as e:
        logger.error(f"Failed to load model file {MODEL_PATH}: {e}. Retrying training...")
        train_and_save_model()
        model = joblib.load(MODEL_PATH)

    # 4. Generate features
    features = generate_ats_features(candidate_id, job_id, db)

    # 5. Build feature DataFrame (with exact column ordering)
    feature_vector_df = pd.DataFrame([features])[FEATURES]

    # 6. Predict suitability class
    prediction = model.predict(feature_vector_df)[0]

    # 7. Get probabilities
    probs = model.predict_proba(feature_vector_df)[0]
    class_idx = list(model.classes_).index(prediction)
    # Convert to percentage (0.0 to 100.0)
    probability = float(round(probs[class_idx] * 100, 1))

    # 8. Determine confidence label
    if probability >= 80.0:
        confidence = "High"
    elif probability >= 50.0:
        confidence = "Medium"
    else:
        confidence = "Low"

    # 9. Get feature importances from model or model.metrics_
    metrics = getattr(model, "metrics_", {})
    feature_importance = metrics.get("feature_importance", {})
    if not feature_importance:
        # Fallback if metrics_ attribute not attached properly
        try:
            importances = model.feature_importances_
            feature_importance = {feat: float(imp) for feat, imp in zip(FEATURES, importances)}
        except Exception:
            feature_importance = {}

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "prediction": prediction,
        "probability": probability,
        "confidence": confidence,
        "features": features,
        "feature_importance": feature_importance
    }
