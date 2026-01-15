"""Nebius API provider implementation."""

import os
from typing import Dict, List, Optional, AsyncGenerator, Any
import logging

logger = logging.getLogger(__name__)

class NebiusProvider:
    """Nebius Token Factory provider (OpenAI-compatible)."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize Nebius provider.
        
        Args:
            api_key: Nebius API key (defaults to NEBIUS_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("NEBIUS_API_KEY")
        # Default to DeepSeek V3 as requested by user ("deepseek novo")
        self.model_name = os.getenv("NEBIUS_MODEL", "deepseek-ai/DeepSeek-V3-0324")
        self._client = None
        self._openai = None

    def _ensure_openai(self):
        """Lazy load openai SDK."""
        if self._openai is None:
            try:
                import openai
                self._openai = openai
            except ImportError:
                logger.error("openai not installed")
                raise RuntimeError("openai not installed")

    @property
    def client(self):
        """Lazy client initialization."""
        if self._client is None:
            if self.api_key:
                self._ensure_openai()
                try:
                    self._client = self._openai.AsyncOpenAI(
                        api_key=self.api_key,
                        base_url="https://api.tokenfactory.nebius.com/v1/"
                    )
                    logger.info(f"Nebius provider initialized with model: {self.model_name}")
                except Exception as e:
                    logger.error(f"Failed to initialize Nebius: {e}")
                    self._client = None
        return self._client

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.client is not None

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model": self.model_name,
            "provider": "nebius",
            "context_window": 128000, # Approximate for V3
            "capabilities": ["code", "chat", "reasoning"]
        }

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.6,
        **kwargs
    ) -> str:
        """Generate completion from messages."""
        if not self.is_available():
            raise RuntimeError("Nebius provider not available")

        # Use passed model or default
        target_model = model or self.model_name

        try:
            response = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                # DeepSeek often benefits from top_p
                top_p=0.95
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Nebius generation failed: {e}")
            raise

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.6,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages."""
        if not self.is_available():
            raise RuntimeError("Nebius provider not available")

        target_model = model or self.model_name

        try:
            stream = await self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                top_p=0.95
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Nebius chat error: {e}")
            raise

    # Compat for older shared protocol if needed
    async def stream_generate(self, *args, **kwargs):
        async for chunk in self.stream_chat(*args, **kwargs):
            yield chunk
