import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.ext.hybrid import hybrid_property
from core.base import Base

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Integer, default=30, nullable=False)  # in minutes
    status = Column(String(50), default="IN_PROGRESS", nullable=False)  # IN_PROGRESS, COMPLETED, TERMINATED
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)  # HR, Technical, Behavioral, Project
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    question_id = Column(Integer, nullable=False)
    audio_path = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)
    communication_score = Column(Float, nullable=True)     # max 25
    technical_score = Column(Float, nullable=True)         # max 40
    confidence_score = Column(Float, nullable=True)        # max 20
    professionalism_score = Column(Float, nullable=True)     # max 15
    score = Column(Float, nullable=True)                    # sum of the above (max 100)
    evaluation_feedback = Column(Text, nullable=True)       # JSON string containing feedback details
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class InterviewResult(Base):
    __tablename__ = "interview_results"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    session_id = Column(Integer, nullable=False, index=True)
    communication_score = Column(Float, nullable=False)     # average (max 25)
    technical_score = Column(Float, nullable=False)         # average (max 40)
    confidence_score = Column(Float, nullable=False)        # average (max 20)
    professionalism_score = Column(Float, nullable=False)     # average (max 15)
    total_score = Column(Float, nullable=False)             # average sum (max 100)
    grade = Column(String(10), nullable=False)              # A+, A, B, C, D
    strengths = Column(Text, nullable=True)                 # JSON string or text
    weaknesses = Column(Text, nullable=True)                # JSON string or text
    suggestions = Column(Text, nullable=True)               # JSON string or text
    hiring_recommendation = Column(String(50), nullable=False)  # Recommended, Not Recommended
    detailed_report = Column(Text, nullable=True)           # Detailed feedback JSON string or text
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    @hybrid_property
    def status(self):
        return "COMPLETED"
