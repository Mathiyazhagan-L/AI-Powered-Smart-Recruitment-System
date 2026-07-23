from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date
from core.base import Base

class OfferLetter(Base):
    __tablename__ = "offer_letters"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, nullable=False, index=True)
    candidate_code = Column(String(50), nullable=True, index=True)
    job_id = Column(Integer, nullable=False, index=True)
    recruiter_id = Column(Integer, nullable=False, index=True)
    hr_id = Column(Integer, nullable=True)
    offer_reference = Column(String(100), nullable=False, index=True)
    offer_version = Column(Integer, nullable=False, default=1)
    company_name = Column(String(255), nullable=False)
    candidate_name = Column(String(255), nullable=False)
    position_title = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False)
    employment_type = Column(String(100), nullable=False)
    package_amount = Column(String(255), nullable=False)
    joining_date = Column(Date, nullable=False)
    joined_date = Column(Date, nullable=True)
    location = Column(String(255), nullable=False)
    reporting_manager = Column(String(255), nullable=False)
    
    # Workflow fields
    offer_status = Column(String(50), nullable=False, default="Draft", index=True) # Draft, Generated, Sent, Accepted, Rejected, Expired, Joined, Hired
    candidate_response = Column(String(50), nullable=False, default="Pending", index=True) # Pending, Accepted, Rejected
    joining_status = Column(String(50), nullable=False, default="Pending", index=True) # Pending, Joined, No Show
    
    response_date = Column(DateTime, nullable=True)
    offer_pdf_path = Column(String(500), nullable=True)
    offer_expiry_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
