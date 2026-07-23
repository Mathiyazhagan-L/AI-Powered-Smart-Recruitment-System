from pathlib import Path

from .base import BaseExtractor


class TxtExtractor(BaseExtractor):
    """Extract text from plain text resumes."""

    def extract(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8", errors="ignore").strip()
