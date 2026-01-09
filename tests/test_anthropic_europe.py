import asyncio
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_europe")

# Ensure we can import from the current directory
sys.path.insert(0, os.getcwd())

async def test_europe():
    """Test Claude in europe-west1."""
    print("=" * 60)
    print("🧪 Testing Claude on europe-west1")
    print("=" * 60)
    
    os.environ["GOOGLE_CLOUD_PROJECT"] = "vertice-ai"
    
    try:
        from vertice_cli.core.providers.anthropic_vertex import AnthropicVertexProvider

        # Try Sonnet 3.5 (stable) in europe-west1
        provider = AnthropicVertexProvider(
            location="europe-west1",
            model_name="sonnet-3.5",
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
