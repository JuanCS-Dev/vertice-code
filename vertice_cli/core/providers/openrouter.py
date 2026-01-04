"""
OpenRouter API provider implementation.

Multi-model gateway with FREE TIER access to:
- Grok 2 (xAI) - FREE temporarily
- DeepSeek R1 - Ultra cheap reasoning
- Llama, Mistral, and many more
"""

import os
from typing import Dict, List, Optional, AsyncGenerator
import logging
import httpx

logger = logging.getLogger(__name__)


class OpenRouterProvider:
    """
    OpenRouter API provider - Multi-model gateway.

    FREE TIER: 200 requests/day on free models
    Access to 30+ models including Grok 2, DeepSeek, Llama, etc.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    MODELS = {
        # Free models
        "grok-2": "x-ai/grok-2-1212",
        "deepseek-r1": "deepseek/deepseek-r1",
        "deepseek-chat": "deepseek/deepseek-chat",
        "llama-70b": "meta-llama/llama-3.3-70b-instruct",
        "llama-8b": "meta-llama/llama-3.1-8b-instruct:free",
        "mistral-7b": "mistralai/mistral-7b-instruct:free",
        "gemma-7b": "google/gemma-7b-it:free",
        # Paid but cheap
        "claude-sonnet": "anthropic/claude-3.5-sonnet",
        "gpt-4o": "openai/gpt-4o",
    }

    # Models with free tier access
    FREE_MODELS = {
        "llama-8b",
        "mistral-7b",
        "gemma-7b",
        "grok-2",  # Temporarily free (Dec 2025)
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "llama-70b",
        site_url: str = "https://github.com/vertice-agency",
        site_name: str = "Vertice-Code",
    ):
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            model_name: Model alias or full name
            site_url: Your site URL (for leaderboard)
            site_name: Your app name (for leaderboard)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = self.MODELS.get(model_name, model_name)
        self.site_url = site_url
        self.site_name = site_name
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

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with OpenRouter-specific fields."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
        }

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """Generate completion from messages."""
        if not self.is_available():
            raise RuntimeError("OpenRouter provider not available - OPENROUTER_API_KEY not set")

        client = await self._ensure_client()

        response = await client.post(
            f"{self.BASE_URL}/chat/completions",
            headers=self._get_headers(),
            json={
                "model": self.model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )

        if response.status_code == 429:
            raise RuntimeError("OpenRouter rate limit exceeded - try again later")

        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"]

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages."""
        if not self.is_available():
            raise RuntimeError("OpenRouter provider not available - OPENROUTER_API_KEY not set")

        client = await self._ensure_client()

        async with client.stream(
            "POST",
            f"{self.BASE_URL}/chat/completions",
            headers=self._get_headers(),
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
                raise RuntimeError(f"OpenRouter API error {response.status_code}: {error_text}")

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
                    except json.JSONDecodeError:
                        continue

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream chat with optional system prompt."""
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        async for chunk in self.stream_generate(
            full_messages, max_tokens=max_tokens, temperature=temperature, **kwargs
        ):
            yield chunk

    async def list_models(self) -> List[Dict]:
        """List available models from OpenRouter."""
        client = await self._ensure_client()

        response = await client.get(
            f"{self.BASE_URL}/models",
            headers=self._get_headers(),
        )

        response.raise_for_status()
        data = response.json()

        return data.get("data", [])

    def get_model_info(self) -> Dict[str, str | bool | int]:
        """Get model information."""
        # Determine if current model is free
        model_key = next((k for k, v in self.MODELS.items() if v == self.model_name), None)
        is_free = model_key in self.FREE_MODELS

        return {
            "provider": "openrouter",
            "model": self.model_name,
            "available": self.is_available(),
            "context_window": 128000,
            "supports_streaming": True,
            "cost_tier": "free" if is_free else "paid",
            "speed_tier": "fast",
        }

    def count_tokens(self, text: str) -> int:
        """Estimate token count."""
        return len(text) // 4
