import asyncio
import os
import sys

sys.path.append(os.getcwd())


async def test():
    print("Testing Vertex AI...")
    if os.getenv("RUN_VERTEX_LIVE_TESTS", "").strip().lower() not in {"1", "true", "yes"}:
        print("Live Vertex test disabled. Set RUN_VERTEX_LIVE_TESTS=1 to enable.")
        return

    from google import genai

    client = genai.Client(
        vertexai=True,
        project=os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai"),
        location=os.getenv("VERTEX_AI_LOCATION", "global"),
    )
    res = await asyncio.to_thread(
        lambda: client.models.generate_content(model="gemini-3-flash", contents="1+1")
    )
    print(f"Vertex Result: {getattr(res, 'text', '')}")


if __name__ == "__main__":
    asyncio.run(test())
