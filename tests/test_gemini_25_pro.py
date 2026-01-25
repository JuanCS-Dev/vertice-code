import asyncio
import os
import sys
import logging

# Configure logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_gemini25")

# Ensure we can import from the current directory
sys.path.insert(0, os.getcwd())


async def test_gemini25_pro():
    """Test Gemini 2.5 Pro on Vertex AI."""
    print("=" * 60)
    print("🧪 Testing Gemini 2.5 Pro on Vertex AI")
    print("=" * 60)

    try:
        from vertice_core.core.providers.vertex_ai import VertexAIProvider

        # Set Project ID
        os.environ["GOOGLE_CLOUD_PROJECT"] = "vertice-ai"

        # Initialize provider with gemini-2.5-pro
        provider = VertexAIProvider(
            location="us-central1",
            model_name="pro",  # This maps to gemini-2.5-pro in vertex_ai.py
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
            {"role": "user", "content": "Hello Gemini 2.5 Pro. Please confirm you are operational."}
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
    success = asyncio.run(test_gemini25_pro())
    sys.exit(0 if success else 1)
