import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from core.base import Base

class CodingAttempt(Base):
    __tablename__ = "coding_attempts"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, default=60, nullable=False)  # in minutes
    status = Column(String(20), default="IN_PROGRESS", nullable=False)  # IN_PROGRESS, COMPLETED, TERMINATED
    score = Column(Float, nullable=True)  # Overall percentage score
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class CodingSubmission(Base):
    __tablename__ = "coding_submissions"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, nullable=False, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, nullable=False)
    source_code = Column(Text, nullable=False)
    language = Column(String(50), default="python", nullable=False)
    passed_test_cases = Column(Integer, default=0, nullable=False)
    total_test_cases = Column(Integer, default=0, nullable=False)
    score = Column(Float, default=0.0, nullable=False)  # passed_test_cases / total_test_cases (percentage)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class CodingResult(Base):
    __tablename__ = "coding_results"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    attempt_id = Column(Integer, nullable=False, index=True)
    total_score = Column(Float, nullable=False)  # Overall average percentage
    easy_score = Column(Float, nullable=False)   # Percentage of easy questions solved
    medium_score = Column(Float, nullable=False) # Percentage of medium questions solved
    hard_score = Column(Float, nullable=False)   # Percentage of hard questions solved
    questions_solved = Column(Integer, nullable=False)
    questions_attempted = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # PASS, FAIL
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class CodingAttemptQuestion(Base):
    __tablename__ = "coding_attempt_questions"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, nullable=False)
    order_index = Column(Integer, nullable=False)
