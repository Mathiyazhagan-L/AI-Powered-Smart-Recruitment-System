from abc import ABC, abstractmethod
from pathlib import Path


class BaseExtractor(ABC):
    """Base interface for resume text extractors."""

    @abstractmethod
    def extract(self, file_path: Path) -> str:
        """Extract raw text from a resume file."""
