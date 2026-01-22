
import os
from google import genai
from google.genai import types

project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or "vertice-ai"
location = os.getenv("VERTEX_AI_LOCATION") or "global"
model_id = "gemini-3-pro-preview"

print(f"Testing Vertex AI SYNC STREAM with:")
print(f"Project: {project_id}")
print(f"Location: {location}")
print(f"Model: {model_id}")

def test_sync_stream():
    try:
        client = genai.Client(
            vertexai=True, 
            project=project_id, 
            location=location
        )
        
        contents = [types.Content(role="user", parts=[types.Part.from_text(text="Hello Gemini 3, sync stream? 'YES SYNC WORKS'")])]
        config = types.GenerateContentConfig(max_output_tokens=100)

        # Sync stream call
        stream = client.models.generate_content_stream(
            model=model_id,
            contents=contents,
            config=config
        )
        
        print("Stream started. Iterating chunks...")
        for chunk in stream:
            print(f"Chunk: {chunk.text}")
            
    except Exception as e:
        print(f"\nCRITICAL FAILURE: {e}")

if __name__ == "__main__":
    test_sync_stream()
