import sys
import os
import json

backend_dir = r"c:\Recruitment\backend"
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from main import app

schema = app.openapi()
with open(os.path.join(backend_dir, "scratch", "openapi.json"), "w") as f:
    json.dump(schema, f, indent=2)
print("OpenAPI schema dumped to scratch/openapi.json")
