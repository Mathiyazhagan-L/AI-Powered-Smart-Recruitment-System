import os
import time
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

def get_gemini_model() -> genai.GenerativeModel:
    """
    Configures and returns the configured Gemini model based on environment variables.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    
    genai.configure(api_key=gemini_key)
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    return genai.GenerativeModel(model_name)

def generate_content_with_retry(model: genai.GenerativeModel, contents, generation_config=None, max_retries=5, initial_delay=5.0) -> any:
    """
    Calls model.generate_content with exponential backoff retry logic for 429 Rate Limits.
    """
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            if generation_config:
                return model.generate_content(contents, generation_config=generation_config)
            else:
                return model.generate_content(contents)
        except Exception as e:
            err_str = str(e).lower()
            # Catch 429, ResourceExhausted, quota limit errors
            if "429" in err_str or "quota" in err_str or "resourceexhausted" in err_str or "rate limit" in err_str:
                # Fail fast on daily or project limits that won't clear in seconds
                if "perday" in err_str or "daily" in err_str or "project" in err_str or "billing" in err_str or "plan" in err_str:
                    logger.error(f"Gemini API daily/project quota limit exceeded. Failing fast: {e}")
                    raise e

                if attempt < max_retries - 1:
                    logger.warning(
                        f"Gemini API rate limited/quota exceeded (429). "
                        f"Retrying in {delay} seconds (Attempt {attempt + 1}/{max_retries}). Error: {e}"
                    )
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                    continue
            logger.error(f"Gemini API call failed permanently: {e}")
            raise e
