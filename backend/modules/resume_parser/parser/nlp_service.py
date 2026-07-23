import re

try:
    import spacy
except ImportError:  # pragma: no cover - exercised only when optional runtime deps are absent.
    spacy = None


class NlpService:
    """Lightweight spaCy wrapper used for sentence-aware parsing helpers."""

    def __init__(self) -> None:
        self.nlp = None
        if spacy:
            self.nlp = spacy.blank("en")
            if "sentencizer" not in self.nlp.pipe_names:
                self.nlp.add_pipe("sentencizer")

    def sentences(self, text: str, limit: int | None = None) -> list[str]:
        if not self.nlp:
            sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
            return sentences[:limit] if limit else sentences
        doc = self.nlp(text)
        sentences = [sentence.text.strip() for sentence in doc.sents if sentence.text.strip()]
        return sentences[:limit] if limit else sentences
