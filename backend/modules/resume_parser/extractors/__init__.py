from pathlib import Path

from .doc_extractor import DocExtractor
from .docx_extractor import DocxExtractor
from .image_extractor import ImageExtractor
from .pdf_extractor import PdfExtractor
from .txt_extractor import TxtExtractor


class UnsupportedFileTypeError(ValueError):
    """Raised when the uploaded resume format is not supported."""


class ExtractorFactory:
    """Selects the correct text extractor for a resume file."""

    _extractors = {
        ".pdf": PdfExtractor,
        ".docx": DocxExtractor,
        ".doc": DocExtractor,
        ".txt": TxtExtractor,
        ".jpg": ImageExtractor,
        ".jpeg": ImageExtractor,
        ".png": ImageExtractor,
    }

    @classmethod
    def get_extractor(cls, file_path: Path):
        extractor_cls = cls._extractors.get(file_path.suffix.lower())
        if not extractor_cls:
            raise UnsupportedFileTypeError(f"Unsupported resume format: {file_path.suffix}")
        return extractor_cls()
