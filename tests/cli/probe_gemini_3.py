
import asyncio
from google.cloud import aiplatform
import vertexai
from vertexai.preview.generative_models import GenerativeModel
import os

PROJECT_ID = "vertice-ai"
LOCATION = "us-central1"

async def probe_gemini_3():
    print(f"🚀 Probing for 'gemini-3' models in {PROJECT_ID} @ {LOCATION}")
    print("=" * 60)
    
    candidates = [
        "gemini-3-pro-preview",
        "gemini-3.0-pro-preview",
        "gemini-3-flash-preview",
        "gemini-3.0-flash-preview",
        "gemini-3-pro",
        "gemini-3-flash",
        "gemini-3.0-pro-001",
        "gemini-experimental"
    ]
    
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    
    for model_id in candidates:
        print(f"Checking {model_id}...", end=" ")
        try:
            model = GenerativeModel(model_id)
            # Dry run
            res = model.count_tokens("Ping")
            print(f"✅ DETECTED! (Tokens: {res.total_tokens})")
        except Exception as e:
            err = str(e).split('\n')[0]
            if "404" in err:
                print("❌ 404 Not Found")
            else:
                print(f"❌ Error: {err}")

if __name__ == "__main__":
    asyncio.run(probe_gemini_3())
