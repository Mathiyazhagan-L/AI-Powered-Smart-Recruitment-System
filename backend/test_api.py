import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.get("/jobs/candidate/1/feed")
print(response.status_code)
print(response.text)
