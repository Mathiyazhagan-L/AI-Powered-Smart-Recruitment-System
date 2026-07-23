import sys
import os
import json
from fastapi.testclient import TestClient

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))
os.environ["DB_USER"] = "dummy"
os.environ["DB_PASSWORD"] = "dummy"

from main import app
from modules.auth.logic import create_access_token

client = TestClient(app)

def run_verifications():
    print("="*50)
    print("PHASE 2 VALIDATION")
    print("="*50)
    
    token = create_access_token({"sub": "2", "role": "candidate"})
    headers = {"Authorization": f"Bearer {token}"}
    
    # 1. Test Resume Parser with dummy resume
    print("\n[1] Verifying Resume Parser Endpoint...")
    dummy_file_content = b"Mock PDF Resume Content"
    files = {"file": ("resume.pdf", dummy_file_content, "application/pdf")}
    res = client.post("/resume-parser/parse", files=files, headers=headers)
    if res.status_code == 200:
        print("  ✓ Resume Parser endpoint reachable and parsed successfully.")
    else:
        print(f"  ✗ Resume Parser failed: {res.status_code} {res.text}")
        
    # 2. Test Profile Completion API logic
    # In my implementation, Profile Completion is largely calculated on the frontend.
    # The requirement was "Verify Profile Completion calculations."
    # Wait, the restrictions are calculated on the frontend (useProfileCompletion hook) and maybe enforced on the backend.
    # The requirement specifically mentions "Verify access restrictions: Apply Job, Assessment, Interview."
    # Since I built this on the frontend, I should verify the backend restrictions if they exist.
    # Let's check if the backend has these restrictions. If not, I should document that they are frontend restrictions, or implement them in the backend.

if __name__ == "__main__":
    run_verifications()
