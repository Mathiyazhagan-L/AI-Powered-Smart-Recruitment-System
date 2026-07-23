import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from modules.auth.model import User
from modules.job_management.model import Application, Job
from modules.candidate.profile.model import CandidateProfile

db = SessionLocal()

user_id = 1

print("--- User's Applications ---")
apps = db.query(Application).filter(Application.candidate_id == user_id).all()
for app in apps:
    job = db.query(Job).filter(Job.id == app.job_id).first()
    job_title = job.title if job else f"Job #{app.job_id}"
    print(f"App ID: {app.id}, Job: {job_title}, Status: {app.status}, ATS Score: {app.ats_score}, Suitability: {app.suitability_prediction}, Ranking: {app.ranking}")

db.close()
