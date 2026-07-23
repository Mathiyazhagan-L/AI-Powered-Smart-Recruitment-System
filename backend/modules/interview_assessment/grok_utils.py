import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


def get_groq_client() -> OpenAI:
    """
    Returns an OpenAI-compatible client configured for the Groq API.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    return OpenAI(api_key=api_key, base_url=GROQ_BASE_URL)


def grok_chat(prompt: str, json_mode: bool = True) -> str:
    """
    Sends a prompt to Groq and returns the response text.
    Uses llama-3.3-70b-versatile by default (set GROQ_MODEL env var to override).
    """
    client = get_groq_client()
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Groq requires the word 'json' in the prompt when using json_object response_format
    if json_mode and "json" not in prompt.lower():
        prompt = prompt + "\n\nRespond with valid JSON only."

    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content.strip()
