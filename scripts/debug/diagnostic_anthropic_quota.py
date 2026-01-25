import asyncio
import os
import sys
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_anthropic_variants")

# Ensure we can import from the current directory
sys.path.insert(0, os.getcwd())


async def test_model(model_alias, location):
    """Test a specific model and location."""
    print("-" * 40)
    print(f"🧪 Testing: {model_alias} in {location}")
    print("-" * 40)

    try:
        from vertice_core.core.providers.anthropic_vertex import AnthropicVertexProvider

        provider = AnthropicVertexProvider(
            location=location,
            model_name=model_alias,
        )

        print(f"📋 Resolved Model: {provider.model_name}")

        messages = [{"role": "user", "content": "ping"}]

        response = await provider.generate(messages, max_tokens=10)
        print(f"✅ Success: {response.strip()}")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def run_tests():
    print("=" * 60)
    print("🔍 Diagnostic: Anthropic Vertex AI Quota/Access Test")
    print("=" * 60)

    os.environ["GOOGLE_CLOUD_PROJECT"] = "vertice-ai"

    results = []

    # Test combinations
    tests = [
        ("opus-4.5", "global"),
        ("opus-4.5", "us-central1"),
        ("sonnet-4.5", "global"),
        ("sonnet-4.5", "us-central1"),
        ("sonnet-3.5", "us-central1"),
    ]

    for model, loc in tests:
        success = await test_model(model, loc)
        results.append((model, loc, success))
        await asyncio.sleep(1)  # Small delay

    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    for model, loc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{model:<15} | {loc:<15} | {status}")


if __name__ == "__main__":
    asyncio.run(run_tests())
