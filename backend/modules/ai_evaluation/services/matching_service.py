import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from core.database import SessionLocal
from modules.candidate.skills.model import CandidateSkill
from modules.job_management.model import Job

logger = logging.getLogger(__name__)


def calculate_skill_match(candidate_id: int, job_id: int, db: Optional[Session] = None) -> Dict[str, Any]:
    """
    Calculates the skill match between a candidate and a job.
    Normalizes case, removes duplicates, and does exact matching.
    """
    if db is None:
        with SessionLocal() as session:
            return _calculate_skill_match_impl(session, candidate_id, job_id)
    return _calculate_skill_match_impl(db, candidate_id, job_id)


def _calculate_skill_match_impl(db: Session, candidate_id: int, job_id: int) -> Dict[str, Any]:
    # 1. Fetch job required skills
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job with ID {job_id} not found.")
        return {
            "candidate_id": candidate_id,
            "job_id": job_id,
            "matched_skills": [],
            "missing_skills": [],
            "extra_skills": [],
            "match_percentage": 0
        }

    # Extract required skills (expected to be a list of strings)
    req_skills_raw = job.required_skills or []
    if isinstance(req_skills_raw, str):
        # Fallback if somehow stored as a raw JSON string instead of deserialized list
        import json
        try:
            req_skills_raw = json.loads(req_skills_raw)
        except Exception:
            req_skills_raw = [req_skills_raw]

    # Clean and remove duplicate required skills
    required_skills_list = []
    seen_req_lower = set()
    for s in req_skills_raw:
        if s and isinstance(s, str):
            s_clean = s.strip()
            s_lower = s_clean.lower()
            if s_lower not in seen_req_lower:
                seen_req_lower.add(s_lower)
                required_skills_list.append(s_clean)

    # 2. Fetch candidate skills
    candidate_skills_raw = db.query(CandidateSkill).filter(CandidateSkill.user_id == candidate_id).all()
    
    # Clean and remove duplicate candidate skills
    candidate_skills_list = []
    seen_cand_lower = set()
    for cs in candidate_skills_raw:
        if cs.skill_name:
            s_clean = cs.skill_name.strip()
            s_lower = s_clean.lower()
            if s_lower not in seen_cand_lower:
                seen_cand_lower.add(s_lower)
                candidate_skills_list.append(s_clean)

    # 3. Match skills
    matched_skills = []
    missing_skills = []
    extra_skills = []

    # Map for lowercase to original casing
    cand_lower_to_orig = {s.lower(): s for s in candidate_skills_list}

    # Find matched and missing (based on required job skills)
    for req_skill in required_skills_list:
        req_lower = req_skill.lower()
        if req_lower in seen_cand_lower:
            matched_skills.append(req_skill)
        else:
            missing_skills.append(req_skill)

    # Find extra skills (candidate skills that are not required)
    for cand_skill in candidate_skills_list:
        cand_lower = cand_skill.lower()
        if cand_lower not in seen_req_lower:
            extra_skills.append(cand_skill)

    # 4. Calculate match percentage
    if not required_skills_list:
        match_percentage = 100
    else:
        match_percentage = round((len(matched_skills) / len(required_skills_list)) * 100)

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "extra_skills": extra_skills,
        "match_percentage": match_percentage
    }
