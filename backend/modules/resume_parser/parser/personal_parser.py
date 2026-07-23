from urllib.parse import urlparse

import regex as re


class PersonalParser:
    """Extract personal/contact details from resume text."""

    EMAIL_RE = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
    PHONE_RE = re.compile(r"(?x)(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4,5}")
    URL_RE = re.compile(r"(?i)\b(?:https?://)?(?:www\.)?[a-z0-9.-]+\.[a-z]{2,}(?:/[^\s,;)]*)?")

    def parse(self, text: str, lines: list[str]) -> dict:
        urls = self._urls(text)
        email = self._first(self.EMAIL_RE.findall(text))
        phone = self._first(self.PHONE_RE.findall(text))

        return {
            "full_name": self._name(lines, email),
            "email": email,
            "phone": phone,
            "location": self._location(lines),
            "linkedin_url": self._find_url(urls, "linkedin.com"),
            "github_url": self._find_url(urls, "github.com"),
            "portfolio_url": self._portfolio_url(urls),
        }

    def _name(self, lines: list[str], email: str | None) -> str | None:
        for line in lines[:8]:
            lowered = line.lower()
            if email and email.lower() in lowered:
                continue
            if any(token in lowered for token in ["resume", "curriculum vitae", "email", "phone", "linkedin", "github"]):
                continue
            if 1 < len(line.split()) <= 5 and not any(char.isdigit() for char in line):
                return line
        return None

    def _location(self, lines: list[str]) -> str | None:
        for line in lines[:16]:
            match = re.search(r"(?i)(?:address|location)\s*[:\-]\s*([^|,\n]+(?:,\s*[^|,\n]+)?)", line)
            if match:
                return match.group(1).strip(" |,") or None
        return None

    def _urls(self, text: str) -> list[str]:
        urls = []
        for raw_url in self.URL_RE.findall(text):
            url = raw_url if raw_url.startswith(("http://", "https://")) else f"https://{raw_url}"
            urls.append(url)
        return urls

    def _find_url(self, urls: list[str], domain: str) -> str | None:
        return next((url for url in urls if domain in urlparse(url).netloc.lower()), None)

    def _portfolio_url(self, urls: list[str]) -> str | None:
        blocked_domains = ["linkedin.com", "github.com", "gmail.com", "google.com", "outlook.com", "yahoo.com"]
        return next((url for url in urls if not any(domain in urlparse(url).netloc.lower() for domain in blocked_domains)), None)

    def _first(self, values: list[str]) -> str | None:
        return values[0].strip() if values else None
