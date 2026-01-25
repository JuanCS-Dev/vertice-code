import asyncio
from google import genai
from google.genai import types


async def test_beta_access():
    print("🧪 Testing Gemini 3 Access via v1beta1 ...")

    # Force v1beta1 via http_options if possible, or just standard SDK (which usually defaults to beta for previews?)
    # google.genai SDK 1.x unifies this.

    # Try using the FULL resource name from the list
    model_resource = "publishers/google/models/gemini-3-flash"

    client = genai.Client(vertexai=True, project="vertice-ai", location="us-central1")

    try:
        response = await client.aio.models.generate_content(
            model=model_resource,
            contents=[types.Content(role="user", parts=[types.Part.from_text(text="Hello")])],
            # config={'api_version': 'v1beta1'} # Hypothetical config
        )
        print(f"✅ SUCCESS with resource name! Response: {response.text}")
    except Exception as e:
        print(f"❌ FAILED with resource name: {str(e)[:200]}")


if __name__ == "__main__":
    asyncio.run(test_beta_access())
