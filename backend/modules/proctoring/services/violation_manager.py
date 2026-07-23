"""
Violation Manager Module for AIHire Proctoring System

This module manages violation tracking, warning generation, and assessment termination.
It maintains a count of violations and triggers appropriate actions based on the violation count.

Rules:
- 6-violation graduated warning system
"""

WARNING_MESSAGES = {
    1: "Suspicious activity detected. Please continue the assessment honestly.",
    2: "Repeated suspicious activity detected. Warning 2 of 6.",
    3: "This is your 3rd warning. Continued violations will end your assessment.",
    4: "Warning 4 of 6. Further violations may result in termination.",
    5: "Final Warning! One more violation will terminate your assessment.",
    6: "Assessment Terminated due to repeated malpractice violations."
}

VIOLATION_MESSAGES = {
    "NO_FACE_DETECTED": "No face detected! Please ensure you are visible in the camera.",
    "NO_FACE": "No face detected! Please ensure you are visible in the camera.",
    "MULTIPLE_FACES": "Multiple faces detected. Only you should be in the camera frame.",
    "MULTIPLE_PERSONS": "Multiple persons detected in the camera. You must be alone.",
    "PHONE_DETECTED": "Phone/Device detected! Electronic devices are not allowed during the assessment.",
    "LOOKING_AWAY": "Please look at the screen. Looking away is flagged as suspicious.",
    "TAB_SWITCH": "You switched away from the assessment tab.",
    "FULLSCREEN_EXIT": "You exited fullscreen mode. Please stay in fullscreen.",
    "COPY_PASTE": "Copy/Paste is not allowed during the assessment.",
    "DEV_TOOLS": "Developer tools are not allowed during the assessment.",
    "RIGHT_CLICK": "Right-click is disabled during the assessment.",
}


class ViolationManager:
    """
    Manages violation tracking and warning system for proctoring.
    
    Attributes:
        violations (int): Current violation count
        max_violations (int): Maximum allowed violations before termination
        is_terminated (bool): Flag indicating if assessment is terminated
    """
    
    def __init__(self, max_violations: int = 6):
        """
        Initialize Violation Manager.
        
        Args:
            max_violations: Maximum number of violations allowed (default: 6)
        """
        self.violations = 0
        self.max_violations = max_violations
        self.is_terminated = False
    
    def add_violation(self, violation_type: str) -> dict:
        """
        Add a violation and return the appropriate response.
        """
        if self.is_terminated:
            return {
                'action': 'TERMINATED',
                'message': 'Assessment already terminated',
                'warning_level': self.max_violations,
                'violations': self.violations,
                'is_terminated': True
            }

        self.violations += 1
        violation_desc = VIOLATION_MESSAGES.get(violation_type, f"{violation_type.replace('_', ' ').title()} detected.")

        if self.violations >= self.max_violations:
            self.is_terminated = True
            action = 'TERMINATED'
            base_msg = WARNING_MESSAGES.get(self.max_violations, "Assessment Terminated.")
            message = f"❌ {base_msg}"
        else:
            action = f'WARNING_{self.violations}'
            base_msg = WARNING_MESSAGES.get(self.violations, f"Warning {self.violations}.")
            message = f"⚠ {violation_desc} ({base_msg})"

        return {
            'action': action,
            'message': message,
            'warning_level': self.violations,
            'violations': self.violations,
            'is_terminated': self.is_terminated
        }
    
    def reset(self):
        """Reset violation count and termination status."""
        self.violations = 0
        self.is_terminated = False
    
    def get_status(self) -> dict:
        """
        Get current violation status.
        
        Returns:
            dict: Current status including violation count and termination status
        """
        return {
            'violations': self.violations,
            'max_violations': self.max_violations,
            'is_terminated': self.is_terminated
        }
