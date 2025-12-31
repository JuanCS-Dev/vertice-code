"""
Enhanced Provider Base - Production-ready base class for all LLM providers.

Features:
- Rate limit header parsing (Groq, Cerebras, OpenRouter compatible)
- Token usage tracking with cost calculation
- Health monitoring and metrics
- Prometheus-compatible metrics export
- Automatic throttling based on utilization

Based on 2025 best practices:
- Groq: https://console.groq.com/docs/rate-limits
- Cerebras: https://inference-docs.cerebras.ai/support/rate-limits
- OpenRouter: https://openrouter.ai/docs/guides/routing/provider-selection

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, AsyncGenerator, Any, Tuple

import httpx

from .types import (
    RateLimitInfo,
    UsageInfo,
    CostInfo,
    ProviderPricing,
    ProviderHealth,
    CostTier,
    SpeedTier,
)

logger = logging.getLogger(__name__)


@dataclass
class ProviderStats:
    """Aggregated statistics for a provider."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cached_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    start_time: datetime = field(default_factory=datetime.now)

    @property
    def avg_latency_ms(self) -> float:
        """Calculate average latency."""
        if self.successful_requests == 0:
            return 0.0
        return self.total_latency_ms / self.successful_requests

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def tokens_per_dollar(self) -> float:
        """Calculate tokens per dollar (efficiency metric)."""
        if self.total_cost_usd == 0:
            return float("inf")  # Free tier
        return (self.total_input_tokens + self.total_output_tokens) / self.total_cost_usd


class EnhancedProviderBase(ABC):
    """Enhanced base class for all LLM providers.

    Provides:
    - Automatic rate limit header parsing
    - Token usage tracking and cost calculation
    - Health monitoring
    - Prometheus metrics export
    - Adaptive throttling

    Subclasses must implement:
    - _get_headers_mapping(): Provider-specific header names
    - generate(): Core generation method
    - stream_generate(): Streaming generation
    """

    # Override in subclasses
    PROVIDER_NAME: str = "base"
    BASE_URL: str = ""
    COST_TIER: CostTier = CostTier.FREE
    SPEED_TIER: SpeedTier = SpeedTier.FAST

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "",
        timeout: float = 120.0,
        max_retries: int = 3,
    ):
        """Initialize enhanced provider.

        Args:
            api_key: API key for authentication
            model_name: Model identifier
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries

        # Tracking
        self._client: Optional[httpx.AsyncClient] = None
        self._rate_limit: RateLimitInfo = RateLimitInfo()
        self._health: ProviderHealth = ProviderHealth(provider=self.PROVIDER_NAME)
        self._stats: ProviderStats = ProviderStats()
        self._last_usage: Optional[UsageInfo] = None
        self._last_cost: Optional[CostInfo] = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Ensure HTTP client is initialized with optimal settings."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                limits=httpx.Limits(
                    max_connections=100,
                    max_keepalive_connections=20,
                    keepalive_expiry=5.0,
                ),
                http2=True,  # Enable HTTP/2 for better performance
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @abstractmethod
    def _get_headers_mapping(self) -> Dict[str, str]:
        """Get provider-specific header name mapping.

        Returns:
            Dict mapping standard names to provider header names.
            Standard names:
            - requests_limit, requests_remaining, requests_reset
            - tokens_limit, tokens_remaining, tokens_reset
            - retry_after
        """
        pass

    def _parse_rate_limit_headers(self, headers: httpx.Headers) -> RateLimitInfo:
        """Parse rate limit information from response headers.

        Args:
            headers: Response headers

        Returns:
            RateLimitInfo with parsed values
        """
        mapping = self._get_headers_mapping()

        def get_int(key: str, default: int = 0) -> int:
            header_name = mapping.get(key, "")
            value = headers.get(header_name, "")
            try:
                return int(value) if value else default
            except ValueError:
                return default

        def get_float(key: str, default: float = 0.0) -> float:
            header_name = mapping.get(key, "")
            value = headers.get(header_name, "")
            try:
                return float(value) if value else default
            except ValueError:
                return default

        return RateLimitInfo(
            requests_limit=get_int("requests_limit"),
            requests_remaining=get_int("requests_remaining"),
            requests_reset_seconds=get_float("requests_reset"),
            tokens_limit=get_int("tokens_limit"),
            tokens_remaining=get_int("tokens_remaining"),
            tokens_reset_seconds=get_float("tokens_reset"),
            retry_after_seconds=get_float("retry_after") or None,
        )

    def _parse_usage(self, response_data: Dict[str, Any]) -> UsageInfo:
        """Parse usage from API response.

        Args:
            response_data: Full API response

        Returns:
            UsageInfo with parsed values
        """
        usage = response_data.get("usage", {})
        return UsageInfo.from_response(usage)

    def _calculate_cost(self, usage: UsageInfo) -> CostInfo:
        """Calculate cost from usage.

        Args:
            usage: Token usage info

        Returns:
            CostInfo with calculated costs
        """
        # Get pricing for this provider/model
        provider_pricing = ProviderPricing.PRICING_DB.get(self.PROVIDER_NAME, {})
        pricing = provider_pricing.get(self.model_name)

        if not pricing:
            # Free tier or unknown pricing
            return CostInfo(input_cost=0.0, output_cost=0.0, total_cost=0.0)

        return CostInfo.calculate(
            usage=usage,
            input_price_per_million=pricing.input_price,
            output_price_per_million=pricing.output_price,
            cached_price_per_million=pricing.cached_price,
        )

    def _update_stats(
        self,
        usage: UsageInfo,
        cost: CostInfo,
        latency_ms: float,
        success: bool,
    ) -> None:
        """Update provider statistics.

        Args:
            usage: Token usage info
            cost: Cost info
            latency_ms: Request latency
            success: Whether request succeeded
        """
        self._stats.total_requests += 1

        if success:
            self._stats.successful_requests += 1
            self._stats.total_input_tokens += usage.prompt_tokens
            self._stats.total_output_tokens += usage.completion_tokens
            self._stats.total_cached_tokens += usage.cached_tokens
            self._stats.total_cost_usd += cost.total_cost
            self._stats.total_latency_ms += latency_ms
            self._health.record_success(latency_ms)
        else:
            self._stats.failed_requests += 1
            self._health.record_failure()

        self._last_usage = usage
        self._last_cost = cost

    async def should_throttle(self) -> Tuple[bool, float]:
        """Check if we should throttle requests.

        Returns:
            Tuple of (should_throttle, wait_seconds)
        """
        if self._rate_limit.is_rate_limited:
            wait = self._rate_limit.retry_after_seconds or 5.0
            return True, wait

        if self._rate_limit.should_throttle:
            # >80% utilization, slow down
            return True, 0.5

        return False, 0.0

    def is_available(self) -> bool:
        """Check if provider is available."""
        return bool(self.api_key) and self._health.is_healthy

    def get_health(self) -> ProviderHealth:
        """Get provider health status."""
        self._health.rate_limit_info = self._rate_limit
        return self._health

    def get_stats(self) -> ProviderStats:
        """Get provider statistics."""
        return self._stats

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus-formatted metrics.

        Returns:
            Prometheus metrics string
        """
        p = self.PROVIDER_NAME
        m = self.model_name.replace("/", "_").replace("-", "_")

        lines = [
            f'# HELP provider_requests_total Total requests to provider',
            f'# TYPE provider_requests_total counter',
            f'provider_requests_total{{provider="{p}",model="{m}"}} {self._stats.total_requests}',
            f'',
            f'# HELP provider_success_rate Success rate (0-1)',
            f'# TYPE provider_success_rate gauge',
            f'provider_success_rate{{provider="{p}",model="{m}"}} {self._stats.success_rate:.4f}',
            f'',
            f'# HELP provider_tokens_total Total tokens used',
            f'# TYPE provider_tokens_total counter',
            f'provider_tokens_total{{provider="{p}",model="{m}",type="input"}} {self._stats.total_input_tokens}',
            f'provider_tokens_total{{provider="{p}",model="{m}",type="output"}} {self._stats.total_output_tokens}',
            f'provider_tokens_total{{provider="{p}",model="{m}",type="cached"}} {self._stats.total_cached_tokens}',
            f'',
            f'# HELP provider_cost_usd_total Total cost in USD',
            f'# TYPE provider_cost_usd_total counter',
            f'provider_cost_usd_total{{provider="{p}",model="{m}"}} {self._stats.total_cost_usd:.6f}',
            f'',
            f'# HELP provider_latency_ms Average latency in milliseconds',
            f'# TYPE provider_latency_ms gauge',
            f'provider_latency_ms{{provider="{p}",model="{m}"}} {self._stats.avg_latency_ms:.2f}',
            f'',
            f'# HELP provider_rate_limit_remaining Remaining rate limit',
            f'# TYPE provider_rate_limit_remaining gauge',
            f'provider_rate_limit_remaining{{provider="{p}",type="requests"}} {self._rate_limit.requests_remaining}',
            f'provider_rate_limit_remaining{{provider="{p}",type="tokens"}} {self._rate_limit.tokens_remaining}',
        ]

        return "\n".join(lines)

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "provider": self.PROVIDER_NAME,
            "model": self.model_name,
            "available": self.is_available(),
            "cost_tier": self.COST_TIER.value,
            "speed_tier": self.SPEED_TIER.value,
            "health": {
                "is_healthy": self._health.is_healthy,
                "success_rate": self._health.success_rate,
                "avg_latency_ms": self._health.avg_latency_ms,
            },
            "rate_limit": {
                "requests_remaining": self._rate_limit.requests_remaining,
                "tokens_remaining": self._rate_limit.tokens_remaining,
                "utilization": max(
                    self._rate_limit.requests_utilization,
                    self._rate_limit.tokens_utilization,
                ),
            },
        }

    def count_tokens(self, text: str) -> int:
        """Estimate token count (override for provider-specific counting).

        Args:
            text: Text to count

        Returns:
            Estimated token count
        """
        # Default: ~4 chars per token (Llama/GPT approximation)
        return len(text) // 4

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """Generate completion from messages.

        Args:
            messages: Conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific arguments

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream generation from messages.

        Args:
            messages: Conversation messages
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional provider-specific arguments

        Yields:
            Generated text chunks
        """
        pass

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream chat with optional system prompt.

        Args:
            messages: Conversation messages
            system_prompt: Optional system instructions
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional arguments

        Yields:
            Generated text chunks
        """
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        async for chunk in self.stream_generate(
            full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        ):
            yield chunk
