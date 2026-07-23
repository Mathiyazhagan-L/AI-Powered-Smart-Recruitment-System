import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

def evaluate_professional_assessment(qa_pairs: list) -> dict:
    """
    Evaluates a candidate's full set of answers using Groq API.
    Returns a structured JSON with exactly 7 metrics, strengths, weaknesses, and recommendation.
    """
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        logger.error("GROQ_API_KEY not found in environment.")
        return get_fallback_result()

    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    qa_text = "\n\n".join(qa_pairs)
    
    prompt = f"""
    You are an expert technical recruiter and HR evaluator.
    Below is a candidate's professional assessment containing 10 questions and their typed answers.
    
    {qa_text}
    
    Evaluate the candidate's answers based on the following 7 metrics (each has a max score):
    1. Problem Solving (Max 20)
    2. Analytical Thinking (Max 20)
    3. Decision Making (Max 15)
    4. Communication (Max 15)
    5. Technical Understanding (Max 15)
    6. Professional Reasoning (Max 10)
    7. Completeness & Clarity (Max 5)
    
    Calculate the Overall Score out of 100.
    Determine Pass/Fail (Pass if Overall Score >= 60).
    Provide a Final Recommendation which must be one of: "Highly Recommended", "Recommended", "Needs Review", "Not Recommended".
    
    Return the result EXCLUSIVELY as a raw JSON object with the following schema:
    {{
      "metrics": {{
        "Problem Solving": <float>,
        "Analytical Thinking": <float>,
        "Decision Making": <float>,
        "Communication": <float>,
        "Technical Understanding": <float>,
        "Professional Reasoning": <float>,
        "Completeness & Clarity": <float>
      }},
      "overall_score": <float>,
      "pass_fail": "<Pass or Fail>",
      "strengths": ["<strength 1>", "<strength 2>"],
      "weaknesses": ["<weakness 1>", "<weakness 2>"],
      "improvement_suggestions": ["<suggestion 1>", "<suggestion 2>"],
      "final_recommendation": "<recommendation>"
    }}
    
    Do not output any markdown formatting, backticks, or extra text. ONLY raw valid JSON.
    """
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a precise JSON-outputting AI."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            content = response.json()["choices"][0]["message"]["content"].strip()
            
            # Remove any markdown formatting if present
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            return json.loads(content.strip())
        else:
            logger.error(f"Groq API Error: {response.text}")
            return get_fallback_result()
    except Exception as e:
        logger.error(f"Failed to parse Groq response: {e}")
        return get_fallback_result()

def get_fallback_result():
    return {
      "metrics": {
        "Problem Solving": 0,
        "Analytical Thinking": 0,
        "Decision Making": 0,
        "Communication": 0,
        "Technical Understanding": 0,
        "Professional Reasoning": 0,
        "Completeness & Clarity": 0
      },
      "overall_score": 0,
      "pass_fail": "Fail",
      "strengths": ["Evaluation failed"],
      "weaknesses": ["Error connecting to AI service"],
      "improvement_suggestions": ["Check API logs"],
      "final_recommendation": "Needs Review"
    }
