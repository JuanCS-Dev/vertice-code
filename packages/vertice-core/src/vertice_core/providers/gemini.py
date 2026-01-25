"""
Vertex AI Wrapper for Legacy GeminiProvider.

REDIRECTS ALL TRAFFIC TO VERTEX AI (ENTERPRISE).
AI Studio (Free Tier) implementation via google-generativeai is REMOVED.

Compliance:
- Enforce Gemini 3.0 Pro/Flash Preview
- Use Vertex AI quotas and billing
- Ignore API Keys (use ADC)
"""

import os
import logging
from typing import Any, Dict, List, Optional, AsyncGenerator
from .vertex_ai import VertexAIProvider

logger = logging.getLogger(__name__)


class GeminiProvider:
    """
    Legacy Adapter: Redirects 'GeminiProvider' calls to VertexAIProvider.

    This ensures that old code requesting 'GeminiProvider' (expecting AI Studio)
    is transparently upgraded to Vertex AI Enterprise (Gemini 3.0).
    """

    def __init__(
        self, api_key: Optional[str] = None, model_name: str = "gemini-3-flash", **kwargs
    ):
        """
        Initialize Adapter.

        Args:
            api_key: Ignored (Vertex AI uses ADC)
            model_name: Default to gemini-3-flash
        """
        if api_key:
            logger.warning("GeminiProvider: API Key ignored. Using Vertex AI (ADC).")

        # Map legacy model names if passed explicitly
        if model_name == "gemini-3-pro":
            model_name = "gemini-3-flash"

        self.model_name = model_name
        self.delegate = VertexAIProvider(
            project=os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai"),
            location=os.getenv("VERTEX_AI_LOCATION", "global"),
            model_name=model_name,
        )
        logger.info(f"GeminiProvider Redirect -> VertexAIProvider ({self.model_name})")

    def is_available(self) -> bool:
        return self.delegate.is_available()

    async def generate(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Delegate generation to Vertex AI."""
        return await self.delegate.generate(messages, **kwargs)

    async def stream_generate(
        self, messages: List[Dict[str, str]], **kwargs
    ) -> AsyncGenerator[str, None]:
        """Delegate streaming to Vertex AI."""
        async for chunk in self.delegate.stream_chat(messages, **kwargs):
            yield chunk

    # Alias for compatibility
    stream_chat = stream_generate

    def count_tokens(self, text: str) -> int:
        return self.delegate.count_tokens(text)

    def get_model_info(self) -> Dict[str, Any]:
        info = self.delegate.get_model_info()
        info["wrapper"] = "GeminiProvider (Legacy Redirect)"
        return info
