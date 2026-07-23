import logging
from typing import Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func

# Import existing models and services
from modules.job_management.model import Job, Application
from modules.candidate.profile.model import CandidateProfile
from modules.candidate.skills.model import CandidateSkill
from modules.ai_evaluation.model import CandidateRanking
from modules.ai_evaluation.services.scoring_service import calculate_ats_score
from modules.ml_prediction.service import predict_candidate_suitability

logger = logging.getLogger(__name__)


def get_standardized_prediction(pred: str) -> str:
    if not pred:
        return "Rejected"
    
    mapping = {
        "Highly Recommended": "Selected",
        "Recommended": "Selected",
        "Consider": "High Potential",
        "Needs Review": "Medium Potential",
        "Not Recommended": "Rejected",
        
        "Selected": "Selected",
        "High Potential": "High Potential",
        "Medium Potential": "Medium Potential",
        "Rejected": "Rejected",
        
        "Average": "Medium Potential",
        "Unknown": "Rejected"
    }
    
    return mapping.get(pred, "Rejected")


def get_dashboard_overview(company_id: int, db: Session) -> Dict[str, Any]:
    """
    Computes overview statistics for jobs, candidates, applications, and suitability buckets.
    """
    # 1. Total Jobs
    total_jobs = db.query(Job).count()

    # 2. Total Candidates
    total_candidates = db.query(CandidateProfile).count()

    # 3. Total Applications
    total_applications = db.query(Application).count()

    # 4. Suitability Counts based on candidate's highest suitability prediction
    selected_count = 0
    high_pot_count = 0
    med_pot_count = 0
    rejected_count = 0

    pred_ranks = {
        "Selected": 4,
        "High Potential": 3,
        "Medium Potential": 2,
        "Rejected": 1
    }

    candidates = db.query(CandidateProfile).all()
    for cand in candidates:
        apps = db.query(Application).filter(Application.candidate_id == cand.user_id).all()
        if apps:
            best_pred = "Rejected"
            best_rank = 0
            for app in apps:
                pred = get_standardized_prediction(app.suitability_prediction)
                rank = pred_ranks.get(pred, 1)
                if rank > best_rank:
                    best_rank = rank
                    best_pred = pred
            
            if best_pred == "Selected":
                selected_count += 1
            elif best_pred == "High Potential":
                high_pot_count += 1
            elif best_pred == "Medium Potential":
                med_pot_count += 1
            else:
                rejected_count += 1
        else:
            # Candidates with no applications default to Rejected
            rejected_count += 1

    return {
        "total_jobs": total_jobs,
        "total_candidates": total_candidates,
        "total_applications": total_applications,
        "selected_candidates": selected_count,
        "high_potential_candidates": high_pot_count,
        "medium_potential_candidates": med_pot_count,
        "rejected_candidates": rejected_count
    }


def get_ats_score_distribution(company_id: int, db: Session) -> Dict[str, int]:
    """
    Returns score counts bucketed by 20-point ranges.
    Uses the highest ATS score application for candidates with multiple applications.
    """
    distribution = {
        "0-20": 0,
        "21-40": 0,
        "41-60": 0,
        "61-80": 0,
        "81-100": 0
    }

    candidates = db.query(CandidateProfile).all()
    for cand in candidates:
        apps = db.query(Application).filter(Application.candidate_id == cand.user_id).all()
        if apps:
            highest_score = max((app.ats_score if app.ats_score is not None else 0) for app in apps)
        else:
            highest_score = 0
        
        score = max(0, min(100, highest_score))
        _bucket_score(score, distribution)

    return distribution


def _bucket_score(score: int, distribution: Dict[str, int]):
    if 0 <= score <= 20:
        distribution["0-20"] += 1
    elif 21 <= score <= 40:
        distribution["21-40"] += 1
    elif 41 <= score <= 60:
        distribution["41-60"] += 1
    elif 61 <= score <= 80:
        distribution["61-80"] += 1
    elif 81 <= score <= 100:
        distribution["81-100"] += 1


def get_skill_gap_analysis(job_id: int, db: Session) -> List[Dict[str, Any]]:
    """
    Compares job required skills with candidate skills and returns missing skill counts.
    """
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return []

    # Get job required skills
    req_skills_raw = job.required_skills or []
    if isinstance(req_skills_raw, str):
        import json
        try:
            req_skills_raw = json.loads(req_skills_raw)
        except Exception:
            req_skills_raw = [req_skills_raw]

    # Clean required skills list
    required_skills = [s.strip().lower() for s in req_skills_raw if s]
    if not required_skills:
        return []

    # Map lowercase to original case for output representation
    orig_case_map = {s.strip().lower(): s.strip() for s in req_skills_raw if s}

    # Fetch all candidates
    candidates = db.query(CandidateProfile).all()
    missing_counts = {skill: 0 for skill in required_skills}

    for cand in candidates:
        # Get candidate skill names
        cand_skills_raw = db.query(CandidateSkill.skill_name).filter(CandidateSkill.user_id == cand.user_id).all()
        cand_skills = {cs[0].strip().lower() for cs in cand_skills_raw if cs[0]}

        for req_skill in required_skills:
            if req_skill not in cand_skills:
                missing_counts[req_skill] += 1

    # Map back to original casing and convert to list
    result = [
        {"skill": orig_case_map[skill], "missing_count": count}
        for skill, count in missing_counts.items()
    ]

    # Sort descending by missing_count
    result.sort(key=lambda x: x["missing_count"], reverse=True)

    return result


def get_top_skills(db: Session) -> List[Dict[str, Any]]:
    """
    Aggregates the top 20 candidate skills by frequency across all candidates.
    Groups case-insensitively, strips whitespace, and displays the most frequent casing format.
    """
    skills = db.query(CandidateSkill.skill_name).all()

    from collections import Counter
    counts = Counter()
    casing_map = {}

    for s_tuple in skills:
        skill = s_tuple[0]
        if not skill:
            continue
        cleaned = skill.strip()
        if not cleaned:
            continue
        lowered = cleaned.lower()
        counts[lowered] += 1
        if lowered not in casing_map:
            casing_map[lowered] = {}
        casing_map[lowered][cleaned] = casing_map[lowered].get(cleaned, 0) + 1

    sorted_skills = counts.most_common(20)
    result = []
    for lowered, count in sorted_skills:
        best_casing = max(casing_map[lowered].items(), key=lambda x: x[1])[0]
        result.append({"skill": best_casing, "count": count})

    return result


def get_candidate_rankings_analytics(job_id: int, db: Session) -> List[Dict[str, Any]]:
    """
    Returns sorted rankings for a job along with ML-predicted suitability labels.
    """
    rankings = db.query(CandidateRanking).filter(CandidateRanking.job_id == job_id).order_by(CandidateRanking.rank).all()
    
    result = []
    for r in rankings:
        # Get ML prediction
        try:
            pred_res = predict_candidate_suitability(candidate_id=r.candidate_id, job_id=job_id, db=db)
            prediction = pred_res.get("prediction", "Unknown")
        except Exception as e:
            logger.error(f"Failed to get prediction for candidate {r.candidate_id}: {e}")
            # Fallback label based on score rules
            if r.score >= 80:
                prediction = "Selected"
            elif r.score >= 60:
                prediction = "High Potential"
            elif r.score >= 40:
                prediction = "Medium Potential"
            else:
                prediction = "Rejected"

        result.append({
            "rank": r.rank,
            "candidate_id": r.candidate_id,
            "score": r.score,
            "prediction": prediction
        })

    return result


def get_prediction_distribution(db: Session) -> Dict[str, int]:
    """
    Returns counts of suitability predictions across all candidates.
    Uses the highest suitability prediction available for candidates with multiple applications.
    """
    distribution = {
        "Selected": 0,
        "High Potential": 0,
        "Medium Potential": 0,
        "Rejected": 0
    }

    pred_ranks = {
        "Selected": 4,
        "High Potential": 3,
        "Medium Potential": 2,
        "Rejected": 1
    }

    candidates = db.query(CandidateProfile).all()
    for cand in candidates:
        apps = db.query(Application).filter(Application.candidate_id == cand.user_id).all()
        if apps:
            best_pred = "Rejected"
            best_rank = 0
            for app in apps:
                pred = get_standardized_prediction(app.suitability_prediction)
                rank = pred_ranks.get(pred, 1)
                if rank > best_rank:
                    best_rank = rank
                    best_pred = pred
            distribution[best_pred] += 1
        else:
            distribution["Rejected"] += 1

    return distribution


def get_hiring_funnel_analytics(db: Session) -> Dict[str, int]:
    """
    Aggregates hiring funnel analytics based on actual application workflow status levels.
    Ensures cumulative progression per candidate (i.e. Selected <= Interviewed <= Shortlisted <= Screened <= Applied).
    """
    status_levels = {
        "Applied": 1,
        "Rejected": 1,
        
        "Screening": 2,
        "Resume Screening": 2,
        "Assessment": 2,
        "Aptitude Test": 2,
        "AI Screening": 2,
        
        "Coding Challenge": 3,
        "Shortlisted": 3,
        "AI Recommendation": 3,
        "Recruiter Review": 3,
        
        "Interview": 4,
        "HR Review": 4,
        "HR Approved": 4,
        
        "Selected": 5,
        "Offer Released": 5,
        "Offer Accepted": 5,
        "Joined": 5,
        "Hired": 5
    }

    applied = 0
    screened = 0
    shortlisted = 0
    interviewed = 0
    selected = 0

    candidates = db.query(CandidateProfile).all()
    for cand in candidates:
        apps = db.query(Application).filter(Application.candidate_id == cand.user_id).all()
        if apps:
            max_level = max(status_levels.get(app.status, 1) for app in apps)
            if max_level >= 1:
                applied += 1
            if max_level >= 2:
                screened += 1
            if max_level >= 3:
                shortlisted += 1
            if max_level >= 4:
                interviewed += 1
            if max_level >= 5:
                selected += 1

    return {
        "Applied": applied,
        "Screened": screened,
        "Shortlisted": shortlisted,
        "Interviewed": interviewed,
        "Selected": selected
    }
