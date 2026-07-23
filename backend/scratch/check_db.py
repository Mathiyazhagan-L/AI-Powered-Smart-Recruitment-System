import sys
import os

# Add parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from modules.auth.model import User
from modules.candidate.profile.model import CandidateProfile
from modules.company_profile.model import CompanyProfile

db = SessionLocal()

print("--- USERS ---")
users = db.query(User).all()
for u in users:
    print(f"ID: {u.id}, Email: {u.email}, Role: {u.role}, Name: {u.full_name}")

print("\n--- CANDIDATE PROFILES ---")
profiles = db.query(CandidateProfile).all()
for p in profiles:
    print(f"ID: {p.id}, User ID: {p.user_id}, Code: {p.candidate_code}, Email: {p.email}, Name: {p.full_name}")

print("\n--- COMPANY PROFILES ---")
companies = db.query(CompanyProfile).all()
for c in companies:
    print(f"ID: {c.id}, User ID: {c.user_id}, Name: {c.company_name}, Email: {c.company_email}")

db.close()
