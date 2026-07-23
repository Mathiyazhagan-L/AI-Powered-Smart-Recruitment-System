import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from core.base import Base


class AssessmentViolation(Base):
    __tablename__ = "assessment_violations"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    assessment_type = Column(String(50), nullable=False)  # APTITUDE, CODING, INTERVIEW
    violation_type = Column(String(100), nullable=False)
    warning_level = Column(Integer, nullable=False)
    integrity_score = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class ProctoringLog(Base):
    __tablename__ = "proctoring_logs"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    assessment_type = Column(String(50), nullable=False)  # APTITUDE, CODING, INTERVIEW
    event_type = Column(String(100), nullable=False)
    event_data = Column(Text, nullable=True)  # JSON text
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class AssessmentIntegrityResult(Base):
    __tablename__ = "assessment_integrity_results"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    assessment_type = Column(String(50), nullable=False)  # APTITUDE, CODING, INTERVIEW
    assessment_score = Column(Float, nullable=True)
    integrity_score = Column(Integer, nullable=False, default=100)
    violation_count = Column(Integer, nullable=False, default=0)
    status = Column(String(50), nullable=False)  # ACTIVE, COMPLETED, TERMINATED
    completed_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=True)
