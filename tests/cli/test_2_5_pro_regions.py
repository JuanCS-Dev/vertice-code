import asyncio
import vertexai
from vertexai.generative_models import GenerativeModel

PROJECT_ID = "vertice-ai"

REGIONS_TO_TEST = [
    "us-central1",  # Default
    "us-east4",  # Often has newer capacity
    "us-west1",
    "europe-west4",
]


async def test_regions():
    print(f"🚀 Testing 'gemini-2.5-pro' availability across regions for {PROJECT_ID}")
    print("=" * 60)

    success = False

    for region in REGIONS_TO_TEST:
        print(f"\n📍 Checking {region}...", end=" ")
        try:
            # Re-init for each region
            vertexai.init(project=PROJECT_ID, location=region)
            model = GenerativeModel("gemini-2.5-pro")

            # Simple inference
            res = model.generate_content("Ping", stream=False)
            print(f"✅ SUCCESS! Response: {res.text.strip()}")
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
        print("💥 CRITICAL: gemini-2.5-pro failed in ALL tested regions.")
    else:
        print("✨ Valid region found. Update configuration.")


if __name__ == "__main__":
    asyncio.run(test_regions())
