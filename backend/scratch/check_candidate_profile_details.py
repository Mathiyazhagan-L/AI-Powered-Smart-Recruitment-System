import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from modules.candidate.skills.model import CandidateSkill
from modules.candidate.experience.model import CandidateExperience
from modules.candidate.education.model import CandidateEducation

db = SessionLocal()

user_id = 1

print("--- Skills ---")
skills = db.query(CandidateSkill).filter(CandidateSkill.user_id == user_id).all()
for s in skills:
    print(f"Skill: {s.skill_name}, Category: {s.skill_category}, Experience: {s.years_of_experience} years")

print("\n--- Experience ---")
exps = db.query(CandidateExperience).filter(CandidateExperience.user_id == user_id).all()
for x in exps:
    print(f"Title: {x.job_title}, Company: {x.company_name}, Description: {x.description}")

print("\n--- Education ---")
edus = db.query(CandidateEducation).filter(CandidateEducation.user_id == user_id).all()
for e in edus:
    print(f"Degree: {e.degree}, Institution: {e.institution}")

db.close()
