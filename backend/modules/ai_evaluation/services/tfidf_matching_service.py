"""
TF-IDF Skill Matching Service
==============================
Uses TF-IDF Vectorization and Cosine Similarity to perform semantic skill
matching between candidates and job requirements.

This supplements the existing exact-match service in matching_service.py
by detecting partial matches, abbreviations, and related skill terms.
"""

import json
import logging
from typing import Dict, Any, List, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from sqlalchemy.orm import Session
from core.database import SessionLocal
from modules.candidate.skills.model import CandidateSkill
from modules.job_management.model import Job

logger = logging.getLogger(__name__)


# ==========================================
# SKILL SYNONYM MAP
# ==========================================
# Expands abbreviated and alternative skill names so TF-IDF can capture
# semantic closeness between "ReactJS" and "React", "ML" and "Machine Learning", etc.

SKILL_SYNONYMS: Dict[str, List[str]] = {
    "python": ["python", "python3", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "reactjs", "react.js", "react js"],
    "angular": ["angular", "angularjs", "angular.js"],
    "vue": ["vue", "vuejs", "vue.js"],
    "node": ["node", "nodejs", "node.js", "node js"],
    "express": ["express", "expressjs", "express.js"],
    "machine learning": ["machine learning", "ml", "machine-learning"],
    "deep learning": ["deep learning", "dl", "deep-learning"],
    "natural language processing": ["natural language processing", "nlp"],
    "artificial intelligence": ["artificial intelligence", "ai"],
    "computer vision": ["computer vision", "cv", "image processing"],
    "data science": ["data science", "data-science", "ds"],
    "tensorflow": ["tensorflow", "tf", "tensor flow"],
    "pytorch": ["pytorch", "torch"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "amazon web services": ["amazon web services", "aws"],
    "google cloud platform": ["google cloud platform", "gcp", "google cloud"],
    "microsoft azure": ["microsoft azure", "azure"],
    "docker": ["docker", "containerization"],
    "kubernetes": ["kubernetes", "k8s"],
    "sql": ["sql", "structured query language"],
    "nosql": ["nosql", "no-sql"],
    "mongodb": ["mongodb", "mongo"],
    "postgresql": ["postgresql", "postgres"],
    "mysql": ["mysql", "my-sql"],
    "c++": ["c++", "cpp", "cplusplus"],
    "c#": ["c#", "csharp", "c sharp"],
    "html": ["html", "html5"],
    "css": ["css", "css3"],
    "rest api": ["rest api", "restful", "rest", "restful api"],
    "graphql": ["graphql", "graph ql"],
    "ci/cd": ["ci/cd", "cicd", "ci cd", "continuous integration", "continuous deployment"],
    "git": ["git", "github", "gitlab", "version control"],
    "agile": ["agile", "scrum", "kanban"],
    "pandas": ["pandas", "pd"],
    "numpy": ["numpy", "np"],
    "fastapi": ["fastapi", "fast api", "fast-api"],
    "flask": ["flask"],
    "django": ["django"],
    "spring boot": ["spring boot", "springboot", "spring-boot"],
    "power bi": ["power bi", "powerbi", "power-bi"],
    "tableau": ["tableau"],
    "excel": ["excel", "ms excel", "microsoft excel"],
}


def _expand_with_synonyms(skill: str) -> str:
    """
    Expands a single skill string with its known synonyms to create a richer
    text representation for TF-IDF vectorization.
    """
    skill_lower = skill.lower().strip()
    for canonical, synonyms in SKILL_SYNONYMS.items():
        if skill_lower in [s.lower() for s in synonyms]:
            return " ".join(synonyms)
    return skill_lower


def _build_skill_document(skills: List[str]) -> str:
    """
    Converts a list of skill strings into a single text document
    suitable for TF-IDF vectorization, with synonym expansion.
    """
    expanded_parts = [_expand_with_synonyms(s) for s in skills if s]
    return " ".join(expanded_parts)


def _parse_skill_list(raw_skills) -> List[str]:
    """
    Safely parses a skill list from a database field that may be a
    Python list, a JSON string, or a single string.
    """
    if not raw_skills:
        return []
    if isinstance(raw_skills, list):
        return [s.strip() for s in raw_skills if isinstance(s, str) and s.strip()]
    if isinstance(raw_skills, str):
        try:
            parsed = json.loads(raw_skills)
            if isinstance(parsed, list):
                return [s.strip() for s in parsed if isinstance(s, str) and s.strip()]
        except (json.JSONDecodeError, TypeError):
            return [raw_skills.strip()] if raw_skills.strip() else []
    return []


# ==========================================
# CORE TF-IDF MATCHING FUNCTION
# ==========================================

def calculate_tfidf_skill_match(
    candidate_id: int,
    job_id: int,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Calculates TF-IDF cosine similarity between a candidate's skills and
    the job's required + preferred skills.

    Returns a dictionary containing:
    - tfidf_similarity: Raw cosine similarity score (0.0 – 1.0)
    - tfidf_match_percentage: Similarity as a percentage (0 – 100)
    - required_similarity: Similarity against required skills only
    - preferred_similarity: Similarity against preferred skills only
    - matched_skills: Skills from the candidate that semantically match
    - missing_skills: Required skills not matched even semantically
    - recommended_skills: Preferred skills the candidate could learn
    - candidate_skills_used: The candidate skills evaluated
    """
    if db is None:
        with SessionLocal() as session:
            return _calculate_tfidf_impl(session, candidate_id, job_id)
    return _calculate_tfidf_impl(db, candidate_id, job_id)


def _calculate_tfidf_impl(
    db: Session,
    candidate_id: int,
    job_id: int
) -> Dict[str, Any]:
    # 1. Fetch job details
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.warning(f"Job with ID {job_id} not found for TF-IDF matching.")
        return _empty_result(candidate_id, job_id, "Job not found.")

    # 2. Fetch candidate skills
    candidate_skill_rows = (
        db.query(CandidateSkill)
        .filter(CandidateSkill.user_id == candidate_id)
        .all()
    )
    candidate_skills = list({
        cs.skill_name.strip()
        for cs in candidate_skill_rows
        if cs.skill_name and cs.skill_name.strip()
    })

    if not candidate_skills:
        logger.warning(f"Candidate {candidate_id} has no skills for TF-IDF matching.")
        return _empty_result(candidate_id, job_id, "Candidate has no skills.")

    # 3. Parse job required and preferred skills
    required_skills = _parse_skill_list(job.required_skills)
    preferred_skills = _parse_skill_list(job.preferred_skills)
    all_job_skills = required_skills + preferred_skills

    if not all_job_skills:
        logger.warning(f"Job {job_id} has no skills defined for TF-IDF matching.")
        return _empty_result(candidate_id, job_id, "Job has no skills defined.")

    # 4. Build TF-IDF documents
    candidate_doc = _build_skill_document(candidate_skills)
    required_doc = _build_skill_document(required_skills) if required_skills else ""
    preferred_doc = _build_skill_document(preferred_skills) if preferred_skills else ""
    combined_job_doc = _build_skill_document(all_job_skills)

    # 5. Vectorize using TF-IDF
    #    We use (1,2)-grams to capture multi-word skills like "machine learning"
    documents = [candidate_doc, combined_job_doc]
    if required_doc:
        documents.append(required_doc)
    if preferred_doc:
        documents.append(preferred_doc)

    try:
        vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            lowercase=True,
            stop_words=None,      # Skills are domain terms; don't strip them
            min_df=1,
            max_df=1.0,
            sublinear_tf=True,
        )
        tfidf_matrix = vectorizer.fit_transform(documents)
    except ValueError as e:
        logger.error(f"TF-IDF vectorization failed: {e}")
        return _empty_result(candidate_id, job_id, f"TF-IDF error: {e}")

    # 6. Calculate cosine similarities
    overall_similarity = float(
        cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    )

    required_similarity = 0.0
    preferred_similarity = 0.0
    idx = 2
    if required_doc:
        required_similarity = float(
            cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[idx:idx + 1])[0][0]
        )
        idx += 1
    if preferred_doc:
        preferred_similarity = float(
            cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[idx:idx + 1])[0][0]
        )

    # 7. Per-skill semantic matching
    matched_skills, missing_skills, recommended_skills = _per_skill_matching(
        candidate_skills, required_skills, preferred_skills
    )

    # 8. Compute weighted match percentage
    match_percentage = round(overall_similarity * 100, 1)

    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "tfidf_similarity": round(overall_similarity, 4),
        "tfidf_match_percentage": match_percentage,
        "required_similarity": round(required_similarity, 4),
        "preferred_similarity": round(preferred_similarity, 4),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommended_skills": recommended_skills,
        "candidate_skills_used": candidate_skills,
        "method": "TF-IDF Cosine Similarity",
    }


def _per_skill_matching(
    candidate_skills: List[str],
    required_skills: List[str],
    preferred_skills: List[str],
) -> tuple:
    """
    Uses TF-IDF cosine similarity to determine per-skill matches
    between individual candidate skills and job skills.

    Returns (matched_skills, missing_skills, recommended_skills).
    """
    if not candidate_skills:
        return [], required_skills[:], preferred_skills[:]

    matched: List[str] = []
    missing: List[str] = []
    recommended: List[str] = []

    cand_docs = [_expand_with_synonyms(s) for s in candidate_skills]

    # Check required skills
    for req_skill in required_skills:
        req_doc = _expand_with_synonyms(req_skill)
        try:
            all_docs = cand_docs + [req_doc]
            vec = TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                lowercase=True,
                min_df=1,
            )
            matrix = vec.fit_transform(all_docs)
            sims = cosine_similarity(matrix[-1:], matrix[:-1])[0]
            best_sim = float(np.max(sims))
            if best_sim >= 0.25:  # Threshold for semantic match
                matched.append(req_skill)
            else:
                missing.append(req_skill)
        except ValueError:
            missing.append(req_skill)

    # Check preferred skills
    for pref_skill in preferred_skills:
        pref_doc = _expand_with_synonyms(pref_skill)
        try:
            all_docs = cand_docs + [pref_doc]
            vec = TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                lowercase=True,
                min_df=1,
            )
            matrix = vec.fit_transform(all_docs)
            sims = cosine_similarity(matrix[-1:], matrix[:-1])[0]
            best_sim = float(np.max(sims))
            if best_sim < 0.25:
                recommended.append(pref_skill)
        except ValueError:
            recommended.append(pref_skill)

    return matched, missing, recommended


def calculate_tfidf_for_all_candidates(
    job_id: int,
    db: Optional[Session] = None
) -> List[Dict[str, Any]]:
    """
    Calculates TF-IDF matching for ALL candidates against a specific job.
    Returns a sorted list (descending by tfidf_match_percentage).
    """
    if db is None:
        with SessionLocal() as session:
            return _tfidf_all_candidates_impl(session, job_id)
    return _tfidf_all_candidates_impl(db, job_id)


def _tfidf_all_candidates_impl(
    db: Session,
    job_id: int
) -> List[Dict[str, Any]]:
    from modules.candidate.profile.model import CandidateProfile

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return []

    profiles = db.query(CandidateProfile).all()
    results = []
    for profile in profiles:
        try:
            result = _calculate_tfidf_impl(db, profile.user_id, job_id)
            results.append(result)
        except Exception as e:
            logger.error(
                f"TF-IDF matching failed for candidate {profile.user_id}: {e}"
            )

    results.sort(key=lambda x: x["tfidf_match_percentage"], reverse=True)
    return results


def _empty_result(
    candidate_id: int,
    job_id: int,
    reason: str
) -> Dict[str, Any]:
    """Returns a zeroed-out result with an explanatory reason."""
    return {
        "candidate_id": candidate_id,
        "job_id": job_id,
        "tfidf_similarity": 0.0,
        "tfidf_match_percentage": 0.0,
        "required_similarity": 0.0,
        "preferred_similarity": 0.0,
        "matched_skills": [],
        "missing_skills": [],
        "recommended_skills": [],
        "candidate_skills_used": [],
        "method": "TF-IDF Cosine Similarity",
        "note": reason,
    }
