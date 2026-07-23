from core.base import Base
from core.database import get_engine

# Import all model modules so they register with the shared `Base`.
import modules.auth.model
import modules.company_profile.model
import modules.candidate.profile.model
import modules.candidate.education.model
import modules.candidate.experience.model
import modules.candidate.projects.model
import modules.candidate.skills.model
import modules.candidate.resume.model
import modules.job_management.model
import modules.resume_parser.model
import modules.ai_evaluation.model
import modules.assessment.models
import modules.interview_assessment.models
import modules.proctoring.models


def init_db():
    engine = get_engine()
    print("Initializing database and creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized and tables created.")


if __name__ == "__main__":
    init_db()
