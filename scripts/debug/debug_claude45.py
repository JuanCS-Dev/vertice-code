#!/usr/bin/env python3
"""
Test Claude 4.5 Sonnet on Vertex AI Model Garden.
"""

import asyncio
import os
import sys
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_claude45")

sys.path.insert(0, os.getcwd())


async def test_claude45():
    """Test Claude 4.5 Sonnet directly."""
    print("=" * 60)
    print("🧪 Testing Claude 4.5 Sonnet on Vertex AI Model Garden")
    print("=" * 60)

    try:
        from vertice_cli.core.providers.anthropic_vertex import AnthropicVertexProvider

        # Force Claude 4.5 Sonnet (the newest model)
        provider = AnthropicVertexProvider(
            location="global",  # Global endpoint for lower cost
            model_name="sonnet-4.5",  # Maps to claude-sonnet-4-5@20250929
        )

        print(f"📋 Model: {provider.model_name}")
        print(f"📍 Location: {provider.location}")
        print(f"🏗️ Project: {provider.project}")
        print(f"✅ Available: {provider.is_available()}")

        if not provider.is_available():
            print("❌ Provider reports unavailable.")
            return False

        print("\n🚀 Attempting generation...")
        messages = [
            {"role": "user", "content": "Say 'Claude 4.5 Sonnet operational' if you can hear me."}
        ]
        response = await provider.generate(messages)
        print(f"\n📝 Response:\n{response}")
        print("\n✅ SUCCESS!")
        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_claude45())
    exit(0 if success else 1)
