import sys, os, time
import base64

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from core.database import SessionLocal
from modules.proctoring.models import AssessmentViolation, ProctoringLog, AssessmentIntegrityResult
from modules.assessment.models import AssessmentAttempt
from modules.proctoring.logic import start_monitoring, report_browser_violation, report_frame
from modules.assessment.logic import generate_assessment

def test_proctoring_flow():
    db = SessionLocal()
    try:
        print("--- 1. Reset & Start Assessment ---")
        try:
            from modules.assessment.logic import reset_assessment
            reset_assessment(1, db)
        except Exception:
            pass
        
        print("Starting monitoring...")
        start_res = start_monitoring(1, "APTITUDE", db)
        print("Proctoring session:", start_res)
        
        print("Generating assessment...")
        attempt_res = generate_assessment(1, db)
        attempt_id = attempt_res["attempt_id"]
        print(f"Active Attempt ID: {attempt_id}")
        
        print("\n--- 2. Simulate Frame Capture ---")
        # Create a dummy 1x1 base64 image
        dummy_base64 = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
        frame_res = report_frame(1, "APTITUDE", dummy_base64, db)
        print("Frame processing result:", frame_res)

        print("\n--- 3. Simulate Violations ---")
        violations_to_test = ["TAB_SWITCH", "FULLSCREEN_EXIT", "COPY_PASTE", "DEV_TOOLS"]
        for v in violations_to_test:
            res = report_browser_violation(1, "APTITUDE", v, db)
            print(f"Violation {v} result:", res)

        print("\n--- 4. Verify Database Persistence ---")
        logs = db.query(ProctoringLog).filter(ProctoringLog.candidate_id == 1).all()
        print(f"Total Proctoring Logs: {len(logs)}")
        for log in logs:
            print(f" - [{log.timestamp}] {log.event_type}: {log.event_data}")

        viols = db.query(AssessmentViolation).filter(AssessmentViolation.candidate_id == 1).all()
        print(f"Total Database Violations: {len(viols)}")
        for viol in viols:
            print(f" - {viol.violation_type} (Score Change: {viol.score_penalty})")

        integrity = db.query(AssessmentIntegrityResult).filter(AssessmentIntegrityResult.candidate_id == 1).first()
        print(f"Current Integrity Score in DB: {integrity.final_score if integrity else 'N/A'}")
        
        attempt = db.query(AssessmentAttempt).filter(AssessmentAttempt.id == attempt_id).first()
        print(f"Attempt Integrity Score sync: {attempt.integrity_score if attempt else 'N/A'}")
        
        print("\n--- 5. Verify Recruiter Visibility ---")
        from modules.hr_review.api import fetch_candidate_profile_hr
        # Wait, fetch_candidate_profile_hr requires Depends. 
        # Let's query exactly what recruiter would see in logic
        from modules.hr_review.logic import get_candidate_hr_view
        hr_view = get_candidate_hr_view(1, db)
        if "proctoring_history" in hr_view:
            print("Proctoring history exists in HR View!")
            for h in hr_view["proctoring_history"]:
                print(f" - HR sees: {h}")
        else:
            print("HR View does not include proctoring_history!")

    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_proctoring_flow()
