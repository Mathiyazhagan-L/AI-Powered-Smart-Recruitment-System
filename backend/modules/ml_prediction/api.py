from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db

from modules.ml_prediction.model import MLPredictionResponse
from modules.ml_prediction.service import predict_candidate_suitability

router = APIRouter(tags=["ML Suitability Prediction"])


@router.post(
    "/ml-prediction/job/{job_id}/candidate/{candidate_id}",
    response_model=MLPredictionResponse,
    status_code=status.HTTP_200_OK
)
def get_ml_suitability_prediction(
    job_id: int,
    candidate_id: int,
    db: Session = Depends(get_db)
):
    """
    Runs the RandomForest ML suitability prediction for a candidate against a job profile.
    """
    try:
        prediction_result = predict_candidate_suitability(candidate_id=candidate_id, job_id=job_id, db=db)
        return MLPredictionResponse(
            prediction=prediction_result["prediction"],
            probability=prediction_result["probability"],
            confidence=prediction_result["confidence"]
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during prediction: {str(e)}"
        )
