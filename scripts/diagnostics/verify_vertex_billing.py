
import os
import sys
import vertexai
from vertexai.generative_models import GenerativeModel
import traceback

def verify_vertex_status():
    project_id = "vertice-ai"
    location = "us-central1"
    
    print(f"🔍 DIAGNOSTIC: Verifying Vertex AI for Project '{project_id}'...")
    
    import vertexai
    print(f"   • SDK Version: {vertexai.__version__}")

    # Force Credentials Path
    adc_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = adc_path
    print(f"   • Forced GOOGLE_APPLICATION_CREDENTIALS = {adc_path}")

    # Try Alternative Region
    locations = ["us-central1", "us-east4", "europe-west4"]
    
    for loc in locations:
        print(f"\n🌍 TESTING REGION: {loc}")
        try:
            vertexai.init(project=project_id, location=loc)
        except Exception as e:
            print(f"   ❌ Init failed for {loc}: {e}")
            continue

        candidates = [
            "gemini-1.5-pro-001",
            "gemini-1.5-flash-001",
            "gemini-1.0-pro"
        ]
        
        for model_name in candidates:
            print(f"   • Probing '{model_name}' in {loc}...")
            try:
                model = GenerativeModel(model_name)
                response = model.generate_content("Hello")
                print(f"     ✅ SUCCESS! Model '{model_name}' is working in {loc}.")
                print("-" * 40)
                print(f"Response: {response.text.strip()}")
                print("-" * 40)
                return
            except Exception as e:
                error_str = str(e)
                if "404" in error_str:
                    print(f"     ❌ Not Found (404)")
                else:
                    print(f"     ❌ Error: {error_str}")
    
    print("\n🚨 ALL REGIONS AND MODELS FAILED.")

if __name__ == "__main__":
    # Ensure no env vars interfere
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        print("⚠️  WARNING: GOOGLE_APPLICATION_CREDENTIALS not set. Using Default Credentials (gcloud auth).")
    
    verify_vertex_status()
