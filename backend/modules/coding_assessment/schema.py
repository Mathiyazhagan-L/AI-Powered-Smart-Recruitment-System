from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class CodingQuestionPublic(BaseModel):
    question_id: int
    title: str
    difficulty: str
    category: str
    problem_statement: str
    constraints: Optional[str] = None
    sample_input: Optional[str] = None
    sample_output: Optional[str] = None
    marks: float
    template: str
    submitted: bool = False
    score: Optional[float] = None

class CodingStartResponse(BaseModel):
    attempt_id: int
    duration: int  # minutes
    remaining_seconds: int
    questions: List[CodingQuestionPublic]
    status: str

class CodeRunRequest(BaseModel):
    attempt_id: int
    question_id: int
    source_code: str
    language: str = "python"

class TestCaseResult(BaseModel):
    test_case_index: int
    input: str
    expected: Optional[str] = None
    actual: Optional[str] = None
    passed: bool
    error: Optional[str] = None

class CodeRunResponse(BaseModel):
    status: str  # SUCCESS, COMPILE_ERROR, TIMEOUT, ERROR
    error: Optional[str] = None
    results: List[TestCaseResult] = []
    stdout: Optional[str] = None

class CodeSubmitRequest(BaseModel):
    attempt_id: int
    question_id: int
    source_code: str
    language: str = "python"

class CodeSubmitResponse(BaseModel):
    passed_test_cases: int
    total_test_cases: int
    score: float
    results: List[TestCaseResult] = []
    stdout: Optional[str] = None

class CodingResultResponse(BaseModel):
    candidate_id: int
    attempt_id: int
    total_score: float
    easy_score: float
    medium_score: float
    hard_score: float
    questions_solved: int
    questions_attempted: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
