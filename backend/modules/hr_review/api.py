from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from .schema import HRReviewCreate, HRReviewUpdate, HRReviewResponse
from .logic import HRReviewLogic

router = APIRouter(prefix="/hr-review", tags=["HR Review Management"])

@router.post("/request", response_model=HRReviewResponse, status_code=status.HTTP_201_CREATED)
def request_hr_review(review_data: HRReviewCreate, db: Session = Depends(get_db)):
    """
    Submits a candidate to the HR review queue.
    Performs auto-eligibility checks and snapshots analytics scores.
    """
    return HRReviewLogic.request_hr_review(db, review_data)

@router.get("/queue", response_model=List[HRReviewResponse])
def get_hr_queue(status_filter: Optional[str] = Query(None, description="Filter queue by review_status"), db: Session = Depends(get_db)):
    """
    Returns candidates in the HR review queue.
    """
    return HRReviewLogic.get_hr_queue(db, status_filter)

@router.put("/{review_id}/status", response_model=HRReviewResponse)
def update_hr_review_status(review_id: int, update_data: HRReviewUpdate, db: Session = Depends(get_db)):
    """
    Updates the HR review status of a candidate (e.g. Approved, Rejected, Hold)
    and sends out automatic candidate notifications.
    """
    return HRReviewLogic.update_hr_review_status(db, review_id, update_data)
