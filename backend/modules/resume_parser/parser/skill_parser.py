import regex as re

from .section_utils import SectionExtractor


SKILL_TAXONOMY = {
    "programming_languages": ["python", "java", "javascript", "typescript", "c", "c++", "c#", "go", "ruby", "php", "r", "scala", "kotlin", "swift", "sql"],
    "ai_ml": ["machine learning", "ml", "scikit-learn", "sklearn", "xgboost", "lightgbm", "pandas", "numpy", "feature engineering"],
    "deep_learning": ["deep learning", "tensorflow", "keras", "pytorch", "cnn", "rnn", "lstm", "transformer"],
    "generative_ai": ["generative ai", "llm", "langchain", "rag", "openai", "prompt engineering", "hugging face"],
    "computer_vision": ["computer vision", "opencv", "yolo", "image processing", "object detection", "segmentation"],
    "nlp": ["nlp", "natural language processing", "spacy", "nltk", "bert", "text classification", "sentiment analysis"],
    "cloud": ["aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "lambda", "ec2", "s3"],
    "databases": ["postgresql", "mysql", "mongodb", "redis", "sqlite", "supabase", "firebase", "oracle"],
    "frameworks": ["fastapi", "flask", "django", "react", "angular", "vue", "node.js", "express", "spring boot"],
    "tools": ["git", "github", "gitlab", "jira", "linux", "postman", "figma", "tableau", "power bi", "excel"],
    "soft_skills": ["communication", "leadership", "teamwork", "problem solving", "critical thinking", "adaptability", "time management"],
}


class SkillParser:
    """Categorize skills into a consistent taxonomy."""

    def __init__(self) -> None:
        self.sections = SectionExtractor()

    def parse(self, text: str) -> list[dict]:
        searchable_text = " ".join([self.sections.split(text).get("skills", ""), text]).lower()
        categorized: list[dict] = []

        for category, skills in SKILL_TAXONOMY.items():
            found = []
            for skill in skills:
                pattern = rf"(?<![a-z0-9+.#]){re.escape(skill.lower())}(?![a-z0-9+.#])"
                if re.search(pattern, searchable_text):
                    found.append(self._display(skill))
            if found:
                categorized.append({"category": category, "skills": sorted(set(found), key=str.lower)})

        return categorized

    def flatten(self, categorized_skills: list[dict]) -> list[str]:
        values: list[str] = []
        for group in categorized_skills:
            values.extend(group.get("skills", []))
        return sorted(set(values), key=str.lower)

    def _display(self, skill: str) -> str:
        overrides = {
            "ml": "ML",
            "nlp": "NLP",
            "llm": "LLM",
            "aws": "AWS",
            "gcp": "GCP",
            "sql": "SQL",
            "cnn": "CNN",
            "rnn": "RNN",
            "lstm": "LSTM",
            "rag": "RAG",
            "openai": "OpenAI",
            "opencv": "OpenCV",
            "langchain": "LangChain",
            "spacy": "spaCy",
        }
        return overrides.get(skill, skill.title())
