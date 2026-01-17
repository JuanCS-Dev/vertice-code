"""
Azure OpenAI Provider

Enterprise-grade GPT-4 access via Azure Cognitive Services.
Used for multi-LLM consensus (second opinion).

Based on ClinicaGenesisOS implementation.
"""

from __future__ import annotations

import os
import asyncio
from typing import Dict, List, Optional, AsyncGenerator
import logging
import httpx

logger = logging.getLogger(__name__)


class AzureOpenAIProvider:
    """
    Azure OpenAI Provider - Enterprise GPT-4 access.

    Features:
    - Retry with exponential backoff
    - Configurable timeout
    - Graceful fallback on failure
    - JSON mode support
    """

    # Default Azure configuration
    DEFAULT_ENDPOINT = "https://eastus2.api.cognitive.microsoft.com/"
    DEFAULT_DEPLOYMENT = "gpt4o-mini"
    DEFAULT_API_VERSION = "2024-10-21"

    MODELS = {
        "gpt4o-mini": "gpt4o-mini",
        "gpt4o": "gpt-4o",
        "gpt4-turbo": "gpt-4-turbo",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment: str = "gpt4o-mini",
        api_version: Optional[str] = None,
    ):
        """Initialize Azure OpenAI provider.

        Args:
            api_key: Azure OpenAI API key (defaults to AZURE_OPENAI_KEY env var)
            endpoint: Azure endpoint URL
            deployment: Model deployment name
            api_version: API version
        """
        self.api_key = api_key or os.getenv("AZURE_OPENAI_KEY")
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", self.DEFAULT_ENDPOINT)
        self.deployment = self.MODELS.get(deployment, deployment)
        self.api_version = api_version or os.getenv(
            "AZURE_OPENAI_API_VERSION", self.DEFAULT_API_VERSION
        )
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
        return bool(self.api_key and self.endpoint)

    def _build_url(self) -> str:
        """Build Azure OpenAI API URL."""
        base = self.endpoint.rstrip("/")
        return f"{base}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        response_format: str = "text",
        retry_count: int = 3,
        **kwargs,
    ) -> str:
        """Generate completion from messages with retry logic.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            response_format: 'text' or 'json'
            retry_count: Number of retries on failure

        Returns:
            Generated text
        """
        if not self.is_available():
            raise RuntimeError("Azure OpenAI provider not available - credentials not set")

        client = await self._ensure_client()
        url = self._build_url()

        body = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if response_format == "json":
            body["response_format"] = {"type": "json_object"}

        last_error = None
        for attempt in range(retry_count):
            try:
                response = await client.post(
                    url,
                    headers={
                        "Content-Type": "application/json",
                        "api-key": self.api_key,
                    },
                    json=body,
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    usage = data.get("usage", {})
                    logger.info(f"Azure OpenAI success, tokens: {usage.get('total_tokens', 'N/A')}")
                    return content

                # Retryable errors
                if response.status_code in [429, 500, 502, 503]:
                    retry_after = response.headers.get("Retry-After")
                    wait_time = int(retry_after) if retry_after else (2**attempt)
                    logger.warning(
                        f"Azure OpenAI {response.status_code}, retrying in {wait_time}s..."
                    )
                    await asyncio.sleep(wait_time)
                    continue

                # Non-retryable error
                error_text = response.text
                last_error = f"Azure OpenAI error {response.status_code}: {error_text[:200]}"
                logger.error(last_error)

            except httpx.TimeoutException:
                last_error = "Azure OpenAI timeout"
                await asyncio.sleep(2**attempt)
            except Exception as e:
                last_error = str(e)
                await asyncio.sleep(2**attempt)

        raise RuntimeError(f"Azure OpenAI failed after {retry_count} attempts: {last_error}")

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages."""
        if not self.is_available():
            raise RuntimeError("Azure OpenAI provider not available - credentials not set")

        client = await self._ensure_client()
        url = self._build_url()

        body = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }

        async with client.stream(
            "POST",
            url,
            headers={
                "Content-Type": "application/json",
                "api-key": self.api_key,
            },
            json=body,
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                raise RuntimeError(f"Azure OpenAI error {response.status_code}: {error_text}")

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

    def get_model_info(self) -> Dict[str, str | bool | int]:
        """Get model information."""
        return {
            "provider": "azure-openai",
            "model": self.deployment,
            "endpoint": self.endpoint,
            "available": self.is_available(),
            "context_window": 128000,
            "supports_streaming": True,
            "cost_tier": "paid",
            "speed_tier": "medium",
        }

    def count_tokens(self, text: str) -> int:
        """Estimate token count (GPT tokenizer ~4 chars/token)."""
        return len(text) // 4
