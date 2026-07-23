import re
from collections import OrderedDict


SECTION_ALIASES = OrderedDict(
    {
        "summary": ["summary", "professional summary", "career objective", "objective", "profile"],
        "skills": ["skills", "technical skills", "core competencies", "technologies"],
        "education": ["education", "academic background", "academics", "qualification"],
        "experience": ["experience", "work experience", "professional experience", "employment", "internship"],
        "projects": ["projects", "academic projects", "personal projects"],
        "certifications": ["certifications", "certificates", "licenses", "awards & certifications"],
        "awards": ["awards", "achievements", "honors", "hackathons", "workshops", "awards & certifications"],
    }
)


class SectionExtractor:
    """Finds common resume sections without relying on a fixed template."""

    def split(self, text: str) -> dict[str, str]:
        matches: list[tuple[int, int, str]] = []
        for canonical, aliases in SECTION_ALIASES.items():
            for alias in aliases:
                pattern = rf"(?im)^\s*{re.escape(alias)}\s*:?\s*$"
                for match in re.finditer(pattern, text):
                    matches.append((match.start(), match.end(), canonical))

        matches.sort(key=lambda item: item[0])
        sections: dict[str, str] = {}
        for index, (_, end, canonical) in enumerate(matches):
            next_start = matches[index + 1][0] if index + 1 < len(matches) else len(text)
            body = text[end:next_start].strip()
            sections.setdefault(canonical, body)
        return sections
