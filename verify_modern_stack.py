
import os
import vertexai
from vertexai.generative_models import GenerativeModel
import logging

logging.basicConfig(level=logging.INFO)

# Force US Central 1
REGION = "us-central1"
os.environ["VERTEX_AI_LOCATION"] = REGION
PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")

print(f"--- 2026 MODERN STACK VERIFICATION ---")
print(f"Target: {PROJECT} @ {REGION}")

# Models to check (The 2026 Lineup)
MODELS_2026 = [
    "gemini-3-flash-preview", # Bleeding Edge
    "gemini-2.5-flash",       # Standard
    "gemini-2.0-flash-exp",   # Previous Stable
    "gemini-3-pro-preview",   # Reasoning
]

vertexai.init(project=PROJECT, location=REGION)

for model_name in MODELS_2026:
    print(f"\nTesting {model_name}...", end=" ")
    try:
        model = GenerativeModel(model_name)
        # Simple ping
        response = model.generate_content("Ping.")
        print(f"✅ ALIVE! (Response: {response.text.strip()})")
    except Exception as e:
        if "404" in str(e):
            print(f"❌ 404 (Not Found / Deprecated)")
        else:
            print(f"⚠️ Error: {str(e)[:100]}")

print("\n--- End Verification ---")
