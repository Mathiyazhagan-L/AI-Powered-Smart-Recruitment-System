import cv2
import time
import base64
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Fallback pattern if YOLO is not installed
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    logger.warning("ultralytics package not found. ObjectDetector will run in fallback simulation mode.")


class ObjectDetector:
    """
    Monitors webcam frames using YOLO to detect phones and multiple persons.
    Throttles processing to 1 run every 3 seconds.
    """
    
    def __init__(self, violation_manager, integrity_score):
        """
        Initialize ObjectDetector with shared managers.
        
        Args:
            violation_manager: Shared ViolationManager
            integrity_score: Shared IntegrityScore
        """
        self.violation_manager = violation_manager
        self.integrity_score_manager = integrity_score
        
        self.last_yolo_time = 0.0
        self.last_phone_violation = 0.0
        self.last_person_violation = 0.0
        self.cooldown = 5.0
        
        if YOLO_AVAILABLE:
            try:
                self.model = YOLO("yolov8n.pt")
            except Exception as e:
                logger.error(f"Failed to load YOLO model: {e}")
                self.model = None
        else:
            self.model = None

    def process_frame(self, frame_bytes) -> dict:
        """
        Process a single frame for object detection.
        
        Args:
            frame_bytes: base64-encoded webcam frame
            
        Returns:
            dict: Detection results containing phone status, person count, etc.
        """
        current_time = time.time()
        
        # YOLO throttling: only process if >= 3 seconds since last run
        if current_time - self.last_yolo_time < 3.0:
            return {
                "status": "THROTTLED",
                "phone_detected": False,
                "person_count": 0,
                "violation_triggered": False,
                "violation_type": None,
                "violation_result": None
            }
            
        self.last_yolo_time = current_time
        
        # Fallback simulation if YOLO model is not loaded
        if self.model is None:
            return {
                "status": "FALLBACK_NO_MODEL",
                "phone_detected": False,
                "person_count": 1,
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
            logger.error(f"Error decoding object detection frame: {e}")
            return {
                "status": "DECODE_ERROR",
                "phone_detected": False,
                "person_count": 0,
                "violation_triggered": False,
                "violation_type": None,
                "violation_result": None
            }
            
        # Run inference
        try:
            results = self.model(frame, verbose=False)
        except Exception as e:
            logger.error(f"Error running YOLO model: {e}")
            return {
                "status": "INFERENCE_ERROR",
                "phone_detected": False,
                "person_count": 0,
                "violation_triggered": False,
                "violation_type": None,
                "violation_result": None
            }
            
        phone_detected = False
        person_count = 0
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                label = self.model.names[cls]
                if label == "person":
                    person_count += 1
                elif label == "cell phone":
                    phone_detected = True
                    
        violation_triggered = False
        violation_type = None
        violation_result = None
        
        # Phone violation check with independent 5s cooldown
        if phone_detected:
            if current_time - self.last_phone_violation >= self.cooldown:
                violation_triggered = True
                violation_type = "PHONE_DETECTED"
                self.last_phone_violation = current_time
                
        # Person violation check with independent 5s cooldown
        if person_count > 1:
            if current_time - self.last_person_violation >= self.cooldown:
                violation_triggered = True
                violation_type = "MULTIPLE_PERSONS"
                self.last_person_violation = current_time
                
        # Emit violation if triggered
        if violation_triggered and violation_type:
            self.integrity_score_manager.apply_penalty(violation_type)
            violation_result = self.violation_manager.add_violation(violation_type)
            
        return {
            "status": "SUCCESS",
            "phone_detected": phone_detected,
            "person_count": person_count,
            "violation_triggered": violation_triggered,
            "violation_type": violation_type,
            "violation_result": violation_result
        }