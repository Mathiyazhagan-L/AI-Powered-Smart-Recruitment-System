from __future__ import annotations

from pathlib import Path
from typing import Any

from supabase import Client, create_client

from ..config import Settings


class SupabaseNotConfiguredError(RuntimeError):
    """Raised when Supabase credentials are missing."""


class SupabaseClient:
    """Small repository wrapper around Supabase storage and PostgreSQL tables."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client: Client | None = None
        if settings.supabase_url and settings.supabase_key:
            self.client = create_client(settings.supabase_url, settings.supabase_key)

    @property
    def enabled(self) -> bool:
        return self.client is not None

    def ensure_enabled(self) -> Client:
        if not self.client:
            raise SupabaseNotConfiguredError("Supabase credentials are not configured.")
        return self.client

    def ensure_bucket(self) -> None:
        client = self.ensure_enabled()
        try:
            client.storage.create_bucket(self.settings.supabase_storage_bucket, options={"public": True})
        except Exception:
            # Bucket creation is idempotent in practice; existing buckets should not stop parsing.
            return

    def upload_resume_file(self, file_path: Path, storage_path: str) -> str:
        client = self.ensure_enabled()
        self.ensure_bucket()
        with file_path.open("rb") as file_obj:
            client.storage.from_(self.settings.supabase_storage_bucket).upload(
                path=storage_path,
                file=file_obj,
                file_options={"upsert": "true"},
            )
        return client.storage.from_(self.settings.supabase_storage_bucket).get_public_url(storage_path)

    def create_resume_record(self, payload: dict[str, Any]) -> dict[str, Any]:
        client = self.ensure_enabled()
        response = client.table("resumes").insert(payload).execute()
        return response.data[0]

    def replace_child_rows(self, table_name: str, resume_id: str, rows: list[dict[str, Any]]) -> None:
        client = self.ensure_enabled()
        client.table(table_name).delete().eq("resume_id", resume_id).execute()
        if rows:
            client.table(table_name).insert([{**row, "resume_id": resume_id} for row in rows]).execute()

    def save_parsed_resume(self, parsed_json: dict[str, Any], searchable: dict[str, Any], file_url: str | None, original_filename: str) -> dict[str, Any]:
        resume_payload = {
            "original_filename": original_filename,
            "file_url": file_url,
            "full_name": searchable.get("full_name"),
            "email": searchable.get("email"),
            "phone": searchable.get("phone"),
            "parsed_json": parsed_json,
        }
        resume = self.create_resume_record(resume_payload)
        resume_id = resume["id"]

        self.replace_child_rows("skills", resume_id, [{"skill_name": skill} for skill in searchable.get("skills", [])])
        self.replace_child_rows("education", resume_id, parsed_json.get("education", []))
        self.replace_child_rows("experience", resume_id, parsed_json.get("experience", []))
        self.replace_child_rows("projects", resume_id, parsed_json.get("projects", []))
        self.replace_child_rows("certifications", resume_id, parsed_json.get("certifications", []))
        self.replace_child_rows("awards", resume_id, parsed_json.get("awards", []))

        return resume

    def get_resume(self, resume_id: str) -> dict[str, Any] | None:
        client = self.ensure_enabled()
        response = client.table("resumes").select("*").eq("id", resume_id).maybe_single().execute()
        return response.data

    def get_resume_json(self, resume_id: str) -> dict[str, Any] | None:
        resume = self.get_resume(resume_id)
        return resume.get("parsed_json") if resume else None
