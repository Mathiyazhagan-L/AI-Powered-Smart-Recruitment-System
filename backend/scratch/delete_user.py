import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database import SessionLocal
from modules.auth.model import User, RefreshToken, OTPRecord
from modules.candidate.profile.model import CandidateProfile
from modules.candidate.resume.model import CandidateResume
from modules.candidate.education.model import CandidateEducation
from modules.candidate.experience.model import CandidateExperience
from modules.candidate.skills.model import CandidateSkill
from modules.candidate.projects.model import CandidateProject
from modules.job_management.model import Application, AIRecommendation
from modules.interview_scheduling.model import InterviewSchedule
from modules.offer_management.model import OfferLetter

db = SessionLocal()

email = "droptomathi422@gmail.com"

# Find user
user = db.query(User).filter(User.email == email).first()

if not user:
    print(f"User {email} not found.")
else:
    user_id = user.id
    print(f"Found user {email} with ID {user_id}. Proceeding to delete all related data...")

    try:
        # Delete resume records
        deleted_resumes = db.query(CandidateResume).filter(CandidateResume.user_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_resumes} resume records.")

        # Delete education records
        deleted_edu = db.query(CandidateEducation).filter(CandidateEducation.user_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_edu} education records.")

        # Delete experience records
        deleted_exp = db.query(CandidateExperience).filter(CandidateExperience.user_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_exp} experience records.")

        # Delete skill records
        deleted_skills = db.query(CandidateSkill).filter(CandidateSkill.user_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_skills} skill records.")

        # Delete project records
        deleted_projects = db.query(CandidateProject).filter(CandidateProject.user_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_projects} project records.")

        # Delete candidate profile
        deleted_profiles = db.query(CandidateProfile).filter(
            (CandidateProfile.user_id == user_id) | (CandidateProfile.email == email)
        ).delete(synchronize_session=False)
        print(f"Deleted {deleted_profiles} candidate profile records.")

        # Delete applications
        deleted_apps = db.query(Application).filter(Application.candidate_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_apps} application records.")

        # Delete AI recommendations
        deleted_recs = db.query(AIRecommendation).filter(AIRecommendation.candidate_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_recs} AI recommendations.")

        # Delete interviews
        deleted_interviews = db.query(InterviewSchedule).filter(InterviewSchedule.candidate_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_interviews} interview schedules.")

        # Delete offer letters
        deleted_offers = db.query(OfferLetter).filter(OfferLetter.candidate_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_offers} offer letter records.")

        # Delete refresh tokens
        deleted_tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete(synchronize_session=False)
        print(f"Deleted {deleted_tokens} refresh tokens.")

        # Delete OTP records
        deleted_otps = db.query(OTPRecord).filter(OTPRecord.target == email).delete(synchronize_session=False)
        print(f"Deleted {deleted_otps} OTP records.")

        # Delete User
        db.delete(user)
        db.commit()
        print(f"Successfully deleted user {email} (ID: {user_id}) entirely.")
    except Exception as e:
        db.rollback()
        print(f"Error during deletion: {e}")

db.close()
