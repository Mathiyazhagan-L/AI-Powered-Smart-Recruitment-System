import os
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from .model import OfferLetter
from .schema import OfferCreate, OfferUpdate
from .pdf_generator import generate_offer_letter_pdf
from modules.candidate.profile.model import CandidateProfile
from modules.job_management.model import Application, Job
from modules.email_automation.triggers import trigger_email

class OfferManagementLogic:

    @staticmethod
    def create_offer_draft(db: Session, data: OfferCreate) -> OfferLetter:
        # Fetch candidate profile to get name and candidate_code
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == data.candidate_id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Candidate Profile with ID {data.candidate_id} not found."
            )
        
        cand_name = profile.full_name
        cand_code = profile.candidate_code or f"AIH{profile.id:04d}"

        # Resolve versioning: find existing offers for this candidate and job
        existing_offers = db.query(OfferLetter).filter(
            OfferLetter.candidate_id == data.candidate_id,
            OfferLetter.job_id == data.job_id
        ).all()
        
        version = 1
        if existing_offers:
            version = max(o.offer_version for o in existing_offers) + 1

        # Generate unique reference
        offer_reference = f"AIH-OFFER-{cand_code}-J{data.job_id}-V{version}"

        offer = OfferLetter(
            candidate_id=data.candidate_id,
            candidate_code=cand_code,
            job_id=data.job_id,
            recruiter_id=data.recruiter_id,
            hr_id=data.hr_id,
            offer_reference=offer_reference,
            offer_version=version,
            company_name=data.company_name,
            candidate_name=cand_name,
            position_title=data.position_title,
            department=data.department,
            employment_type=data.employment_type,
            package_amount=data.package_amount,
            joining_date=data.joining_date,
            location=data.location,
            reporting_manager=data.reporting_manager,
            offer_status="Draft",
            candidate_response="Pending",
            joining_status="Pending",
            offer_expiry_date=data.offer_expiry_date,
            notes=data.notes
        )

        db.add(offer)
        db.commit()
        db.refresh(offer)
        return offer

    @staticmethod
    def generate_offer(db: Session, offer_id: int) -> OfferLetter:
        offer = db.query(OfferLetter).filter(OfferLetter.id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offer with ID {offer_id} not found."
            )

        # Build paths
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        relative_path = f"uploads/offer_letters/Offer_{offer.candidate_code}_V{offer.offer_version}.pdf"
        absolute_path = os.path.join(backend_dir, relative_path)

        # Populate dictionary for PDF rendering
        offer_data_dict = {
            "company_name": offer.company_name,
            "offer_version": offer.offer_version,
            "offer_reference": offer.offer_reference,
            "candidate_name": offer.candidate_name,
            "candidate_code": offer.candidate_code,
            "position_title": offer.position_title,
            "department": offer.department,
            "employment_type": offer.employment_type,
            "package_amount": offer.package_amount,
            "joining_date": offer.joining_date,
            "location": offer.location,
            "reporting_manager": offer.reporting_manager,
            "offer_expiry_date": offer.offer_expiry_date
        }

        # Render PDF
        generate_offer_letter_pdf(offer_data_dict, absolute_path)

        # Update model
        offer.offer_status = "Generated"
        offer.offer_pdf_path = relative_path
        db.commit()
        db.refresh(offer)

        # Trigger Email event
        trigger_email(
            event_type="OFFER_GENERATED",
            candidate_id=offer.candidate_id,
            recruiter_id=offer.recruiter_id,
            job_id=offer.job_id,
            context={
                "candidate_name": offer.candidate_name,
                "candidate_code": offer.candidate_code,
                "position_title": offer.position_title,
                "company_name": offer.company_name,
                "package_amount": offer.package_amount,
                "joining_date": str(offer.joining_date),
                "offer_reference": offer.offer_reference,
                "offer_expiry_date": str(offer.offer_expiry_date) if offer.offer_expiry_date else "N/A"
            },
            db=db
        )

        return offer

    @staticmethod
    def send_offer(db: Session, offer_id: int) -> OfferLetter:
        offer = db.query(OfferLetter).filter(OfferLetter.id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offer with ID {offer_id} not found."
            )

        if not offer.offer_pdf_path:
            # Generate first if missing
            OfferManagementLogic.generate_offer(db, offer_id)

        offer.offer_status = "Sent"
        db.commit()
        db.refresh(offer)

        # Get absolute PDF path for attachment
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        absolute_pdf_path = os.path.join(backend_dir, offer.offer_pdf_path)

        # Update application status
        application = db.query(Application).filter(
            Application.candidate_id == offer.candidate_id,
            Application.job_id == offer.job_id
        ).first()
        if application:
            application.status = "Offer Released"
            db.commit()

        # Trigger Send Email event with attachment
        trigger_email(
            event_type="Offer Letter Release",
            candidate_id=offer.candidate_id,
            recruiter_id=offer.recruiter_id,
            job_id=offer.job_id,
            context={
                "candidate_name": offer.candidate_name,
                "candidate_code": offer.candidate_code,
                "position_title": offer.position_title,
                "company_name": offer.company_name,
                "package_amount": offer.package_amount,
                "joining_date": str(offer.joining_date),
                "offer_reference": offer.offer_reference,
                "offer_expiry_date": str(offer.offer_expiry_date) if offer.offer_expiry_date else "N/A",
                "attachment_path": absolute_pdf_path,
                "attachment_name": f"Offer_{offer.candidate_code}.pdf"
            },
            db=db
        )

        return offer

    @staticmethod
    def accept_offer(db: Session, offer_id: int) -> OfferLetter:
        offer = db.query(OfferLetter).filter(OfferLetter.id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offer with ID {offer_id} not found."
            )

        offer.offer_status = "Accepted"
        offer.candidate_response = "Accepted"
        offer.response_date = datetime.utcnow()
        
        # Update Application status to Offer Accepted (DO NOT mark candidate as Hired yet)
        application = db.query(Application).filter(
            Application.candidate_id == offer.candidate_id,
            Application.job_id == offer.job_id
        ).first()
        if application:
            application.status = "Offer Accepted"
            
        db.commit()
        db.refresh(offer)

        # Trigger Email event
        trigger_email(
            event_type="OFFER_ACCEPTED",
            candidate_id=offer.candidate_id,
            recruiter_id=offer.recruiter_id,
            job_id=offer.job_id,
            context={
                "candidate_name": offer.candidate_name,
                "candidate_code": offer.candidate_code,
                "position_title": offer.position_title,
                "company_name": offer.company_name,
                "package_amount": offer.package_amount,
                "joining_date": str(offer.joining_date),
                "offer_reference": offer.offer_reference
            },
            db=db
        )

        return offer

    @staticmethod
    def reject_offer(db: Session, offer_id: int) -> OfferLetter:
        offer = db.query(OfferLetter).filter(OfferLetter.id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offer with ID {offer_id} not found."
            )

        offer.offer_status = "Rejected"
        offer.candidate_response = "Rejected"
        offer.response_date = datetime.utcnow()
        
        # Update Application status
        application = db.query(Application).filter(
            Application.candidate_id == offer.candidate_id,
            Application.job_id == offer.job_id
        ).first()
        if application:
            application.status = "Offer Declined"
            
        db.commit()
        db.refresh(offer)

        # Trigger Email event
        trigger_email(
            event_type="OFFER_REJECTED",
            candidate_id=offer.candidate_id,
            recruiter_id=offer.recruiter_id,
            job_id=offer.job_id,
            context={
                "candidate_name": offer.candidate_name,
                "candidate_code": offer.candidate_code,
                "position_title": offer.position_title,
                "company_name": offer.company_name,
                "package_amount": offer.package_amount,
                "joining_date": str(offer.joining_date),
                "offer_reference": offer.offer_reference
            },
            db=db
        )

        return offer

    @staticmethod
    def mark_joined(db: Session, offer_id: int) -> OfferLetter:
        offer = db.query(OfferLetter).filter(OfferLetter.id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offer with ID {offer_id} not found."
            )

        offer.offer_status = "Joined"
        offer.joining_status = "Joined"
        offer.joined_date = date.today()

        # Update Application status to Joined
        application = db.query(Application).filter(
            Application.candidate_id == offer.candidate_id,
            Application.job_id == offer.job_id
        ).first()
        if application:
            application.status = "Joined"

        db.commit()
        db.refresh(offer)

        # Trigger Email event
        trigger_email(
            event_type="OFFER_JOINED",
            candidate_id=offer.candidate_id,
            recruiter_id=offer.recruiter_id,
            job_id=offer.job_id,
            context={
                "candidate_name": offer.candidate_name,
                "candidate_code": offer.candidate_code,
                "position_title": offer.position_title,
                "company_name": offer.company_name,
                "package_amount": offer.package_amount,
                "joining_date": str(offer.joining_date),
                "joined_date": str(offer.joined_date),
                "offer_reference": offer.offer_reference
            },
            db=db
        )

        return offer

    @staticmethod
    def mark_hired(db: Session, offer_id: int) -> OfferLetter:
        offer = db.query(OfferLetter).filter(OfferLetter.id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offer with ID {offer_id} not found."
            )

        offer.offer_status = "Hired"

        # Update Application status to Hired
        application = db.query(Application).filter(
            Application.candidate_id == offer.candidate_id,
            Application.job_id == offer.job_id
        ).first()
        if application:
            application.status = "Hired"

        # Update CandidateProfile interview_status to Hired
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == offer.candidate_id).first()
        if profile:
            profile.interview_status = "Hired"

        db.commit()
        db.refresh(offer)

        # Trigger Email event
        trigger_email(
            event_type="OFFER_HIRED",
            candidate_id=offer.candidate_id,
            recruiter_id=offer.recruiter_id,
            job_id=offer.job_id,
            context={
                "candidate_name": offer.candidate_name,
                "candidate_code": offer.candidate_code,
                "position_title": offer.position_title,
                "company_name": offer.company_name,
                "package_amount": offer.package_amount,
                "joining_date": str(offer.joining_date),
                "offer_reference": offer.offer_reference
            },
            db=db
        )

        return offer

    @staticmethod
    def mark_no_show(db: Session, offer_id: int) -> OfferLetter:
        offer = db.query(OfferLetter).filter(OfferLetter.id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offer with ID {offer_id} not found."
            )

        offer.joining_status = "No Show"
        offer.offer_status = "Expired"

        # Update Application status
        application = db.query(Application).filter(
            Application.candidate_id == offer.candidate_id,
            Application.job_id == offer.job_id
        ).first()
        if application:
            application.status = "No Show"

        db.commit()
        db.refresh(offer)
        return offer

    @staticmethod
    def revoke_offer(db: Session, offer_id: int) -> OfferLetter:
        offer = db.query(OfferLetter).filter(OfferLetter.id == offer_id).first()
        if not offer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Offer with ID {offer_id} not found."
            )

        offer.offer_status = "Expired"
        
        # Update Application status
        application = db.query(Application).filter(
            Application.candidate_id == offer.candidate_id,
            Application.job_id == offer.job_id
        ).first()
        if application:
            application.status = "Offer Expired"

        db.commit()
        db.refresh(offer)

        # Trigger Email event
        trigger_email(
            event_type="OFFER_EXPIRED",
            candidate_id=offer.candidate_id,
            recruiter_id=offer.recruiter_id,
            job_id=offer.job_id,
            context={
                "candidate_name": offer.candidate_name,
                "candidate_code": offer.candidate_code,
                "position_title": offer.position_title,
                "company_name": offer.company_name,
                "offer_reference": offer.offer_reference
            },
            db=db
        )

        return offer

    @staticmethod
    def auto_expire_offers(db: Session) -> int:
        """
        Scans and expires offers that have passed their expiration date without response.
        """
        today = date.today()
        expired_offers = db.query(OfferLetter).filter(
            OfferLetter.offer_status == "Sent",
            OfferLetter.offer_expiry_date != None,
            OfferLetter.offer_expiry_date < today
        ).all()

        for offer in expired_offers:
            offer.offer_status = "Expired"
            
            # Update Application
            application = db.query(Application).filter(
                Application.candidate_id == offer.candidate_id,
                Application.job_id == offer.job_id
            ).first()
            if application:
                application.status = "Offer Expired"
                
            trigger_email(
                event_type="OFFER_EXPIRED",
                candidate_id=offer.candidate_id,
                recruiter_id=offer.recruiter_id,
                job_id=offer.job_id,
                context={
                    "candidate_name": offer.candidate_name,
                    "candidate_code": offer.candidate_code,
                    "position_title": offer.position_title,
                    "company_name": offer.company_name,
                    "offer_reference": offer.offer_reference
                },
                db=db
            )

        db.commit()
        return len(expired_offers)

    @staticmethod
    def send_expiry_reminders(db: Session) -> int:
        """
        Sends expiry warning reminders for offers that expire in <= 2 days.
        """
        today = date.today()
        two_days_later = today + timedelta(days=2)
        
        # Select active "Sent" offers that expire between tomorrow and two days later
        remind_offers = db.query(OfferLetter).filter(
            OfferLetter.offer_status == "Sent",
            OfferLetter.offer_expiry_date != None,
            OfferLetter.offer_expiry_date >= today,
            OfferLetter.offer_expiry_date <= two_days_later
        ).all()

        for offer in remind_offers:
            trigger_email(
                event_type="OFFER_EXPIRY_REMINDER",
                candidate_id=offer.candidate_id,
                recruiter_id=offer.recruiter_id,
                job_id=offer.job_id,
                context={
                    "candidate_name": offer.candidate_name,
                    "candidate_code": offer.candidate_code,
                    "position_title": offer.position_title,
                    "company_name": offer.company_name,
                    "offer_reference": offer.offer_reference,
                    "offer_expiry_date": str(offer.offer_expiry_date)
                },
                db=db
            )

        return len(remind_offers)

    @staticmethod
    def get_analytics(db: Session) -> Dict[str, Any]:
        total_gen = db.query(OfferLetter).count()
        total_sent = db.query(OfferLetter).filter(
            OfferLetter.offer_status.in_(["Sent", "Accepted", "Rejected", "Joined", "Hired"])
        ).count()
        accepted = db.query(OfferLetter).filter(
            OfferLetter.offer_status.in_(["Accepted", "Joined", "Hired"])
        ).count()
        rejected = db.query(OfferLetter).filter(OfferLetter.offer_status == "Rejected").count()
        expired = db.query(OfferLetter).filter(OfferLetter.offer_status == "Expired").count()

        rate = 0.0
        if total_sent > 0:
            rate = round((accepted / total_sent) * 100, 2)

        return {
            "total_generated": total_gen,
            "total_sent": total_sent,
            "accepted_offers": accepted,
            "rejected_offers": rejected,
            "expired_offers": expired,
            "acceptance_rate": rate
        }

    @staticmethod
    def auto_generate_offer(db: Session, interview_id: int) -> OfferLetter:
        from modules.interview_scheduling.model import InterviewSchedule
        from modules.company_profile.model import CompanyProfile
        
        interview = db.query(InterviewSchedule).filter(InterviewSchedule.id == interview_id).first()
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
            
        job = db.query(Job).filter(Job.id == interview.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
            
        company = db.query(CompanyProfile).filter(CompanyProfile.user_id == interview.recruiter_id).first()
        company_name = company.company_name if company else "AIHire"
        
        # Determine base salary
        base_salary = 80000.0
        if job.salary_rules:
            if isinstance(job.salary_rules, dict):
                base_salary = job.salary_rules.get("min_salary", 80000.0) or 80000.0
                
        offer_data = OfferCreate(
            candidate_id=interview.candidate_id,
            job_id=interview.job_id,
            recruiter_id=interview.recruiter_id,
            company_name=company_name,
            position_title=job.title,
            department=getattr(job, "department", "Engineering") or "Engineering",
            employment_type=getattr(job, "employment_type", "Full-Time") or "Full-Time",
            package_amount=str(base_salary),
            joining_date=date.today() + timedelta(days=30),
            location=job.location or "Remote",
            reporting_manager="Hiring Manager",
            offer_expiry_date=date.today() + timedelta(days=7),
            equity_percentage=0.0,
            signing_bonus=0.0
        )
        
        # 1. Create Draft
        offer = OfferManagementLogic.create_offer_draft(db, offer_data)
        
        # 2. Generate PDF
        OfferManagementLogic.generate_offer(db, offer.id)
        
        # 3. Send Email
        OfferManagementLogic.send_offer(db, offer.id)
        
        return offer
