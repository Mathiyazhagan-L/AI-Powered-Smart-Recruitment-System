"""
Browser Monitor Module for AIHire Proctoring System

This module provides the detection logic for browser-based malpractice activities.
It integrates with the ViolationManager and IntegrityScore to track and penalize violations.

Detection Types:
- TAB_SWITCH: When candidate leaves the assessment tab
- FULLSCREEN_EXIT: When candidate exits fullscreen mode
- COPY: When candidate copies content (CTRL+C)
- PASTE: When candidate pastes content (CTRL+V)
- RIGHT_CLICK: When candidate right-clicks
- REFRESH: When candidate refreshes the page (F5, CTRL+R)
- LEAVE_PAGE: When candidate attempts to leave the assessment
"""

from typing import Dict, Any
from .violation_manager import ViolationManager
from .integrity_score import IntegrityScore


class BrowserMonitor:
    """
    Main browser monitoring class that coordinates violation detection,
    integrity scoring, and violation management.
    
    Attributes:
        violation_manager (ViolationManager): Manages violation tracking
        integrity_score (IntegrityScore): Manages integrity scoring
        is_monitoring (bool): Flag indicating if monitoring is active
    """
    
    def __init__(self, violation_manager: ViolationManager = None, integrity_score: IntegrityScore = None):
        """
        Initialize Browser Monitor with optional shared violation and score managers.
        """
        self.violation_manager = violation_manager if violation_manager is not None else ViolationManager()
        self.integrity_score = integrity_score if integrity_score is not None else IntegrityScore()
        self.is_monitoring = False
    
    def start_monitoring(self):
        """Start the browser monitoring system."""
        self.is_monitoring = True
        self.violation_manager.reset()
        self.integrity_score.reset()
    
    def stop_monitoring(self):
        """Stop the browser monitoring system."""
        self.is_monitoring = False
    
    def detect_violation(self, violation_type: str) -> Dict[str, Any]:
        """
        Detect and process a violation.
        
        Args:
            violation_type: Type of violation detected
        
        Returns:
            dict: Response containing violation details, score change, and action
        """
        if not self.is_monitoring:
            return {
                'status': 'NOT_MONITORING',
                'message': 'Monitoring is not active'
            }
        
        # Apply penalty to integrity score
        score_result = self.integrity_score.apply_penalty(violation_type)
        
        # Add violation and get response
        violation_result = self.violation_manager.add_violation(violation_type)
        
        # Check if assessment should be terminated
        if violation_result.get('action') == 'TERMINATED':
            self.stop_monitoring()
        
        return {
            'status': 'VIOLATION_DETECTED',
            'violation_type': violation_type,
            'score_change': score_result,
            'violation_response': violation_result,
            'is_terminated': violation_result.get('action') == 'TERMINATED',
            'warning_level': violation_result.get('warning_level', 0)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status.
        
        Returns:
            dict: Current status including score, violations, and monitoring state
        """
        return {
            'is_monitoring': self.is_monitoring,
            'integrity_score': self.integrity_score.get_score(),
            'violations': self.violation_manager.get_status()
        }
    
    def reset(self):
        """Reset the monitoring system to initial state."""
        self.violation_manager.reset()
        self.integrity_score.reset()
        self.is_monitoring = False


# Violation type constants for easy reference
VIOLATION_TYPES = {
    'TAB_SWITCH': 'Tab Switching',
    'FULLSCREEN_EXIT': 'Fullscreen Exit',
    'COPY': 'Copy Action',
    'PASTE': 'Paste Action',
    'RIGHT_CLICK': 'Right Click',
    'REFRESH': 'Page Refresh',
    'LEAVE_PAGE': 'Leave Page'
}
