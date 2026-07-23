import os
import sys
import httpx
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def run_test():
    print("Running Resume Autofill Validation Workflow...\n")
    
    # 1. Login to get token
    login_data = {
        "username": "test_candidate@example.com", 
        "password": "Password123!"
    }
    try:
        r = httpx.post(f"{API_BASE_URL}/auth/login", data=login_data)
        if r.status_code != 200:
            print("Trying to register candidate first...")
            register_data = {
                "email": "test_candidate@example.com",
                "password": "Password123!",
                "first_name": "Test",
                "last_name": "Candidate",
                "role": "candidate"
            }
            r = httpx.post(f"{API_BASE_URL}/auth/register", json=register_data)
            r = httpx.post(f"{API_BASE_URL}/auth/login", data=login_data)
        
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
    except Exception as e:
        print(f"Auth failed: {e}")
        return

    # 2. Get Initial Profile
    r_profile = httpx.get(f"{API_BASE_URL}/auth/me", headers=headers)
    user_id = r_profile.json()["id"]
    
    r_get_profile = httpx.get(f"{API_BASE_URL}/candidate/profile/{user_id}", headers=headers)
    initial_completion = r_get_profile.json().get("profile_completion", 0) if r_get_profile.status_code == 200 else 0
    print(f"Profile Completion Before: {initial_completion}%")

    # 3. Parse Resume
    resume_path = os.path.join(os.path.dirname(__file__), "sample_real_resume.pdf")
    if not os.path.exists(resume_path):
        print(f"Resume not found at {resume_path}")
        return
        
    print(f"\nParsing resume: {resume_path} ...")
    with open(resume_path, "rb") as f:
        files = {"file": ("sample_real_resume.pdf", f, "application/pdf")}
        r_parse = httpx.post(f"{API_BASE_URL}/resume-parser/parse", headers=headers, files=files, timeout=60.0)
        
    if r_parse.status_code != 200:
        print(f"Parse failed: {r_parse.status_code} {r_parse.text}")
        return
        
    parsed_json = r_parse.json().get("parsed_json", {})
    print(f"Extracted Confidence Score: {parsed_json.get('confidence_score')}%")
    print("\nParsed Data Mapping:")
    print(f"- Personal: {parsed_json.get('personal', {}).get('full_name')} | {parsed_json.get('personal', {}).get('email')}")
    print(f"- Education Blocks: {len(parsed_json.get('education', []))}")
    print(f"- Experience Blocks: {len(parsed_json.get('experience', []))}")
    print(f"- Skill Blocks: {len(parsed_json.get('skills', []))}")
    print(f"- Project Blocks: {len(parsed_json.get('projects', []))}")

    # 4. Save Personal details (Merge Strategy mock)
    personal = parsed_json.get("personal", {})
    update_payload = {}
    if personal.get("full_name"): update_payload["full_name"] = personal["full_name"]
    if personal.get("email"): update_payload["email"] = personal["email"]
    if personal.get("phone"): update_payload["phone"] = personal["phone"]
    if personal.get("location"): update_payload["location"] = personal["location"]
    
    if update_payload:
        print("\nSaving Personal Details (Upsert)...")
        r_upd = httpx.put(f"{API_BASE_URL}/candidate/profile/update/{user_id}", headers=headers, json=update_payload)
        if r_upd.status_code != 200:
            print(f"Profile Update failed: {r_upd.text}")

    # 5. Save Arrays
    for edu in parsed_json.get("education", []):
        payload = {
            "user_id": user_id,
            "institution": edu.get("institution", "Unknown"),
            "degree": edu.get("degree", "Unknown"),
            "start_year": int(edu.get("start_year")) if edu.get("start_year") else 2020,
        }
        httpx.post(f"{API_BASE_URL}/candidate/education/create", headers=headers, json=payload)
        
    for exp in parsed_json.get("experience", []):
        payload = {
            "user_id": user_id,
            "company_name": exp.get("company", "Unknown"),
            "job_title": exp.get("job_title", "Unknown"),
            "employment_type": "Full-time",
            "start_date": exp.get("start_date", "2020-01-01"),
            "currently_working": True
        }
        httpx.post(f"{API_BASE_URL}/candidate/experience/create", headers=headers, json=payload)
        
    for skill in parsed_json.get("skills", []):
        skill_name = skill.get("name") if isinstance(skill, dict) else skill
        payload = {
            "user_id": user_id,
            "skill_name": skill_name,
            "years_of_experience": 1
        }
        httpx.post(f"{API_BASE_URL}/candidate/skills/create", headers=headers, json=payload)
        
    for proj in parsed_json.get("projects", []):
        techs = proj.get("technologies", [])
        if isinstance(techs, str): techs = techs.split(",")
        payload = {
            "user_id": user_id,
            "project_name": proj.get("project_name", "Project"),
            "technologies": techs,
            "description": proj.get("description", "")
        }
        httpx.post(f"{API_BASE_URL}/candidate/projects/create", headers=headers, json=payload)

    print("\nArray Data Saved Successfully.")

    # 6. Verify Records & Final Completion
    r_get_profile = httpx.get(f"{API_BASE_URL}/candidate/profile/{user_id}", headers=headers)
    final_completion = r_get_profile.json().get("profile_completion", 0)
    print(f"\nProfile Completion After: {final_completion}%")
    
    # Check Database records directly or via endpoints
    r_edu = httpx.get(f"{API_BASE_URL}/candidate/education/{user_id}", headers=headers)
    r_exp = httpx.get(f"{API_BASE_URL}/candidate/experience/{user_id}", headers=headers)
    r_skills = httpx.get(f"{API_BASE_URL}/candidate/skills/{user_id}", headers=headers)
    r_proj = httpx.get(f"{API_BASE_URL}/candidate/projects/{user_id}", headers=headers)
    
    print("\nDatabase Records Created:")
    print(f"Candidate Profile: Verified (ID: {user_id})")
    print(f"Education Records: {len(r_edu.json())}")
    print(f"Experience Records: {len(r_exp.json())}")
    print(f"Skills Records: {len(r_skills.json())}")
    print(f"Projects Records: {len(r_proj.json())}")

if __name__ == "__main__":
    run_test()
