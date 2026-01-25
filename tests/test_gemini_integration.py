"""
Real integration tests for Gemini provider (Legacy Wrapper).

VERIFIES:
- GeminiProvider redirects to VertexAIProvider
- Uses gemini-3-flash
- Ignores API keys (uses ADC)
"""

import os
import pytest

from vertice_core.providers.gemini import GeminiProvider
from vertice_core.providers.vertex_ai import VertexAIProvider

# Mark as integration
pytestmark = pytest.mark.integration


class TestGeminiProviderLegacyWrapper:
    """Integration tests verifying the Legacy -> Vertex wrapper."""

    def test_provider_initialization(self):
        """Should initialize wrapper and delegate to Vertex."""
        if os.getenv("RUN_VERTEX_LIVE_TESTS", "").strip().lower() not in {"1", "true", "yes"}:
            pytest.skip("Live Vertex test disabled. Set RUN_VERTEX_LIVE_TESTS=1 to enable.")

        # API key should be ignored but allowed in init
        provider = GeminiProvider(api_key="fake-key")
        assert provider.is_available() is True

        # Verify delegation
        assert isinstance(provider.delegate, VertexAIProvider)
        assert provider.model_name == "gemini-3-flash"

    def test_verify_config_redirect(self):
        """Verify configuration redirects to correct Vertex defaults."""
        provider = GeminiProvider(model_name="gemini-3-pro")

        # Wrapper forces a default for compatibility
        assert provider.delegate.model_alias == "gemini-3-flash"
        assert provider.delegate.location == "global"

    @pytest.mark.asyncio
    async def test_generate_simple(self):
        """Should generate response via Vertex delegate."""
        if os.getenv("RUN_VERTEX_LIVE_TESTS", "").strip().lower() not in {"1", "true", "yes"}:
            pytest.skip("Live Vertex test disabled. Set RUN_VERTEX_LIVE_TESTS=1 to enable.")

        provider = GeminiProvider()

        result = await provider.generate(
            [{"role": "user", "content": 'Say "Hello World" and nothing else.'}], temperature=0.1
        )

        assert result is not None
        assert len(result) > 0
        assert isinstance(result, str)
        print(f"Wrapper Response: {result}")
        assert "hello" in result.lower() or "world" in result.lower()

    @pytest.mark.asyncio
    async def test_stream_generate(self):
        """Should stream response chunks via Vertex delegate."""
        if os.getenv("RUN_VERTEX_LIVE_TESTS", "").strip().lower() not in {"1", "true", "yes"}:
            pytest.skip("Live Vertex test disabled. Set RUN_VERTEX_LIVE_TESTS=1 to enable.")

        provider = GeminiProvider()

        chunks = []
        async for chunk in provider.stream_generate(
            [{"role": "user", "content": "Count from 1 to 3."}], temperature=0.1
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0
        print(f"Wrapper Stream: {full_response}")
        assert "1" in full_response

    def test_model_info_claims_legacy(self):
        """Should return wrapper info."""
        provider = GeminiProvider()
        info = provider.get_model_info()

        assert info["provider"] == "vertex-ai"
        assert info["wrapper"] == "GeminiProvider (Legacy Redirect)"
        assert info["context_window"] == 1000000


if __name__ == "__main__":
    import sys
    from pytest import main

    sys.exit(main(["-v", __file__]))
