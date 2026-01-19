import asyncio
import os
import sys

sys.path.append(os.getcwd())


async def test():
    print("Testing Vertex AI...")
    from src.providers.vertex_ai import VertexAIProvider

    # Use flash for speed test
    p = VertexAIProvider(model_name="gemini-2.5-flash")
    res = await p.generate([{"role": "user", "content": "1+1"}])
    print(f"Vertex Result: {res}")


if __name__ == "__main__":
    asyncio.run(test())
