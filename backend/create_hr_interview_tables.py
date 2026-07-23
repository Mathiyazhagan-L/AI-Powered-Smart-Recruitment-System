import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.base import Base
from core.database import engine

# Import the new modules to register them on Base
import modules.hr_review.model
import modules.interview_scheduling.model

print("Creating HR Review and Interview Scheduling tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully!")
