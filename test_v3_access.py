import asyncio
from google import genai
from google.genai import types


async def test_v3_access():
    configurations = [
        {"model": "gemini-3-flash", "location": "us-central1"},
        {"model": "gemini-3-flash", "location": "us-west1"},  # Try another region
        # {"model": "gemini-3-flash", "location": "global"}, # SDK 1.2 might not support global for vertexai=True, but worth a try if supported
        {"model": "gemini-3-flash-preview", "location": "us-central1"},
    ]

    print("🧪 Testing Gemini 3 Access Configurations...")

    for config in configurations:
        model = config["model"]
        loc = config["location"]
        print(f"\n--- Testing {model} in {loc} ---")

        try:
            client = genai.Client(vertexai=True, project="vertice-ai", location=loc)

            response = await client.aio.models.generate_content(
                model=model,
                contents=[types.Content(role="user", parts=[types.Part.from_text(text="Hello")])],
            )
            print(f"✅ SUCCESS! Response: {response.text}")
            return  # Stop on first success

        except Exception as e:
            print(f"❌ FAILED: {str(e)[:200]}")


if __name__ == "__main__":
    asyncio.run(test_v3_access())
