import cv2
import mediapipe as mp
import time
import base64
import numpy as np
import logging

logger = logging.getLogger(__name__)


class WebcamMonitor:
    """
    Monitors webcam frame for candidate behavior (no face, looking away, multiple faces).
    Throttles frame processing to 1 frame per second.
    """
    
    def __init__(self, violation_manager, integrity_score):
        """
        Initialize WebcamMonitor with shared managers.
        
        Args:
            violation_manager: Shared ViolationManager
            integrity_score: Shared IntegrityScore
        """
        self.violation_manager = violation_manager
        self.integrity_score_manager = integrity_score
        
        self.last_frame_time = 0.0
        self.no_face_start = None
        self.look_away_start = None
        self.last_multiple_faces_violation = 0.0
        
        # Initialize MediaPipe Solutions
        try:
            self.mp_face_detection = mp.solutions.face_detection
            self.face_detection = self.mp_face_detection.FaceDetection(
                model_selection=0,
                min_detection_confidence=0.5
            )

            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                static_image_mode=False,
                max_num_faces=2,
                refine_landmarks=True
            )
            self.mp_available = True
        except (AttributeError, ImportError):
            self.mp_available = False
            logger.warning("MediaPipe solutions not available. WebcamMonitor will run in fallback simulation mode.")

    def detect_head_direction(self, landmarks) -> str:
        """
        Determine if the candidate is looking away based on face mesh landmarks.
        """
        nose = landmarks.landmark[1]
        left_eye = landmarks.landmark[33]
        right_eye = landmarks.landmark[263]

        center_x = (left_eye.x + right_eye.x) / 2
        diff = nose.x - center_x

        if diff < -0.04:
            return "LOOKING_LEFT"
        elif diff > 0.04:
            return "LOOKING_RIGHT"
        return "LOOKING_CENTER"

    def process_frame(self, frame_bytes) -> dict:
        """
        Process a single base64-encoded frame.
        
        Args:
            frame_bytes: base64-encoded string of the webcam frame image
            
        Returns:
            dict: Results containing face count, status, violation status, etc.
        """
        current_time = time.time()
        
        # Frame throttling: Process 1 webcam frame per second
        if current_time - self.last_frame_time < 1.0:
            return {
                "status": "THROTTLED",
                "face_count": None,
                "violation_triggered": False,
                "violation_type": None,
                "violation_result": None
            }
            
        self.last_frame_time = current_time
        
        if not self.mp_available:
            return {
                "status": "FALLBACK_NO_MODEL",
                "face_count": 1,
                "violation_triggered": False,
                "violation_type": None,
                "violation_result": None
            }
        
        try:
            # Decode frame
            if isinstance(frame_bytes, str):
                if "," in frame_bytes:
                    frame_bytes = frame_bytes.split(",")[1]
                decoded = base64.b64decode(frame_bytes)
            else:
                decoded = frame_bytes
                
            nparr = np.frombuffer(decoded, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if frame is None:
                raise ValueError("Could not decode image frame.")
        except Exception as e:
            logger.error(f"Error decoding webcam frame: {e}")
            return {
                "status": "DECODE_ERROR",
                "face_count": 0,
                "violation_triggered": False,
                "violation_type": None,
                "violation_result": None
            }
            
        # Convert BGR to RGB for MediaPipe
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Process detection and mesh
        face_results = self.face_detection.process(rgb)
        mesh_results = self.face_mesh.process(rgb)
        
        face_count = len(face_results.detections) if (face_results and face_results.detections) else 0
        status = "FACE_PRESENT" if face_count == 1 else "NO_FACE"
        
        violation_triggered = False
        violation_type = None
        violation_result = None
        
        # 1. No Face Detection — trigger after 3 continuous seconds of no face
        if face_count == 0:
            if self.no_face_start is None:
                self.no_face_start = current_time
            elif current_time - self.no_face_start >= 3.0:
                violation_triggered = True
                violation_type = "NO_FACE_DETECTED"
                self.no_face_start = None  # Reset so next absence starts a fresh window
        else:
            self.no_face_start = None
            
        # 2. Multiple Faces Cooldown (5 seconds)
        if face_count > 1:
            status = "MULTIPLE_FACES"
            if current_time - self.last_multiple_faces_violation >= 5.0:
                violation_triggered = True
                violation_type = "MULTIPLE_FACES"
                self.last_multiple_faces_violation = current_time
                
        # 3. Looking Away Timer (3 seconds)
        if face_count == 1 and mesh_results and mesh_results.multi_face_landmarks:
            direction = self.detect_head_direction(mesh_results.multi_face_landmarks[0])
            status = direction
            if direction in ("LOOKING_LEFT", "LOOKING_RIGHT"):
                if self.look_away_start is None:
                    self.look_away_start = current_time
                elif current_time - self.look_away_start >= 3.0:
                    violation_triggered = True
                    violation_type = "LOOKING_AWAY"
                    self.look_away_start = current_time  # Reset timer
            else:
                self.look_away_start = None
        else:
            self.look_away_start = None
            
        # Apply violation via managers
        if violation_triggered and violation_type:
            self.integrity_score_manager.apply_penalty(violation_type)
            violation_result = self.violation_manager.add_violation(violation_type)
            
        return {
            "face_count": face_count,
            "status": status,
            "violation_triggered": violation_triggered,
            "violation_type": violation_type,
            "violation_result": violation_result
        }
