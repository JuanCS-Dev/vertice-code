
import asyncio
import os
from google import genai
from google.genai import types

project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or "vertice-ai"
location = os.getenv("VERTEX_AI_LOCATION") or "global"
model_id = "gemini-3-flash"

print(f"Testing Vertex AI ASYNC STREAM with:")
print(f"Project: {project_id}")
print(f"Location: {location}")
print(f"Model: {model_id}")

async def test_async_stream():
    try:
        client = genai.Client(
            vertexai=True, 
            project=project_id, 
            location=location
        )

        print("Client initialized. Sending async stream request...")
        
        # Exact pattern from VertexAIProvider
        contents = [types.Content(role="user", parts=[types.Part.from_text(text="Hello Gemini 3, are you working via ASYNC STREAM? Respond with 'YES ASYNC WORKS'")])]
        config = types.GenerateContentConfig(max_output_tokens=100)

        stream = await client.aio.models.generate_content_stream(
            model=model_id,
            contents=contents,
            config=config
        )
        
        print("Stream started. Iterating chunks...")
        async for chunk in stream:
            print(f"Chunk: {chunk.text}")
            
        print("\n--- DONE ---")
        
    except Exception as e:
        print(f"\nCRITICAL FAILURE: {e}")

if __name__ == "__main__":
    asyncio.run(test_async_stream())
