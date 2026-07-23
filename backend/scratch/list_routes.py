import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app

print("--- REGISTERED ROUTES ---")
for route in app.routes:
    # Print the route path and methods
    methods = getattr(route, "methods", None)
    print(f"Path: {route.path}, Methods: {methods}")
