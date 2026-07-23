import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from modules.interview_scheduling.model import InterviewSchedule

db = SessionLocal()

print("--- INTERVIEW SCHEDULES ---")
schedules = db.query(InterviewSchedule).all()
for s in schedules:
    print(f"ID: {s.id}, Date: {s.interview_date} ({type(s.interview_date)}), Time: {s.interview_time} ({type(s.interview_time)}), Link: {s.meeting_link}, Status: {s.status}")

db.close()
