from core.base import Base
from core.database import engine

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
import modules.assessment.models
import modules.coding_assessment.models
import modules.interview_assessment.models
import modules.proctoring.models

print("Creating tables...")

Base.metadata.create_all(bind=engine)

print("Tables created successfully!")