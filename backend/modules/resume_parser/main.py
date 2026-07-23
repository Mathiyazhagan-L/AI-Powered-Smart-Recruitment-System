from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .auth import router as auth_router
from .config import Settings, get_settings
from .database.storage import LocalUploadStorage
from .database.supabase_client import SupabaseClient, SupabaseNotConfiguredError
from .extractors import ExtractorFactory, UnsupportedFileTypeError
from .models.json_generator import JsonGenerator
from .parser import ResumeParser

app = FastAPI(title="AI Resume Parsing Module", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)

settings = get_settings()
if settings.frontend_dir and settings.frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=settings.frontend_dir), name="frontend")


class ResumeParsingService:
    """Application service for upload, extraction, parsing, and persistence."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.local_storage = LocalUploadStorage(settings)
        self.supabase = SupabaseClient(settings)
        self.parser = ResumeParser()
        self.json_generator = JsonGenerator()

    async def parse_upload(self, file: UploadFile, persist: bool) -> dict[str, Any]:
        file_path = await self.local_storage.save(file)
        try:
            self._validate_file(file_path)
            raw_text = ExtractorFactory.get_extractor(file_path).extract(file_path)
            if not raw_text:
                raise ValueError("No text could be extracted from the uploaded resume.")

            parsed = self.parser.parse(raw_text)
            searchable = parsed.pop("_searchable", {})
            public_json = self.json_generator.generate(parsed)

            if not persist:
                return {"filename": file.filename, "data": public_json}

            storage_path = f"{uuid4().hex}/{file.filename or file_path.name}"
            file_url = self.supabase.upload_resume_file(file_path, storage_path) if self.supabase.enabled else None
            public_json = self.json_generator.generate(parsed, file_url=file_url)
            saved = self.supabase.save_parsed_resume(public_json, searchable, file_url, file.filename or file_path.name) if self.supabase.enabled else None
            if saved:
                public_json["resume_id"] = saved["id"]
            return {"filename": file.filename, "data": public_json, "stored": bool(saved)}
        except (UnsupportedFileTypeError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except SupabaseNotConfiguredError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Resume parsing failed: {exc}") from exc

    def _validate_file(self, file_path: Path) -> None:
        extension = file_path.suffix.lower().lstrip(".")
        if extension not in self.settings.allowed_extensions:
            raise UnsupportedFileTypeError(f"Unsupported resume format: {extension}")


def get_service() -> ResumeParsingService:
    return ResumeParsingService(get_settings())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def home():
    """Serve the static start page when the frontend design folder is available."""
    settings = get_settings()
    if settings.frontend_dir:
        start_page = settings.frontend_dir / "startpage.html"
        if start_page.exists():
            return FileResponse(start_page)
    return {"message": "AIHire backend is running. Open /docs for API documentation."}


@app.get("/candidate page.html")
def candidate_page() -> FileResponse:
    page = get_settings().frontend_dir / "candidate page.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="Candidate page not found.")
    return FileResponse(page)


@app.get("/recruiter page.html")
def recruiter_page() -> FileResponse:
    page = get_settings().frontend_dir / "recruiter page.html"
    if not page.exists():
        raise HTTPException(status_code=404, detail="Recruiter page not found.")
    return FileResponse(page)


@app.post("/parse")
async def parse_resumes(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    """Parse one or more resumes without storing them in Supabase."""
    service = get_service()
    results = [await service.parse_upload(file, persist=False) for file in files]
    return {"count": len(results), "results": results}


@app.post("/upload")
async def upload_resumes(files: list[UploadFile] = File(...)) -> dict[str, Any]:
    """Parse one or more resumes and store files/data in Supabase when configured."""
    service = get_service()
    results = [await service.parse_upload(file, persist=True) for file in files]
    return {"count": len(results), "results": results}


@app.get("/resume/{resume_id}")
def get_resume(resume_id: str) -> dict[str, Any]:
    """Return a stored resume database record."""
    try:
        resume = get_service().supabase.get_resume(resume_id)
    except SupabaseNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return resume


@app.get("/resume/{resume_id}/json")
def get_resume_json(resume_id: str) -> dict[str, Any]:
    """Return only the standardized parsed JSON for a stored resume."""
    try:
        parsed_json = get_service().supabase.get_resume_json(resume_id)
    except SupabaseNotConfiguredError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not parsed_json:
        raise HTTPException(status_code=404, detail="Resume JSON not found.")
    return parsed_json
