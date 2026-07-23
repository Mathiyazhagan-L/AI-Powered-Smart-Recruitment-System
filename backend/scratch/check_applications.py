import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from modules.job_management.model import Application, Job
from modules.candidate.profile.model import CandidateProfile

db = SessionLocal()

print("--- APPLICATIONS ---")
apps = db.query(Application).all()
for a in apps:
    job = db.query(Job).filter(Job.id == a.job_id).first()
    cand = db.query(CandidateProfile).filter(CandidateProfile.user_id == a.candidate_id).first()
    job_title = job.title if job else f"Job #{a.job_id}"
    cand_name = cand.full_name if cand else f"Candidate user #{a.candidate_id}"
    print(f"ID: {a.id}, Job: {job_title}, Candidate: {cand_name}, Status: {a.status}, ATS Score: {a.ats_score}, Suitability: {a.suitability_prediction}")

db.close()
