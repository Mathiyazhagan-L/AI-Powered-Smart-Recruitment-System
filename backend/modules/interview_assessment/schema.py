from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class InterviewQuestionPublic(BaseModel):
    id: int
    question_text: str
    category: str
    order_index: int

    class Config:
        from_attributes = True


class InterviewStartResponse(BaseModel):
    session_id: int
    duration: int
    questions: List[InterviewQuestionPublic]
    status: str
    current_index: int


class InterviewQuestionResponse(BaseModel):
    question_id: int
    question_text: str
    category: str
    order_index: int
    total_questions: int


class InterviewAnswerResponse(BaseModel):
    transcript: str
    question_id: int
    session_id: int


class InterviewEvaluateResponse(BaseModel):
    session_id: int
    question_id: int
    communication_score: float
    technical_score: float
    confidence_score: float
    professionalism_score: float
    score: float
    feedback: Dict[str, Any]


class QuestionAnswerItem(BaseModel):
    question_text: str
    category: str
    transcript: str

    class Config:
        from_attributes = True


class InterviewResultResponse(BaseModel):
    candidate_id: int
    session_id: int
    communication_score: float
    technical_score: float
    confidence_score: float
    professionalism_score: float
    total_score: float
    grade: str
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    hiring_recommendation: str
    detailed_report: Optional[str] = None
    created_at: datetime
    questions_answers: Optional[List[QuestionAnswerItem]] = None

    class Config:
        from_attributes = True


class BulkAnswerItem(BaseModel):
    question_id: int
    answer_text: str

class BulkSubmitRequest(BaseModel):
    answers: List[BulkAnswerItem]

class ProfessionalAssessmentResult(BaseModel):
    message: str
    total_score: float
    grade: str
    hiring_recommendation: str
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
