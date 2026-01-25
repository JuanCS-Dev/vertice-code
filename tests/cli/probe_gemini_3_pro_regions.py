import asyncio
import os

PROJECT_ID = "vertice-ai"

REGIONS_TO_TEST = [
    "us-central1",  # Default
    "us-east4",  # Often has newer capacity
    "us-west1",
    "europe-west4",
]


async def test_regions():
    print(f"🚀 Testing 'gemini-3-pro' availability across regions for {PROJECT_ID}")
    print("=" * 60)

    if os.getenv("RUN_VERTEX_LIVE_TESTS", "").strip().lower() not in {"1", "true", "yes"}:
        print("Live Vertex test disabled. Set RUN_VERTEX_LIVE_TESTS=1 to enable.")
        return

    success = False

    for region in REGIONS_TO_TEST:
        print(f"\n📍 Checking {region}...", end=" ")
        try:
            from google import genai

            client = genai.Client(vertexai=True, project=PROJECT_ID, location=region)

            res = await asyncio.to_thread(
                lambda: client.models.generate_content(model="gemini-3-pro", contents="Ping")
            )
            text = getattr(res, "text", "") or ""
            print(f"✅ SUCCESS! Response: {text.strip()}")
            print(f"   >>> RECOMMENDATION: Use '{region}' context!")
            success = True
            break

        except Exception as e:
            err = str(e).split("\n")[0]
            if "404" in err:
                print("❌ 404 Not Found (Model not available in region/project)")
            elif "429" in err:
                print("⚠️ 429 Quota Exceeded (Exists but busy)")
            else:
                print(f"❌ Error: {err}")

    print("\n" + "=" * 60)
    if not success:
        print("💥 CRITICAL: gemini-3-pro failed in ALL tested regions.")
    else:
        print("✨ Valid region found. Update configuration.")


if __name__ == "__main__":
    asyncio.run(test_regions())
