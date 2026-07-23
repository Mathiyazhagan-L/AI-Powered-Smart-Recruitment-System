import sys
import os
from datetime import datetime, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from modules.auth.model import User
from modules.candidate.profile.model import CandidateProfile
from modules.candidate.resume.model import CandidateResume
from modules.candidate.education.model import CandidateEducation
from modules.candidate.experience.model import CandidateExperience
from modules.candidate.skills.model import CandidateSkill
from modules.candidate.projects.model import CandidateProject

db = SessionLocal()

user_id = 10003

# 1. Update CandidateProfile
p = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
if p:
    p.location = "Bangalore, India"
    p.headline = "Software Engineer"
    p.profile_completion = 85
    print("Updated CandidateProfile basic info and completion to 85%")
else:
    print("CandidateProfile not found!")

# Clean up existing records for clean state
db.query(CandidateResume).filter(CandidateResume.user_id == user_id).delete()
db.query(CandidateEducation).filter(CandidateEducation.user_id == user_id).delete()
db.query(CandidateExperience).filter(CandidateExperience.user_id == user_id).delete()
db.query(CandidateSkill).filter(CandidateSkill.user_id == user_id).delete()
db.query(CandidateProject).filter(CandidateProject.user_id == user_id).delete()
db.commit()

# 2. Insert Resume
resume = CandidateResume(
    user_id=user_id,
    resume_name="resume.pdf",
    resume_path="/uploads/resume.pdf",
    file_type="pdf",
    file_size=1024,
    parsed_status=True,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
db.add(resume)

# 3. Insert Education
edu = CandidateEducation(
    user_id=user_id,
    degree="Bachelor of Engineering",
    institution="Anna University",
    department="Computer Science",
    cgpa=8.5,
    start_year=2020,
    end_year=2024,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
db.add(edu)

# 4. Insert Experience
exp = CandidateExperience(
    user_id=user_id,
    company_name="AIHire Corp",
    job_title="Software Engineering Intern",
    employment_type="Full-time",
    start_date=date(2023, 6, 1),
    end_date=date(2023, 12, 31),
    currently_working=False,
    description="Worked on frontend and backend features.",
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
db.add(exp)

# 5. Insert Skill
skill = CandidateSkill(
    user_id=user_id,
    skill_name="React",
    skill_category="Frontend",
    proficiency_level="Intermediate",
    years_of_experience=2,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)
db.add(skill)

db.commit()
print("Successfully inserted 1 Resume, 1 Education, 1 Experience, and 1 Skill record.")
db.close()
