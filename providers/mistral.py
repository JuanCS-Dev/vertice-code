"""
Mistral API provider implementation - Enhanced for Phase 8.

European AI with generous FREE TIER
- 1,000,000,000 tokens/month (1B!)
- High quality code generation

Features (2025 Best Practices):
- Rate limit header parsing
- Token usage tracking
- Budget tracking for 1B monthly allocation
- Codestral support with 256K context

References:
- https://docs.mistral.ai/deployment/ai-studio/tier
- https://docs.mistral.ai/api

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, AsyncGenerator, Any

import httpx

from .base import EnhancedProviderBase
from .types import CostTier, SpeedTier, UsageInfo

logger = logging.getLogger(__name__)


class MistralProvider(EnhancedProviderBase):
    """
    Mistral API provider - European AI excellence.

    FREE TIER: 1,000,000,000 tokens/month (1 BILLION)
    Excellent for code generation and analysis.

    Models:
    - mistral-large-latest: Best quality
    - codestral-latest: Code specialist (256K context)
    - mistral-small-latest: Fast and cheap
    """

    PROVIDER_NAME = "mistral"
    BASE_URL = "https://api.mistral.ai/v1"
    COST_TIER = CostTier.FREE
    SPEED_TIER = SpeedTier.FAST

    MODELS = {
        "large": "mistral-large-latest",
        "medium": "mistral-medium-latest",
        "small": "mistral-small-latest",
        "codestral": "codestral-latest",
        "nemo": "open-mistral-nemo",
    }

    # Codestral is paid, others free
    PAID_MODELS = {"codestral"}

    # Rate limits (free tier)
    RATE_LIMITS = {
        "tokens_per_month": 1_000_000_000,  # 1B!
        "requests_per_second": 1,
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "large",
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """Initialize Mistral provider.

        Args:
            api_key: Mistral API key (defaults to MISTRAL_API_KEY env var)
            model_name: Model alias or full name
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        resolved_model = self.MODELS.get(model_name, model_name)
        super().__init__(
            api_key=api_key or os.getenv("MISTRAL_API_KEY"),
            model_name=resolved_model,
            timeout=timeout,
            max_retries=max_retries,
        )

        # Determine cost tier
        if model_name in self.PAID_MODELS:
            self.COST_TIER = CostTier.LOW_COST

        # Track monthly budget
        self._month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        self._monthly_tokens_used = 0

    def _get_headers_mapping(self) -> Dict[str, str]:
        """Get Mistral header mapping."""
        return {
            "requests_limit": "x-ratelimit-limit-requests",
            "requests_remaining": "x-ratelimit-remaining-requests",
            "requests_reset": "x-ratelimit-reset-requests",
            "tokens_limit": "x-ratelimit-limit-tokens",
            "tokens_remaining": "x-ratelimit-remaining-tokens",
            "tokens_reset": "x-ratelimit-reset-tokens",
            "retry_after": "retry-after",
        }

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _check_monthly_budget(self, estimated_tokens: int = 0) -> None:
        """Check if we're within monthly budget.

        Args:
            estimated_tokens: Estimated tokens for this request

        Raises:
            RuntimeError: If monthly budget exceeded
        """
        # Reset counter if new month
        now = datetime.now()
        if now.month != self._month_start.month:
            self._month_start = now.replace(day=1, hour=0, minute=0, second=0)
            self._monthly_tokens_used = 0

        projected = self._monthly_tokens_used + estimated_tokens
        if projected > self.RATE_LIMITS["tokens_per_month"]:
            remaining = self.RATE_LIMITS["tokens_per_month"] - self._monthly_tokens_used
            raise RuntimeError(
                f"Mistral monthly budget exceeded. "
                f"Used: {self._monthly_tokens_used:,}, Remaining: {remaining:,}"
            )

    def _update_monthly_usage(self, tokens: int) -> None:
        """Update monthly token usage."""
        self._monthly_tokens_used += tokens

    @property
    def monthly_budget_remaining(self) -> int:
        """Get remaining monthly token budget."""
        return self.RATE_LIMITS["tokens_per_month"] - self._monthly_tokens_used

    @property
    def monthly_budget_utilization(self) -> float:
        """Get monthly budget utilization percentage."""
        return self._monthly_tokens_used / self.RATE_LIMITS["tokens_per_month"]

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate completion with budget tracking."""
        if not self.is_available():
            raise RuntimeError("Mistral provider not available - MISTRAL_API_KEY not set")

        # Estimate tokens and check budget
        estimated = sum(len(m.get("content", "")) // 4 for m in messages) + max_tokens
        self._check_monthly_budget(estimated)

        should_wait, wait_time = await self.should_throttle()
        if should_wait and wait_time > 0:
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

            self._rate_limit = self._parse_rate_limit_headers(response.headers)

            if response.status_code == 429:
                self._health.record_failure(is_rate_limit=True)
                raise RuntimeError("Mistral rate limit exceeded - try again later")

            response.raise_for_status()
            data = response.json()

            usage = self._parse_usage(data)
            cost = self._calculate_cost(usage)
            latency_ms = (time.perf_counter() - start_time) * 1000

            # Update monthly tracking
            self._update_monthly_usage(usage.total_tokens)

            self._update_stats(usage, cost, latency_ms, success=True)

            logger.debug(
                f"Mistral: {usage.total_tokens} tokens, ${cost.total_cost:.6f}, "
                f"monthly: {self._monthly_tokens_used:,}/{self.RATE_LIMITS['tokens_per_month']:,}"
            )

            return data["choices"][0]["message"]["content"]

        except httpx.HTTPStatusError as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_stats(UsageInfo(), self._calculate_cost(UsageInfo()), latency_ms, success=False)
            raise RuntimeError(f"Mistral API error {e.response.status_code}: {e.response.text[:200]}")

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
        """Stream generation with budget tracking."""
        if not self.is_available():
            raise RuntimeError("Mistral provider not available - MISTRAL_API_KEY not set")

        estimated = sum(len(m.get("content", "")) // 4 for m in messages) + max_tokens
        self._check_monthly_budget(estimated)

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
                    raise RuntimeError(f"Mistral API error {response.status_code}: {error_text}")

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
                                self._update_monthly_usage(usage.total_tokens)
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
                self._update_monthly_usage(estimated_usage.total_tokens)
                latency_ms = (time.perf_counter() - start_time) * 1000
                self._update_stats(estimated_usage, self._calculate_cost(estimated_usage), latency_ms, success=True)

        except Exception:
            latency_ms = (time.perf_counter() - start_time) * 1000
            self._update_stats(UsageInfo(), self._calculate_cost(UsageInfo()), latency_ms, success=False)
            raise

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information with Mistral-specific details."""
        info = super().get_model_info()

        # Codestral has 256K context, others 128K
        context_window = 256000 if "codestral" in self.model_name else 128000

        info.update({
            "context_window": context_window,
            "supports_streaming": True,
            "tokens_per_month": self.RATE_LIMITS["tokens_per_month"],
            "monthly_used": self._monthly_tokens_used,
            "monthly_remaining": self.monthly_budget_remaining,
            "monthly_utilization": f"{self.monthly_budget_utilization:.2%}",
        })
        return info
