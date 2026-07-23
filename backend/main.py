import sys
import os
import logging
from dotenv import load_dotenv

# Ensure dotenv is loaded with explicit path before anything else and overrides existing empty vars
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path, override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.getenv("GOOGLE_CLIENT_ID"):
    logger.error("STARTUP ERROR: GOOGLE_CLIENT_ID is not configured in the environment. Google Sign-In will fail.")
if not os.getenv("GOOGLE_CLIENT_SECRET"):
    logger.warning("STARTUP WARNING: GOOGLE_CLIENT_SECRET is missing. Google Auth code exchange may fail.")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add the current directory to python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.job_management.api import router as job_router
from modules.auth.api import router as auth_router
from modules.company_profile.api import router as company_router
from modules.candidate.profile.api import router as candidate_profile_router
from modules.candidate.education.api import router as candidate_education_router
from modules.candidate.experience.api import router as candidate_experience_router
from modules.candidate.projects.api import router as candidate_projects_router
from modules.candidate.skills.api import router as candidate_skills_router
from modules.candidate.resume.api import router as candidate_resume_router
from modules.resume_parser.api import router as resume_parser_router
from modules.ai_evaluation.api import router as ai_evaluation_router
from modules.ml_prediction.api import router as ml_prediction_router
from modules.analytics.api import router as analytics_router
from modules.assessment.api import router as assessment_router
from modules.coding_assessment.api import router as coding_router
from modules.interview_assessment.api import router as interview_router
from modules.proctoring.api import router as proctoring_router
from modules.job_management.notification_api import router as notification_router
from modules.email_automation.api import router as email_router
from modules.hr_review.api import router as hr_review_router
from modules.interview_scheduling.api import router as interview_schedule_router
from modules.offer_management.api import router as offer_router
from modules.uploads.api import router as uploads_router
from modules.recruiter_workspace.api import router as recruiter_workspace_router

app = FastAPI(
    title="AIHire Recruitment Platform",
    description="Backend API service for the AI-powered Recruitment Platform.",
    version="1.0.0"
)

# CORS configuration to enable frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    path = request.url.path.lower()
    if path.endswith(".html") or path == "/" or path.endswith(".js") or path.endswith(".css"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

# Include the Job Management router
app.include_router(job_router)
app.include_router(auth_router)
app.include_router(company_router)
app.include_router(candidate_profile_router)
app.include_router(candidate_education_router)
app.include_router(candidate_experience_router)
app.include_router(candidate_projects_router)
app.include_router(candidate_skills_router)
app.include_router(candidate_resume_router)
app.include_router(resume_parser_router)
app.include_router(ai_evaluation_router)
app.include_router(ml_prediction_router)
app.include_router(analytics_router)
app.include_router(assessment_router)
app.include_router(coding_router)
app.include_router(interview_router)
app.include_router(proctoring_router)
app.include_router(notification_router)
app.include_router(email_router)
app.include_router(hr_review_router)
app.include_router(interview_schedule_router)
app.include_router(offer_router)
app.include_router(uploads_router)
app.include_router(recruiter_workspace_router)

from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

@app.get("/")
def home():
    return RedirectResponse(url="/startpage.html")

# Mount the frontend directory to serve HTML/CSS/JS files
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

# Mount the static uploads directory
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/static_uploads", StaticFiles(directory=uploads_dir), name="static_uploads")

if __name__ == "__main__":
    import uvicorn
    # Start the server on http://127.0.0.1:8000
    print("Starting Job Management API service...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
