import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from modules.coding_assessment.evaluator import Evaluator

def test(label, code, expect_blocked=True):
    test_cases = [{"lhs": "x=1", "rhs": "1"}]
    result = Evaluator.run_code(code, test_cases, timeout=3.0)
    status = result.get("status", "UNKNOWN")
    if expect_blocked:
        blocked = status in ("COMPILE_ERROR", "TIMEOUT", "ERROR")
        print(f"[{'PASS' if blocked else 'FAIL'}] {label} -> status={status}")
    else:
        print(f"[INFO] {label} -> status={status}")

print("=== Infinite Loop Test ===")
test("Infinite while loop", "while True: pass", expect_blocked=True)

print("\n=== Dangerous Import Tests ===")
test("import os", "import os\ndef solve(x): return os.listdir('.')", expect_blocked=True)
test("import subprocess", "import subprocess\ndef solve(x): return subprocess.run(['whoami'])", expect_blocked=True)
test("import socket", "import socket\ndef solve(x): return socket.gethostname()", expect_blocked=True)
test("import shutil", "import shutil\ndef solve(x): return shutil.disk_usage('.')", expect_blocked=True)
test("import requests", "import requests\ndef solve(x): return requests.get('http://google.com')", expect_blocked=True)
test("open() file read", "def solve(x): return open('c:/windows/system32/drivers/etc/hosts').read()", expect_blocked=True)
test("open() file write", "def solve(x): open('/tmp/pwn.txt', 'w').write('hacked')", expect_blocked=True)

print("\n=== Valid Code Test ===")
valid_code = """
def solve(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return seen[target - n]
        seen[n] = i
"""
valid_cases = [{"lhs": "nums=[2,7,11,15], target=9", "rhs": "0"}]
res = Evaluator.run_code(valid_code, valid_cases)
print(f"[INFO] Valid code → status={res.get('status')}, results={res.get('results')}")

print("\n=== Hidden Test Case Exposure Check ===")
# Verify _get_public_question_details does not return 'Hidden Test Cases'
from modules.coding_assessment.logic import CodingAssessmentLogic
from modules.coding_assessment.question_loader import QuestionLoader
from core.database import SessionLocal
db = SessionLocal()
try:
    all_qs = QuestionLoader.load_all_questions()
    if all_qs:
        sample = CodingAssessmentLogic._get_public_question_details(all_qs[0]['question_id'], db, 999)
        keys = list(sample.keys())
        has_hidden = 'Hidden Test Cases' in keys or 'hidden_test_cases' in keys
        print(f"[{'FAIL - EXPOSED' if has_hidden else 'PASS'}] Hidden Test Cases in public response: {has_hidden}")
        print(f"[INFO] Keys returned to frontend: {keys}")
    else:
        print("[SKIP] No questions loaded")
except Exception as e:
    print(f"[ERROR] {e}")
finally:
    db.close()
