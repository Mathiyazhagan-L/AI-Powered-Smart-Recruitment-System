import os
import json
import logging
import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()



from modules.interview_assessment.models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewResult
)
from modules.interview_assessment.question_generator import generate_interview_questions
from modules.interview_assessment.speech_to_text import transcribe_audio
from modules.interview_assessment.evaluator import evaluate_answer
from modules.interview_assessment.scoring import calculate_grade, determine_recommendation
from modules.candidate.profile.model import CandidateProfile

logger = logging.getLogger(__name__)

class InterviewManager:

    @classmethod
    def start_session(cls, candidate_id: int, db: Session) -> dict:
        """
        Starts a new interview session or resumes an active one.
        Generates 10 customized questions if it's a new session.
        """
        # 1. Check for active session
        active_session = db.query(InterviewSession).filter(
            InterviewSession.candidate_id == candidate_id,
            InterviewSession.status == "IN_PROGRESS"
        ).first()

        if active_session:
            logger.info(f"Resuming active session {active_session.id} for candidate {candidate_id}")
            questions = db.query(InterviewQuestion).filter(
                InterviewQuestion.session_id == active_session.id
            ).order_by(InterviewQuestion.order_index).all()
            
            # Find current question index (the first question without a completed evaluation)
            current_index = 0
            for i, q in enumerate(questions):
                ans = db.query(InterviewAnswer).filter(
                    InterviewAnswer.session_id == active_session.id,
                    InterviewAnswer.question_id == q.id
                ).first()
                if not ans or ans.score is None:
                    current_index = i
                    break
            else:
                current_index = 9 # all answered but not finalized

            return {
                "session_id": active_session.id,
                "duration": active_session.duration,
                "questions": questions,
                "status": "IN_PROGRESS",
                "current_index": current_index
            }

        # 2. Check Daily Limits and Pass Cooldown
        from sqlalchemy import cast, Date
        today = datetime.datetime.utcnow().date()
        
        # Check how many sessions were created today
        today_sessions = db.query(InterviewSession).filter(
            InterviewSession.candidate_id == candidate_id,
            cast(InterviewSession.created_at, Date) == today
        ).count()
        
        if today_sessions >= 2:
            raise HTTPException(
                status_code=403, 
                detail="You have reached the maximum limit of 2 attempts per day."
            )
            
        # Check if they have a passing result within the last 2 months
        two_months_ago = datetime.datetime.utcnow() - datetime.timedelta(days=60)
        recent_pass = db.query(InterviewResult).filter(
            InterviewResult.candidate_id == candidate_id,
            InterviewResult.total_score >= 60,
            InterviewResult.created_at >= two_months_ago
        ).order_by(InterviewResult.created_at.desc()).first()
        
        if recent_pass:
            # If they have a passing result, block them and return the completed session
            questions = db.query(InterviewQuestion).filter(
                InterviewQuestion.session_id == recent_pass.session_id
            ).order_by(InterviewQuestion.order_index).all()
            return {
                "session_id": recent_pass.session_id,
                "duration": 30,
                "questions": questions,
                "status": "COMPLETED",
                "current_index": 9
            }
        
        # Otherwise, they are allowed to take it again (if they failed previously)

        # 3. Create a new session
        logger.info(f"Creating new interview session for candidate {candidate_id}")
        new_session = InterviewSession(
            candidate_id=candidate_id,
            start_time=datetime.datetime.utcnow(),
            duration=30,  # 30 minutes limit
            status="IN_PROGRESS"
        )
        db.add(new_session)
        db.flush()  # get session ID

        # 4. Generate 10 questions
        try:
            generated_qs = generate_interview_questions(candidate_id, db)
            for idx, q_data in enumerate(generated_qs):
                q = InterviewQuestion(
                    session_id=new_session.id,
                    question_text=q_data.get("question_text", "Could you speak about your experiences?"),
                    category=q_data.get("category", "HR"),
                    order_index=idx
                )
                db.add(q)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to generate questions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate interview questions: {e}"
            )

        # Fetch newly created questions
        questions = db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id == new_session.id
        ).order_by(InterviewQuestion.order_index).all()

        return {
            "session_id": new_session.id,
            "duration": new_session.duration,
            "questions": questions,
            "status": "IN_PROGRESS",
            "current_index": 0
        }

    @classmethod
    def save_answer(cls, session_id: int, question_id: int, audio_file_path: str, db: Session, speech_text: str = None) -> InterviewAnswer:
        """
        Transcribes the candidate response audio file using Gemini,
        and saves the transcript in the InterviewAnswer record.
        """
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session or session.status not in ("IN_PROGRESS", "COMPLETED"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active interview session found."
            )

        # Verify the question belongs to this session
        question = db.query(InterviewQuestion).filter(
            InterviewQuestion.id == question_id,
            InterviewQuestion.session_id == session_id
        ).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview question not found in this session."
            )

        # Use browser speech recognition text if provided, otherwise fallback to Gemini STT
        if speech_text and speech_text.strip():
            transcript = speech_text
        else:
            try:
                transcript = transcribe_audio(audio_file_path)
            except Exception as e:
                logger.error(f"Audio transcription failed: {e}")
                transcript = "[Transcription error occurred]"

        # Check if answer already exists
        answer = db.query(InterviewAnswer).filter(
            InterviewAnswer.session_id == session_id,
            InterviewAnswer.question_id == question_id
        ).first()

        if not answer:
            answer = InterviewAnswer(
                session_id=session_id,
                question_id=question_id,
                audio_path=audio_file_path,
                transcript=transcript
            )
            db.add(answer)
        else:
            answer.audio_path = audio_file_path
            answer.transcript = transcript
            # Reset scores for re-evaluation
            answer.communication_score = None
            answer.technical_score = None
            answer.confidence_score = None
            answer.professionalism_score = None
            answer.score = None
            answer.evaluation_feedback = None

        db.commit()
        db.refresh(answer)
        return answer

    @classmethod
    def evaluate_answer_record(cls, session_id: int, question_id: int, db: Session) -> InterviewAnswer:
        """
        Evaluates the saved transcript for a given question using Gemini.
        Saves scores and feedback on the InterviewAnswer record.
        """
        answer = db.query(InterviewAnswer).filter(
            InterviewAnswer.session_id == session_id,
            InterviewAnswer.question_id == question_id
        ).first()

        if not answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Answer not found. Submit the answer audio first."
            )

        question = db.query(InterviewQuestion).filter(InterviewQuestion.id == question_id).first()
        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found."
            )

        # Call Gemini evaluator
        try:
            eval_result = evaluate_answer(
                question_text=question.question_text,
                category=question.category,
                transcript=answer.transcript or ""
            )
            
            # Save results
            answer.communication_score = eval_result["communication_score"]
            answer.technical_score = eval_result["technical_score"]
            answer.confidence_score = eval_result["confidence_score"]
            answer.professionalism_score = eval_result["professionalism_score"]
            
            # Weighted total score
            answer.score = (
                eval_result["communication_score"] +
                eval_result["technical_score"] +
                eval_result["confidence_score"] +
                eval_result["professionalism_score"]
            )
            answer.evaluation_feedback = json.dumps(eval_result["feedback"])
            
            db.commit()
            db.refresh(answer)
            return answer
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to evaluate answer record: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to evaluate answer: {e}"
            )

    @classmethod
    def finalize_session(cls, session_id: int, db: Session, is_terminated: bool = False) -> InterviewResult:
        """
        Finalizes the interview session, calculates averages,
        generates the overall feedback report via Gemini, and updates CandidateProfile.
        """
        session = db.query(InterviewSession).filter(InterviewSession.id == session_id).first()
        if not session:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview session not found."
            )
        
        # If already completed or terminated, return the existing result
        if session.status in ("COMPLETED", "TERMINATED"):
            existing_result = db.query(InterviewResult).filter(
                InterviewResult.session_id == session_id
            ).first()
            if existing_result:
                return existing_result

        if is_terminated:
            # Save InterviewResult
            result = InterviewResult(
                candidate_id=session.candidate_id,
                session_id=session.id,
                communication_score=0.0,
                technical_score=0.0,
                confidence_score=0.0,
                professionalism_score=0.0,
                total_score=0.0,
                grade="F",
                strengths=json.dumps(["None (Assessment terminated)"]),
                weaknesses=json.dumps(["Assessment terminated due to integrity policy violations."]),
                suggestions=json.dumps(["Please follow candidate proctoring guidelines in future attempts."]),
                hiring_recommendation="Not Recommended",
                detailed_report="Assessment terminated due to integrity policy violations."
            )
            db.add(result)

            # Update session status
            session.status = "TERMINATED"
            session.end_time = datetime.datetime.utcnow()

            # Update CandidateProfile
            profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == session.candidate_id).first()
            if profile:
                profile.interview_score = 0.0
                profile.interview_date = datetime.datetime.utcnow()
                profile.interview_status = "Not Recommended"
                db.add(profile)

            db.commit()
            db.refresh(result)
            return result


        # Fetch questions and answers
        questions = db.query(InterviewQuestion).filter(InterviewQuestion.session_id == session_id).all()
        answers = db.query(InterviewAnswer).filter(InterviewAnswer.session_id == session_id).all()
        
        # Build answer map
        answer_map = {ans.question_id: ans for ans in answers}
        
        # Ensure all 10 questions have evaluations
        evaluated_answers = []
        for q in questions:
            ans = answer_map.get(q.id)
            if not ans:
                # Blank answer
                ans = InterviewAnswer(
                    session_id=session_id,
                    question_id=q.id,
                    audio_path=None,
                    transcript="",
                    communication_score=0.0,
                    technical_score=0.0,
                    confidence_score=0.0,
                    professionalism_score=0.0,
                    score=0.0,
                    evaluation_feedback=json.dumps({
                        "strengths": [],
                        "weaknesses": ["No answer was submitted."],
                        "improvement_tips": ["Ensure you record and submit answers for all questions."]
                    })
                )
                db.add(ans)
                db.flush()
            elif ans.score is None:
                # Had transcript but wasn't evaluated
                cls.evaluate_answer_record(session_id, q.id, db)
                db.refresh(ans)
            
            evaluated_answers.append(ans)

        # Calculate Averages
        total_q = len(evaluated_answers)
        avg_comm = sum(a.communication_score or 0.0 for a in evaluated_answers) / total_q
        avg_tech = sum(a.technical_score or 0.0 for a in evaluated_answers) / total_q
        avg_conf = sum(a.confidence_score or 0.0 for a in evaluated_answers) / total_q
        avg_prof = sum(a.professionalism_score or 0.0 for a in evaluated_answers) / total_q
        total_score = avg_comm + avg_tech + avg_conf + avg_prof
        
        grade = calculate_grade(total_score)
        recommendation = determine_recommendation(total_score, avg_tech)

        # Gather performance details to send to Gemini for Feedback Report Generation
        performance_list = []
        for idx, q in enumerate(questions):
            ans = [a for a in evaluated_answers if a.question_id == q.id][0]
            feedback_data = {}
            if ans.evaluation_feedback:
                try:
                    feedback_data = json.loads(ans.evaluation_feedback)
                except Exception:
                    pass
            performance_list.append({
                "question": q.question_text,
                "category": q.category,
                "transcript": ans.transcript or "[No response]",
                "scores": {
                    "communication": ans.communication_score,
                    "technical": ans.technical_score,
                    "confidence": ans.confidence_score,
                    "professionalism": ans.professionalism_score
                },
                "feedback": feedback_data
            })

        mock_report = {
            "strengths": [
                "Demonstrates solid technical communication and problem-solving structure.",
                "Consistently professional tone and vocabulary.",
                "Good project descriptions with clear tech stacks."
            ],
            "weaknesses": [
                "Could expand on technical tradeoffs in architectural explanations.",
                "Slight hesitation when answering behavioral scenario questions."
            ],
            "suggestions": [
                "Practice active behavioral interviewing using the STAR method.",
                "Be ready to elaborate on scalability and bottlenecks of your projects."
            ],
            "detailed_summary": f"The candidate demonstrated strong baseline communication skills (score: {avg_comm:.1f}/25) and solid domain knowledge (score: {avg_tech:.1f}/40). Professionalism was a clear strength (score: {avg_prof:.1f}/15) and confidence was strong throughout the session (score: {avg_conf:.1f}/20). Recommendation is {recommendation} with grade {grade}."
        }

        grok_key = os.environ.get("GROQ_API_KEY")
        if not grok_key:
            logger.warning("GROQ_API_KEY is not set. Using mock report data.")
            report_data = mock_report
        else:
            report_prompt = f"""You are an expert AI HR Director.
Review the following candidate's interview performance across 10 questions:

Candidate Performance Details:
{json.dumps(performance_list, indent=2)}

Overall Score Details:
- Communication average: {avg_comm:.2f}/25
- Technical average: {avg_tech:.2f}/40
- Confidence average: {avg_conf:.2f}/20
- Professionalism average: {avg_prof:.2f}/15
- Total Score: {total_score:.2f}/100
- Grade: {grade}
- Recommendation: {recommendation}

Provide a comprehensive, high-level feedback report for the candidate.
Return ONLY a valid JSON object (no markdown, no extra text) matching this schema:
{{
  "strengths": ["string"],
  "weaknesses": ["string"],
  "suggestions": ["string"],
  "detailed_summary": "string"
}}"""

            try:
                from modules.interview_assessment.grok_utils import grok_chat
                raw = grok_chat(report_prompt, json_mode=True)
                report_data = json.loads(raw)
            except Exception as e:
                logger.error(f"Failed to generate final report via Grok: {e}")
                report_data = mock_report

        # Save InterviewResult
        result = InterviewResult(
            candidate_id=session.candidate_id,
            session_id=session.id,
            communication_score=round(avg_comm, 2),
            technical_score=round(avg_tech, 2),
            confidence_score=round(avg_conf, 2),
            professionalism_score=round(avg_prof, 2),
            total_score=round(total_score, 2),
            grade=grade,
            strengths=json.dumps(report_data.get("strengths", [])),
            weaknesses=json.dumps(report_data.get("weaknesses", [])),
            suggestions=json.dumps(report_data.get("suggestions", [])),
            hiring_recommendation=recommendation,
            detailed_report=report_data.get("detailed_summary", "")
        )
        db.add(result)

        # Update session status
        session.status = "COMPLETED"
        session.end_time = datetime.datetime.utcnow()

        # Update CandidateProfile
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == session.candidate_id).first()
        if profile:
            profile.interview_score = round(total_score, 2)
            profile.interview_date = datetime.datetime.utcnow()
            profile.interview_status = recommendation
            db.add(profile)

        try:
            db.commit()
            db.refresh(result)
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to finalize session and commit: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to finalize interview: {e}"
            )
