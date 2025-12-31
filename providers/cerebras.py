"""
Cerebras API provider implementation - Enhanced for Phase 8.

FASTEST inference in the world - FREE TIER
- 1,000,000 tokens/day
- ~3,000 tokens/second

Features (2025 Best Practices):
- Rate limit header parsing (x-ratelimit-*)
- Token usage tracking with response parsing
- Automatic throttling based on utilization
- Prometheus metrics export

References:
- https://inference-docs.cerebras.ai/support/rate-limits
- https://inference-docs.cerebras.ai/support/pricing

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
from .types import CostTier, SpeedTier, UsageInfo

logger = logging.getLogger(__name__)


class CerebrasProvider(EnhancedProviderBase):
    """
    Cerebras API provider - World's fastest inference.

    FREE TIER: 1,000,000 tokens/day
    Speed: ~3,000 tokens/second (fastest in the world)

    Headers parsed:
    - x-ratelimit-limit-requests-day (daily request ceiling)
    - x-ratelimit-limit-tokens-minute (per-minute token cap)
    - x-ratelimit-remaining-requests-day (available requests today)
    - x-ratelimit-remaining-tokens-minute (available tokens this minute)
    - x-ratelimit-reset-requests-day (seconds until daily reset)
    - x-ratelimit-reset-tokens-minute (seconds until minute reset)
    """

    PROVIDER_NAME = "cerebras"
    BASE_URL = "https://api.cerebras.ai/v1"
    COST_TIER = CostTier.FREE
    SPEED_TIER = SpeedTier.INSTANT

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
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """Initialize Cerebras provider.

        Args:
            api_key: Cerebras API key (defaults to CEREBRAS_API_KEY env var)
            model_name: Model alias or full name
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        resolved_model = self.MODELS.get(model_name, model_name)
        super().__init__(
            api_key=api_key or os.getenv("CEREBRAS_API_KEY"),
            model_name=resolved_model,
            timeout=timeout,
            max_retries=max_retries,
        )

    def _get_headers_mapping(self) -> Dict[str, str]:
        """Get Cerebras-specific header name mapping.

        Note: Cerebras uses different header naming (day/minute granularity).
        """
        return {
            "requests_limit": "x-ratelimit-limit-requests-day",
            "requests_remaining": "x-ratelimit-remaining-requests-day",
            "requests_reset": "x-ratelimit-reset-requests-day",
            "tokens_limit": "x-ratelimit-limit-tokens-minute",
            "tokens_remaining": "x-ratelimit-remaining-tokens-minute",
            "tokens_reset": "x-ratelimit-reset-tokens-minute",
            "retry_after": "retry-after",
        }

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate completion from messages with full tracking."""
        if not self.is_available():
            raise RuntimeError("Cerebras provider not available - CEREBRAS_API_KEY not set")

        # Check throttling
        should_wait, wait_time = await self.should_throttle()
        if should_wait and wait_time > 0:
            logger.debug(f"Throttling Cerebras request for {wait_time:.2f}s")
            import asyncio
            await asyncio.sleep(wait_time)

        client = await self._ensure_client()
        start_time = time.perf_counter()

        try:
            response = await client.post(
                f"{self.BASE_URL}/chat/completions",
                headers=self._get_auth_headers(),
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )

            # Parse rate limit headers
            self._rate_limit = self._parse_rate_limit_headers(response.headers)

            if response.status_code == 429:
                self._health.record_failure(is_rate_limit=True)
                retry_after = self._rate_limit.retry_after_seconds or 5.0
                raise RuntimeError(
                    f"Cerebras rate limit exceeded. Retry after {retry_after:.1f}s. "
                    f"Remaining: {self._rate_limit.tokens_remaining} tokens/min"
                )

            response.raise_for_status()
            data = response.json()

            # Parse usage and calculate cost
            usage = self._parse_usage(data)
            cost = self._calculate_cost(usage)
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Update stats
            self._update_stats(usage, cost, latency_ms, success=True)

            logger.debug(
                f"Cerebras: {usage.total_tokens} tokens, {latency_ms:.0f}ms, "
                f"remaining: {self._rate_limit.tokens_remaining} tokens/min"
            )

            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_stats(UsageInfo(), self._calculate_cost(UsageInfo()), latency_ms, success=False)
            raise RuntimeError(f"Cerebras API error {e.response.status_code}: {e.response.text[:200]}")

        except Exception:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_stats(UsageInfo(), self._calculate_cost(UsageInfo()), latency_ms, success=False)
            raise

    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages."""
        if not self.is_available():
            raise RuntimeError("Cerebras provider not available - CEREBRAS_API_KEY not set")

        should_wait, wait_time = await self.should_throttle()
        if should_wait and wait_time > 0:
            import asyncio
            await asyncio.sleep(wait_time)

        client = await self._ensure_client()
        start_time = time.perf_counter()
        total_tokens = 0

        try:
            async with client.stream(
                "POST",
                f"{self.BASE_URL}/chat/completions",
                headers=self._get_auth_headers(),
                json={
                    "model": self.model_name,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": True,
                },
            ) as response:
                self._rate_limit = self._parse_rate_limit_headers(response.headers)

                if response.status_code != 200:
                    error_text = await response.aread()
                    self._health.record_failure(is_rate_limit=response.status_code == 429)
                    raise RuntimeError(f"Cerebras API error {response.status_code}: {error_text}")

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

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information with Cerebras-specific details."""
        info = super().get_model_info()
        info.update({
            "context_window": 128000,
            "supports_streaming": True,
            "tokens_per_day": self.RATE_LIMITS["tokens_per_day"],
        })
        return info
