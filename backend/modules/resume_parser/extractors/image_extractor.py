from pathlib import Path

import pytesseract
from PIL import Image

from .base import BaseExtractor


class ImageExtractor(BaseExtractor):
    """Extract text from image resumes using OCR."""

    def extract(self, file_path: Path) -> str:
        with Image.open(file_path) as image:
            return pytesseract.image_to_string(image).strip()
