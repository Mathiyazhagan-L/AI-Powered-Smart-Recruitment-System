import json
import io
from fastapi.testclient import TestClient
from sqlalchemy import text
from core.database import SessionLocal
from main import app

# Import models to clean up database
from modules.interview_assessment.models import (
    InterviewSession,
    InterviewQuestion,
    InterviewAnswer,
    InterviewResult
)
from modules.candidate.profile.model import CandidateProfile
from modules.interview_assessment.api import get_current_user_id

# Override authentication dependency to return candidate user 1
app.dependency_overrides[get_current_user_id] = lambda: 1

client = TestClient(app)

def run_tests():
    print("=" * 60)
    print("RUNNING END-TO-END INTERVIEW ENGINE TEST")
    print("=" * 60)

    # 1. Clean up old records for candidate 1
    with SessionLocal() as db:
        # Check if candidate 1 profile exists
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == 1).first()
        if not profile:
            # Create a dummy candidate profile for testing if not exists
            profile = CandidateProfile(
                user_id=1,
                full_name="Test Candidate",
                email="test_candidate@recruitment.com",
                profile_completion=80,
                assessment_status="PASSED"  # Set to PASSED so frontend logic would let them start Round 3
            )
            db.add(profile)
            db.commit()
            print("Created new dummy CandidateProfile for testing.")
        else:
            # Set profile assessment status to PASSED to make sure it's correct
            profile.assessment_status = "PASSED"
            profile.interview_score = None
            profile.interview_date = None
            profile.interview_status = None
            db.add(profile)
            db.commit()
            print("Reset CandidateProfile state.")

        # Clean old interview sessions / results
        db.query(InterviewAnswer).filter(
            InterviewAnswer.session_id.in_(
                db.query(InterviewSession.id).filter(InterviewSession.candidate_id == 1)
            )
        ).delete(synchronize_session=False)
        
        db.query(InterviewQuestion).filter(
            InterviewQuestion.session_id.in_(
                db.query(InterviewSession.id).filter(InterviewSession.candidate_id == 1)
            )
        ).delete(synchronize_session=False)

        db.query(InterviewResult).filter(InterviewResult.candidate_id == 1).delete()
        db.query(InterviewSession).filter(InterviewSession.candidate_id == 1).delete()
        db.commit()
        print("Cleaned up existing interview records for Candidate 1.")

    # 2. Start Interview Session
    print("\n[STEP 1] Starting interview...")
    response = client.post("/interview/start")
    assert response.status_code == 200, f"Failed start: {response.text}"
    start_data = response.json()
    session_id = start_data["session_id"]
    questions = start_data["questions"]
    print(f"Session started successfully. Session ID: {session_id}")
    print(f"Total questions generated: {len(questions)}")
    assert len(questions) == 10, "Expected 10 questions"

    # 3. Submit and evaluate each question
    print("\n[STEP 2] Submitting voice responses and evaluating...")
    for idx, q in enumerate(questions):
        q_id = q["id"]
        q_text = q["question_text"]
        q_cat = q["category"]
        print(f"  Question {idx+1}/10 ({q_cat}): \"{q_text}\"")

        # Create dummy WAV bytes
        dummy_wav = io.BytesIO(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\x3e\x00\x00\x00\x7d\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00")

        # Submit answer audio
        ans_response = client.post(
            "/interview/answer",
            data={
                "session_id": session_id,
                "question_id": q_id
            },
            files={
                "file": ("test_answer.wav", dummy_wav, "audio/wav")
            }
        )
        assert ans_response.status_code == 200, f"Submit answer failed: {ans_response.text}"
        ans_data = ans_response.json()
        print(f"    -> Transcript: \"{ans_data['transcript']}\"")

        # Evaluate answer
        eval_response = client.post(
            "/interview/evaluate",
            json={
                "session_id": session_id,
                "question_id": q_id
            }
        )
        assert eval_response.status_code == 200, f"Evaluation failed: {eval_response.text}"
        eval_data = eval_response.json()
        print(f"    -> Scores: Comm: {eval_data['communication_score']}, Tech: {eval_data['technical_score']}, Conf: {eval_data['confidence_score']}, Prof: {eval_data['professionalism_score']}")

    # 4. Finalize Interview
    print("\n[STEP 3] Finalizing interview and generating report...")
    finish_response = client.post(f"/interview/finish?session_id={session_id}")
    assert finish_response.status_code == 200, f"Finish failed: {finish_response.text}"
    result_data = finish_response.json()
    print("AI Mock Interview Result Scorecard Compiled:")
    print(f"  Total Score: {result_data['total_score']} / 100")
    print(f"  Grade: {result_data['grade']}")
    print(f"  Recommendation: {result_data['hiring_recommendation']}")
    print(f"  Strengths: {result_data['strengths']}")
    print(f"  Weaknesses: {result_data['weaknesses']}")
    print(f"  Suggestions: {result_data['suggestions']}")
    print(f"  Summary Report: {result_data['detailed_report']}")

    # 5. Retrieve result
    print("\n[STEP 4] Retrieving result via GET endpoint...")
    get_response = client.get("/interview/result/1")
    assert get_response.status_code == 200, f"Get result failed: {get_response.text}"
    get_data = get_response.json()
    assert get_data["session_id"] == session_id
    print("Successfully retrieved compiled report via API.")

    # 6. Verify CandidateProfile is updated
    print("\n[STEP 5] Checking database profile updates...")
    with SessionLocal() as db:
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == 1).first()
        print(f"Candidate Profile: user_id = {profile.user_id}")
        print(f"  interview_score = {profile.interview_score}")
        print(f"  interview_date = {profile.interview_date}")
        print(f"  interview_status = {profile.interview_status}")
        
        assert profile.interview_score == result_data["total_score"], "Profile score mismatch"
        assert profile.interview_status == result_data["hiring_recommendation"], "Profile recommendation mismatch"
        assert profile.interview_date is not None, "Profile date is empty"
        print("Database profile verification SUCCESSFUL.")

    # 7. Test Reset Endpoint
    print("\n[STEP 6] Testing reset endpoint to allow reattempt...")
    reset_response = client.post("/interview/reset")
    assert reset_response.status_code == 200, f"Reset failed: {reset_response.text}"
    reset_data = reset_response.json()
    assert reset_data["status"] == "success", "Expected success status"
    print("Reset API endpoint responded successfully.")

    # Verify database records are cleared
    with SessionLocal() as db:
        sessions_count = db.query(InterviewSession).filter(InterviewSession.candidate_id == 1).count()
        results_count = db.query(InterviewResult).filter(InterviewResult.candidate_id == 1).count()
        profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == 1).first()

        print("Verifying database state after reset:")
        print(f"  Sessions count: {sessions_count} (Expected: 0)")
        print(f"  Results count: {results_count} (Expected: 0)")
        print(f"  Profile interview_score: {profile.interview_score} (Expected: None)")
        print(f"  Profile interview_status: {profile.interview_status} (Expected: None)")

        assert sessions_count == 0, "Sessions were not deleted"
        assert results_count == 0, "Results were not deleted"
        assert profile.interview_score is None, "Profile score was not reset"
        assert profile.interview_status is None, "Profile status was not reset"
        assert profile.interview_date is None, "Profile date was not reset"
        print("Database verification after reset SUCCESSFUL.")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()

