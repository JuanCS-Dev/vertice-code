"""
Cerebras API provider implementation.

FASTEST inference in the world - FREE TIER
- 1,000,000 tokens/day
- ~3,000 tokens/second
"""

import os
from typing import Dict, List, Optional, AsyncGenerator
import logging
import httpx

logger = logging.getLogger(__name__)


class CerebrasProvider:
    """
    Cerebras API provider - World's fastest inference.

    FREE TIER: 1,000,000 tokens/day
    Speed: ~3,000 tokens/second (fastest in the world)
    """

    BASE_URL = "https://api.cerebras.ai/v1"

    MODELS = {
        "llama-70b": "llama-3.3-70b",
        "llama-8b": "llama3.1-8b",
    }

    # Rate limits (free tier)
    RATE_LIMITS = {
        "tokens_per_day": 1000000,
        "requests_per_minute": 60,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "llama-70b",
    ):
        """Initialize Cerebras provider.

        Args:
            api_key: Cerebras API key (defaults to CEREBRAS_API_KEY env var)
            model_name: Model alias or full name
        """
        self.api_key = api_key or os.getenv("CEREBRAS_API_KEY")
        self.model_name = self.MODELS.get(model_name, model_name)
        self._client: Optional[httpx.AsyncClient] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=10.0),
                limits=httpx.Limits(max_connections=10),
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def is_available(self) -> bool:
        """Check if provider is available."""
        return self.api_key is not None

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate completion from messages."""
        if not self.is_available():
            raise RuntimeError("Cerebras provider not available - CEREBRAS_API_KEY not set")

        client = await self._ensure_client()

        response = await client.post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )

        if response.status_code == 429:
            raise RuntimeError("Cerebras rate limit exceeded - try again later")

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages."""
        if not self.is_available():
            raise RuntimeError("Cerebras provider not available - CEREBRAS_API_KEY not set")

        client = await self._ensure_client()

        async with client.stream(
            "POST",
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            },
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise RuntimeError(f"Cerebras API error {response.status_code}: {error_text}")

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        import json
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except Exception:
                        continue

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream chat with optional system prompt."""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        async for chunk in self.stream_generate(
            full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        ):
            yield chunk

    def get_model_info(self) -> Dict[str, str | bool | int]:
        """Get model information."""
        return {
            'provider': 'cerebras',
            'model': self.model_name,
            'available': self.is_available(),
            'context_window': 128000,
            'supports_streaming': True,
            'cost_tier': 'free',
            'speed_tier': 'fastest',
            'tokens_per_day': self.RATE_LIMITS['tokens_per_day'],
        }

    def count_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text) // 4
