import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float
from core.base import Base

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(100), nullable=True)
    difficulty = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(String(10), nullable=False)
    explanation = Column(Text, nullable=True)
    marks = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, default=25, nullable=False)  # in minutes
    total_questions = Column(Integer, default=25, nullable=False)
    score = Column(Float, nullable=True)  # Overall percentage
    integrity_score = Column(Integer, default=100, nullable=False)
    status = Column(String(20), default="IN_PROGRESS", nullable=False)  # IN_PROGRESS, PASSED, FAILED, TERMINATED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class AssessmentQuestionMap(Base):
    __tablename__ = "assessment_question_map"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)
    selected_answer = Column(String(10), nullable=True)  # A, B, C, or D (or None)
    correct_answer = Column(String(10), nullable=True)
    is_correct = Column(Boolean, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    attempt_id = Column(Integer, nullable=False, index=True)
    aptitude_score = Column(Float, nullable=False)  # Overall percentage
    quantitative_score = Column(Float, nullable=False)  # Percentage
    logical_score = Column(Float, nullable=False)  # Percentage
    verbal_score = Column(Float, nullable=False)  # Percentage
    analytical_reasoning_score = Column(Float, nullable=False)  # Percentage
    computer_fundamentals_score = Column(Float, nullable=False)  # Percentage
    total_correct = Column(Integer, nullable=False)
    total_wrong = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False)  # PASSED, FAILED, TERMINATED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
