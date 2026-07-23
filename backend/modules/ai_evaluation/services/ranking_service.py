import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from core.database import SessionLocal
from modules.candidate.profile.model import CandidateProfile
from modules.ai_evaluation.model import CandidateRanking
from modules.ai_evaluation.services.scoring_service import calculate_ats_score

logger = logging.getLogger(__name__)


def rank_candidates(job_id: int, db: Optional[Session] = None) -> List[Dict[str, Any]]:
    """
    Ranks all candidates with a populated candidate_profiles record for the given job_id.
    Saves/updates records in the candidate_rankings table and returns sorted results.
    """
    if db is None:
        with SessionLocal() as session:
            return _rank_candidates_impl(session, job_id)
    return _rank_candidates_impl(db, job_id)
def _rank_candidates_impl(db: Session, job_id: int) -> List[Dict[str, Any]]:
    from modules.coding_assessment.models import CodingResult
    from modules.proctoring.models import AssessmentIntegrityResult
    from modules.job_management.model import Application

    # 1. Fetch all candidate profiles
    profiles = db.query(CandidateProfile).all()
    if not profiles:
        logger.info(f"No candidate profiles found to rank for job {job_id}.")
        return []

    # 2. Calculate scores
    scored_candidates = []
    for profile in profiles:
        cand_id = profile.user_id
        
        # Base ATS/Resume Match Score
        score_res = calculate_ats_score(candidate_id=cand_id, job_id=job_id, db=db)
        ats_score = score_res.get("ats_score", 0.0)
        resume_match = score_res.get("resume_match", ats_score) # Fallback if not specifically separated
        
        # Assessment Scores
        aptitude = profile.aptitude_score or 0.0
        interview = profile.interview_score or 0.0
        github = profile.github_score or 0.0
        
        coding_result = db.query(CodingResult).filter(CodingResult.candidate_id == cand_id).first()
        coding = coding_result.total_score if coding_result else 0.0
        
        # Integrity Score (avg across modules)
        integrity_records = db.query(AssessmentIntegrityResult).filter(AssessmentIntegrityResult.candidate_id == cand_id).all()
        integrity = sum(r.integrity_score for r in integrity_records) / len(integrity_records) if integrity_records else 100.0
        
        # Current Stage
        application = db.query(Application).filter(Application.job_id == job_id, Application.candidate_id == cand_id).first()
        current_stage = application.status if application else "Applied"

        # Weighted Overall Score Calculation (max 100)
        raw_score = (
            (ats_score * 0.15) +
            (aptitude * 0.15) +
            (coding * 0.25) +
            (interview * 0.25) +
            (resume_match * 0.10) +
            (github * 0.10)
        )
        
        overall_score = min(100.0, max(0.0, raw_score * (integrity / 100.0)))
        
        scored_candidates.append({
            "candidate_id": cand_id,
            "candidate_name": profile.full_name,
            "current_stage": current_stage,
            "overall_score": overall_score,
            "ats_score": ats_score,
            "aptitude_score": aptitude,
            "coding_score": coding,
            "interview_score": interview,
            "github_score": github,
            "resume_match": resume_match,
            "integrity_score": integrity,
            "explanation": score_res.get("score_breakdown", {})
        })

    # 3. Sort descending by Overall Score. 
    # Tie-breakers: Interview > Coding > Aptitude > ATS > Resume Match
    scored_candidates.sort(
        key=lambda x: (
            x["overall_score"],
            x["interview_score"],
            x["coding_score"],
            x["aptitude_score"],
            x["ats_score"],
            x["resume_match"]
        ),
        reverse=True
    )

    # 4. Clear existing rankings for this job_id
    db.query(CandidateRanking).filter(CandidateRanking.job_id == job_id).delete()

    # 5. Save new rankings
    ranking_records = []
    rankings_output = []
    for rank_idx, cand in enumerate(scored_candidates, start=1):
        ranking_rec = CandidateRanking(
            candidate_id=cand["candidate_id"],
            job_id=job_id,
            score=cand["overall_score"],
            rank=rank_idx
        )
        db.add(ranking_rec)
        ranking_records.append(ranking_rec)
        
        rankings_output.append(cand)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save candidate rankings for job {job_id}: {e}")
        raise e

    return rankings_output
