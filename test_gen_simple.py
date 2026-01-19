import asyncio
from google import genai
from google.genai import types


async def test_generation():
    client = genai.Client(vertexai=True, project="vertice-ai", location="us-central1")

    models_to_test = [
        "gemini-3-pro-preview",
        "publishers/google/models/gemini-3-pro-preview",
        "gemini-3.0-pro-preview",  # Just in case
    ]

    print("🧪 Testing Generation with Model Variations...")

    for model_name in models_to_test:
        print(f"\nTrying model: '{model_name}'")
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text="Hello")])],
            )
            print(f"✅ SUCCESS! Response: {response.text}")
            return  # Stop on first success
        except Exception as e:
            print(f"❌ FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(test_generation())
