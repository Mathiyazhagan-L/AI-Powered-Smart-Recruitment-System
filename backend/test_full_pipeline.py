"""
Full Assessment Pipeline Test
Validates: Aptitude → Coding → Interview with proper JWT auth
"""
import requests
import sys

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "jane.candidate@test.com"
TEST_PASSWORD = "password123"
HEADERS = {}

def ok(msg):  print(f"\033[92m[PASS]\033[0m {msg}")
def warn(msg): print(f"\033[93m[WARN]\033[0m {msg}")
def err(msg):  print(f"\033[91m[FAIL]\033[0m {msg}")
def step(msg): print(f"\n\033[94m--- {msg} ---\033[0m")

def login():
    step("1. AUTHENTICATION")
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    if r.status_code != 200:
        err(f"Login failed ({r.status_code}): {r.text[:200]}")
        return None
    data = r.json()
    token = data.get("access_token") or data.get("token")
    if not token:
        err(f"No token in response: {data}")
        return None
    candidate_id = (data.get("user") or {}).get("id") or data.get("id")
    HEADERS["Authorization"] = f"Bearer {token}"
    ok(f"Authenticated — candidate_id={candidate_id}")
    return candidate_id

def test_aptitude(candidate_id):
    step("2. APTITUDE ASSESSMENT")

    # Reset any existing attempt first (dev action)
    requests.post(f"{BASE_URL}/assessment/reset", headers=HEADERS)

    r = requests.post(f"{BASE_URL}/assessment/start", headers=HEADERS)
    if r.status_code != 200:
        err(f"assessment/start failed: {r.text[:300]}")
        return False
    data = r.json()
    attempt_id = data["attempt_id"]
    questions = data["questions"]
    ok(f"Started aptitude: attempt_id={attempt_id}, {len(questions)} questions, remaining={data.get('remaining_seconds')}s")

    # Build answers — answer first option for each question
    answers = [{"question_id": q["question_id"], "selected_answer": list(q["options"].keys())[0] if q.get("options") else "A"} for q in questions]
    r = requests.post(f"{BASE_URL}/assessment/submit", headers=HEADERS, json={
        "attempt_id": attempt_id,
        "answers": answers,
        "integrity_score": 100,
    })
    if r.status_code != 200:
        err(f"assessment/submit failed: {r.text[:300]}")
        return False
    ok(f"Aptitude submitted")

    r = requests.get(f"{BASE_URL}/assessment/result/{candidate_id}", headers=HEADERS)
    if r.status_code != 200:
        warn(f"assessment/result failed: {r.text[:200]}")
        return True  # not a blocker
    result = r.json()
    ok(f"Aptitude result: score={result.get('aptitude_score')}%, status={result.get('status')}")
    return True

def test_coding(candidate_id):
    step("3. CODING ASSESSMENT")

    r = requests.post(f"{BASE_URL}/coding/start", headers=HEADERS)
    if r.status_code != 200:
        err(f"coding/start failed: {r.text[:300]}")
        return False, None
    data = r.json()
    attempt_id = data["attempt_id"]
    questions = data["questions"]
    ok(f"Started coding: attempt_id={attempt_id}, {len(questions)} questions, remaining={data.get('remaining_seconds')}s")

    if questions:
        q = questions[0]
        ok(f"Q1: {q.get('title')} [{q.get('difficulty')}]")

        # Run code
        r = requests.post(f"{BASE_URL}/coding/run", headers=HEADERS, json={
            "attempt_id": attempt_id,
            "question_id": q["question_id"],
            "source_code": "def twoSum(nums, target):\n    seen = {}\n    for i, v in enumerate(nums):\n        if target-v in seen:\n            return [seen[target-v], i]\n        seen[v] = i\n    return []",
            "language": "python",
        })
        if r.status_code == 200:
            run = r.json()
            ok(f"Run code: status={run.get('status')}, results={[x.get('passed') for x in run.get('results', [])]}")
        else:
            warn(f"Run code failed: {r.text[:200]}")

        # Submit solution
        r = requests.post(f"{BASE_URL}/coding/submit", headers=HEADERS, json={
            "attempt_id": attempt_id,
            "question_id": q["question_id"],
            "source_code": "def twoSum(nums, target):\n    seen = {}\n    for i, v in enumerate(nums):\n        if target-v in seen:\n            return [seen[target-v], i]\n        seen[v] = i\n    return []",
            "language": "python",
        })
        if r.status_code == 200:
            sub = r.json()
            ok(f"Submit: {sub.get('passed_test_cases')}/{sub.get('total_test_cases')} passed, score={sub.get('score')}%")
        else:
            warn(f"Submit failed: {r.text[:200]}")

    # Finish
    r = requests.post(f"{BASE_URL}/coding/finish?attempt_id={attempt_id}", headers=HEADERS)
    if r.status_code == 200:
        fin = r.json()
        ok(f"Coding finished: total_score={fin.get('total_score')}%, status={fin.get('status')}")
    else:
        warn(f"coding/finish: {r.text[:200]}")

    # Check result
    r = requests.get(f"{BASE_URL}/coding/result/{candidate_id}", headers=HEADERS)
    if r.status_code == 200:
        ok(f"Coding result verified in DB: score={r.json().get('total_score')}%")
    return True, attempt_id

def test_interview(candidate_id):
    step("4. INTERVIEW ASSESSMENT")

    r = requests.post(f"{BASE_URL}/interview/start", headers=HEADERS)
    if r.status_code != 200:
        err(f"interview/start failed: {r.text[:300]}")
        return False
    data = r.json()
    session_id = data["session_id"]
    questions = data.get("questions", [])
    ok(f"Started interview: session_id={session_id}, {len(questions)} questions, status={data.get('status')}")

    if questions:
        q = questions[0]
        ok(f"Q1: [{q.get('category')}] {q.get('question_text')[:80]}...")

        # Evaluate (no audio for test, use text)
        r = requests.post(f"{BASE_URL}/interview/evaluate", headers=HEADERS, json={
            "session_id": session_id,
            "question_id": q["id"],
        })
        if r.status_code == 200:
            ev = r.json()
            ok(f"Evaluation: score={ev.get('score')}, comm={ev.get('communication_score')}, tech={ev.get('technical_score')}")
        else:
            warn(f"Evaluate: {r.text[:200]}")

    # Finish
    r = requests.post(f"{BASE_URL}/interview/finish?session_id={session_id}", headers=HEADERS)
    if r.status_code == 200:
        fin = r.json()
        ok(f"Interview finished: grade={fin.get('grade')}, score={fin.get('total_score')}, recommendation={fin.get('hiring_recommendation')}")
    else:
        warn(f"interview/finish: {r.text[:200]}")

    # Check result
    r = requests.get(f"{BASE_URL}/interview/result/{candidate_id}", headers=HEADERS)
    if r.status_code == 200:
        ok(f"Interview result in DB: score={r.json().get('total_score')}")
    return True

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  AIHire Full Assessment Pipeline Test")
    print("="*60)

    candidate_id = login()
    if not candidate_id:
        print("\n[ABORT] Cannot authenticate. Ensure backend is running and test user exists.")
        sys.exit(1)

    test_aptitude(candidate_id)
    test_coding(candidate_id)
    test_interview(candidate_id)

    print("\n" + "="*60)
    print("  Pipeline Test Complete")
    print("="*60 + "\n")
