import os
import logging
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def transcribe_audio(file_path: str) -> str:
    """
    Audio-to-text transcription fallback using Groq's whisper-large-v3 API.
    This is called when the browser transcript is empty.
    """
    try:
        load_dotenv()
        groq_api_key = os.environ.get("GROQ_API_KEY")
        if not groq_api_key:
            logger.error("GROQ_API_KEY not found in environment for STT fallback.")
            return ""
            
        logger.info(f"Uploading {file_path} to Groq API for transcription...")
        
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {groq_api_key}"
        }
        
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, "audio/webm")
            }
            data = {
                "model": "whisper-large-v3",
                "response_format": "json"
            }
            response = requests.post(url, headers=headers, files=files, data=data)
            
        if response.status_code == 200:
            transcript = response.json().get("text", "").strip()
            logger.info(f"Groq STT successful (Length: {len(transcript)})")
            return transcript
        else:
            logger.error(f"Groq STT failed. Status: {response.status_code}, Error: {response.text}")
            return ""
    except Exception as e:
        logger.error(f"Error transcribing audio with Groq: {e}")
        return ""
