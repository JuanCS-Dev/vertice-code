import asyncio
from google import genai
from google.genai import types


async def probe_global_models():
    print("\n📡 **Global Region Probe (Strict Mode)**")
    print("-" * 40)

    project = "vertice-ai"
    location = "global"  # STRICTLY GLOBAL

    print(f"🌍 Connecting to: Project='{project}', Location='{location}'")

    try:
        client = genai.Client(vertexai=True, project=project, location=location)

        # 1. LIST MODELS
        print("   📋 Listing Models (Page Size: 20)...")
        try:
            # Note: In some SDK versions, listing in 'global' might behave differently.
            # We await the list call.
            response = await client.aio.models.list(config={"page_size": 20})

            # Handle standard Pager response
            count = 0
            # Try to iterate directly
            async for m in response:
                print(f"      FOUND: {m.name}")
                # m.name usually looks like "publishers/google/models/gemini-1.5-flash"
                count += 1

            if count == 0:
                print("      ⚠️ Zero models returned.")

        except TypeError as te:
            # If async iterator fails, try synchronous list wrapper logic or direct attribute
            print(f"   ⚠️ Async Iterator Error: {te}. Trying alternative access...")
            try:
                resp = await client.aio.models.list()
                # If it returns a non-async iterable?
                print(f"      Response Type: {type(resp)}")
            except Exception as e2:
                print(f"      Alternative failed: {e2}")

        except Exception as e:
            print(f"   🔥 List Models Failed: {e}")

        # 2. BLIND TEST (If list fails, try known global IDs)
        # Try both "gemini-1.5-pro-001" and "gemini-pro"
        candidates = ["gemini-1.5-flash-001", "gemini-pro", "gemini-1.5-pro-preview-0409"]

        for model_id in candidates:
            print(f"\n   ⚡ Blind Test: {model_id}")
            try:
                stream = await client.aio.models.generate_content_stream(
                    model=model_id,
                    contents="Ping",
                    config=types.GenerateContentConfig(temperature=0),
                )
                async for chunk in stream:
                    print(f"      ✅ SUCCESS with {model_id}!")
                    if hasattr(chunk, "text"):
                        print(f"      Response: {chunk.text}")
                    break
            except Exception as e:
                print(f"      ❌ Failed: {e}")

    except Exception as e:
        print(f"   🔥 Client Init Failed: {e}")


if __name__ == "__main__":
    asyncio.run(probe_global_models())
