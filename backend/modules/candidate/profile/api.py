from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from core.database import get_db
from .schema import (
    CandidateProfileCreate,
    CandidateProfileResponse,
    CandidateProfileUpdate,
)
from .logic import (
    create_profile,
    delete_profile,
    get_profile,
    update_profile,
)

router = APIRouter(prefix="/candidate/profile", tags=["Candidate Profile"])


@router.post("/create", response_model=CandidateProfileResponse, status_code=status.HTTP_201_CREATED)
def create_candidate_profile(
    payload: CandidateProfileCreate,
    db: Session = Depends(get_db),
):
    try:
        return create_profile(db=db, data=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/{profile_id}", response_model=CandidateProfileResponse)
def get_candidate_profile(profile_id: int, db: Session = Depends(get_db)):
    from .logic import get_profile_by_user
    profile = get_profile_by_user(db=db, user_id=profile_id)
    if not profile:
        profile = get_profile(db=db, profile_id=profile_id)
    if not profile:
        from modules.auth.model import User
        from modules.auth.logic import auto_create_profile_for_user
        user = db.query(User).filter(User.id == profile_id).first()
        if user and user.role.lower() == "candidate":
            try:
                auto_create_profile_for_user(db=db, user=user)
                profile = get_profile_by_user(db=db, user_id=profile_id)
            except Exception as e:
                print(f"Failed to auto-create candidate profile on-the-fly: {e}")
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/update/{profile_id}", response_model=CandidateProfileResponse)
def update_candidate_profile(
    profile_id: int,
    payload: CandidateProfileUpdate,
    db: Session = Depends(get_db),
):
    from .logic import get_profile_by_user
    profile = get_profile_by_user(db=db, user_id=profile_id)
    if not profile:
        profile = get_profile(db=db, profile_id=profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    try:
        return update_profile(db=db, profile=profile, data=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete("/delete/{profile_id}")
def delete_candidate_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = get_profile(db=db, profile_id=profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    delete_profile(db=db, profile=profile)
    return {"message": "Profile deleted successfully"}


@router.get("/", response_model=List[CandidateProfileResponse])
def list_candidate_profiles(db: Session = Depends(get_db)):
    from .model import CandidateProfile
    from modules.job_management.model import Application
    from modules.coding_assessment.models import CodingResult
    from sqlalchemy import func
    
    profiles = db.query(CandidateProfile).all()
    results = []
    
    for profile in profiles:
        # Get highest ATS Score
        ats_score = db.query(func.max(Application.ats_score)).filter(Application.candidate_id == profile.user_id).scalar()
        
        # Get highest Technical Score
        tech_score = db.query(func.max(CodingResult.total_score)).filter(CodingResult.candidate_id == profile.user_id).scalar()
        
        prof_dict = profile.__dict__.copy()
        prof_dict['ats_score'] = ats_score
        prof_dict['technical_score'] = tech_score
        prof_dict['status'] = prof_dict.get('candidate_status', 'Applied')
        
        results.append(prof_dict)
        
    return results


@router.post("/{profile_id}/refresh-github", response_model=CandidateProfileResponse)
def refresh_candidate_github(profile_id: int, db: Session = Depends(get_db)):
    from datetime import datetime
    from .logic import get_profile_by_user, get_profile
    profile = get_profile_by_user(db=db, user_id=profile_id)
    if not profile:
        profile = get_profile(db=db, profile_id=profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
        
    if not profile.github_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No GitHub URL defined on profile.")
        
    try:
        from modules.github_intelligence.service import evaluate_github_profile
        eval_res = evaluate_github_profile(profile.github_url)
        if eval_res:
            profile.github_score = eval_res["github_score"]
            profile.github_summary = eval_res["github_summary"]
            profile.github_last_updated = datetime.utcnow()
            profile.github_repositories = eval_res["github_repositories"]
            profile.github_stars = eval_res["github_stars"]
            profile.github_followers = eval_res["github_followers"]
            profile.github_languages = eval_res["github_languages"]
            db.commit()
            db.refresh(profile)
        return profile
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

