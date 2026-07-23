import datetime
import random
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Dict, Any, List
from fastapi import HTTPException

from modules.coding_assessment.models import (
    CodingAttempt,
    CodingSubmission,
    CodingResult,
    CodingAttemptQuestion
)
from modules.coding_assessment.question_loader import QuestionLoader
from modules.coding_assessment.evaluator import Evaluator

def parse_test_cases(tc_str: str) -> List[Dict[str, str]]:
    """Helper to parse Excel multi-line test cases in LHS -> RHS format."""
    cases = []
    if not tc_str:
        return cases
    lines = [line.strip() for line in tc_str.split('\n') if line.strip()]
    for line in lines:
        if ' -> ' in line:
            lhs, rhs = line.split(' -> ', 1)
            cases.append({
                'lhs': lhs.strip(),
                'rhs': rhs.strip()
            })
    return cases

class CodingAssessmentLogic:
    @classmethod
    def start_attempt(cls, candidate_id: int, db: Session) -> Dict[str, Any]:
        """Starts a new coding assessment attempt or resumes an active one."""
        # 1. Check for active attempts
        active_attempt = db.query(CodingAttempt).filter(
            CodingAttempt.candidate_id == candidate_id,
            CodingAttempt.status == "IN_PROGRESS"
        ).first()

        if active_attempt:
            # Check if time has expired
            elapsed = (datetime.datetime.utcnow() - active_attempt.start_time).total_seconds()
            limit = active_attempt.duration * 60
            if elapsed >= limit:
                # Auto-finalize expired attempt
                cls.finish_attempt(active_attempt.id, db)
                raise HTTPException(
                    status_code=400,
                    detail="Your coding assessment attempt has expired and has been automatically finalized."
                )
            
            # Resume existing attempt
            q_mappings = db.query(CodingAttemptQuestion).filter(
                CodingAttemptQuestion.attempt_id == active_attempt.id
            ).order_by(CodingAttemptQuestion.order_index).all()
            
            questions = []
            for q_map in q_mappings:
                questions.append(cls._get_public_question_details(q_map.question_id, db, active_attempt.id))

            remaining = int(limit - elapsed)
            return {
                "attempt_id": active_attempt.id,
                "duration": active_attempt.duration,
                "remaining_seconds": remaining,
                "questions": questions,
                "status": "IN_PROGRESS"
            }

        # 2. Check if candidate has already completed an attempt
        completed_result = db.query(CodingResult).filter(
            CodingResult.candidate_id == candidate_id
        ).first()
        if completed_result:
            raise HTTPException(
                status_code=400,
                detail="You have already completed your coding assessment attempt. Only one attempt is allowed."
            )

        # 3. Generate randomized set: 2 Easy, 2 Medium, 1 Hard
        grouped = QuestionLoader.get_grouped()
        if len(grouped.get('Easy', [])) < 2 or len(grouped.get('Medium', [])) < 2 or len(grouped.get('Hard', [])) < 1:
            raise HTTPException(
                status_code=500,
                detail="Insufficient coding questions in the question bank to generate assessment."
            )

        selected_easy = random.sample(grouped['Easy'], 2)
        selected_medium = random.sample(grouped['Medium'], 2)
        selected_hard = random.sample(grouped['Hard'], 1)
        selected_all = selected_easy + selected_medium + selected_hard
        
        # Randomize question order
        random.shuffle(selected_all)

        # 4. Save Attempt
        new_attempt = CodingAttempt(
            candidate_id=candidate_id,
            start_time=datetime.datetime.utcnow(),
            duration=60,  # 60 minutes
            status="IN_PROGRESS"
        )
        db.add(new_attempt)
        db.flush()  # Populates new_attempt.id

        # Save question mappings
        for index, q in enumerate(selected_all):
            q_map = CodingAttemptQuestion(
                attempt_id=new_attempt.id,
                question_id=q['question_id'],
                order_index=index
            )
            db.add(q_map)
        
        db.commit()

        # Build response questions list
        questions = []
        for q in selected_all:
            questions.append(cls._get_public_question_details(q['question_id'], db, new_attempt.id))

        return {
            "attempt_id": new_attempt.id,
            "duration": new_attempt.duration,
            "remaining_seconds": new_attempt.duration * 60,
            "questions": questions,
            "status": "IN_PROGRESS"
        }

    @classmethod
    def _get_public_question_details(cls, question_id: int, db: Session, attempt_id: int) -> Dict[str, Any]:
        """Fetch question info and append user's saved source code template if existing."""
        q = QuestionLoader.get_by_id(question_id)
        
        # Check if they have a saved submission for this question
        sub = db.query(CodingSubmission).filter(
            CodingSubmission.attempt_id == attempt_id,
            CodingSubmission.question_id == question_id
        ).order_by(desc(CodingSubmission.created_at)).first()

        saved_code = sub.source_code if sub else q['template']
        submitted = (sub is not None)
        score = sub.score if sub else None

        return {
            "question_id": q['question_id'],
            "title": q['Title'],
            "difficulty": q['Difficulty'],
            "category": q['Category'],
            "problem_statement": q['Problem Statement'],
            "constraints": q['Constraints'],
            "sample_input": q['Sample Input'],
            "sample_output": q['Sample Output'],
            "marks": q['Marks'],
            "template": saved_code,
            "submitted": submitted,
            "score": score
        }

    @classmethod
    def run_candidate_code(cls, attempt_id: int, question_id: int, source_code: str, language: str, db: Session) -> Dict[str, Any]:
        """Runs the code against the public test cases."""
        attempt = db.query(CodingAttempt).filter(CodingAttempt.id == attempt_id).first()
        if not attempt or attempt.status != "IN_PROGRESS":
            raise HTTPException(status_code=400, detail="No active attempt in progress.")

        q = QuestionLoader.get_by_id(question_id)
        
        # Save/update submission draft in database so code is never lost
        sub = db.query(CodingSubmission).filter(
            CodingSubmission.attempt_id == attempt_id,
            CodingSubmission.question_id == question_id
        ).first()
        if sub:
            sub.source_code = source_code
            sub.created_at = datetime.datetime.utcnow()
        else:
            sub = CodingSubmission(
                attempt_id=attempt_id,
                candidate_id=attempt.candidate_id,
                question_id=question_id,
                source_code=source_code,
                language=language,
                passed_test_cases=0,
                total_test_cases=0,
                score=0.0
            )
            db.add(sub)
        db.commit()

        public_test_cases = parse_test_cases(q['Test Cases'])
        if not public_test_cases:
            # Fallback to sample input if no test cases defined
            public_test_cases = [{'lhs': q['Sample Input'], 'rhs': q['Sample Output']}]

        # Run code against public test cases
        eval_result = Evaluator.run_code(source_code, public_test_cases, category=q.get('Category', ''))
        return eval_result

    @classmethod
    def submit_candidate_solution(cls, attempt_id: int, question_id: int, source_code: str, language: str, db: Session) -> Dict[str, Any]:
        """Submits code, runs against all test cases, and stores the submission."""
        attempt = db.query(CodingAttempt).filter(CodingAttempt.id == attempt_id).first()
        if not attempt or attempt.status != "IN_PROGRESS":
            raise HTTPException(status_code=400, detail="No active attempt in progress.")

        q = QuestionLoader.get_by_id(question_id)
        
        # Combine public and hidden test cases
        public_cases = parse_test_cases(q['Test Cases'])
        hidden_cases = parse_test_cases(q['Hidden Test Cases'])
        all_cases = public_cases + hidden_cases
        if not all_cases:
            all_cases = [{'lhs': q['Sample Input'], 'rhs': q['Sample Output']}]

        # Evaluate code
        eval_result = Evaluator.run_code(source_code, all_cases, category=q.get('Category', ''))
        
        passed = 0
        total = len(all_cases)
        results = []

        if eval_result.get("status") == "SUCCESS":
            for tc_res in eval_result.get("results", []):
                passed += 1 if tc_res.get("passed") else 0
                results.append(tc_res)
        
        score = (passed / total * 100.0) if total > 0 else 0.0

        # Save or update submission in database
        sub = db.query(CodingSubmission).filter(
            CodingSubmission.attempt_id == attempt_id,
            CodingSubmission.question_id == question_id
        ).first()

        if sub:
            sub.source_code = source_code
            sub.passed_test_cases = passed
            sub.total_test_cases = total
            sub.score = score
            sub.created_at = datetime.datetime.utcnow()
        else:
            sub = CodingSubmission(
                attempt_id=attempt_id,
                candidate_id=attempt.candidate_id,
                question_id=question_id,
                source_code=source_code,
                language=language,
                passed_test_cases=passed,
                total_test_cases=total,
                score=score
            )
            db.add(sub)
        
        db.commit()

        return {
            "passed_test_cases": passed,
            "total_test_cases": total,
            "score": score,
            "results": results,
            "stdout": eval_result.get("stdout", "")
        }

    @classmethod
    def finish_attempt(cls, attempt_id: int, db: Session, is_terminated: bool = False) -> Dict[str, Any]:
        """Finalizes the assessment and computes the candidate results."""
        attempt = db.query(CodingAttempt).filter(CodingAttempt.id == attempt_id).first()
        if not attempt:
            raise HTTPException(status_code=404, detail="Attempt not found.")
            
        if attempt.status != "IN_PROGRESS":
            # Already completed
            res = db.query(CodingResult).filter(CodingResult.attempt_id == attempt_id).first()
            if res:
                return res
            raise HTTPException(status_code=400, detail="Attempt is already finalized.")

        # Update attempt status
        if is_terminated:
            attempt.status = "TERMINATED"
        else:
            attempt.status = "COMPLETED"
        attempt.end_time = datetime.datetime.utcnow()

        # Get questions associated with this attempt
        q_mappings = db.query(CodingAttemptQuestion).filter(
            CodingAttemptQuestion.attempt_id == attempt_id
        ).all()
        
        questions_solved = 0
        questions_attempted = 0
        
        # Difficulty splits: Easy, Medium, Hard
        easy_scores = []
        medium_scores = []
        hard_scores = []
        
        total_passed = 0
        total_test_cases = 0

        for q_map in q_mappings:
            q = QuestionLoader.get_by_id(q_map.question_id)
            diff = q['Difficulty']
            
            # Fetch candidate's submission
            sub = db.query(CodingSubmission).filter(
                CodingSubmission.attempt_id == attempt_id,
                CodingSubmission.question_id == q_map.question_id
            ).first()

            if sub:
                score = sub.score
                questions_attempted += 1
                if sub.passed_test_cases == sub.total_test_cases and sub.total_test_cases > 0:
                    questions_solved += 1
                total_passed += sub.passed_test_cases
                total_test_cases += sub.total_test_cases
            else:
                score = 0.0
                # If they didn't submit anything, count total test cases of the question
                tc_count = len(parse_test_cases(q['Test Cases']) + parse_test_cases(q['Hidden Test Cases']))
                total_test_cases += tc_count if tc_count > 0 else 1

            if diff == 'Easy':
                easy_scores.append(score)
            elif diff == 'Medium':
                medium_scores.append(score)
            elif diff == 'Hard':
                hard_scores.append(score)

        # Average difficulty scores
        easy_avg = sum(easy_scores) / len(easy_scores) if easy_scores else 0.0
        medium_avg = sum(medium_scores) / len(medium_scores) if medium_scores else 0.0
        hard_avg = sum(hard_scores) / len(hard_scores) if hard_scores else 0.0

        # Overall coding score is the average score of all 5 questions
        overall_score = (easy_avg * 0.4) + (medium_avg * 0.4) + (hard_avg * 0.2)
        # Note: If we do a straight average: (easy_avg*2 + medium_avg*2 + hard_avg*1) / 5
        straight_avg = (sum(easy_scores) + sum(medium_scores) + sum(hard_scores)) / 5.0

        if is_terminated:
            total_score = 0.0
            status = "TERMINATED"
        else:
            total_score = straight_avg
            # Passing threshold: >= 60.0%
            status = "PASS" if total_score >= 60.0 else "FAIL"

        # Save to coding_results
        result = CodingResult(
            candidate_id=attempt.candidate_id,
            attempt_id=attempt_id,
            total_score=total_score,
            easy_score=easy_avg,
            medium_score=medium_avg,
            hard_score=hard_avg,
            questions_solved=questions_solved,
            questions_attempted=questions_attempted,
            status=status
        )
        db.add(result)
        
        # Save score on the attempt
        attempt.score = total_score
        
        # Update CandidateProfile with coding score and status
        from modules.candidate.profile.model import CandidateProfile
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == attempt.candidate_id).first()
        if profile:
            profile.coding_score = round(total_score, 2)
            profile.coding_status = status
            db.add(profile)

        db.commit()

        # Trigger Coding Assessment Result Email
        try:
            from modules.email_automation.triggers import trigger_email
            trigger_email(
                event_type="Coding Assessment Result",
                candidate_id=attempt.candidate_id,
                context={
                    "coding_score": int(total_score),
                    "extra_details": f"Result Status: {status} with score of {int(total_score)}%."
                },
                db=db
            )
        except Exception as e:
            print(f"Failed to trigger Coding Assessment Result email: {e}")

        return result

    @classmethod
    def get_latest_result(cls, candidate_id: int, db: Session) -> CodingResult:
        """Fetch latest coding result for candidate."""
        res = db.query(CodingResult).filter(
            CodingResult.candidate_id == candidate_id
        ).order_by(desc(CodingResult.created_at)).first()
        if not res:
            raise HTTPException(status_code=404, detail="No coding results found for this candidate.")
        return res
