import regex as re

from .section_utils import SectionExtractor


class ExperienceParser:
    """Extract professional experience and internships."""

    DATE_RE = re.compile(r"(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}|\b(?:19|20)\d{2}\b|present|current")

    def __init__(self) -> None:
        self.sections = SectionExtractor()

    def parse(self, text: str) -> list[dict]:
        section = self.sections.split(text).get("experience", "")
        blocks = self._blocks(section)
        return [self._entry(block) for block in blocks if len(block.split()) >= 4]

    def _blocks(self, section: str) -> list[str]:
        if not section:
            return []
        return [block.strip(" -\n\t") for block in re.split(r"\n\s*\n|(?=\n\s*[-])", section) if block.strip(" -\n\t")]

    def _entry(self, block: str) -> dict:
        lines = [line.strip(" -") for line in block.splitlines() if line.strip(" -")]
        dates = [match.group(0) for match in self.DATE_RE.finditer(block)]
        title, company = self._title_company(lines)
        return {
            "company_name": company,
            "job_title": title,
            "internship": "intern" in block.lower() or "internship" in block.lower(),
            "start_date": dates[0] if dates else None,
            "end_date": dates[1] if len(dates) > 1 else None,
            "duration": self._duration(block),
            "responsibilities": [line for line in lines[1:] if line != company],
        }

    def _title_company(self, lines: list[str]) -> tuple[str | None, str | None]:
        if not lines:
            return None, None
        first = lines[0]
        for separator in [" at ", " @ ", " - ", " | "]:
            if separator in first:
                left, right = first.split(separator, 1)
                return left.strip(), right.strip()
        company = next((line for line in lines[1:] if not self.DATE_RE.search(line) and "tools used" not in line.lower()), None)
        return first, company

    def _duration(self, text: str) -> str | None:
        match = re.search(r"(?i)\b\d+\s*(?:months?|years?|yrs?)\b", text)
        return match.group(0) if match else None
