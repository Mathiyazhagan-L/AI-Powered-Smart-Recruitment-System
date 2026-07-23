import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from core.database import SessionLocal
from modules.auth.model import User

db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(u.id, u.email, u.role)
db.close()
