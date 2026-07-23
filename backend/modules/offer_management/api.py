import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from core.database import get_db
from .schema import OfferCreate, OfferResponse
from .logic import OfferManagementLogic
from .model import OfferLetter

router = APIRouter(prefix="/offers", tags=["Offer Letter Management"])

@router.post("/generate", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def generate_offer_draft(create_data: OfferCreate, db: Session = Depends(get_db)):
    """
    Generates a draft offer letter, assigns revision version, and renders PDF.
    """
    offer = OfferManagementLogic.create_offer_draft(db, create_data)
    # Automatically trigger PDF generation
    offer = OfferManagementLogic.generate_offer(db, offer.id)
    return offer

@router.post("/auto-generate/{interview_id}", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
def auto_generate_offer(interview_id: int, db: Session = Depends(get_db)):
    """
    Automatically creates a draft, generates a PDF, and sends the offer in 1-click.
    """
    return OfferManagementLogic.auto_generate_offer(db, interview_id)

@router.post("/{offer_id}/send", response_model=OfferResponse)
def send_offer(offer_id: int, db: Session = Depends(get_db)):
    """
    Sends the generated offer letter PDF via email and sets status to Sent.
    """
    return OfferManagementLogic.send_offer(db, offer_id)

@router.get("/candidate/{candidate_id}", response_model=List[OfferResponse])
def get_candidate_offers(candidate_id: int, db: Session = Depends(get_db)):
    """
    Lists all offer letters received by a specific candidate.
    """
    offers = db.query(OfferLetter).filter(OfferLetter.candidate_id == candidate_id).order_by(OfferLetter.offer_version.desc()).all()
    return offers

@router.post("/{offer_id}/accept", response_model=OfferResponse)
def accept_offer(offer_id: int, db: Session = Depends(get_db)):
    """
    Marks the offer letter as Accepted by the candidate.
    """
    return OfferManagementLogic.accept_offer(db, offer_id)

@router.post("/{offer_id}/reject", response_model=OfferResponse)
def reject_offer(offer_id: int, db: Session = Depends(get_db)):
    """
    Marks the offer letter as Rejected by the candidate.
    """
    return OfferManagementLogic.reject_offer(db, offer_id)

@router.post("/{offer_id}/joined", response_model=OfferResponse)
def mark_candidate_joined(offer_id: int, db: Session = Depends(get_db)):
    """
    Recruiter marks the candidate as Joined.
    """
    return OfferManagementLogic.mark_joined(db, offer_id)

@router.post("/{offer_id}/hired", response_model=OfferResponse)
def mark_candidate_hired(offer_id: int, db: Session = Depends(get_db)):
    """
    Recruiter marks the candidate as Hired (final step).
    """
    return OfferManagementLogic.mark_hired(db, offer_id)

@router.post("/{offer_id}/no-show", response_model=OfferResponse)
def mark_candidate_no_show(offer_id: int, db: Session = Depends(get_db)):
    """
    Recruiter marks the candidate as No Show.
    """
    return OfferManagementLogic.mark_no_show(db, offer_id)

@router.post("/{offer_id}/revoke", response_model=OfferResponse)
def revoke_offer(offer_id: int, db: Session = Depends(get_db)):
    """
    Recruiter revokes the active offer (sets status to Expired).
    """
    return OfferManagementLogic.revoke_offer(db, offer_id)

@router.get("/recruiter", response_model=List[OfferResponse])
def get_recruiter_offers(db: Session = Depends(get_db)):
    """
    Lists all offer letters for the recruiter's overview tab.
    """
    offers = db.query(OfferLetter).order_by(OfferLetter.created_at.desc()).all()
    return offers

@router.get("/analytics")
def get_offer_analytics(db: Session = Depends(get_db)):
    """
    Retrieves aggregated offer metrics for the recruiter dashboard.
    """
    return OfferManagementLogic.get_analytics(db)

@router.post("/cron/auto-expire")
def trigger_auto_expiry(db: Session = Depends(get_db)):
    """
    Cron simulation endpoint to expire past-due sent offers.
    """
    expired_count = OfferManagementLogic.auto_expire_offers(db)
    return {"status": "success", "expired_count": expired_count}

@router.post("/cron/reminders")
def trigger_expiry_reminders(db: Session = Depends(get_db)):
    """
    Cron simulation endpoint to dispatch reminder emails for close expiration dates.
    """
    reminder_count = OfferManagementLogic.send_expiry_reminders(db)
    return {"status": "success", "reminder_count": reminder_count}

@router.get("/{offer_id}/download")
def download_offer_pdf(offer_id: int, db: Session = Depends(get_db)):
    """
    Downloads the offer letter PDF file.
    """
    offer = db.query(OfferLetter).filter(OfferLetter.id == offer_id).first()
    if not offer or not offer.offer_pdf_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer letter PDF not found."
        )
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    absolute_pdf_path = os.path.join(backend_dir, offer.offer_pdf_path)
    
    if not os.path.exists(absolute_pdf_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offer letter PDF file does not exist on disk."
        )
        
    return FileResponse(
        absolute_pdf_path,
        media_type="application/pdf",
        filename=f"Offer_{offer.candidate_code}.pdf"
    )
