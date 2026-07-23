import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

print(f"Loaded GEMINI_API_KEY: {'[SET]' if api_key else '[NOT SET]'}")
print(f"Loaded GEMINI_MODEL: {model_name}")

if not api_key:
    print("Error: GEMINI_API_KEY is not set in .env")
    exit(1)

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Say Gemini is working successfully")
    print("\nAPI Response:")
    print(response.text)
    print("\nStatus: SUCCESS - The Gemini API is working correctly in this folder!")
except Exception as e:
    print(f"\nStatus: FAILED - Error calling Gemini: {e}")
