import sys
import os

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

print("--- Candidate Profile ---")
p = db.query(CandidateProfile).filter(CandidateProfile.user_id == user_id).first()
if p:
    print(f"ID: {p.id}, Email: {p.email}, Name: {p.full_name}, Location: {p.location}, Headline: {p.headline}, Profile Completion: {p.profile_completion}")
else:
    print("No profile found.")

print("\n--- Resume Status ---")
resumes = db.query(CandidateResume).filter(CandidateResume.user_id == user_id).all()
print(f"Count: {len(resumes)}")
for r in resumes:
    print(f"  ID: {r.id}, Name: {r.resume_name}, Path: {r.resume_path}, Parsed: {r.parsed_status}")

print("\n--- Education ---")
edu = db.query(CandidateEducation).filter(CandidateEducation.user_id == user_id).all()
print(f"Count: {len(edu)}")
for e in edu:
    print(f"  ID: {e.id}, Degree: {e.degree}, Institution: {e.institution}")

print("\n--- Experience ---")
exp = db.query(CandidateExperience).filter(CandidateExperience.user_id == user_id).all()
print(f"Count: {len(exp)}")
for x in exp:
    print(f"  ID: {x.id}, Title: {x.job_title}, Company: {x.company_name}")

print("\n--- Skills ---")
skills = db.query(CandidateSkill).filter(CandidateSkill.user_id == user_id).all()
print(f"Count: {len(skills)}")
for s in skills:
    print(f"  ID: {s.id}, Name: {s.skill_name}")

print("\n--- Projects ---")
projects = db.query(CandidateProject).filter(CandidateProject.user_id == user_id).all()
print(f"Count: {len(projects)}")
for pr in projects:
    print(f"  ID: {pr.id}, Title: {pr.project_name}")

db.close()
