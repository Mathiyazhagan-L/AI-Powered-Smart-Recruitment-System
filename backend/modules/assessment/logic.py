import os
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import random

from .models import (
    AssessmentQuestion,
    AssessmentAttempt,
    AssessmentQuestionMap,
    AssessmentAnswer,
    AssessmentResult
)
from modules.candidate.profile.model import CandidateProfile
from modules.auth.model import User

def ensure_questions_imported(db: Session):
    """Checks if the questions table is populated. If not, reads Excel sheets and populates it."""
    count = db.query(AssessmentQuestion).count()
    if count > 0:
        return

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "question_bank", "aptitude"))
    categories = {
        "quantitative": ["Quantitative_questions.xlsx"],
        "logical": ["Logical_questions.xlsx"],
        "verbal": ["Verbal_questions.xlsx"],
        "analytical_reasoning": ["Analytical_Reasoning.xlsx"],
        "computer_fundamentals": ["Computer_Fundamentals.xlsx"]
    }

    print(f"Importer: Loading questions from Excel bank in {base_dir}...")
    for cat_key, filenames in categories.items():
        file_path = None
        for filename in filenames:
            temp_path = os.path.join(base_dir, filename)
            if os.path.exists(temp_path):
                file_path = temp_path
                break
        if not file_path:
            raise FileNotFoundError(f"Question sheet for category '{cat_key}' not found in {base_dir}")

        df = pd.read_excel(file_path)
        for index, row in df.iterrows():
            question_text = str(row.get("Question", "")).strip()
            if not question_text or question_text.lower() == "nan":
                continue

            option_a = str(row.get("Option A", row.get("OptionA", ""))).strip()
            option_b = str(row.get("Option B", row.get("OptionB", ""))).strip()
            option_c = str(row.get("Option C", row.get("OptionC", ""))).strip()
            option_d = str(row.get("Option D", row.get("OptionD", ""))).strip()
            correct_ans = str(row.get("Correct Answer", row.get("CorrectAnswer", ""))).strip().upper()
            
            # Normalize correct answer to key letter (A, B, C, or D)
            norm_correct = correct_ans
            if correct_ans == "OPTIONA" or correct_ans == "OPTION A":
                norm_correct = "A"
            elif correct_ans == "OPTIONB" or correct_ans == "OPTION B":
                norm_correct = "B"
            elif correct_ans == "OPTIONC" or correct_ans == "OPTION C":
                norm_correct = "C"
            elif correct_ans == "OPTIOND" or correct_ans == "OPTION D":
                norm_correct = "D"
            elif correct_ans == option_a.upper():
                norm_correct = "A"
            elif correct_ans == option_b.upper():
                norm_correct = "B"
            elif correct_ans == option_c.upper():
                norm_correct = "C"
            elif correct_ans == option_d.upper():
                norm_correct = "D"
            
            if norm_correct not in ("A", "B", "C", "D"):
                if len(norm_correct) > 10:
                    norm_correct = norm_correct[:10]

            subcat = str(row.get("Subcategory", row.get("Sub Category", row.get("SubCategory", "")))).strip()
            if not subcat or subcat.lower() == "nan":
                subcat = None
            diff = str(row.get("Difficulty", "Medium")).strip()
            exp = str(row.get("Explanation", "")).strip()
            if not exp or exp.lower() == "nan":
                exp = None
            
            try:
                marks = int(row.get("Mark", row.get("Marks", 2)))
            except Exception:
                marks = 2

            q = AssessmentQuestion(
                category=cat_key,
                subcategory=subcat,
                difficulty=diff,
                question_text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_answer=norm_correct,
                explanation=exp,
                marks=marks
            )
            db.add(q)
        db.commit()
    print("Importer: Question bank loaded successfully!")


def evaluate_and_close_attempt(attempt: AssessmentAttempt, db: Session, is_timeout: bool = False, is_terminated: bool = False) -> dict:
    """Closes an active attempt, grades it, writes the result record, and updates the candidate's profile."""
    # Check if attempt is already closed
    if attempt.status in ("PASSED", "FAILED", "TERMINATED"):
        result = db.query(AssessmentResult).filter(AssessmentResult.attempt_id == attempt.id).first()
        if result:
            return {
                "score": result.aptitude_score,
                "correct": result.total_correct,
                "wrong": result.total_wrong,
                "status": result.status
            }
        return {
            "score": attempt.score or 0.0,
            "correct": 0,
            "wrong": 25,
            "status": attempt.status
        }

    # Retrieve all saved answers
    answers = db.query(AssessmentAnswer).filter(AssessmentAnswer.attempt_id == attempt.id).all()
    ans_dict = {a.question_id: a for a in answers}

    # Section counts and scores
    categories = ["quantitative", "logical", "verbal", "analytical_reasoning", "computer_fundamentals"]
    cat_correct = {cat: 0 for cat in categories}
    cat_total = {cat: 0 for cat in categories}

    total_correct = 0
    total_wrong = 0

    # Process all mapped questions
    mapped = db.query(AssessmentQuestionMap).filter(AssessmentQuestionMap.attempt_id == attempt.id).all()
    
    for m in mapped:
        if m.category in cat_total:
            cat_total[m.category] += 1
            ans = ans_dict.get(m.question_id)
            if ans and ans.selected_answer and ans.selected_answer == ans.correct_answer:
                ans.is_correct = True
                cat_correct[m.category] += 1
                total_correct += 1
            else:
                if ans:
                    ans.is_correct = False
                total_wrong += 1

    total_questions = len(mapped) if len(mapped) > 0 else 25
    overall_score = (total_correct / total_questions) * 100.0

    # Calculate section percentages
    sec_scores = {}
    for cat in categories:
        total_sec = cat_total[cat]
        correct_sec = cat_correct[cat]
        sec_scores[cat] = (correct_sec / total_sec * 100.0) if total_sec > 0 else 0.0

    # Determine status
    if is_terminated or attempt.integrity_score <= 0:
        status = "TERMINATED"
        overall_score = 0.0  # Reset overall score for terminal integrity breaches
    else:
        status = "PASSED" if overall_score >= 50.0 else "FAILED"

    # Close the attempt
    attempt.end_time = datetime.utcnow()
    attempt.score = overall_score
    attempt.status = status
    db.add(attempt)

    # Save to assessment_results
    result = AssessmentResult(
        candidate_id=attempt.candidate_id,
        attempt_id=attempt.id,
        aptitude_score=overall_score,
        quantitative_score=sec_scores["quantitative"],
        logical_score=sec_scores["logical"],
        verbal_score=sec_scores["verbal"],
        analytical_reasoning_score=sec_scores["analytical_reasoning"],
        computer_fundamentals_score=sec_scores["computer_fundamentals"],
        total_correct=total_correct,
        total_wrong=total_wrong,
        status=status
    )
    db.add(result)

    # Save or update candidate profile
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == attempt.candidate_id).first()
    if not profile:
        # Automatically create basic profile
        user = db.query(User).filter(User.id == attempt.candidate_id).first()
        email = user.email if user else f"candidate_{attempt.candidate_id}@aihire.local"
        fullname = user.full_name if user else "Candidate"
        profile = CandidateProfile(
            user_id=attempt.candidate_id,
            full_name=fullname,
            email=email,
            profile_completion=10
        )
        db.add(profile)
        db.flush()

    profile.aptitude_score = int(overall_score)
    profile.assessment_date = datetime.utcnow()
    profile.assessment_status = status
    db.add(profile)

    db.commit()

    # Trigger Aptitude Assessment Result Email
    try:
        from modules.email_automation.triggers import trigger_email
        trigger_email(
            event_type="Aptitude Assessment Result",
            candidate_id=attempt.candidate_id,
            context={
                "aptitude_score": int(overall_score),
                "extra_details": f"Result Status: {status} with score of {int(overall_score)}%."
            },
            db=db
        )
    except Exception as e:
        print(f"Failed to trigger Aptitude Assessment Result email: {e}")

    return {
        "score": overall_score,
        "correct": total_correct,
        "wrong": total_wrong,
        "status": status
    }


def generate_assessment(candidate_id: int, db: Session) -> dict:
    """Prepares or resumes an assessment for the candidate. Restricts to exactly one completed attempt."""
    ensure_questions_imported(db)

    # Retrieve candidate attempts
    existing = db.query(AssessmentAttempt).filter(
        AssessmentAttempt.candidate_id == candidate_id
    ).order_by(AssessmentAttempt.created_at.desc()).all()

    if existing:
        latest = existing[0]
        if latest.status in ("PASSED", "FAILED", "TERMINATED"):
            raise ValueError("You have already completed your aptitude assessment. Only one attempt is allowed.")
        
        # Check active attempt for timeout
        elapsed = datetime.utcnow() - latest.start_time
        time_limit = timedelta(minutes=latest.duration)
        if elapsed < time_limit:
            # Active and valid - Resume!
            remaining_seconds = int((time_limit - elapsed).total_seconds())
            
            # Fetch mapped questions
            mapped = db.query(AssessmentQuestionMap).filter(
                AssessmentQuestionMap.attempt_id == latest.id
            ).all()
            q_ids = [m.question_id for m in mapped]
            questions = db.query(AssessmentQuestion).filter(AssessmentQuestion.id.in_(q_ids)).all()
            
            q_map = {q.id: q for q in questions}
            sorted_questions = []
            for m in mapped:
                q = q_map.get(m.question_id)
                if q:
                    sorted_questions.append(q)

            # Fetch existing answers to pre-populate selected option
            answers = db.query(AssessmentAnswer).filter(
                AssessmentAnswer.attempt_id == latest.id
            ).all()
            ans_map = {a.question_id: a.selected_answer for a in answers}

            questions_data = []
            for q in sorted_questions:
                questions_data.append({
                    "question_id": q.id,
                    "question": q.question_text,
                    "options": {
                        "A": q.option_a,
                        "B": q.option_b,
                        "C": q.option_c,
                        "D": q.option_d
                    },
                    "category": q.category,
                    "selected_answer": ans_map.get(q.id)
                })
            
            return {
                "attempt_id": latest.id,
                "duration": latest.duration,
                "remaining_seconds": remaining_seconds,
                "questions": questions_data,
                "status": "IN_PROGRESS"
            }
        else:
            # Attempt timed out - Grade and close it
            evaluate_and_close_attempt(latest, db, is_timeout=True)
            raise ValueError("Your previous assessment attempt has expired. No new attempts are allowed.")

    # Create new attempt
    attempt = AssessmentAttempt(
        candidate_id=candidate_id,
        start_time=datetime.utcnow(),
        duration=25,
        total_questions=25,
        integrity_score=100,
        status="IN_PROGRESS"
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    # Pick 5 random questions from each category
    categories = ["quantitative", "logical", "verbal", "analytical_reasoning", "computer_fundamentals"]
    selected = []
    
    for cat in categories:
        cat_qs = db.query(AssessmentQuestion).filter(AssessmentQuestion.category == cat).all()
        if len(cat_qs) < 5:
            raise ValueError(f"Insufficient questions in category '{cat}' (needed 5, got {len(cat_qs)})")
        picked = random.sample(cat_qs, 5)
        selected.extend(picked)

    # Shuffle the combined set
    random.shuffle(selected)

    # Map questions and initialize empty answers
    for q in selected:
        q_map = AssessmentQuestionMap(
            attempt_id=attempt.id,
            question_id=q.id,
            category=q.category
        )
        db.add(q_map)

        ans = AssessmentAnswer(
            attempt_id=attempt.id,
            question_id=q.id,
            category=q.category,
            selected_answer=None,
            correct_answer=q.correct_answer,
            is_correct=False
        )
        db.add(ans)

    db.commit()

    questions_data = []
    for q in selected:
        questions_data.append({
            "question_id": q.id,
            "question": q.question_text,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d
            },
            "category": q.category,
            "selected_answer": None
        })

    return {
        "attempt_id": attempt.id,
        "duration": attempt.duration,
        "remaining_seconds": attempt.duration * 60,
        "questions": questions_data,
        "status": "IN_PROGRESS"
    }


def save_answer(attempt_id: int, question_id: int, selected_answer: str, integrity_score: int, db: Session) -> bool:
    """Updates candidate answer in real-time. Manages tab violations and timeout status."""
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt:
        raise ValueError("Attempt not found")
    if attempt.status != "IN_PROGRESS":
        raise ValueError("Assessment is already submitted or closed")

    # Time expiration check
    elapsed = datetime.utcnow() - attempt.start_time
    time_limit = timedelta(minutes=attempt.duration)
    if elapsed >= time_limit:
        evaluate_and_close_attempt(attempt, db, is_timeout=True)
        raise ValueError("Assessment session has expired")

    # Sync integrity score
    if integrity_score is not None:
        attempt.integrity_score = integrity_score
        if integrity_score <= 0:
            evaluate_and_close_attempt(attempt, db, is_terminated=True)
            raise ValueError("Assessment terminated due to integrity policy violations")

    # Save answer sheet
    ans = db.query(AssessmentAnswer).filter(
        AssessmentAnswer.attempt_id == attempt_id,
        AssessmentAnswer.question_id == question_id
    ).first()

    if not ans:
        q = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == question_id).first()
        if not q:
            raise ValueError("Question not found")
        ans = AssessmentAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            category=q.category,
            correct_answer=q.correct_answer
        )
        db.add(ans)

    norm_ans = str(selected_answer).strip().upper() if selected_answer else None
    if norm_ans not in ("A", "B", "C", "D"):
        norm_ans = None

    ans.selected_answer = norm_ans
    ans.is_correct = (norm_ans == ans.correct_answer)
    db.commit()
    return True


def submit_assessment(attempt_id: int, answers_list: list, integrity_score: int, db: Session) -> dict:
    """Saves any final answers, evaluates scores, and closes the assessment."""
    attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
    if not attempt:
        raise ValueError("Attempt not found")
    
    if attempt.status in ("PASSED", "FAILED", "TERMINATED"):
        return evaluate_and_close_attempt(attempt, db)

    if integrity_score is not None:
        attempt.integrity_score = integrity_score

    # Save submitted answers
    for ans_data in answers_list:
        ans = db.query(AssessmentAnswer).filter(
            AssessmentAnswer.attempt_id == attempt_id,
            AssessmentAnswer.question_id == ans_data.question_id
        ).first()

        norm_ans = str(ans_data.selected_answer).strip().upper() if ans_data.selected_answer else None
        if norm_ans not in ("A", "B", "C", "D"):
            norm_ans = None

        if ans:
            ans.selected_answer = norm_ans
            ans.is_correct = (norm_ans == ans.correct_answer)
            db.add(ans)
        else:
            q = db.query(AssessmentQuestion).filter(AssessmentQuestion.id == ans_data.question_id).first()
            if q:
                ans = AssessmentAnswer(
                    attempt_id=attempt_id,
                    question_id=ans_data.question_id,
                    category=q.category,
                    selected_answer=norm_ans,
                    correct_answer=q.correct_answer,
                    is_correct=(norm_ans == q.correct_answer)
                )
                db.add(ans)

    db.commit()

    is_terminated = (attempt.integrity_score <= 0)
    return evaluate_and_close_attempt(attempt, db, is_terminated=is_terminated)


def get_latest_result(candidate_id: int, db: Session) -> AssessmentResult:
    """Fetches the latest completed result details for the candidate profile."""
    return db.query(AssessmentResult).filter(
        AssessmentResult.candidate_id == candidate_id
    ).order_by(AssessmentResult.created_at.desc()).first()


def reset_assessment(candidate_id: int, db: Session) -> dict:
    """Deletes all aptitude assessment attempts, question maps, answers, and results for the candidate."""
    from fastapi import HTTPException, status
    try:
        # 1. Get all attempt IDs for the candidate
        attempts = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.candidate_id == candidate_id
        ).all()
        attempt_ids = [a.id for a in attempts]

        if attempt_ids:
            # Delete answers
            db.query(AssessmentAnswer).filter(
                AssessmentAnswer.attempt_id.in_(attempt_ids)
            ).delete(synchronize_session=False)

            # Delete question map
            db.query(AssessmentQuestionMap).filter(
                AssessmentQuestionMap.attempt_id.in_(attempt_ids)
            ).delete(synchronize_session=False)

            # Delete attempts
            db.query(AssessmentAttempt).filter(
                AssessmentAttempt.id.in_(attempt_ids)
            ).delete(synchronize_session=False)

        # Ensure any lingering attempts/results are deleted
        db.query(AssessmentResult).filter(
            AssessmentResult.candidate_id == candidate_id
        ).delete(synchronize_session=False)

        # 2. Delete proctoring data for APTITUDE
        try:
            from modules.proctoring.models import AssessmentViolation, ProctoringLog, AssessmentIntegrityResult
            from modules.proctoring.session import registry
            
            # Remove from active proctoring registry
            registry.remove_session(candidate_id, "APTITUDE")

            db.query(AssessmentViolation).filter(
                AssessmentViolation.candidate_id == candidate_id,
                AssessmentViolation.assessment_type == "APTITUDE"
            ).delete(synchronize_session=False)

            db.query(ProctoringLog).filter(
                ProctoringLog.candidate_id == candidate_id,
                ProctoringLog.assessment_type == "APTITUDE"
            ).delete(synchronize_session=False)

            db.query(AssessmentIntegrityResult).filter(
                AssessmentIntegrityResult.candidate_id == candidate_id,
                AssessmentIntegrityResult.assessment_type == "APTITUDE"
            ).delete(synchronize_session=False)
        except Exception as pe:
            print(f"Error resetting proctoring data: {pe}")

        # 3. Reset CandidateProfile fields
        profile = db.query(CandidateProfile).filter(
            CandidateProfile.user_id == candidate_id
        ).first()
        if profile:
            profile.aptitude_score = None
            profile.assessment_date = None
            profile.assessment_status = None
            db.add(profile)

        db.commit()
        return {"status": "success", "message": "Aptitude assessment attempts and results reset successfully."}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset assessment: {str(e)}"
        )

