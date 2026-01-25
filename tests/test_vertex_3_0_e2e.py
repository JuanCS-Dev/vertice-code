import pytest
from vertice_core.core.providers.vertex_ai import VertexAIProvider

# Mark as integration test
pytestmark = pytest.mark.integration


class TestVertexGemini3:
    """Explicit E2E verification for Gemini 3.0 on Vertex AI."""

    @pytest.mark.asyncio
    async def test_vertex_3_0_pro_initialization(self):
        """Verify we can initialize the mandated model."""
        # Force global location if not set (though .env has it)
        provider = VertexAIProvider(
            project="vertice-ai", location="global", model_name="gemini-3-flash"
        )
        assert provider.model_id == "gemini-3-flash"
        assert provider.location == "global"

        # Test availability checks (lazy load)
        assert provider.is_available() is True

    @pytest.mark.asyncio
    async def test_vertex_3_0_inference(self):
        """Verify actual inference logic with Gemini 3.0."""
        provider = VertexAIProvider(
            project="vertice-ai", location="global", model_name="gemini-3-flash"
        )

        # Simple math test
        response = await provider.generate(
            messages=[{"role": "user", "content": "What is 2 + 2? Reply with just the number."}],
            temperature=0.0,
        )

        print(f"Vertex Gemini 3.0 Response: {response}")
        assert "4" in response
        assert len(response) < 10

    @pytest.mark.asyncio
    async def test_vertex_3_0_streaming(self):
        """Verify streaming works on Gemini 3.0."""
        provider = VertexAIProvider(
            project="vertice-ai", location="global", model_name="gemini-3-flash"
        )

        chunks = []
        async for chunk in provider.stream_chat(
            messages=[{"role": "user", "content": "Count to 3."}]
        ):
            chunks.append(chunk)

        full_text = "".join(chunks)
        print(f"Vertex Gemini 3.0 Stream: {full_text}")
        assert len(chunks) > 0
        assert "1" in full_text
        assert "2" in full_text
        assert "3" in full_text


if __name__ == "__main__":
    import sys

    # Manually run if executed directly
    from pytest import main

    sys.exit(main(["-v", __file__]))
