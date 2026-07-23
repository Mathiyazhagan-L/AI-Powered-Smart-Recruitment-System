"""
Integrity Score Module for AIHire Proctoring System

This module manages the integrity score calculation for proctoring.
It tracks the candidate's integrity score and applies penalties for violations.

Initial Score: 100
Score never goes below 0

Penalties:
- TAB_SWITCH: -5
- COPY: -5
- PASTE: -5
- RIGHT_CLICK: -5
- REFRESH: -10
- LEAVE_PAGE: -10
- FULLSCREEN_EXIT: -10
- NO_FACE: -10
- LOOKING_AWAY: -10
- MULTIPLE_FACES: -20
- MULTIPLE_PERSONS: -20
- PHONE_DETECTED: -25
"""


class IntegrityScore:
    """
    Manages integrity score calculation and penalty system.
    
    Attributes:
        score (int): Current integrity score
        initial_score (int): Starting score (default: 100)
        penalties (dict): Penalty values for each violation type
    """
    
    def __init__(self, initial_score: int = 100):
        """
        Initialize Integrity Score Manager.
        
        Args:
            initial_score: Starting integrity score (default: 100)
        """
        self.score = initial_score
        self.initial_score = initial_score
        self.penalties = {
            'TAB_SWITCH': -5,
            'COPY': -5,
            'PASTE': -5,
            'COPY_PASTE': -5,
            'RIGHT_CLICK': -5,
            'REFRESH': -10,
            'LEAVE_PAGE': -10,
            'FULLSCREEN_EXIT': -10,
            'NO_FACE': -15,
            'NO_FACE_DETECTED': -15,
            'LOOKING_AWAY': -10,
            'MULTIPLE_FACES': -20,
            'MULTIPLE_PERSONS': -20,
            'PHONE_DETECTED': -25,
            'DEV_TOOLS': -10,
        }
    
    def apply_penalty(self, violation_type: str) -> dict:
        """
        Apply penalty for a violation type.
        
        Args:
            violation_type: Type of violation (e.g., 'TAB_SWITCH', 'COPY', etc.)
        
        Returns:
            dict: Response containing new score and penalty applied
        """
        penalty = self.penalties.get(violation_type, 0)
        
        # Apply penalty and ensure score doesn't go below 0
        self.score = max(0, self.score + penalty)
        
        return {
            'violation_type': violation_type,
            'penalty': penalty,
            'new_score': self.score,
            'previous_score': self.score - penalty
        }
    
    def get_score(self) -> int:
        """
        Get current integrity score.
        
        Returns:
            int: Current integrity score
        """
        return self.score
    
    def reset(self):
        """Reset score to initial value."""
        self.score = self.initial_score
    
    def get_status(self) -> dict:
        """
        Get current integrity score status.
        
        Returns:
            dict: Current status including score and penalty information
        """
        return {
            'score': self.score,
            'initial_score': self.initial_score,
            'penalties': self.penalties
        }
