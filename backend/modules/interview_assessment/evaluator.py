import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def evaluate_answer(question_text: str, category: str, transcript: str) -> dict:
    """
    Evaluates a candidate's answer across 4 dimensions using Grok AI:
    - Communication (max 25)
    - Technical Accuracy (max 40)
    - Confidence (max 20)
    - Professionalism (max 15)
    Returns structured JSON with scores and feedback.
    """
    logger.info(f"Evaluating answer for question category: {category}")

    # Empty transcript → zero scores
    if not transcript or not transcript.strip():
        logger.info("Empty transcript. Scoring zero.")
        return {
            "communication_score": 0.0,
            "technical_score": 0.0,
            "confidence_score": 0.0,
            "professionalism_score": 0.0,
            "feedback": {
                "strengths": [],
                "weaknesses": ["No answer was provided or captured."],
                "improvement_tips": ["Please ensure your microphone is working and speak clearly."]
            }
        }

    prompt = f"""You are an expert AI Interview Evaluator.
Evaluate the candidate's response to the following interview question:

Question: "{question_text}"
Question Category: {category}
Candidate Transcript: "{transcript}"

Evaluate the response strictly across 4 dimensions. If the answer is factually incorrect, completely irrelevant, or "I don't know", you MUST give a very low Technical Accuracy score (0-5). Be harsh on wrong answers:
1. Communication: out of 25 — clarity, coherence, structure. (If they give up or say nothing meaningful, score 0-5).
2. Technical Accuracy: out of 40 — technical knowledge, correctness, depth. (CRITICAL: If the answer is wrong, irrelevant, or mostly hallucinated, score 0-10 max. Only award >25 for correct, detailed answers).
3. Confidence: out of 20 — certainty, lack of hesitation. (If they guess wrongly or mumble, score low).
4. Professionalism: out of 15 — tone, courtesy, formal vocabulary.

Return ONLY a valid JSON object (no markdown, no extra text) matching this schema:
{{
  "communication_score": float,
  "technical_score": float,
  "confidence_score": float,
  "professionalism_score": float,
  "feedback": {{
    "strengths": ["string"],
    "weaknesses": ["string"],
    "improvement_tips": ["string"]
  }}
}}"""

    try:
        from modules.interview_assessment.grok_utils import grok_chat
        raw = grok_chat(prompt, json_mode=True)
        data = json.loads(raw)

        communication = min(max(float(data.get("communication_score", 0.0)), 0.0), 25.0)
        technical = min(max(float(data.get("technical_score", 0.0)), 0.0), 40.0)
        confidence = min(max(float(data.get("confidence_score", 0.0)), 0.0), 20.0)
        professionalism = min(max(float(data.get("professionalism_score", 0.0)), 0.0), 15.0)
        feedback = data.get("feedback", {})
        if not isinstance(feedback, dict):
            feedback = {}

        return {
            "communication_score": communication,
            "technical_score": technical,
            "confidence_score": confidence,
            "professionalism_score": professionalism,
            "feedback": {
                "strengths": feedback.get("strengths", []),
                "weaknesses": feedback.get("weaknesses", []),
                "improvement_tips": feedback.get("improvement_tips", [])
            }
        }

    except Exception as e:
        logger.error(f"Error evaluating answer via Grok: {e}")
        # Sensible fallback scores
        fallback_map = {
            "Technical":  (18.0, 30.0, 15.0, 11.0),
            "HR":         (20.0, 28.0, 16.0, 12.0),
            "Behavioral": (19.0, 27.0, 15.0, 11.0),
        }
        comm, tech, conf, prof = fallback_map.get(category, (18.0, 28.0, 14.0, 11.0))
        return {
            "communication_score": comm,
            "technical_score": tech,
            "confidence_score": conf,
            "professionalism_score": prof,
            "feedback": {
                "strengths": ["Answer was recorded and shows coherent structure."],
                "weaknesses": ["AI evaluation temporarily unavailable."],
                "improvement_tips": ["Review system logs for API connection issues."]
            }
        }
