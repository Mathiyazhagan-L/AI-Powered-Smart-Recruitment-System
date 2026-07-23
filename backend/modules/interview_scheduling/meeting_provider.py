# Future-Proof Meeting Provider Configuration
# Prepared for future integrations like Google Calendar API, MS Teams, Zoom, etc.

PROVIDER_ID = "MANUAL_GOOGLE_MEET"
PROVIDER_NAME = "Google Meet"

def get_meeting_provider_info():
    """
    Returns active meeting provider configuration.
    """
    return {
        "provider": PROVIDER_ID,
        "meeting_provider": PROVIDER_NAME
    }
