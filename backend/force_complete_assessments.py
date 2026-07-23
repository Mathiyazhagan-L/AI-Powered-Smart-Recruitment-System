"""
Force-complete all assessments for a given user with score=100.
Usage: python force_complete_assessments.py
"""
import sys, os, datetime
sys.path.insert(0, '.')
from core.database import SessionLocal
from modules.auth.model import User

CANDIDATE_EMAIL = "ml7785792@gmail.com"

def run():
    db = SessionLocal()

    # ── Resolve user ──────────────────────────────────────────────────────────
    user = db.query(User).filter(User.email == CANDIDATE_EMAIL).first()
    if not user:
        print(f"[ERROR] User {CANDIDATE_EMAIL} not found."); db.close(); return
    uid = user.id
    print(f"[INFO] Found user: id={uid} email={user.email}")

    # ── 1. Aptitude ───────────────────────────────────────────────────────────
    from modules.assessment.models import AssessmentResult, AssessmentAttempt
    from modules.candidate.profile.model import CandidateProfile

    # Close any in-progress attempts
    db.query(AssessmentAttempt).filter(
        AssessmentAttempt.candidate_id == uid,
        AssessmentAttempt.status == "IN_PROGRESS"
    ).update({"status": "COMPLETED"})

    result = db.query(AssessmentResult).filter(AssessmentResult.candidate_id == uid).first()
    if result:
        result.aptitude_score = 100.0
        result.status = "PASSED"
        result.created_at = datetime.datetime.utcnow()
    else:
        result = AssessmentResult(
            candidate_id=uid,
            aptitude_score=100.0,
            status="PASSED",
            created_at=datetime.datetime.utcnow()
        )
        db.add(result)
    print("[OK] Aptitude → PASSED (100%)")

    # Update profile
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == uid).first()
    if profile:
        profile.aptitude_score = 100.0
        profile.assessment_status = "PASSED"

    # ── 2. Coding ─────────────────────────────────────────────────────────────
    from modules.coding_assessment.models import CodingResult, CodingAttempt

    db.query(CodingAttempt).filter(
        CodingAttempt.candidate_id == uid,
        CodingAttempt.status == "IN_PROGRESS"
    ).update({"status": "COMPLETED"})

    coding_result = db.query(CodingResult).filter(CodingResult.candidate_id == uid).first()
    if coding_result:
        coding_result.total_score = 100.0
        coding_result.questions_solved = 5
        coding_result.status = "PASSED"
        coding_result.created_at = datetime.datetime.utcnow()
    else:
        coding_result = CodingResult(
            candidate_id=uid,
            total_score=100.0,
            questions_solved=5,
            status="PASSED",
            created_at=datetime.datetime.utcnow()
        )
        db.add(coding_result)
    print("[OK] Coding → PASSED (100%)")

    # No coding_score/coding_status column on CandidateProfile — skip

    # ── 3. Interview ──────────────────────────────────────────────────────────
    from modules.interview_assessment.models import InterviewResult, InterviewSession

    db.query(InterviewSession).filter(
        InterviewSession.candidate_id == uid,
        InterviewSession.status == "IN_PROGRESS"
    ).update({"status": "COMPLETED"})

    interview_result = db.query(InterviewResult).filter(InterviewResult.candidate_id == uid).first()
    if interview_result:
        interview_result.total_score = 100.0
        interview_result.communication_score = 25.0
        interview_result.technical_score = 40.0
        interview_result.confidence_score = 20.0
        interview_result.professionalism_score = 15.0
        interview_result.grade = "A"
        interview_result.hiring_recommendation = "Strong Hire"
        interview_result.created_at = datetime.datetime.utcnow()
    else:
        interview_result = InterviewResult(
            candidate_id=uid,
            total_score=100.0,
            communication_score=25.0,
            technical_score=40.0,
            confidence_score=20.0,
            professionalism_score=15.0,
            grade="A",
            hiring_recommendation="Strong Hire",
            created_at=datetime.datetime.utcnow()
        )
        db.add(interview_result)
    print("[OK] Interview → COMPLETED, Grade=A, 100%")

    if profile:
        profile.interview_score = 100.0
        profile.interview_status = "COMPLETED"

    # ── Commit ────────────────────────────────────────────────────────────────
    db.commit()
    db.close()
    print("\n[DONE] All assessments marked complete with score=100 for user", CANDIDATE_EMAIL)

if __name__ == "__main__":
    run()
