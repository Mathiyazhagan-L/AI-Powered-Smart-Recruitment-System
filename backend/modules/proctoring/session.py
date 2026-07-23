import uuid
import datetime
import threading
from dataclasses import dataclass, field
from typing import Dict, Tuple, Optional

from modules.proctoring.services.browser_monitor import BrowserMonitor
from modules.proctoring.services.webcam_monitor import WebcamMonitor
from modules.proctoring.services.object_detector import ObjectDetector
from modules.proctoring.services.violation_manager import ViolationManager
from modules.proctoring.services.integrity_score import IntegrityScore


@dataclass
class ProctoringSession:
    candidate_id: int
    assessment_type: str  # APTITUDE | CODING | INTERVIEW
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    last_activity: datetime.datetime = field(default_factory=datetime.datetime.utcnow)
    
    violation_manager: ViolationManager = field(default_factory=ViolationManager)
    integrity_score_manager: IntegrityScore = field(default_factory=IntegrityScore)
    
    browser_monitor: BrowserMonitor = None
    webcam_monitor: WebcamMonitor = None
    object_detector: ObjectDetector = None

    @property
    def integrity_score(self) -> int:
        return self.integrity_score_manager.get_score()

    @property
    def violation_count(self) -> int:
        return self.violation_manager.violations

    @property
    def warning_level(self) -> int:
        return self.violation_manager.violations

    @property
    def status(self) -> str:
        return "TERMINATED" if self.violation_manager.is_terminated else "ACTIVE"

    def __post_init__(self):
        self.browser_monitor = BrowserMonitor(self.violation_manager, self.integrity_score_manager)
        self.webcam_monitor = WebcamMonitor(self.violation_manager, self.integrity_score_manager)
        self.object_detector = ObjectDetector(self.violation_manager, self.integrity_score_manager)


class ProctoringSessionRegistry:
    """
    Thread-safe registry for active proctoring sessions.
    """
    
    def __init__(self):
        self._sessions: Dict[Tuple[int, str], ProctoringSession] = {}
        self._lock = threading.Lock()

    def create_session(self, candidate_id: int, assessment_type: str) -> ProctoringSession:
        """Create a new monitoring session for a candidate."""
        with self._lock:
            key = (candidate_id, assessment_type.upper())
            session = ProctoringSession(candidate_id=candidate_id, assessment_type=assessment_type.upper())
            # Start browser monitoring
            session.browser_monitor.start_monitoring()
            self._sessions[key] = session
            return session

    def get_session(self, candidate_id: int, assessment_type: str) -> Optional[ProctoringSession]:
        """Retrieve active monitoring session."""
        with self._lock:
            key = (candidate_id, assessment_type.upper())
            session = self._sessions.get(key)
            if session:
                session.last_activity = datetime.datetime.utcnow()
            return session

    def remove_session(self, candidate_id: int, assessment_type: str) -> Optional[ProctoringSession]:
        """Remove and return active monitoring session."""
        with self._lock:
            key = (candidate_id, assessment_type.upper())
            return self._sessions.pop(key, None)

    def list_sessions(self) -> list:
        """List all current sessions."""
        with self._lock:
            return list(self._sessions.values())


# Global registry instance
registry = ProctoringSessionRegistry()
