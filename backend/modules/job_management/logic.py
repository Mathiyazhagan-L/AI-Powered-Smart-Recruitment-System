import datetime
from datetime import timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .model import Job, JobCreate, JobUpdate, coerce_selection_rounds

# ==========================================
# 1. Validation Logic
# ==========================================

def validate_job_data(job_data: JobCreate) -> List[str]:
    """
    Validates a job's eligibility rules, deadlines, selection rounds, and packages.
    Returns a list of error messages. If empty, the job is valid.
    """
    errors = []
    
    # 1. Deadline validation
    deadline = job_data.deadline
    if deadline.tzinfo is None:
        deadline = deadline.replace(tzinfo=timezone.utc)
    else:
        deadline = deadline.astimezone(timezone.utc)

    if deadline <= datetime.datetime.now(timezone.utc):
        errors.append("Deadline must be in the future.")
        
    # 2. Openings validation
    if job_data.openings < 1:
        errors.append("Number of openings must be at least 1.")
        
    # 3. Required skills validation
    if not job_data.required_skills:
        errors.append("At least one required skill must be specified.")
        
    # 4. Salary rules validation
    sal_rules = job_data.salary_rules
    if sal_rules.min_salary is not None and sal_rules.min_salary < 0:
        errors.append("Minimum salary cannot be negative.")
    if sal_rules.max_salary is not None and sal_rules.max_salary < 0:
        errors.append("Maximum salary cannot be negative.")
    if (sal_rules.min_salary is not None and 
            sal_rules.max_salary is not None and 
            sal_rules.min_salary > sal_rules.max_salary):
        errors.append("Minimum salary cannot be greater than maximum salary.")
        
    # 5. Selection rounds validation
    if not job_data.selection_rounds:
        job_data.selection_rounds = coerce_selection_rounds([])
    rounds = job_data.selection_rounds
                
    # 6. Eligibility rules validation
    elig_rules = job_data.eligibility_rules
    if elig_rules.min_cgpa is not None and (elig_rules.min_cgpa < 0.0 or elig_rules.min_cgpa > 10.0):
        errors.append("Minimum CGPA must be between 0.0 and 10.0.")
    if elig_rules.max_backlogs < 0:
        errors.append("Maximum backlogs cannot be negative.")
    if elig_rules.min_experience_years < 0:
        errors.append("Minimum experience years cannot be negative.")

    return errors


# ==========================================
# 2. Database Operations (CRUD)
# ==========================================

def get_job_by_id(db: Session, job_id: int) -> Optional[Job]:
    """Retrieves a single job by its ID."""
    return db.query(Job).filter(Job.id == job_id).first()


def create_job(db: Session, job_data: JobCreate) -> Job:
    """
    Creates a new job. Performs validations first.
    Raises ValueError if validations fail.
    """
    validation_errors = validate_job_data(job_data)
    if validation_errors:
        raise ValueError(f"Validation failed: {', '.join(validation_errors)}")
        
    # Create the SQLAlchemy Job model
    db_job = Job(
        title=job_data.title,
        description=job_data.description,
        required_skills=job_data.required_skills,
        preferred_skills=job_data.preferred_skills,
        experience=job_data.experience,
        package=job_data.package,
        location=job_data.location,
        criteria=job_data.criteria,
        openings=job_data.openings,
        deadline=job_data.deadline,
        status=job_data.status,
        selection_rounds=[
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in job_data.selection_rounds
        ],
        salary_rules=job_data.salary_rules.model_dump(),
        eligibility_rules=job_data.eligibility_rules.model_dump(),
        application_settings=job_data.application_settings.model_dump()
    )
    
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job


def update_job(db: Session, job_id: int, job_data: JobUpdate) -> Optional[Job]:
    """
    Updates an existing job. Partial updates are supported.
    Performs validation if critical fields are updated.
    """
    db_job = get_job_by_id(db, job_id)
    if not db_job:
        return None
        
    # Apply updates
    update_dict = job_data.model_dump(exclude_unset=True)
    
    # If we are updating fields, we need to convert Pydantic schemas to dicts for DB storage
    for key, value in update_dict.items():
        if key in ["selection_rounds", "salary_rules", "eligibility_rules", "application_settings"]:
            if isinstance(value, list):
                setattr(db_job, key, [item.model_dump() if hasattr(item, "model_dump") else item for item in value])
            elif hasattr(value, "model_dump"):
                setattr(db_job, key, value.model_dump())
            else:
                setattr(db_job, key, value)
        else:
            setattr(db_job, key, value)
            
    # Re-validate the updated job state
    # Create a temporary JobCreate object to run the full validation check
    temp_create = JobCreate(
        title=db_job.title,
        description=db_job.description,
        required_skills=db_job.required_skills,
        preferred_skills=db_job.preferred_skills,
        experience=db_job.experience,
        package=db_job.package,
        location=db_job.location,
        criteria=db_job.criteria,
        openings=db_job.openings,
        deadline=db_job.deadline,
        status=db_job.status,
        selection_rounds=db_job.selection_rounds,
        salary_rules=db_job.salary_rules,
        eligibility_rules=db_job.eligibility_rules,
        application_settings=db_job.application_settings
    )
    
    # We do a softer validation check on update, but if they set it to published, we enforce it
    validation_errors = validate_job_data(temp_create)
    if db_job.status == "published" and validation_errors:
        raise ValueError(f"Cannot update to invalid state while published: {', '.join(validation_errors)}")
        
    db_job.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_job)
    return db_job


def delete_job(db: Session, job_id: int) -> bool:
    """Deletes a job from the database."""
    db_job = get_job_by_id(db, job_id)
    if not db_job:
        return False
    db.delete(db_job)
    db.commit()
    return True


def publish_job(db: Session, job_id: int) -> Optional[Job]:
    """
    Publishes a job. Enforces all job validations before publishing.
    """
    db_job = get_job_by_id(db, job_id)
    if not db_job:
        return None
        
    # Re-verify validations
    temp_create = JobCreate(
        title=db_job.title,
        description=db_job.description,
        required_skills=db_job.required_skills,
        preferred_skills=db_job.preferred_skills,
        experience=db_job.experience,
        package=db_job.package,
        location=db_job.location,
        criteria=db_job.criteria,
        openings=db_job.openings,
        deadline=db_job.deadline,
        status="published",
        selection_rounds=db_job.selection_rounds,
        salary_rules=db_job.salary_rules,
        eligibility_rules=db_job.eligibility_rules,
        application_settings=db_job.application_settings
    )
    
    validation_errors = validate_job_data(temp_create)
    if validation_errors:
        raise ValueError(f"Cannot publish job due to validation errors: {', '.join(validation_errors)}")
        
    db_job.status = "published"
    db_job.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_job)

    try:
        from modules.email_automation.triggers import trigger_email
        from modules.auth.model import User
        recruiters = db.query(User).filter(User.role.in_(["recruiter", "admin"])).all()
        for rec in recruiters:
            trigger_email(
                event_type="Recruiter Registration",
                candidate_id=None,
                recruiter_id=rec.id,
                job_id=db_job.id,
                context={
                    "extra_details": f"A new job '{db_job.title}' has been published successfully and is now open for applications."
                },
                db=db
            )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to send job published email: {e}")

    return db_job


def close_job(db: Session, job_id: int) -> Optional[Job]:
    """Closes a job (applications no longer accepted)."""
    db_job = get_job_by_id(db, job_id)
    if not db_job:
        return None
    db_job.status = "closed"
    db_job.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(db_job)
    return db_job


# ==========================================
# 3. Search and Filtering
# ==========================================

def search_and_filter_jobs(
    db: Session,
    search_query: Optional[str] = None,
    status: Optional[str] = None,
    location: Optional[str] = None,
    experience: Optional[str] = None,
    min_salary: Optional[float] = None,
    skills: Optional[List[str]] = None
) -> List[Job]:
    """
    Search and filter jobs using query parameters.
    - Database filters are applied for simple fields (status, location, experience, title/description).
    - Post-filtering is applied for nested JSON attributes (min_salary, skills) for cross-DB compatibility.
    """
    query = db.query(Job)
    
    if status:
        query = query.filter(Job.status == status)
        
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
        
    if experience:
        query = query.filter(Job.experience.ilike(f"%{experience}%"))
        
    if search_query:
        query = query.filter(
            or_(
                Job.title.ilike(f"%{search_query}%"),
                Job.description.ilike(f"%{search_query}%")
            )
        )
        
    results = query.all()
    
    # Post-filtering for compatibility
    filtered_results = []
    for job in results:
        # Filter by min_salary rule
        if min_salary is not None:
            job_min_salary = job.salary_rules.get("min_salary")
            if job_min_salary is None or job_min_salary < min_salary:
                continue
                
        # Filter by required skills (must match all or at least one, let's do "at least one" matching)
        if skills:
            job_skills = [s.lower() for s in job.required_skills]
            match_found = any(s.lower() in job_skills for s in skills)
            if not match_found:
                continue
                
        filtered_results.append(job)
        
    return filtered_results


# ==========================================
# 4. Job Analytics
# ==========================================

def get_job_analytics(db: Session) -> Dict[str, Any]:
    """
    Computes key metrics for job posts:
    - Counts by status (draft, published, closed)
    - Total job openings
    - Location distributions
    - Salary ranges metrics
    """
    all_jobs = db.query(Job).all()
    
    total_jobs = len(all_jobs)
    draft_count = 0
    published_count = 0
    closed_count = 0
    total_openings = 0
    locations = {}
    salaries = []
    
    for job in all_jobs:
        if job.status == "draft":
            draft_count += 1
        elif job.status == "published":
            published_count += 1
            total_openings += job.openings
        elif job.status == "closed":
            closed_count += 1
            
        # Location distribution
        loc = job.location.strip()
        locations[loc] = locations.get(loc, 0) + 1
        
        # Collect salaries of active/published jobs for average salary
        if job.status == "published" and job.salary_rules:
            min_sal = job.salary_rules.get("min_salary")
            max_sal = job.salary_rules.get("max_salary")
            if min_sal is not None:
                salaries.append(min_sal)
            elif max_sal is not None:
                salaries.append(max_sal)
                
    avg_salary = sum(salaries) / len(salaries) if salaries else 0.0
    
    return {
        "total_jobs": total_jobs,
        "status_counts": {
            "draft": draft_count,
            "published": published_count,
            "closed": closed_count
        },
        "total_openings_active": total_openings,
        "location_distribution": locations,
        "average_salary_published": round(avg_salary, 2)
    }


# ==========================================
# 5. Candidate Match Scoring
# ==========================================

def calculate_match_score(db: Session, job: Job, candidate_id: int) -> int:
    """
    Calculates a 0-100% Match Score based on:
    - Skills (50%)
    - Experience (30%)
    - Education (20%)
    """
    score = 0

    # 1. Skills Match (50%)
    from modules.candidate.skills.model import CandidateSkill
    cand_skills_db = db.query(CandidateSkill).filter(CandidateSkill.user_id == candidate_id).all()
    cand_skills = {s.skill_name.lower().strip() for s in cand_skills_db if s.skill_name}

    job_req_skills = {s.lower().strip() for s in job.required_skills} if job.required_skills else set()
    job_pref_skills = {s.lower().strip() for s in job.preferred_skills} if job.preferred_skills else set()
    
    total_skills = len(job_req_skills) + len(job_pref_skills)
    if total_skills > 0:
        matched_req = len(job_req_skills.intersection(cand_skills))
        matched_pref = len(job_pref_skills.intersection(cand_skills))
        
        # Required skills are weighted more
        req_weight = (matched_req / len(job_req_skills)) * 40 if job_req_skills else 0
        pref_weight = (matched_pref / len(job_pref_skills)) * 10 if job_pref_skills else 0
        score += min(50, req_weight + pref_weight)
    else:
        score += 50 # If no skills required, full marks for skills

    # 2. Experience Match (30%)
    from modules.candidate.experience.model import CandidateExperience
    cand_exp = db.query(CandidateExperience).filter(CandidateExperience.user_id == candidate_id).all()
    # Simple logic: if candidate has any experience, give some points. If job req is 0, full points.
    min_exp_req = job.eligibility_rules.get("min_experience_years", 0) if isinstance(job.eligibility_rules, dict) else getattr(job.eligibility_rules, 'min_experience_years', 0)
    
    if min_exp_req == 0:
        score += 30
    else:
        total_months = 0
        for exp in cand_exp:
            if exp.start_date and exp.end_date:
                diff = exp.end_date - exp.start_date
                total_months += diff.days / 30
        
        years_exp = total_months / 12
        if years_exp >= min_exp_req:
            score += 30
        elif years_exp > 0:
            score += int((years_exp / min_exp_req) * 30)

    # 3. Education Match (20%)
    from modules.candidate.education.model import CandidateEducation
    cand_edu = db.query(CandidateEducation).filter(CandidateEducation.user_id == candidate_id).all()
    
    allowed_degrees = job.eligibility_rules.get("allowed_degrees", []) if isinstance(job.eligibility_rules, dict) else getattr(job.eligibility_rules, 'allowed_degrees', [])
    allowed_degrees_lower = {d.lower().strip() for d in allowed_degrees}
    
    if not allowed_degrees_lower:
        score += 20
    else:
        cand_degrees = {e.degree.lower().strip() for e in cand_edu if e.degree}
        if cand_degrees.intersection(allowed_degrees_lower):
            score += 20
        elif cand_degrees:
            # Has education but maybe not exact match, give partial
            score += 10

    return int(min(100, score))
