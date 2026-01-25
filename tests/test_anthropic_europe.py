import asyncio
import os
import sys
import logging
import pytest

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_europe")

# Ensure we can import from the current directory
sys.path.insert(0, os.getcwd())


async def test_europe():
    """Test Claude in europe-west1."""
    if os.getenv("RUN_VERTEX_LIVE_TESTS", "").strip().lower() not in {"1", "true", "yes"}:
        pytest.skip("Live Vertex test disabled. Set RUN_VERTEX_LIVE_TESTS=1 to enable.")

    print("=" * 60)
    print("🧪 Testing Claude on europe-west1")
    print("=" * 60)

    os.environ["GOOGLE_CLOUD_PROJECT"] = "vertice-ai"

    try:
        from vertice_core.providers.anthropic_vertex import AnthropicVertexProvider

        # Sonnet 4.5 via Vertex AI
        provider = AnthropicVertexProvider(
            location="europe-west1",
            model_name="sonnet-4.5",
        )

        print(f"📋 Model: {provider.model_name} @ {provider.location}")

        messages = [{"role": "user", "content": "hi"}]
        response = await provider.generate(messages, max_tokens=10)
        print(f"✅ Success: {response.strip()}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_europe())
