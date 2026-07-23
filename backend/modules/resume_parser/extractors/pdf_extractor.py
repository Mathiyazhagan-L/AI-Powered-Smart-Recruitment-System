from pathlib import Path

import fitz

from .base import BaseExtractor


class PdfExtractor(BaseExtractor):
    """Extract text from PDF files using PyMuPDF."""

    def extract(self, file_path: Path) -> str:
        text_parts: list[str] = []
        with fitz.open(file_path) as document:
            for page in document:
                text_parts.append(page.get_text("text"))
        return "\n".join(text_parts).strip()
