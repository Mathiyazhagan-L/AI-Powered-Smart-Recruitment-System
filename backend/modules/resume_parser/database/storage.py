from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from ..config import Settings


class LocalUploadStorage:
    """Persists uploaded files locally before extraction and optional Supabase upload."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.settings.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(self, file: UploadFile) -> Path:
        extension = Path(file.filename or "").suffix.lower()
        safe_name = f"{uuid4().hex}{extension}"
        destination = self.settings.upload_dir / safe_name

        total = 0
        with destination.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > self.settings.max_upload_bytes:
                    destination.unlink(missing_ok=True)
                    raise ValueError(f"File exceeds {self.settings.max_upload_mb} MB limit.")
                output.write(chunk)
        await file.seek(0)
        return destination
