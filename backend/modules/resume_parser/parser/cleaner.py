import html
import re
import unicodedata


class TextCleaner:
    """Normalize extracted resume text before structured parsing."""

    MOJIBAKE_REPLACEMENTS = {
        "â€“": "-",
        "â€”": "-",
        "â€‹": "",
        "â€¢": "-",
        "â€˜": "'",
        "â€™": "'",
        "â€œ": '"',
        "â€�": '"',
        "Â": "",
    }

    INLINE_HEADINGS = [
        "Professional Summary",
        "Career Objective",
        "Technical Skills",
        "Professional Experience",
        "Work Experience",
        "Awards & Certifications",
        "Certifications",
        "Achievements",
        "Summary",
        "Skills",
        "Education",
        "Experience",
        "Projects",
        "Awards",
    ]

    def clean(self, text: str) -> str:
        text = html.unescape(text or "")
        text = unicodedata.normalize("NFKC", text)
        for bad, good in self.MOJIBAKE_REPLACEMENTS.items():
            text = text.replace(bad, good)
        text = text.replace("\r", "\n")
        text = self._isolate_inline_headings(text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return "\n".join(line.strip() for line in text.splitlines()).strip()

    def lines(self, text: str) -> list[str]:
        return [line.strip(" -\t") for line in text.splitlines() if line.strip(" -\t")]

    def _isolate_inline_headings(self, text: str) -> str:
        for heading in sorted(self.INLINE_HEADINGS, key=len, reverse=True):
            pattern = rf"(?<!^)(?<!\n)(?<=[.!?])\s+({re.escape(heading)})(?:\s*:)?(?=\s+[A-Z0-9])"
            text = re.sub(pattern, rf"\n\1\n", text, flags=re.IGNORECASE)
        return text
