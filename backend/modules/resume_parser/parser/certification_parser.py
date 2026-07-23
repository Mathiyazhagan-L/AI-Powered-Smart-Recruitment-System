import regex as re

from .section_utils import SectionExtractor


class CertificationParser:
    """Extract certifications and issuing organizations."""

    DATE_RE = re.compile(r"(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}|\b(?:19|20)\d{2}\b")

    def __init__(self) -> None:
        self.sections = SectionExtractor()

    def parse(self, text: str) -> list[dict]:
        section = self.sections.split(text).get("certifications", "")
        lines = [line.strip(" -") for line in section.splitlines() if line.strip(" -")]
        return [self._entry(line) for line in lines if self._looks_like_certificate(line)]

    def _entry(self, line: str) -> dict:
        date_match = self.DATE_RE.search(line)
        name_part = self.DATE_RE.sub("", line).strip(" ,-")
        organization = None
        if " - " in name_part:
            name, organization = [part.strip() for part in name_part.split(" - ", 1)]
        elif " by " in name_part.lower():
            name, organization = re.split(r"(?i)\s+by\s+", name_part, maxsplit=1)
        else:
            name = name_part
        return {"certificate_name": name or None, "issuing_organization": organization, "completion_date": date_match.group(0) if date_match else None}

    def _looks_like_certificate(self, line: str) -> bool:
        lowered = line.lower()
        return not any(token in lowered for token in ["hackathon participant", "competition", "winner"])
