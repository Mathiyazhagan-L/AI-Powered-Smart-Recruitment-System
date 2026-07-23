def calculate_grade(total_score: float) -> str:
    """
    Assigns grades based on criteria:
    A+ (90-100), A (80-89), B (70-79), C (60-69), D (Below 60)
    """
    if total_score >= 90.0:
        return "A+"
    elif total_score >= 80.0:
        return "A"
    elif total_score >= 70.0:
        return "B"
    elif total_score >= 60.0:
        return "C"
    else:
        return "D"

def determine_recommendation(total_score: float, technical_score: float) -> str:
    """
    Generates final recommendation status: 'Recommended' or 'Not Recommended'.
    Typically recommends if total score is >= 70 and technical score is >= 25.
    """
    if total_score >= 70.0 and technical_score >= 24.0:
        return "Recommended"
    return "Not Recommended"
