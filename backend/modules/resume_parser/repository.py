from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .model import ResumeParserResult


class ResumeParserRepository:
    """SQLAlchemy CRUD operations for the resume_parser_results table."""

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create_resume_record(
        self,
        db: Session,
        candidate_id: int,
        original_filename: str,
        resume_file: str | None = None,
        file_type: str | None = None,
        raw_text: str | None = None,
        cleaned_text: str | None = None,
        parsed_json: dict[str, Any] | None = None,
        parsing_status: str = "pending",
    ) -> ResumeParserResult:
        """Insert a new resume parser result record."""
        record = ResumeParserResult(
            candidate_id=candidate_id,
            original_filename=original_filename,
            resume_file=resume_file,
            file_type=file_type,
            raw_text=raw_text,
            cleaned_text=cleaned_text,
            parsed_json=parsed_json,
            parsing_status=parsing_status,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update_resume_record(
        self,
        db: Session,
        record_id: int,
        **kwargs: Any,
    ) -> ResumeParserResult | None:
        """Partially update any fields of an existing record by id."""
        record = self.get_resume_record(db, record_id)
        if not record:
            return None
        for field, value in kwargs.items():
            if hasattr(record, field):
                setattr(record, field, value)
        db.commit()
        db.refresh(record)
        return record

    # ------------------------------------------------------------------
    # READ SINGLE
    # ------------------------------------------------------------------

    def get_resume_record(
        self,
        db: Session,
        record_id: int,
    ) -> ResumeParserResult | None:
        """Fetch a single record by primary key."""
        return (
            db.query(ResumeParserResult)
            .filter(ResumeParserResult.id == record_id)
            .first()
        )

    # ------------------------------------------------------------------
    # READ LIST
    # ------------------------------------------------------------------

    def list_resume_records(
        self,
        db: Session,
        candidate_id: int | None = None,
        parsing_status: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[ResumeParserResult]:
        """List records with optional filters. Defaults to most-recent-first."""
        query = db.query(ResumeParserResult)
        if candidate_id is not None:
            query = query.filter(ResumeParserResult.candidate_id == candidate_id)
        if parsing_status is not None:
            query = query.filter(ResumeParserResult.parsing_status == parsing_status)
        return (
            query.order_by(ResumeParserResult.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def delete_resume_record(
        self,
        db: Session,
        record_id: int,
    ) -> bool:
        """Delete a record by primary key. Returns True if deleted, False if not found."""
        record = self.get_resume_record(db, record_id)
        if not record:
            return False
        db.delete(record)
        db.commit()
        return True
