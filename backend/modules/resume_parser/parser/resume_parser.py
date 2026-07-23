from .award_parser import AwardParser
from .certification_parser import CertificationParser
from .cleaner import TextCleaner
from .education_parser import EducationParser
from .experience_parser import ExperienceParser
from .personal_parser import PersonalParser
from .project_parser import ProjectParser
from .skill_parser import SkillParser
from .summary_parser import SummaryParser


class ResumeParser:
    """Coordinates all resume parsing components."""

    def __init__(self) -> None:
        self.cleaner = TextCleaner()
        self.personal = PersonalParser()
        self.summary = SummaryParser()
        self.skills = SkillParser()
        self.education = EducationParser()
        self.experience = ExperienceParser()
        self.projects = ProjectParser()
        self.certifications = CertificationParser()
        self.awards = AwardParser()

    def parse(self, raw_text: str) -> dict:
        text = self.cleaner.clean(raw_text)
        lines = self.cleaner.lines(text)
        personal = self.personal.parse(text, lines)
        categorized_skills = self.skills.parse(text)

        return {
            "personal": personal,
            "summary": self.summary.parse(text),
            "skills": categorized_skills,
            "education": self.education.parse(text),
            "experience": self.experience.parse(text),
            "projects": self.projects.parse(text),
            "certifications": self.certifications.parse(text),
            "awards": self.awards.parse(text),
            "_searchable": {
                "full_name": personal.get("full_name"),
                "email": personal.get("email"),
                "phone": personal.get("phone"),
                "skills": self.skills.flatten(categorized_skills),
            },
        }
