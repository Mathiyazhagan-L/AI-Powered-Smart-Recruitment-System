from .section_utils import SectionExtractor
from .nlp_service import NlpService


class SummaryParser:
    """Extract a short candidate summary/objective."""

    def __init__(self) -> None:
        self.sections = SectionExtractor()
        self.nlp = NlpService()

    def parse(self, text: str) -> str | None:
        summary = self.sections.split(text).get("summary")
        if summary:
            sentences = self.nlp.sentences(" ".join(summary.split()), limit=5)
            return " ".join(sentences)[:1500] if sentences else " ".join(summary.split())[:1500]
        return None
