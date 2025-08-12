import requests
import json
import sys
import os
from dotenv import load_dotenv

load_dotenv()  # Loads variables from the .env file
API_KEY = os.getenv("GOOGLE_AI_API_KEY")

if not API_KEY:
    print("❌ GOOGLE_AI_API_KEY is not set. Export it before running: export GOOGLE_AI_API_KEY=your_key_here")
    sys.exit(1)

API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"
headers = {"Content-Type": "application/json"}

data = {
    "contents": [
        {
            "parts": [
                {"text": "Who are u"}
            ]
        }
    ],
    "generationConfig": {
        "temperature": 0.7,
        "maxOutputTokens": 128
    }
}

print("=== Testing Gemini API Connection ===")
try:
    resp = requests.post(API_URL, headers=headers, json=data, timeout=30)
    if not resp.ok:
        print(f"❌ HTTP {resp.status_code}: {resp.text}")
        resp.raise_for_status()

    print("✅ Gemini API responded with status:", resp.status_code)
    payload = resp.json()
    print("Response JSON:")
    print(json.dumps(payload, indent=2))

    # Extract the text field
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
        assert isinstance(text, str) and text.strip()
        print("\n=== Extracted Text ===")
        print(text)
    except Exception:
        print("\nℹ️ Could not extract text field from response; full JSON printed above.")

    # Print responseId if present
    print("responseId:", payload.get("responseId"))

except requests.exceptions.Timeout:
    print("❌ Request timed out. Check network connectivity or increase timeout.")
except requests.exceptions.RequestException as e:
    print("❌ Gemini API request failed:", str(e))
