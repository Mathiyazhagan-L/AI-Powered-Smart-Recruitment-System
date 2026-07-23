import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

if client_id:
    print(f"SUCCESS: GOOGLE_CLIENT_ID found -> {client_id[:15]}...[REDACTED]")
else:
    print("ERROR: GOOGLE_CLIENT_ID is missing!")

if client_secret:
    print(f"SUCCESS: GOOGLE_CLIENT_SECRET found -> {client_secret[:5]}...[REDACTED]")
else:
    print("ERROR: GOOGLE_CLIENT_SECRET is missing!")
