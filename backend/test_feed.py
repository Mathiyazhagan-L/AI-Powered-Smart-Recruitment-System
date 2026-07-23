import sys
import os

# Add backend to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.database import SessionLocal
from modules.job_management.api import get_candidate_job_feed

db = SessionLocal()
try:
    results = get_candidate_job_feed(candidate_id=1, db=db)
    print(results)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
