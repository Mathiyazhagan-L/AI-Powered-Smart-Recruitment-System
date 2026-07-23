import regex as re

from .section_utils import SectionExtractor


class ProjectParser:
    """Extract project details from resume sections."""

    URL_RE = re.compile(r"(?i)\b(?:https?://)?(?:www\.)?(?:github\.com|[a-z0-9.-]+\.[a-z]{2,})/[^\s,;)]*")

    def __init__(self) -> None:
        self.sections = SectionExtractor()

    def parse(self, text: str) -> list[dict]:
        section = self.sections.split(text).get("projects", "")
        blocks = [block.strip(" -\n\t") for block in re.split(r"\n\s*\n|(?=\n\s*[-])", section) if block.strip(" -\n\t")]
        return [self._entry(block) for block in blocks if len(block.split()) >= 3]

    def _entry(self, block: str) -> dict:
        lines = [line.strip(" -") for line in block.splitlines() if line.strip(" -")]
        urls = [url if url.startswith(("http://", "https://")) else f"https://{url}" for url in self.URL_RE.findall(block)]
        return {
            "project_title": lines[0] if lines else None,
            "technologies_used": self._technologies(block),
            "description": " ".join(lines[1:]) if len(lines) > 1 else None,
            "github_link": next((url for url in urls if "github.com" in url.lower()), None),
            "live_demo_link": next((url for url in urls if "github.com" not in url.lower()), None),
        }

    def _technologies(self, text: str) -> list[str]:
        lines = text.splitlines()
        match = re.search(r"(?i)(?:technologies|tech stack|tools)\s*[:\-]\s*([^\n]+)", text)
        tech_text = match.group(1) if match else ""
        if not tech_text and lines and "|" in lines[0]:
            tech_text = lines[0].split("|", 1)[1]
        return sorted({item.strip() for item in re.split(r"[,|/]", tech_text) if item.strip()}, key=str.lower)
