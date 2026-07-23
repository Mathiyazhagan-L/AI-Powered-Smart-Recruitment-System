from pydantic import BaseModel


class MLPredictionResponse(BaseModel):
    prediction: str
    probability: float
    confidence: str
