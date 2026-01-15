
import os
import vertexai
from vertexai.generative_models import GenerativeModel
import google.auth
from google.cloud import aiplatform

def probe():
    print("--- VERTEX AI PROBE ---")
    
    # 1. Auth Check
    try:
        credentials, project = google.auth.default()
        print(f"Auth: Success using {type(credentials).__name__}")
        print(f"Detected Project: {project}")
    except Exception as e:
        print(f"Auth: FAILED - {e}")
        return

    # 2. Env Var Check
    env_project = "vertice-ai" # FORCE PROJECT per User Instruction
    env_location = "us-central1"
    print(f"FORCING PROJECT: {env_project}")

    target_project = env_project or project
    if not target_project:
        print("CRITICAL: No project ID found.")
        return

    # 3. Init
    print(f"Initializing Vertex AI with project={target_project}, location={env_location}")
    try:
        vertexai.init(project=target_project, location=env_location)
    except Exception as e:
        print(f"Init: FAILED - {e}")
        return

    # 4. Model Probe
    models_to_check = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-3-flash-preview",
    ]

    for model_name in models_to_test:
        print(f"\nProbing {model_name}...")
        try:
            model = GenerativeModel(model_name)
            response = model.generate_content("Hello, system check.")
            print(f"SUCCESS: {model_name} responded: {response.text[:50]}...")
            return  # Stop on first success
        except Exception as e:
            print(f"FAILED: {model_name} - {e}")

if __name__ == "__main__":
    probe()
