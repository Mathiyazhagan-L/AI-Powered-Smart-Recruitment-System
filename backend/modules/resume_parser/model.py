from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from core.base import Base


class ResumeParserResult(Base):
    """Stores raw text, cleaned text, and structured parsed JSON for each uploaded resume."""

    __tablename__ = "resume_parser_results"

    id = Column(Integer, primary_key=True, index=True)

    # Link to the authenticated user who uploaded the resume
    candidate_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # File metadata
    original_filename = Column(String(500), nullable=False)
    resume_file = Column(String(1000), nullable=True)   # local path: uploads/resumes/<uuid>.pdf
    file_type = Column(String(20), nullable=True)       # pdf | docx | doc | txt | jpg | png

    # Text pipeline columns
    raw_text = Column(Text, nullable=True)
    cleaned_text = Column(Text, nullable=True)

    # Structured output
    parsed_json = Column(JSON, nullable=True)

    # Status tracking
    parsing_status = Column(
        String(20),
        nullable=False,
        default="pending"
    )  # pending | processing | completed | failed

    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
