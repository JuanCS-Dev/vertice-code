#!/usr/bin/env python3
"""
Test Gemini 2.5 Pro on Vertex AI.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.getcwd())


async def test_gemini_vertex():
    """Test Gemini 2.5 Pro via Vertex AI provider."""
    print("=" * 60)
    print("🧪 Testing Gemini 2.5 Pro on Vertex AI")
    print("=" * 60)

    try:
        from vertice_core.core.providers.vertex_ai import VertexAIProvider

        provider = VertexAIProvider(
            location="us-central1",
            model_name="pro",  # Should map to gemini-2.5-pro or similar
        )

        print(f"📋 Model: {provider.model_name}")
        print(f"📍 Location: {provider.location}")
        print(f"🏗️ Project: {provider.project}")
        print(f"✅ Available: {provider.is_available()}")

        if not provider.is_available():
            print("❌ Provider reports unavailable.")
            return False

        print("\n🚀 Attempting generation...")
        messages = [{"role": "user", "content": "Say 'Gemini operational' if you can hear me."}]

        full_response = ""
        async for chunk in provider.stream_chat(messages):
            full_response += chunk
            print(chunk, end="", flush=True)

        print(f"\n\n✅ SUCCESS! Response length: {len(full_response)}")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_gemini_vertex())
    exit(0 if success else 1)
