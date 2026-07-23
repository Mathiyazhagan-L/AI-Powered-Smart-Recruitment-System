from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


# ------------------------------------------------------------------
# Response Schemas
# ------------------------------------------------------------------

class ResumeParserResultResponse(BaseModel):
    """Full response schema for a resume_parser_results record."""

    id: int
    candidate_id: int
    original_filename: str
    resume_file: str | None
    file_type: str | None
    raw_text: str | None
    cleaned_text: str | None
    parsed_json: dict[str, Any] | None
    parsing_status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ResumeParserResultSummary(BaseModel):
    """Lightweight list-view response (excludes raw/cleaned text)."""

    id: int
    candidate_id: int
    original_filename: str
    resume_file: str | None
    file_type: str | None
    parsing_status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ParseOnlyResponse(BaseModel):
    """Response for parse-only endpoint (no database record created)."""

    filename: str
    raw_text: str
    cleaned_text: str
    parsed_json: dict[str, Any]
