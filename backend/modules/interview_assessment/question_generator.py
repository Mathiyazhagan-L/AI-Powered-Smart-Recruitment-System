import os
import json
import logging
from sqlalchemy.orm import Session
from dotenv import load_dotenv

load_dotenv()

from modules.candidate.skills.model import CandidateSkill
from modules.candidate.projects.model import CandidateProject
from modules.candidate.profile.model import CandidateProfile

logger = logging.getLogger(__name__)


def generate_interview_questions(candidate_id: int, db: Session) -> list:
    """
    Generates exactly 10 customized interview questions via Grok AI:
    - 3 HR, 3 Technical, 2 Behavioral, 2 Project
    Falls back to realistic static questions if API is unavailable.
    """
    logger.info(f"Generating questions for candidate {candidate_id}")

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == candidate_id).first()
    skills = db.query(CandidateSkill).filter(CandidateSkill.user_id == candidate_id).all()
    projects = db.query(CandidateProject).filter(CandidateProject.user_id == candidate_id).all()

    skills_summary = ", ".join([
        f"{s.skill_name} ({s.proficiency_level or 'Intermediate'}, {s.years_of_experience} yrs)"
        for s in skills
    ])

    projects_list = []
    for p in projects:
        proj_str = f"Name: {p.project_name}."
        if p.description:
            proj_str += f" Description: {p.description}."
        if p.technologies:
            proj_str += f" Technologies: {p.technologies}."
        projects_list.append(proj_str)
    projects_summary = "; ".join(projects_list)

    headline = profile.headline if profile else ""
    summary = profile.summary if profile else ""
    full_name = profile.full_name if profile else "Candidate"

    # Fallback static questions
    fallback = [
        {"category": "HR", "question_text": f"Welcome, {full_name}. Tell me about yourself and why you are interested in this role."},
        {"category": "HR", "question_text": "What are your greatest professional strengths and how do they align with our engineering culture?"},
        {"category": "HR", "question_text": "Where do you see yourself in five years, and how does this position help you get there?"},
        {"category": "Technical", "question_text": f"Given your experience with {skills_summary or 'software development'}, what is the difference between synchronous and asynchronous programming?"},
        {"category": "Technical", "question_text": "How do you ensure code quality, test coverage, and write effective unit tests in your projects?"},
        {"category": "Technical", "question_text": "Explain database indexing, its impact on performance, and when you should avoid it."},
        {"category": "Behavioral", "question_text": "Describe a situation where you had a conflict with a team member. How did you resolve it?"},
        {"category": "Behavioral", "question_text": "Tell me about a time you faced a tight deadline. How did you manage it?"},
        {"category": "Project", "question_text": f"Looking at your project: {projects_summary or 'your portfolio'}, walk me through a recent technical challenge you resolved."},
        {"category": "Project", "question_text": "If you had to rebuild your most successful project from scratch, what architectural decisions would you change?"}
    ]

    prompt = f"""You are an expert HR and Technical Interviewer.
Generate exactly 10 customized interview questions for candidate: {full_name}

Candidate Profile:
- Headline: {headline or 'Not provided'}
- Summary: {summary or 'Not provided'}
- Skills: {skills_summary or 'Not provided'}
- Projects: {projects_summary or 'Not provided'}

Generate exactly 10 questions distributed as:
- 3 HR questions (cultural fit, work ethics, company alignment)
- 3 Technical questions (customized for skills: {skills_summary or 'general tech/coding'})
- 2 Behavioral questions (conflict resolution, teamwork, handling challenges)
- 2 Project questions (probe their specific projects: {projects_summary or 'past project scenarios'})

Mix and randomize questions into a realistic interview flow.
Return ONLY a valid JSON object (no markdown, no extra text) with this schema:
{{
  "questions": [
    {{
      "category": "HR" | "Technical" | "Behavioral" | "Project",
      "question_text": "string"
    }}
  ]
}}"""

    try:
        from modules.interview_assessment.grok_utils import grok_chat
        raw = grok_chat(prompt, json_mode=True)
        data = json.loads(raw)
        questions = data.get("questions", [])

        if len(questions) != 10:
            logger.warning(f"Grok returned {len(questions)} questions instead of 10. Padding with fallback.")
            cats = ["HR", "Technical", "Behavioral", "Project"]
            while len(questions) < 10:
                cat = cats[len(questions) % len(cats)]
                questions.append({
                    "category": cat,
                    "question_text": f"Tell me about a time you applied your {cat.lower()} skills in a real-world scenario."
                })
            questions = questions[:10]

        return questions

    except Exception as e:
        logger.error(f"Error generating questions via Grok: {e}. Falling back to default questions.")
        return fallback
