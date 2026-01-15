
import asyncio
from google.cloud import aiplatform
import os

def list_all_publisher_models():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
    location = os.getenv("VERTEX_AI_LOCATION", "us-central1")
    
    print(f"🔍 Audit: Listing ALL Publisher Models in {project_id} @ {location}")
    print("="*60)
    
    aiplatform.init(project=project_id, location=location)
    
    # Use the gapic client for direct access
    from google.cloud import aiplatform_v1
    client = aiplatform_v1.ModelGardenServiceClient(
        client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
    )
    
    parent = f"projects/{project_id}/locations/{location}"
    request = aiplatform_v1.ListPublisherModelsRequest(parent=parent)
    
    try:
        # Iterate through pages
        count = 0
        found_gemini = []
        for model in client.list_publisher_models(request=request):
            count += 1
            if "gemini" in model.name.lower():
                found_gemini.append(model.name)
                print(f"✅ FOUND: {model.name} (Launch Stage: {model.launch_stage})")
                
        print("="*60)
        print(f"Total Models Found: {count}")
        print(f"Gemini Models Found: {len(found_gemini)}")
        
        if not found_gemini:
            print("❌ NO GEMINI MODELS FOUND IN PUBLISHER LIST!")
            print("Possible causes: Region mismatch, API disabled, or Service Account restrictions.")
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    list_all_publisher_models()
