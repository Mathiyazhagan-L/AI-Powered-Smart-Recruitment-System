import os
import sys
from fastapi.testclient import TestClient

print("--- STARTING TRACE ---")
print(f"CWD: {os.getcwd()}")
print(f"Initial os.getenv('GOOGLE_CLIENT_ID'): {os.getenv('GOOGLE_CLIENT_ID')}")

# Import main (which loads dotenv)
from main import app

print(f"After main import os.getenv('GOOGLE_CLIENT_ID'): {os.getenv('GOOGLE_CLIENT_ID')}")

client = TestClient(app)

response = client.post("/auth/google/verify", json={"credential": "dummy_code"})

print(f"Response Status: {response.status_code}")
print(f"Response Body: {response.json()}")
print("--- END TRACE ---")
