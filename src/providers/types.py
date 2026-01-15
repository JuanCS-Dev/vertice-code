"""
Provider Types - Shared types for all LLM providers.

Based on 2025 best practices from:
- Groq API: https://console.groq.com/docs/rate-limits
- Cerebras: https://inference-docs.cerebras.ai/support/rate-limits
- OpenRouter: https://openrouter.ai/docs/guides/routing/provider-selection
- LiteLLM: https://docs.litellm.ai/docs/routing

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any


class CostTier(str, Enum):
    """Provider cost tier classification."""

    FREE = "free"
    LOW_COST = "low_cost"
    MEDIUM = "medium"
    PREMIUM = "premium"


class SpeedTier(str, Enum):
    """Provider speed tier classification."""

    INSTANT = "instant"  # < 100ms TTFT (Groq, Cerebras)
    FAST = "fast"  # < 500ms TTFT
    MEDIUM = "medium"  # < 2s TTFT
    SLOW = "slow"  # > 2s TTFT


@dataclass
class RateLimitInfo:
    """Rate limit information from API response headers.

    Attributes:
        requests_limit: Maximum requests per period
        requests_remaining: Remaining requests in period
        requests_reset_seconds: Seconds until requests reset
        tokens_limit: Maximum tokens per period
        tokens_remaining: Remaining tokens in period
        tokens_reset_seconds: Seconds until tokens reset
        retry_after_seconds: Seconds to wait on 429 (optional)
    """

    requests_limit: int = 0
    requests_remaining: int = 0
    requests_reset_seconds: float = 0.0
    tokens_limit: int = 0
    tokens_remaining: int = 0
    tokens_reset_seconds: float = 0.0
    retry_after_seconds: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def requests_utilization(self) -> float:
        """Calculate request utilization percentage."""
        if self.requests_limit == 0:
            return 0.0
        return 1.0 - (self.requests_remaining / self.requests_limit)

    @property
    def tokens_utilization(self) -> float:
        """Calculate token utilization percentage."""
        if self.tokens_limit == 0:
            return 0.0
        return 1.0 - (self.tokens_remaining / self.tokens_limit)

    @property
    def should_throttle(self) -> bool:
        """Check if we should throttle requests (>80% utilization)."""
        return self.requests_utilization > 0.8 or self.tokens_utilization > 0.8

    @property
    def is_rate_limited(self) -> bool:
        """Check if we're currently rate limited."""
        return self.retry_after_seconds is not None and self.retry_after_seconds > 0


@dataclass
class UsageInfo:
    """Token usage information from API response.

    Based on OpenAI/Groq/Cerebras response format.
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0  # Groq: cached tokens don't count toward rate limits
    prompt_time: float = 0.0  # Groq: time to process prompt
    completion_time: float = 0.0  # Groq: time to generate completion
    total_time: float = 0.0  # Total processing time
    queue_time: float = 0.0  # Groq: time in queue

    @classmethod
    def from_response(cls, usage: Dict[str, Any]) -> UsageInfo:
        """Parse usage from API response.

        Args:
            usage: Usage dict from API response

        Returns:
            UsageInfo instance
        """
        return cls(
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cached_tokens=usage.get("cached_tokens", 0),
            prompt_time=usage.get("prompt_time", 0.0),
            completion_time=usage.get("completion_time", 0.0),
            total_time=usage.get("total_time", 0.0),
            queue_time=usage.get("queue_time", 0.0),
        )

    @property
    def tokens_per_second(self) -> float:
        """Calculate tokens per second throughput."""
        if self.completion_time == 0:
            return 0.0
        return self.completion_tokens / self.completion_time


@dataclass
class CostInfo:
    """Cost information for a request.

    Pricing based on 2025 rates:
    - Groq: FREE (14,400 req/day)
    - Cerebras: FREE (1M tokens/day)
    - Mistral: FREE (1B tokens/month)
    - OpenRouter: Varies by model
    - Vertex AI: $0.075/$0.30 per 1M tokens (flash)
    - Azure OpenAI: $0.15/$0.60 per 1M tokens (gpt-4o-mini)
    """

    input_cost: float = 0.0
    output_cost: float = 0.0
    total_cost: float = 0.0
    currency: str = "USD"
    cached_discount: float = 0.0  # Discount from cached tokens

    @classmethod
    def calculate(
        cls,
        usage: UsageInfo,
        input_price_per_million: float,
        output_price_per_million: float,
        cached_price_per_million: float = 0.0,
    ) -> CostInfo:
        """Calculate cost from usage.

        Args:
            usage: Token usage info
            input_price_per_million: Price per 1M input tokens
            output_price_per_million: Price per 1M output tokens
            cached_price_per_million: Price per 1M cached tokens (usually discounted)

        Returns:
            CostInfo with calculated costs
        """
        billable_input = usage.prompt_tokens - usage.cached_tokens
        input_cost = (billable_input / 1_000_000) * input_price_per_million
        output_cost = (usage.completion_tokens / 1_000_000) * output_price_per_million
        cached_cost = (usage.cached_tokens / 1_000_000) * cached_price_per_million
        cached_discount = (usage.cached_tokens / 1_000_000) * (
            input_price_per_million - cached_price_per_million
        )

        return cls(
            input_cost=input_cost + cached_cost,
            output_cost=output_cost,
            total_cost=input_cost + output_cost + cached_cost,
            cached_discount=cached_discount,
        )


@dataclass
class ProviderPricing:
    """Pricing configuration for a provider/model.

    All prices in USD per 1 million tokens.
    """

    provider: str
    model: str
    input_price: float
    output_price: float
    cached_price: float = 0.0  # Usually 10% of input price
    cost_tier: CostTier = CostTier.FREE


# Provider-specific pricing database (2025)
# Class attribute set after definition to avoid mutable default
_PRICING_DB: Dict[str, Dict[str, ProviderPricing]] = {
    "groq": {
        "llama-3.3-70b-versatile": ProviderPricing(
            "groq", "llama-3.3-70b-versatile", 0.0, 0.0, 0.0, CostTier.FREE
        ),
        "llama-3.1-8b-instant": ProviderPricing(
            "groq", "llama-3.1-8b-instant", 0.0, 0.0, 0.0, CostTier.FREE
        ),
    },
    "cerebras": {
        "llama-3.3-70b": ProviderPricing(
            "cerebras", "llama-3.3-70b", 0.0, 0.0, 0.0, CostTier.FREE
        ),
        "llama3.1-8b": ProviderPricing(
            "cerebras", "llama3.1-8b", 0.0, 0.0, 0.0, CostTier.FREE
        ),
    },
    "mistral": {
        "mistral-large-latest": ProviderPricing(
            "mistral", "mistral-large-latest", 0.0, 0.0, 0.0, CostTier.FREE
        ),
        "codestral-latest": ProviderPricing(
            "mistral", "codestral-latest", 1.0, 3.0, 0.1, CostTier.LOW_COST
        ),
    },
    "openrouter": {
        "meta-llama/llama-3.3-70b-instruct": ProviderPricing(
            "openrouter", "meta-llama/llama-3.3-70b-instruct", 0.0, 0.0, 0.0, CostTier.FREE
        ),
        "deepseek/deepseek-r1": ProviderPricing(
            "openrouter", "deepseek/deepseek-r1", 0.55, 2.19, 0.055, CostTier.LOW_COST
        ),
        "anthropic/claude-3.5-sonnet": ProviderPricing(
            "openrouter", "anthropic/claude-3.5-sonnet", 3.0, 15.0, 0.3, CostTier.PREMIUM
        ),
    },
    "vertex-ai": {
        "gemini-2.5-flash": ProviderPricing(
            "vertex-ai", "gemini-2.5-flash", 0.075, 0.30, 0.0075, CostTier.LOW_COST
        ),
            "gemini-2.5-pro": ProviderPricing(
                "vertex-ai", "gemini-2.5-pro", 1.25, 5.0, 0.125, CostTier.MEDIUM
            ),    },
    "azure-openai": {
        "gpt4o-mini": ProviderPricing(
            "azure-openai", "gpt4o-mini", 0.15, 0.60, 0.015, CostTier.LOW_COST
        ),
        "gpt-4o": ProviderPricing(
            "azure-openai", "gpt-4o", 2.50, 10.0, 0.25, CostTier.PREMIUM
        ),
    },
}

# Attach to class for access via ProviderPricing.PRICING_DB
ProviderPricing.PRICING_DB = _PRICING_DB  # type: ignore[attr-defined]


@dataclass
class ProviderHealth:
    """Health status for a provider."""

    provider: str
    is_healthy: bool = True
    is_rate_limited: bool = False
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    failure_count: int = 0
    success_count: int = 0
    avg_latency_ms: float = 0.0
    rate_limit_info: Optional[RateLimitInfo] = None

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return 1.0
        return self.success_count / total

    def record_success(self, latency_ms: float) -> None:
        """Record a successful request.

        Args:
            latency_ms: Request latency in milliseconds
        """
        self.success_count += 1
        self.last_success = datetime.now()
        self.is_healthy = True
        self.failure_count = max(0, self.failure_count - 1)

        # Update rolling average latency
        total = self.success_count
        self.avg_latency_ms = (
            (self.avg_latency_ms * (total - 1) + latency_ms) / total if total > 1 else latency_ms
        )

    def record_failure(self, is_rate_limit: bool = False) -> None:
        """Record a failed request.

        Args:
            is_rate_limit: Whether failure was due to rate limiting
        """
        self.failure_count += 1
        self.last_failure = datetime.now()
        self.is_rate_limited = is_rate_limit

        if self.failure_count >= 3:
            self.is_healthy = False


@dataclass
class OpenRouterProviderPrefs:
    """OpenRouter provider preferences for request routing.

    Based on: https://openrouter.ai/docs/guides/routing/provider-selection
    """

    sort: Optional[str] = None  # "price", "latency", "throughput"
    order: Optional[List[str]] = None  # Provider priority order
    allow: Optional[List[str]] = None  # Only these providers
    ignore: Optional[List[str]] = None  # Exclude these providers
    allow_fallbacks: bool = True  # Enable automatic fallbacks
    require_parameters: bool = False  # Only providers supporting all params
    data_collection: Optional[str] = None  # "deny" for no logging
    max_price: Optional[Dict[str, float]] = None  # {"prompt": X, "completion": Y}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API request format."""
        result = {}
        if self.sort:
            result["sort"] = self.sort
        if self.order:
            result["order"] = self.order
        if self.allow:
            result["allow"] = self.allow
        if self.ignore:
            result["ignore"] = self.ignore
        if not self.allow_fallbacks:
            result["allow_fallbacks"] = False
        if self.require_parameters:
            result["require_parameters"] = True
        if self.data_collection:
            result["data_collection"] = self.data_collection
        if self.max_price:
            result["max_price"] = self.max_price
        return result
