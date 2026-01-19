import asyncio
import os
from google import genai
from google.genai import types


async def test_ai_studio():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ SKIPPING: GEMINI_API_KEY not found in env.")
        return

    print(f"🧪 Testing AI Studio Access (Key: {api_key[:5]}...)")

    # vertexai=False means use AI Studio
    client = genai.Client(api_key=api_key, vertexai=False)

    models = [
        "gemini-2.0-flash-exp",
        "gemini-3.0-pro-preview",
    ]  # Note: AI Studio names might differ slightly?
    # Usually AI Studio uses 'gemini-2.0-flash-exp'

    for model in models:
        print(f"\nTargeting: '{model}' on AI Studio")
        try:
            response = await client.aio.models.generate_content(
                model=model,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text="Hello")])],
            )
            print(f"✅ SUCCESS! Response: {response.text}")
        except Exception as e:
            print(f"❌ FAILED: {str(e)[:200]}")


if __name__ == "__main__":
    asyncio.run(test_ai_studio())
