from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.database import get_db
from modules.job_management.model import Job, coerce_selection_rounds
from modules.candidate.profile.model import CandidateProfile

# Service imports
from modules.ai_evaluation.services.matching_service import calculate_skill_match
from modules.ai_evaluation.services.scoring_service import calculate_ats_score
from modules.ai_evaluation.services.ranking_service import rank_candidates
from modules.ai_evaluation.services.recommendation_service import generate_recommendations
from modules.ai_evaluation.services.tfidf_matching_service import (
    calculate_tfidf_skill_match,
    calculate_tfidf_for_all_candidates,
)

router = APIRouter(tags=["AI Evaluation"])


@router.post("/matching/job/{job_id}/candidate/{candidate_id}")
def get_skill_matching(job_id: int, candidate_id: int, db: Session = Depends(get_db)):
    """
    Computes exact skill matching metrics for a candidate and job.
    """
    # 1. Existence check for candidate
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile with ID {candidate_id} not found."
        )

    # 2. Existence check for job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    return calculate_skill_match(candidate_id=candidate_id, job_id=job_id, db=db)


@router.post("/ats-score/job/{job_id}/candidate/{candidate_id}")
def get_ats_score(job_id: int, candidate_id: int, db: Session = Depends(get_db)):
    """
    Calculates candidate ATS score for a job based on skills, education, experience, and projects.
    """
    # 1. Existence check for candidate
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile with ID {candidate_id} not found."
        )

    # 2. Existence check for job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    return calculate_ats_score(candidate_id=candidate_id, job_id=job_id, db=db)


@router.get("/ranking/job/{job_id}")
def get_candidate_rankings(job_id: int, db: Session = Depends(get_db)):
    """
    Ranks all candidates with profile records for a job, updates DB ranking, and returns sorted list.
    """
    # Existence check for job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    return rank_candidates(job_id=job_id, db=db)


@router.get("/recommendation/job/{job_id}/candidate/{candidate_id}")
def get_candidate_recommendations(job_id: int, candidate_id: int, db: Session = Depends(get_db)):
    """
    Generates Strengths, Weaknesses, Skill Gaps, and recommendations.
    Uses LLM if API keys exist, otherwise rule-based.
    """
    # 1. Existence check for candidate
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile with ID {candidate_id} not found."
        )

    # 2. Existence check for job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    return generate_recommendations(candidate_id=candidate_id, job_id=job_id, db=db)


@router.get("/recommendation/jobs/{candidate_id}")
def get_recommended_jobs(candidate_id: int, db: Session = Depends(get_db)):
    """
    Returns a list of recommended active jobs for a candidate based on ATS score matching.
    """
    # 1. Existence check for candidate
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile with ID {candidate_id} not found."
        )

    # 2. Fetch all published jobs
    published_jobs = db.query(Job).filter(Job.status == "published").all()
    
    recommended = []
    for job in published_jobs:
        score_res = calculate_ats_score(candidate_id=candidate_id, job_id=job.id, db=db)
        if score_res["ats_score"] > 20:  # Only recommend jobs with > 20% match
            # Dump the job model and add the score - convert datetime objects to ISO strings for JSON serialization
            job_dict = {}
            for c in job.__table__.columns:
                val = getattr(job, c.name)
                # Convert datetime objects to ISO format strings
                if hasattr(val, 'isoformat'):
                    val = val.isoformat()
                if c.name == "selection_rounds":
                    val = coerce_selection_rounds(val)
                job_dict[c.name] = val
            job_dict["match_score"] = score_res["ats_score"]
            job_dict["score_breakdown"] = score_res["score_breakdown"]
            recommended.append(job_dict)

    # Sort descending by match score
    recommended.sort(key=lambda x: x["match_score"], reverse=True)
    return recommended[:10]  # Return top 10


# ==========================
# TF-IDF Skill Matching
# ==========================

@router.post("/matching/tfidf/job/{job_id}/candidate/{candidate_id}")
def get_tfidf_skill_matching(job_id: int, candidate_id: int, db: Session = Depends(get_db)):
    """
    Computes TF-IDF cosine-similarity based skill matching between a candidate
    and a job, supplementing the exact string matching with semantic analysis.

    Returns similarity scores, matched/missing/recommended skills, and the
    NLP method used.
    """
    # 1. Existence check for candidate
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate profile with ID {candidate_id} not found."
        )

    # 2. Existence check for job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    # 3. Also fetch exact match for side-by-side comparison
    exact_result = calculate_skill_match(candidate_id=candidate_id, job_id=job_id, db=db)
    tfidf_result = calculate_tfidf_skill_match(candidate_id=candidate_id, job_id=job_id, db=db)

    return {
        "exact_match": exact_result,
        "tfidf_match": tfidf_result,
    }


@router.get("/matching/tfidf/job/{job_id}")
def get_tfidf_all_candidates(job_id: int, db: Session = Depends(get_db)):
    """
    Computes TF-IDF cosine-similarity skill matching for ALL candidates
    against a specific job. Returns results sorted by match percentage (descending).
    """
    # Existence check for job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found."
        )

    return calculate_tfidf_for_all_candidates(job_id=job_id, db=db)

