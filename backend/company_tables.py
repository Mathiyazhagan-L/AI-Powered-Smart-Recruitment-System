from core.database import engine
from core.base import Base

# Ensure the company model is imported so it attaches to the shared Base
import modules.company_profile.model

Base.metadata.create_all(bind=engine)

print("Company Profile Tables Created Successfully")