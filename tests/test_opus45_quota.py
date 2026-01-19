import asyncio
import os
import sys
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("test_opus45")

# Ensure we can import from the current directory
sys.path.insert(0, os.getcwd())


async def test_opus45():
    """Test Claude 3 Opus 4.5 on Vertex AI."""
    print("=" * 60)
    print("🧪 Testing Claude Opus 4.5 on Vertex AI Model Garden")
    print("=" * 60)

    try:
        from vertice_cli.core.providers.anthropic_vertex import AnthropicVertexProvider

        # Initialize provider with opus-4.5
        provider = AnthropicVertexProvider(
            location="global",
            model_name="opus-4.5",
        )

        print(f"📋 Model: {provider.model_name}")
        print(f"📍 Location: {provider.location}")
        print(f"🏗️ Project: {provider.project}")

        # Check if project is set
        if not provider.project:
            print("❌ GOOGLE_CLOUD_PROJECT is not set.")
            return False

        print("\n🚀 Attempting generation...")
        messages = [
            {
                "role": "user",
                "content": "Hello Claude Opus 4.5. Please identify yourself and confirm you are running on Vertex AI.",
            }
        ]

        # Try generation
        response = await provider.generate(messages, max_tokens=100)
        print(f"\n📝 Response:\n{response}")
        print("\n✅ SUCCESS!")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_opus45())
    sys.exit(0 if success else 1)
