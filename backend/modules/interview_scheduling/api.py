from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from .schema import (
    InterviewScheduleCreate, InterviewScheduleUpdate, 
    InterviewStatusUpdate, InterviewScheduleResponse
)
from .logic import InterviewSchedulingLogic

router = APIRouter(prefix="/interviews", tags=["Interview Scheduling Management"])

@router.post("/schedule", response_model=InterviewScheduleResponse, status_code=status.HTTP_201_CREATED)
def schedule_interview(create_data: InterviewScheduleCreate, db: Session = Depends(get_db)):
    """
    Schedules a new candidate interview.
    Sends automated candidate invitations.
    """
    return InterviewSchedulingLogic.create_interview(db, create_data)

@router.get("/candidate/{candidate_id}", response_model=List[InterviewScheduleResponse])
def get_interviews_by_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """
    Fetches all scheduled interviews for a candidate.
    """
    return InterviewSchedulingLogic.get_interviews_by_candidate(db, candidate_id)

@router.get("/recruiter/{recruiter_id}", response_model=List[InterviewScheduleResponse])
def get_interviews_by_recruiter(recruiter_id: int, db: Session = Depends(get_db)):
    """
    Fetches all scheduled interviews managed by a recruiter.
    """
    return InterviewSchedulingLogic.get_interviews_by_recruiter(db, recruiter_id)

@router.put("/{interview_id}", response_model=InterviewScheduleResponse)
def update_interview(interview_id: int, update_data: InterviewScheduleUpdate, db: Session = Depends(get_db)):
    """
    Updates details of an interview (e.g., reschedule, update interviewer, or meeting link).
    """
    return InterviewSchedulingLogic.update_interview(db, interview_id, update_data)

@router.put("/{interview_id}/status", response_model=InterviewScheduleResponse)
def update_interview_status(interview_id: int, status_data: InterviewStatusUpdate, db: Session = Depends(get_db)):
    """
    Updates the status of an interview (Scheduled, Confirmed, Completed, Cancelled, Rescheduled).
    """
    update_obj = InterviewScheduleUpdate(status=status_data.status)
    if status_data.notes:
        update_obj.interview_notes = status_data.notes
    return InterviewSchedulingLogic.update_interview(db, interview_id, update_obj)

@router.post("/{interview_id}/final-decision", response_model=InterviewScheduleResponse)
def execute_final_decision(
    interview_id: int, 
    decision: str = Query(..., description="Decision must be: Selection, Rejection, OfferReleased"),
    notes: Optional[str] = Query(None, description="Optional feedback or offer notes"),
    db: Session = Depends(get_db)
):
    """
    Executes the final candidate selection, rejection, or offer letter release.
    Updates application status and triggers target emails.
    """
    return InterviewSchedulingLogic.execute_final_decision(db, interview_id, decision, notes)
