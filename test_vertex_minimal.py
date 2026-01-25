
from google import genai
from google.genai import types
import os

project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or "vertice-ai"
location = os.getenv("VERTEX_AI_LOCATION") or "global"
model_id = "gemini-3-flash"

print(f"Testing Vertex AI with:")
print(f"Project: {project_id}")
print(f"Location: {location}")
print(f"Model: {model_id}")

try:
    client = genai.Client(
        vertexai=True, 
        project=project_id, 
        location=location
    )

    print("Client initialized. Sending request...")
    
    response = client.models.generate_content(
        model=model_id,
        contents=["Hello Gemini 3, are you working? Respond with 'YES I AM WORKING'"]
    )
    
    print("\n--- RESPONSE ---")
    print(response.text)
    print("----------------\n")
    
except Exception as e:
    print(f"\nCRITICAL FAILURE: {e}")
