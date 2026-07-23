from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class AssessmentSaveAnswerRequest(BaseModel):
    attempt_id: int
    question_id: int
    selected_answer: Optional[str] = None  # A, B, C, D or None
    integrity_score: Optional[int] = None

class AssessmentAnswerSubmit(BaseModel):
    question_id: int
    selected_answer: Optional[str] = None

class AssessmentSubmitRequest(BaseModel):
    attempt_id: int
    answers: List[AssessmentAnswerSubmit]
    integrity_score: Optional[int] = None

class AssessmentQuestionResponse(BaseModel):
    question_id: int
    question: str
    options: Dict[str, str]
    category: str
    selected_answer: Optional[str] = None

    model_config = {"from_attributes": True}

class AssessmentStartResponse(BaseModel):
    attempt_id: int
    duration: int  # Duration in minutes (total)
    remaining_seconds: int  # Remaining seconds to complete the exam
    questions: List[AssessmentQuestionResponse]
    status: str

    model_config = {"from_attributes": True}

class AssessmentSubmitResponse(BaseModel):
    score: float
    correct: int
    wrong: int
    status: str

    model_config = {"from_attributes": True}

class AssessmentResultResponse(BaseModel):
    id: int
    candidate_id: int
    attempt_id: int
    aptitude_score: float
    quantitative_score: float
    logical_score: float
    verbal_score: float
    analytical_reasoning_score: float
    computer_fundamentals_score: float
    total_correct: int
    total_wrong: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
