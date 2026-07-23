import json
import datetime
import logging
from sqlalchemy.orm import Session

from modules.proctoring.models import AssessmentViolation, ProctoringLog, AssessmentIntegrityResult
from modules.proctoring.session import registry

logger = logging.getLogger(__name__)


def start_monitoring(candidate_id: int, assessment_type: str, db: Session) -> dict:
    """
    Starts the monitoring lifecycle for a candidate assessment.
    Creates ProctoringSession, logs a START event, and returns the session details.
    """
    assessment_type = assessment_type.upper()
    
    # Check if there is already an active session, remove it to start clean
    existing = registry.get_session(candidate_id, assessment_type)
    if existing:
        logger.info(f"Removing pre-existing active monitoring session for candidate {candidate_id}, type {assessment_type}")
        registry.remove_session(candidate_id, assessment_type)
        
    session = registry.create_session(candidate_id, assessment_type)
    
    # Log START event
    log_event = ProctoringLog(
        candidate_id=candidate_id,
        assessment_type=assessment_type,
        event_type="START",
        event_data=json.dumps({
            "session_id": session.session_id,
            "started_at": session.started_at.isoformat()
        }),
        timestamp=datetime.datetime.utcnow()
    )
    db.add(log_event)
    
    # Ensure AssessmentIntegrityResult placeholder is created or updated
    existing_result = db.query(AssessmentIntegrityResult).filter(
        AssessmentIntegrityResult.candidate_id == candidate_id,
        AssessmentIntegrityResult.assessment_type == assessment_type
    ).first()
    
    if existing_result:
        existing_result.integrity_score = 100
        existing_result.violation_count = 0
        existing_result.status = "ACTIVE"
        existing_result.completed_at = None
        db.add(existing_result)
    else:
        new_result = AssessmentIntegrityResult(
            candidate_id=candidate_id,
            assessment_type=assessment_type,
            assessment_score=None,
            integrity_score=100,
            violation_count=0,
            status="ACTIVE",
            completed_at=None
        )
        db.add(new_result)
        
    db.commit()
    
    return {
        "session_id": session.session_id,
        "candidate_id": session.candidate_id,
        "assessment_type": session.assessment_type,
        "started_at": session.started_at,
        "status": session.status
    }


def stop_monitoring(candidate_id: int, assessment_type: str, db: Session, final_status: str = None) -> dict:
    """
    Stops monitoring for candidate assessment.
    Removes session, calculates final assessment scores, logs STOP event, and saves final integrity results.
    """
    assessment_type = assessment_type.upper()
    session = registry.remove_session(candidate_id, assessment_type)
    
    # Extract values
    session_id = session.session_id if session else "NO_SESSION"
    integrity_score = session.integrity_score if session else 100
    violation_count = session.violation_count if session else 0
    
    if final_status is None:
        if session:
            final_status = "TERMINATED" if session.status == "TERMINATED" else "COMPLETED"
        else:
            final_status = "COMPLETED"
            
    # Log STOP event
    log_event = ProctoringLog(
        candidate_id=candidate_id,
        assessment_type=assessment_type,
        event_type="STOP",
        event_data=json.dumps({
            "session_id": session_id,
            "integrity_score": integrity_score,
            "violation_count": violation_count,
            "status": final_status
        }),
        timestamp=datetime.datetime.utcnow()
    )
    db.add(log_event)
    
    # Query final assessment score from DB
    assessment_score = None
    if assessment_type == "APTITUDE":
        from modules.assessment.models import AssessmentResult
        res = db.query(AssessmentResult).filter(
            AssessmentResult.candidate_id == candidate_id
        ).order_by(AssessmentResult.created_at.desc()).first()
        if res:
            assessment_score = res.aptitude_score
    elif assessment_type == "CODING":
        from modules.coding_assessment.models import CodingResult
        res = db.query(CodingResult).filter(
            CodingResult.candidate_id == candidate_id
        ).order_by(CodingResult.created_at.desc()).first()
        if res:
            assessment_score = res.total_score
    elif assessment_type == "INTERVIEW":
        from modules.interview_assessment.models import InterviewResult
        res = db.query(InterviewResult).filter(
            InterviewResult.candidate_id == candidate_id
        ).order_by(InterviewResult.created_at.desc()).first()
        if res:
            assessment_score = res.total_score

    # Save to dedicated assessment_integrity_results table
    existing = db.query(AssessmentIntegrityResult).filter(
        AssessmentIntegrityResult.candidate_id == candidate_id,
        AssessmentIntegrityResult.assessment_type == assessment_type
    ).first()
    
    if existing:
        existing.integrity_score = integrity_score
        existing.violation_count = violation_count
        existing.status = final_status
        existing.completed_at = datetime.datetime.utcnow()
        if assessment_score is not None:
            existing.assessment_score = assessment_score
        db.add(existing)
    else:
        new_result = AssessmentIntegrityResult(
            candidate_id=candidate_id,
            assessment_type=assessment_type,
            assessment_score=assessment_score,
            integrity_score=integrity_score,
            violation_count=violation_count,
            status=final_status,
            completed_at=datetime.datetime.utcnow()
        )
        db.add(new_result)
        
    db.commit()
    
    return {
        "candidate_id": candidate_id,
        "assessment_type": assessment_type,
        "integrity_score": integrity_score,
        "violation_count": violation_count,
        "status": final_status
    }


def report_browser_violation(candidate_id: int, assessment_type: str, violation_type: str, db: Session) -> dict:
    """
    Reports a browser violation. Triggers auto-submit policy if the 6-violation limit is breached.
    """
    assessment_type = assessment_type.upper()
    session = registry.get_session(candidate_id, assessment_type)
    if not session:
        return {"status": "NO_SESSION", "message": "No active proctoring session found."}
        
    res = session.browser_monitor.detect_violation(violation_type)
    
    if res.get("status") == "VIOLATION_DETECTED":
        # Add violation to DB
        violation = AssessmentViolation(
            candidate_id=candidate_id,
            assessment_type=assessment_type,
            violation_type=violation_type,
            warning_level=res.get("warning_level", 0),
            integrity_score=session.integrity_score,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(violation)
        
        # Log event
        log_entry = ProctoringLog(
            candidate_id=candidate_id,
            assessment_type=assessment_type,
            event_type="VIOLATION",
            event_data=json.dumps({
                "source": "BROWSER",
                "violation_type": violation_type,
                "warning_level": res.get("warning_level", 0),
                "integrity_score": session.integrity_score
            }),
            timestamp=datetime.datetime.utcnow()
        )
        db.add(log_entry)
        db.commit()
        
        # Auto-submit if terminated
        if res.get("is_terminated"):
            logger.warning(f"Malpractice limit reached for candidate {candidate_id} on {assessment_type}. Triggering auto-submit.")
            stop_monitoring(candidate_id, assessment_type, db, final_status="TERMINATED")
            auto_submit(candidate_id, assessment_type, db)
            
    return res


def report_frame(candidate_id: int, assessment_type: str, frame_b64: str, db: Session) -> dict:
    """
    Processes a submitted webcam frame, running webcam face checks and object detection.
    Triggers auto-submit policy if the 6-violation limit is breached.
    """
    assessment_type = assessment_type.upper()
    session = registry.get_session(candidate_id, assessment_type)
    if not session:
        return {"status": "NO_SESSION", "message": "No active proctoring session found."}
        
    # Process webcam (face/gaze check)
    webcam_res = session.webcam_monitor.process_frame(frame_b64)
    # Process object detection (phone/person check)
    object_res = session.object_detector.process_frame(frame_b64)
    
    merged_violations = []
    
    # Check webcam violation
    if webcam_res.get("violation_triggered") and webcam_res.get("violation_type"):
        v_res = webcam_res["violation_result"]
        merged_violations.append({
            "source": "WEBCAM",
            "violation_type": webcam_res["violation_type"],
            "warning_level": v_res.get("warning_level", 0),
            "is_terminated": v_res.get("is_terminated", False),
            "message": v_res.get("message")
        })
        
    # Check object detection violation
    if object_res.get("violation_triggered") and object_res.get("violation_type"):
        v_res = object_res["violation_result"]
        merged_violations.append({
            "source": "OBJECT_DETECTOR",
            "violation_type": object_res["violation_type"],
            "warning_level": v_res.get("warning_level", 0),
            "is_terminated": v_res.get("is_terminated", False),
            "message": v_res.get("message")
        })
        
    is_terminated = False
    warning_level = session.warning_level
    integrity_score = session.integrity_score
    
    for v in merged_violations:
        # Write to AssessmentViolation
        violation = AssessmentViolation(
            candidate_id=candidate_id,
            assessment_type=assessment_type,
            violation_type=v["violation_type"],
            warning_level=v["warning_level"],
            integrity_score=integrity_score,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(violation)
        
        # Log event
        log_entry = ProctoringLog(
            candidate_id=candidate_id,
            assessment_type=assessment_type,
            event_type="VIOLATION",
            event_data=json.dumps({
                "source": v["source"],
                "violation_type": v["violation_type"],
                "warning_level": v["warning_level"],
                "integrity_score": integrity_score
            }),
            timestamp=datetime.datetime.utcnow()
        )
        db.add(log_entry)
        
        if v["is_terminated"]:
            is_terminated = True
            
    if merged_violations:
        db.commit()
        
    if is_terminated or (session.status == "TERMINATED"):
        logger.warning(f"Malpractice limit reached for candidate {candidate_id} on {assessment_type} via camera monitoring. Triggering auto-submit.")
        stop_monitoring(candidate_id, assessment_type, db, final_status="TERMINATED")
        auto_submit(candidate_id, assessment_type, db)
        
    # Get the first warning message to return to client
    warning_message = None
    if merged_violations:
        warning_message = merged_violations[0].get("message")
        
    return {
        "status": "PROCESSED",
        "webcam_status": webcam_res.get("status"),
        "object_status": object_res.get("status"),
        "integrity_score": integrity_score,
        "warning_level": warning_level,
        "is_terminated": is_terminated or (session.status == "TERMINATED"),
        "message": warning_message
    }


def auto_submit(candidate_id: int, assessment_type: str, db: Session):
    """
    Executes the auto-submit policy on violation termination.
    Aptitude -> submits current answers with integrity score 0
    Coding -> saves current code draft and finalizes
    Interview -> ends interview session and generates report
    """
    assessment_type = assessment_type.upper()
    
    if assessment_type == "APTITUDE":
        from modules.assessment.models import AssessmentAttempt
        from modules.assessment.logic import evaluate_and_close_attempt
        
        attempt = db.query(AssessmentAttempt).filter(
            AssessmentAttempt.candidate_id == candidate_id,
            AssessmentAttempt.status == "IN_PROGRESS"
        ).first()
        if attempt:
            attempt.integrity_score = 0
            evaluate_and_close_attempt(attempt, db, is_terminated=True)
            
    elif assessment_type == "CODING":
        from modules.coding_assessment.models import CodingAttempt
        from modules.coding_assessment.logic import CodingAssessmentLogic
        
        attempt = db.query(CodingAttempt).filter(
            CodingAttempt.candidate_id == candidate_id,
            CodingAttempt.status == "IN_PROGRESS"
        ).first()
        if attempt:
            CodingAssessmentLogic.finish_attempt(attempt.id, db, is_terminated=True)
            
    elif assessment_type == "INTERVIEW":
        from modules.interview_assessment.models import InterviewSession
        from modules.interview_assessment.interview_manager import InterviewManager
        
        session_record = db.query(InterviewSession).filter(
            InterviewSession.candidate_id == candidate_id,
            InterviewSession.status == "IN_PROGRESS"
        ).first()
        if session_record:
            InterviewManager.finalize_session(session_record.id, db, is_terminated=True)


def get_proctoring_status(candidate_id: int, assessment_type: str) -> dict:
    """
    Get current in-memory status of monitoring.
    """
    assessment_type = assessment_type.upper()
    session = registry.get_session(candidate_id, assessment_type)
    if session:
        return {
            "is_monitoring": True,
            "integrity_score": session.integrity_score,
            "violation_count": session.violation_count,
            "warning_level": session.warning_level,
            "status": session.status
        }
    return {
        "is_monitoring": False,
        "integrity_score": 100,
        "violation_count": 0,
        "warning_level": 0,
        "status": "INACTIVE"
    }
