"""
OpenRouter API provider implementation - Enhanced for Phase 8.

Multi-model gateway with FREE TIER access and advanced routing features.

Features (2025 Best Practices):
- Provider routing: :floor suffix for cost optimization
- allow_fallbacks, order, ignore for control
- Token usage tracking
- Cost-aware routing

References:
- https://openrouter.ai/docs/guides/routing/provider-selection
- https://openrouter.ai/docs/api/reference/parameters

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Dict, List, Optional, AsyncGenerator, Any

import httpx

from .base import EnhancedProviderBase
from .types import CostTier, SpeedTier, UsageInfo, OpenRouterProviderPrefs

logger = logging.getLogger(__name__)


class OpenRouterProvider(EnhancedProviderBase):
    """
    OpenRouter API provider - Multi-model gateway.

    FREE TIER: 200 requests/day on free models
    Access to 30+ models including Grok 2, DeepSeek, Llama, etc.

    Advanced routing features:
    - :floor suffix = sort by lowest price
    - :nitro suffix = sort by throughput
    - provider.order = ["provider1", "provider2"]
    - provider.ignore = ["provider3"]
    - allow_fallbacks = true/false
    """

    PROVIDER_NAME = "openrouter"
    BASE_URL = "https://openrouter.ai/api/v1"
    COST_TIER = CostTier.LOW_COST
    SPEED_TIER = SpeedTier.FAST

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
        "llama-8b", "mistral-7b", "gemma-7b",
        "grok-2",  # Temporarily free (Dec 2025)
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "llama-70b",
        site_url: str = "https://github.com/vertice-agency",
        site_name: str = "Vertice-Code",
        provider_prefs: Optional[OpenRouterProviderPrefs] = None,
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
            model_name: Model alias or full name
            site_url: Your site URL (for leaderboard)
            site_name: Your app name (for leaderboard)
            provider_prefs: Provider routing preferences
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        resolved_model = self.MODELS.get(model_name, model_name)
        super().__init__(
            api_key=api_key or os.getenv("OPENROUTER_API_KEY"),
            model_name=resolved_model,
            timeout=timeout,
            max_retries=max_retries,
        )
        self.site_url = site_url
        self.site_name = site_name
        self.provider_prefs = provider_prefs or OpenRouterProviderPrefs()

        # Determine cost tier
        model_key = next((k for k, v in self.MODELS.items() if v == resolved_model), None)
        if model_key in self.FREE_MODELS:
            self.COST_TIER = CostTier.FREE

    def _get_headers_mapping(self) -> Dict[str, str]:
        """Get OpenRouter header mapping (limited headers)."""
        return {
            "requests_limit": "x-ratelimit-limit",
            "requests_remaining": "x-ratelimit-remaining",
            "requests_reset": "x-ratelimit-reset",
            "tokens_limit": "",
            "tokens_remaining": "",
            "tokens_reset": "",
            "retry_after": "retry-after",
        }

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers with OpenRouter-specific fields."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url,
            "X-Title": self.site_name,
        }

    def _apply_cost_suffix(self, model: str, optimize_cost: bool = True) -> str:
        """Apply :floor suffix for cost optimization.

        Args:
            model: Model name
            optimize_cost: Whether to add :floor suffix

        Returns:
            Model name with optional :floor suffix
        """
        if optimize_cost and ":floor" not in model and ":nitro" not in model:
            return f"{model}:floor"
        return model

    def _build_request_body(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        optimize_cost: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Build request body with provider preferences.

        Args:
            messages: Conversation messages
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            optimize_cost: Whether to optimize for lowest cost

        Returns:
            Request body dict
        """
        model = self._apply_cost_suffix(self.model_name, optimize_cost)

        body: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Add provider preferences if configured
        provider_dict = self.provider_prefs.to_dict()
        if provider_dict:
            body["provider"] = provider_dict

        return body

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        optimize_cost: bool = True,
        **kwargs: Any,
    ) -> str:
        """Generate completion with cost-optimized routing.

        Args:
            messages: Conversation messages
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            optimize_cost: Use :floor suffix for lowest cost

        Returns:
            Generated text
        """
        if not self.is_available():
            raise RuntimeError("OpenRouter provider not available - OPENROUTER_API_KEY not set")

        should_wait, wait_time = await self.should_throttle()
        if should_wait and wait_time > 0:
            import asyncio
            await asyncio.sleep(wait_time)

        client = await self._ensure_client()
        start_time = time.perf_counter()

        try:
            body = self._build_request_body(
                messages, max_tokens, temperature, optimize_cost, **kwargs
            )

            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._get_auth_headers(),
                json=body,
            )

            self._rate_limit = self._parse_rate_limit_headers(response.headers)

            if response.status_code == 429:
                self._health.record_failure(is_rate_limit=True)
                raise RuntimeError("OpenRouter rate limit exceeded - try again later")

            response.raise_for_status()
            data = response.json()

            usage = self._parse_usage(data)
            cost = self._calculate_cost(usage)
            latency_ms = (time.perf_counter() - start_time) * 1000

            self._update_stats(usage, cost, latency_ms, success=True)

            # Log which provider was used (if available)
            generation_id = data.get("id", "")
            logger.debug(
                f"OpenRouter: {usage.total_tokens} tokens, ${cost.total_cost:.6f}, "
                f"{latency_ms:.0f}ms, gen_id: {generation_id}"
            )

            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_stats(UsageInfo(), self._calculate_cost(UsageInfo()), latency_ms, success=False)
            raise RuntimeError(f"OpenRouter API error {e.response.status_code}: {e.response.text[:200]}")

        except Exception:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_stats(UsageInfo(), self._calculate_cost(UsageInfo()), latency_ms, success=False)
            raise

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        optimize_cost: bool = True,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream generation with cost-optimized routing."""
        if not self.is_available():
            raise RuntimeError("OpenRouter provider not available - OPENROUTER_API_KEY not set")

        should_wait, wait_time = await self.should_throttle()
        if should_wait and wait_time > 0:
            import asyncio
            await asyncio.sleep(wait_time)

        client = await self._ensure_client()
        start_time = time.perf_counter()
        total_tokens = 0

        try:
            body = self._build_request_body(
                messages, max_tokens, temperature, optimize_cost, **kwargs
            )
            body["stream"] = True

            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self._get_auth_headers(),
                json=body,
            ) as response:
                self._rate_limit = self._parse_rate_limit_headers(response.headers)

                if response.status_code != 200:
                    error_text = await response.aread()
                    self._health.record_failure(is_rate_limit=response.status_code == 429)
                    raise RuntimeError(f"OpenRouter API error {response.status_code}: {error_text}")

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                total_tokens += 1
                                yield content

                            if "usage" in data:
                                usage = self._parse_usage(data)
                                cost = self._calculate_cost(usage)
                                latency_ms = (time.perf_counter() - start_time) * 1000
                                self._update_stats(usage, cost, latency_ms, success=True)

                        except json.JSONDecodeError:
                            continue

            if self._last_usage is None or self._last_usage.completion_tokens == 0:
                estimated_usage = UsageInfo(
                    prompt_tokens=sum(len(m.get("content", "")) // 4 for m in messages),
                    completion_tokens=total_tokens,
                    total_tokens=total_tokens,
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._update_stats(estimated_usage, self._calculate_cost(estimated_usage), latency_ms, success=True)

        except Exception:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_stats(UsageInfo(), self._calculate_cost(UsageInfo()), latency_ms, success=False)
            raise

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models from OpenRouter."""
        client = await self._ensure_client()

        response = await client.get(
            f"{self.BASE_URL}/models",
            headers=self._get_auth_headers(),
        )

        response.raise_for_status()
        data = response.json()

        return data.get("data", [])

    def set_provider_preferences(
        self,
        sort: Optional[str] = None,
        order: Optional[List[str]] = None,
        ignore: Optional[List[str]] = None,
        allow_fallbacks: bool = True,
    ) -> None:
        """Update provider preferences for routing.

        Args:
            sort: Sort strategy ("price", "latency", "throughput")
            order: Provider priority order
            ignore: Providers to exclude
            allow_fallbacks: Enable automatic fallbacks
        """
        self.provider_prefs = OpenRouterProviderPrefs(
            sort=sort,
            order=order,
            ignore=ignore,
            allow_fallbacks=allow_fallbacks,
        )

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information with OpenRouter-specific details."""
        info = super().get_model_info()
        info.update({
            "context_window": 128000,
            "supports_streaming": True,
            "provider_prefs": self.provider_prefs.to_dict(),
        })
        return info
