import json
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from modules.interview_assessment.interview_manager import InterviewManager
from modules.interview_assessment.models import InterviewQuestion, InterviewResult, InterviewSession, InterviewAnswer
from modules.candidate.profile.model import CandidateProfile

logger = logging.getLogger(__name__)

class InterviewAssessmentLogic:

    @classmethod
    def start_interview(cls, candidate_id: int, db: Session) -> dict:
        """Starts or resumes an interview session for the candidate."""
        try:
            return InterviewManager.start_session(candidate_id, db)
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error starting interview for candidate {candidate_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start interview: {str(e)}"
            )

    @classmethod
    def get_question_details(cls, session_id: int, question_id: int, db: Session) -> dict:
        """Gets details for a specific interview question."""
        question = db.query(InterviewQuestion).filter(
            InterviewQuestion.id == question_id,
            InterviewQuestion.session_id == session_id
        ).first()

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview question not found."
            )

        # Count total questions in session
        total_questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == session_id
        ).count()

        return {
            "question_id": question.id,
            "question_text": question.question_text,
            "category": question.category,
            "order_index": question.order_index,
            "total_questions": total_questions
        }

    @classmethod
    def submit_answer(cls, session_id: int, question_id: int, audio_file_path: str, db: Session, speech_text: str = None) -> dict:
        """Transcribes candidate audio and saves the answer record."""
        try:
            ans = InterviewManager.save_answer(session_id, question_id, audio_file_path, db, speech_text=speech_text)
            return {
                "transcript": ans.transcript or "",
                "question_id": ans.question_id,
                "session_id": ans.session_id
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error submitting answer: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to submit answer: {str(e)}"
            )

    @classmethod
    def evaluate_answer(cls, session_id: int, question_id: int, db: Session) -> dict:
        """Evaluates candidate response and returns the dimension scores."""
        try:
            ans = InterviewManager.evaluate_answer_record(session_id, question_id, db)
            
            feedback = {}
            if ans.evaluation_feedback:
                try:
                    feedback = json.loads(ans.evaluation_feedback)
                except Exception:
                    pass

            return {
                "session_id": ans.session_id,
                "question_id": ans.question_id,
                "communication_score": ans.communication_score or 0.0,
                "technical_score": ans.technical_score or 0.0,
                "confidence_score": ans.confidence_score or 0.0,
                "professionalism_score": ans.professionalism_score or 0.0,
                "score": ans.score or 0.0,
                "feedback": feedback
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to evaluate answer: {str(e)}"
            )

    @classmethod
    def finalize_interview(cls, session_id: int, db: Session) -> dict:
        """Finalizes the session and computes overall scores and feedback report."""
        try:
            res = InterviewManager.finalize_session(session_id, db)
            
            # Trigger Interview Result Email
            try:
                from modules.email_automation.triggers import trigger_email
                trigger_email(
                    event_type="Interview Result",
                    candidate_id=res.candidate_id,
                    context={
                        "interview_score": int(res.total_score),
                        "interview_status": "COMPLETED",
                        "extra_details": f"Result Grade: {res.grade} with recommendation: {res.hiring_recommendation}."
                    },
                    db=db
                )
            except Exception as e:
                logger.error(f"Failed to trigger Interview Result email: {e}")
            return cls._format_result(res, db)
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"Error finalizing interview session {session_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to finalize interview: {str(e)}"
            )

    @classmethod
    def get_latest_result(cls, candidate_id: int, db: Session) -> dict:
        """Retrieves the final results for the candidate."""
        res = db.query(InterviewResult).filter(
            InterviewResult.candidate_id == candidate_id
        ).order_by(InterviewResult.created_at.desc()).first()

        if not res:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview result not found for candidate."
            )
            
        return cls._format_result(res, db)

    @classmethod
    def _format_result(cls, res: InterviewResult, db: Session) -> dict:
        """Formats InterviewResult model into JSON-compliant dictionary."""
        strengths = []
        weaknesses = []
        suggestions = []

        if res.strengths:
            try:
                strengths = json.loads(res.strengths)
            except Exception:
                strengths = [res.strengths]
        if res.weaknesses:
            try:
                weaknesses = json.loads(res.weaknesses)
            except Exception:
                weaknesses = [res.weaknesses]
        if res.suggestions:
            try:
                suggestions = json.loads(res.suggestions)
            except Exception:
                suggestions = [res.suggestions]

        # Fetch questions and answers to show the candidate what they said
        questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == res.session_id
        ).order_by(InterviewQuestion.order_index).all()
        answers = db.query(InterviewAnswer).filter(
            InterviewAnswer.session_id == res.session_id
        ).all()
        answer_map = {ans.question_id: ans for ans in answers}

        qa_list = []
        for q in questions:
            ans = answer_map.get(q.id)
            qa_list.append({
                "question_text": q.question_text,
                "category": q.category,
                "transcript": ans.transcript if ans else "[No response submitted]"
            })

        return {
            "candidate_id": res.candidate_id,
            "session_id": res.session_id,
            "communication_score": res.communication_score,
            "technical_score": res.technical_score,
            "confidence_score": res.confidence_score,
            "professionalism_score": res.professionalism_score,
            "total_score": res.total_score,
            "grade": res.grade,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "suggestions": suggestions,
            "hiring_recommendation": res.hiring_recommendation,
            "detailed_report": res.detailed_report,
            "created_at": res.created_at,
            "questions_answers": qa_list
        }

    @classmethod
    def reset_interview(cls, candidate_id: int, db: Session) -> dict:
        """Deletes all interview sessions, questions, answers, and results for the candidate."""
        try:
            # 1. Get all session IDs for the candidate
            sessions = db.query(InterviewSession).filter(
                InterviewSession.candidate_id == candidate_id
            ).all()
            session_ids = [s.id for s in sessions]

            if session_ids:
                # Delete answers
                db.query(InterviewAnswer).filter(
                    InterviewAnswer.session_id.in_(session_ids)
                ).delete(synchronize_session=False)

                # Delete questions
                db.query(InterviewQuestion).filter(
                    InterviewQuestion.session_id.in_(session_ids)
                ).delete(synchronize_session=False)

                # Delete results
                db.query(InterviewResult).filter(
                    InterviewResult.session_id.in_(session_ids)
                ).delete(synchronize_session=False)

                # Delete sessions
                db.query(InterviewSession).filter(
                    InterviewSession.id.in_(session_ids)
                ).delete(synchronize_session=False)

            # Also ensure any lingering results for this candidate are deleted
            db.query(InterviewResult).filter(
                InterviewResult.candidate_id == candidate_id
            ).delete(synchronize_session=False)

            # 2. Reset CandidateProfile fields
            profile = db.query(CandidateProfile).filter(
                CandidateProfile.user_id == candidate_id
            ).first()
            if profile:
                profile.interview_score = None
                profile.interview_date = None
                profile.interview_status = None
                db.add(profile)

            db.commit()
            return {"status": "success", "message": "Interview session and results reset successfully."}
        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting interview for candidate {candidate_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to reset interview: {str(e)}"
            )

    @classmethod
    def submit_professional_assessment(cls, candidate_id: int, answers: list, db: Session) -> dict:
        """Submits and evaluates all professional assessment answers at once using Groq API."""
        session = db.query(InterviewSession).filter(
            InterviewSession.candidate_id == candidate_id,
            InterviewSession.status == "IN_PROGRESS"
        ).first()
        
        if not session:
            raise HTTPException(status_code=400, detail="No active assessment session found.")
            
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session.id).all()
        q_map = {q.id: q.question_text for q in questions}
        
        # Build prompt
        qa_pairs = []
        for ans in answers:
            q_text = q_map.get(ans.question_id, "Unknown Question")
            qa_pairs.append(f"Q: {q_text}\nA: {ans.answer_text}")
            
            # Save to db
            answer_record = InterviewAnswer(
                session_id=session.id,
                question_id=ans.question_id,
                transcript=ans.answer_text
            )
            db.add(answer_record)
            
        db.commit()
        
        from modules.interview_assessment.grok_evaluator import evaluate_professional_assessment
        result_json = evaluate_professional_assessment(qa_pairs)
        
        total_score = result_json.get("overall_score", 0)
        grade = "A" if total_score >= 90 else "B" if total_score >= 80 else "C" if total_score >= 70 else "D" if total_score >= 60 else "F"
        
        result_record = InterviewResult(
            candidate_id=candidate_id,
            session_id=session.id,
            communication_score=result_json.get("metrics", {}).get("Communication", 0),
            technical_score=result_json.get("metrics", {}).get("Technical Understanding", 0),
            confidence_score=0,
            professionalism_score=result_json.get("metrics", {}).get("Professional Reasoning", 0),
            total_score=total_score,
            grade=grade,
            strengths=json.dumps(result_json.get("strengths", [])),
            weaknesses=json.dumps(result_json.get("weaknesses", [])),
            suggestions=json.dumps(result_json.get("improvement_suggestions", [])),
            hiring_recommendation=result_json.get("final_recommendation", "Needs Review"),
            detailed_report=json.dumps(result_json)
        )
        db.add(result_record)
        
        session.status = "COMPLETED"
        
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
        if profile:
            profile.interview_score = total_score
            profile.interview_status = "COMPLETED"
            
        db.commit()
        
        return {
            "message": "Assessment evaluated successfully",
            "total_score": total_score,
            "grade": grade,
            "hiring_recommendation": result_record.hiring_recommendation,
            "strengths": result_json.get("strengths", []),
            "weaknesses": result_json.get("weaknesses", []),
            "suggestions": result_json.get("improvement_suggestions", [])
        }
