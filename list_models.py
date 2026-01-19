import asyncio
from google import genai


async def list_models():
    client = genai.Client(vertexai=True, project="vertice-ai", location="us-central1")

    print("🔍 Listing available models for project: vertice-ai")
    try:
        # Pager object, need to iterate
        pager = await client.aio.models.list(config={"page_size": 100})
        found_gemini = False
        async for model in pager:
            if "gemini" in model.name.lower():
                print(f"✅ Found: {model.name}")
                found_gemini = True

        if not found_gemini:
            print("❌ No Gemini models found! Check permissions or region.")

    except Exception as e:
        print(f"❌ Error listing models: {e}")


if __name__ == "__main__":
    asyncio.run(list_models())
