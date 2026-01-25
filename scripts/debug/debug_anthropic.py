import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_anthropic")

# Add project root to path
sys.path.insert(0, os.getcwd())


async def test_anthropic():
    print("Testing AnthropicVertexProvider...")
    try:
        from vertice_core.core.providers.anthropic_vertex import AnthropicVertexProvider

        provider = AnthropicVertexProvider(
            location="us-central1",
            model_name="claude-3-5-sonnet@20240620",  # Explicit known model
        )

        print(f"Provider initialized. Available: {provider.is_available()}")

        if not provider.is_available():
            print("Provider reports unavailable.")
            return

        print("Attempting generation...")
        messages = [{"role": "user", "content": "Hello, are you Claude?"}]
        response = await provider.generate(messages)
        print(f"Response: {response}")

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_anthropic())
