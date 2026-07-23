import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from modules.hr_review.model import HRReview
from modules.job_management.model import Application, Job

db = SessionLocal()

print("--- HR Reviews in DB ---")
reviews = db.query(HRReview).all()
for r in reviews:
    job = db.query(Job).filter(Job.id == r.job_id).first()
    app = db.query(Application).filter(Application.candidate_id == r.candidate_id, Application.job_id == r.job_id).first()
    job_title = job.title if job else f"Job #{r.job_id}"
    app_status = app.status if app else "No Application"
    print(f"ID: {r.id}, Candidate ID: {r.candidate_id}, Job: {job_title}, Review Status: {r.review_status}, Application Status: {app_status}")

db.close()
