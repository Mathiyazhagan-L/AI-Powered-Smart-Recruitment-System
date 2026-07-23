from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from .extractors import ExtractorFactory, UnsupportedFileTypeError
from .model import ResumeParserResult
from .models.json_generator import JsonGenerator
from .parser import ResumeParser
from .parser.cleaner import TextCleaner
from .repository import ResumeParserRepository
from .services.autofill_service import autofill_candidate_tables

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

UPLOAD_DIR = Path(__file__).parent.parent.parent / "modules" / "uploads" / "resumes"
MAX_UPLOAD_MB = 25
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc", "txt", "jpg", "jpeg", "png"}


# ------------------------------------------------------------------
# Local File Storage  (replaces Supabase Storage)
# ------------------------------------------------------------------

class LocalResumeStorage:
    """Saves uploaded resume files to the local filesystem."""

    def __init__(self, upload_dir: Path = UPLOAD_DIR) -> None:
        self.upload_dir = upload_dir
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, file: UploadFile) -> Path:
        extension = Path(file.filename or "").suffix.lower()
        safe_name = f"{uuid4().hex}{extension}"
        destination = self.upload_dir / safe_name
        max_bytes = MAX_UPLOAD_MB * 1024 * 1024

        total = 0
        with destination.open("wb") as out:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    destination.unlink(missing_ok=True)
                    raise ValueError(f"File exceeds {MAX_UPLOAD_MB} MB limit.")
                out.write(chunk)

        await file.seek(0)
        return destination


# ------------------------------------------------------------------
# Resume Parsing Service  (replaces Supabase database operations)
# ------------------------------------------------------------------

class ResumeParsingService:
    """
    Orchestrates the full resume pipeline:
        Upload → Local Storage → Text Extraction → Cleaning
        → Parsing → JSON Generation → Store in resume_parser_results
    """

    def __init__(self) -> None:
        self.storage = LocalResumeStorage()
        self.extractor_factory = ExtractorFactory
        self.cleaner = TextCleaner()
        self.parser = ResumeParser()
        self.json_generator = JsonGenerator()
        self.repo = ResumeParserRepository()

    # ------------------------------------------------------------------
    # VALIDATE
    # ------------------------------------------------------------------

    def _validate_extension(self, filename: str) -> str:
        """Raises ValueError if the extension is not allowed. Returns the extension string."""
        ext = Path(filename or "").suffix.lower().lstrip(".")
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(f"Unsupported file type: .{ext}")
        return ext

    # ------------------------------------------------------------------
    # UPLOAD + PARSE  (main entry point)
    # ------------------------------------------------------------------

    async def upload_and_parse(
        self,
        db: Session,
        file: UploadFile,
        candidate_id: int,
    ) -> ResumeParserResult:
        """
        Full pipeline: save file → extract text → clean → parse → store.
        Returns the ResumeParserResult ORM object.
        """
        original_filename = file.filename or "unknown"
        file_ext = self._validate_extension(original_filename)

        # 1. Create a pending record first so we can update it on failure
        record = self.repo.create_resume_record(
            db=db,
            candidate_id=candidate_id,
            original_filename=original_filename,
            file_type=file_ext,
            parsing_status="processing",
        )

        try:
            # 2. Save file to local storage
            file_path = await self.storage.save(file)
            resume_file_str = str(file_path.relative_to(Path(__file__).parent.parent.parent))

            # 3. Extract raw text
            import logging
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.INFO)
            if not logger.handlers:
                logger.addHandler(logging.StreamHandler())

            extractor = self.extractor_factory.get_extractor(file_path)
            
            logger.info(f"Uploaded file path: {file_path}")
            logger.info(f"Selected extractor: {extractor.__class__.__name__}")
            
            raw_text = extractor.extract(file_path)
            
            logger.info(f"Extracted text length: {len(raw_text) if raw_text else 0}")
            
            if not raw_text or not raw_text.strip():
                raise ValueError("No text could be extracted from the uploaded resume.")

            # 4. Clean text
            cleaned_text = self.cleaner.clean(raw_text)

            # 5. Parse → structured sections
            parsed = self.parser.parse(raw_text)
            parsed.pop("_searchable", {})   # internal key — not stored in JSON

            # 6. Generate standardized JSON
            parsed_json = self.json_generator.generate(parsed)

            # 7. Update record with all results
            record = self.repo.update_resume_record(
                db=db,
                record_id=record.id,
                resume_file=resume_file_str,
                raw_text=raw_text,
                cleaned_text=cleaned_text,
                parsed_json=parsed_json,
                parsing_status="completed",
            )
            
            # 8. AutoFill ATS Candidate Tables
            counts = autofill_candidate_tables(db, candidate_id, parsed_json)
            logger.info(f"AutoFill complete. Counts: {counts}")

        except Exception as exc:
            # Mark the record as failed and preserve the error
            self.repo.update_resume_record(
                db=db,
                record_id=record.id,
                parsing_status="failed",
                error_message=str(exc),
            )
            raise

        return record

    # ------------------------------------------------------------------
    # PARSE ONLY (no persist)
    # ------------------------------------------------------------------

    async def parse_only(
        self,
        file: UploadFile,
    ) -> dict[str, Any]:
        """
        Parse a resume file and return the structured JSON without storing
        anything in the database.
        """
        original_filename = file.filename or "unknown"
        self._validate_extension(original_filename)

        # Save temporarily for extraction
        file_path = await self.storage.save(file)
        try:
            raw_text = self.extractor_factory.get_extractor(file_path).extract(file_path)
            if not raw_text or not raw_text.strip():
                raise ValueError("No text could be extracted from the uploaded resume.")
            cleaned_text = self.cleaner.clean(raw_text)
            parsed = self.parser.parse(raw_text)
            parsed.pop("_searchable", {})
            parsed_json = self.json_generator.generate(parsed)
        finally:
            # Clean up the temp file — parse_only does not persist
            try:
                file_path.unlink(missing_ok=True)
            except Exception:
                pass

        return {
            "filename": original_filename,
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "parsed_json": parsed_json,
        }
