import regex as re

from .section_utils import SectionExtractor


class EducationParser:
    """Extract education entries from resume text."""

    DEGREE_RE = re.compile(r"(?i)\b(B\.?Tech|M\.?Tech|B\.?E|M\.?E|B\.?Sc|M\.?Sc|BCA|MCA|MBA|Ph\.?D|Bachelor[^,\n]*|Master[^,\n]*)\b")
    YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
    CGPA_RE = re.compile(r"(?i)\b(?:cgpa|gpa)\s*[:\-]?\s*(\d(?:\.\d{1,2})?)")
    PERCENT_RE = re.compile(r"(?i)(\d{2,3}(?:\.\d{1,2})?)\s*%")

    def __init__(self) -> None:
        self.sections = SectionExtractor()

    def parse(self, text: str) -> list[dict]:
        section = self.sections.split(text).get("education", "")
        entries = self._blocks(section)
        return [self._entry(block) for block in entries if self.DEGREE_RE.search(block) or self.YEAR_RE.search(block)]

    def _blocks(self, section: str) -> list[str]:
        if not section:
            return []
        blocks = re.split(r"\n\s*\n|(?=\n\s*[-])", section)
        return [block.strip(" -\n\t") for block in blocks if block.strip(" -\n\t")]

    def _entry(self, block: str) -> dict:
        degree = self._match(self.DEGREE_RE, block)
        years = [match.group(0) for match in self.YEAR_RE.finditer(block)]
        lines = [line.strip(" -") for line in block.splitlines() if line.strip(" -")]
        return {
            "degree": degree,
            "branch": self._branch(block),
            "college": self._institution(lines, ["college", "institute", "school"]),
            "university": self._institution(lines, ["university"]),
            "cgpa": self._match(self.CGPA_RE, block),
            "percentage": self._match(self.PERCENT_RE, block),
            "graduation_year": years[-1] if years else None,
            "current_status": self._status(block),
        }

    def _branch(self, text: str) -> str | None:
        match = re.search(r"(?i)(?:in|of)\s+([A-Za-z &]+(?:Engineering|Science|Technology|Applications|Management|Data Science|AI|ML))", text)
        return match.group(1).strip() if match else None

    def _institution(self, lines: list[str], keywords: list[str]) -> str | None:
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords):
                return line
        return None

    def _status(self, text: str) -> str | None:
        lowered = text.lower()
        if any(token in lowered for token in ["pursuing", "currently", "present"]):
            return "currently_pursuing"
        if any(token in lowered for token in ["completed", "graduated"]):
            return "completed"
        return None

    def _match(self, pattern, text: str) -> str | None:
        match = pattern.search(text)
        return match.group(1).strip() if match else None
