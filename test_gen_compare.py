import asyncio
from google import genai
from google.genai import types


async def test_generation():
    client = genai.Client(vertexai=True, project="vertice-ai", location="us-central1")

    models_to_test = [
        "gemini-2.0-flash-exp",  # Control: Should work
        "gemini-3-pro-preview",  # Target: Failing
    ]

    print("🧪 Comparative Model Test (us-central1)...")

    for model_name in models_to_test:
        print(f"\nTargeting: '{model_name}'")
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text="Hello")])],
            )
            print(f"✅ SUCCESS! Response: {response.text}")
        except Exception as e:
            print(f"❌ FAILED: {str(e)[:200]}...")  # Truncate error


if __name__ == "__main__":
    asyncio.run(test_generation())
