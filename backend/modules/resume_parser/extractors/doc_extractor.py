from pathlib import Path

import textract

from .base import BaseExtractor


class DocExtractor(BaseExtractor):
    """Extract text from legacy DOC files using textract."""

    def extract(self, file_path: Path) -> str:
        return textract.process(str(file_path)).decode("utf-8", errors="ignore").strip()
