from .section_utils import SectionExtractor


class AwardParser:
    """Extract awards, hackathons, workshops, and competitions."""

    def __init__(self) -> None:
        self.sections = SectionExtractor()

    def parse(self, text: str) -> list[dict]:
        sections = self.sections.split(text)
        section = sections.get("awards") or sections.get("certifications", "")
        lines = [line.strip(" -") for line in section.splitlines() if line.strip(" -")]
        return [{"title": line, "type": self._type(line)} for line in lines if self._type(line)]

    def _type(self, line: str) -> str | None:
        lowered = line.lower()
        for label in ["hackathon", "workshop", "competition", "award"]:
            if label in lowered:
                return label
        return None
