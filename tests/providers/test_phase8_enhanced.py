"""
Phase 8 Enhanced Provider Tests - Comprehensive test suite.

Tests for:
- Rate limit header parsing
- Token usage tracking
- Cost calculation
- Monthly budget tracking (Mistral)
- OpenRouter :floor suffix optimization
- Prometheus metrics export

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from providers import (
    CostTier,
    SpeedTier,
    RateLimitInfo,
    UsageInfo,
    CostInfo,
    ProviderPricing,
    ProviderHealth,
    ProviderStats,
    OpenRouterProviderPrefs,
    GroqProvider,
    CerebrasProvider,
    MistralProvider,
    OpenRouterProvider,
)


class TestRateLimitInfo:
    """Test RateLimitInfo dataclass."""

    def test_default_values(self) -> None:
        """Test default initialization."""
        info = RateLimitInfo()
        assert info.requests_limit == 0
        assert info.requests_remaining == 0
        assert info.tokens_limit == 0
        assert info.tokens_remaining == 0
        assert info.retry_after_seconds is None

    def test_utilization_calculation(self) -> None:
        """Test utilization percentage calculation."""
        info = RateLimitInfo(
            requests_limit=100,
            requests_remaining=20,
            tokens_limit=10000,
            tokens_remaining=2000,
        )
        assert info.requests_utilization == 0.8  # 80% used
        assert info.tokens_utilization == 0.8

    def test_should_throttle_high_utilization(self) -> None:
        """Test throttle trigger at >80% utilization."""
        info = RateLimitInfo(requests_limit=100, requests_remaining=19)
        assert info.should_throttle is True

    def test_should_not_throttle_low_utilization(self) -> None:
        """Test no throttle at <80% utilization."""
        info = RateLimitInfo(requests_limit=100, requests_remaining=50)
        assert info.should_throttle is False

    def test_is_rate_limited(self) -> None:
        """Test rate limit detection."""
        info = RateLimitInfo(retry_after_seconds=5.0)
        assert info.is_rate_limited is True

        info2 = RateLimitInfo()
        assert info2.is_rate_limited is False


class TestUsageInfo:
    """Test UsageInfo dataclass."""

    def test_from_response(self) -> None:
        """Test parsing from API response."""
        response = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "cached_tokens": 10,
        }
        usage = UsageInfo.from_response(response)

        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150
        assert usage.cached_tokens == 10

    def test_tokens_per_second(self) -> None:
        """Test throughput calculation."""
        usage = UsageInfo(completion_tokens=100, completion_time=0.1)
        assert usage.tokens_per_second == 1000.0

    def test_tokens_per_second_zero_time(self) -> None:
        """Test throughput with zero time."""
        usage = UsageInfo(completion_tokens=100, completion_time=0)
        assert usage.tokens_per_second == 0.0


class TestCostInfo:
    """Test CostInfo dataclass."""

    def test_calculate_basic(self) -> None:
        """Test basic cost calculation."""
        usage = UsageInfo(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
        cost = CostInfo.calculate(
            usage=usage,
            input_price_per_million=1.0,  # $1/1M
            output_price_per_million=2.0,  # $2/1M
        )

        assert cost.input_cost == pytest.approx(0.001)  # 1000/1M * $1
        assert cost.output_cost == pytest.approx(0.001)  # 500/1M * $2
        assert cost.total_cost == pytest.approx(0.002)

    def test_calculate_with_cached_tokens(self) -> None:
        """Test cost calculation with cached tokens."""
        usage = UsageInfo(
            prompt_tokens=1000, completion_tokens=500, total_tokens=1500, cached_tokens=200
        )
        cost = CostInfo.calculate(
            usage=usage,
            input_price_per_million=1.0,
            output_price_per_million=2.0,
            cached_price_per_million=0.1,  # 90% discount
        )

        # Billable: 1000-200 = 800 * $1/1M = $0.0008
        # Cached: 200 * $0.1/1M = $0.00002
        # Output: 500 * $2/1M = $0.001
        assert cost.input_cost == pytest.approx(0.0008 + 0.00002)
        assert cost.cached_discount == pytest.approx(200 / 1_000_000 * 0.9)

    def test_free_tier_zero_cost(self) -> None:
        """Test free tier has zero cost."""
        usage = UsageInfo(prompt_tokens=1000000, completion_tokens=500000)
        cost = CostInfo.calculate(usage=usage, input_price_per_million=0, output_price_per_million=0)

        assert cost.total_cost == 0.0


class TestProviderPricing:
    """Test ProviderPricing and pricing database."""

    def test_pricing_db_has_providers(self) -> None:
        """Test pricing database initialization."""
        assert "groq" in ProviderPricing.PRICING_DB
        assert "cerebras" in ProviderPricing.PRICING_DB
        assert "mistral" in ProviderPricing.PRICING_DB
        assert "openrouter" in ProviderPricing.PRICING_DB
        assert "vertex-ai" in ProviderPricing.PRICING_DB
        assert "azure-openai" in ProviderPricing.PRICING_DB

    def test_groq_free_tier(self) -> None:
        """Test Groq is free tier."""
        groq_pricing = ProviderPricing.PRICING_DB["groq"]
        for model_pricing in groq_pricing.values():
            assert model_pricing.cost_tier == CostTier.FREE
            assert model_pricing.input_price == 0.0
            assert model_pricing.output_price == 0.0


class TestProviderHealth:
    """Test ProviderHealth tracking."""

    def test_initial_healthy(self) -> None:
        """Test initial state is healthy."""
        health = ProviderHealth(provider="test")
        assert health.is_healthy is True
        assert health.success_rate == 1.0

    def test_record_success(self) -> None:
        """Test success recording updates stats."""
        health = ProviderHealth(provider="test")
        health.record_success(latency_ms=100.0)

        assert health.success_count == 1
        assert health.avg_latency_ms == 100.0
        assert health.last_success is not None

    def test_record_failure_degrades_health(self) -> None:
        """Test failures degrade health after threshold."""
        health = ProviderHealth(provider="test")

        for _ in range(3):
            health.record_failure()

        assert health.is_healthy is False
        assert health.failure_count == 3

    def test_success_decrements_failures(self) -> None:
        """Test success reduces failure count."""
        health = ProviderHealth(provider="test", failure_count=2)
        health.record_success(latency_ms=100.0)

        assert health.failure_count == 1


class TestOpenRouterProviderPrefs:
    """Test OpenRouter provider preferences."""

    def test_to_dict_empty(self) -> None:
        """Test empty prefs produces empty dict."""
        prefs = OpenRouterProviderPrefs()
        assert prefs.to_dict() == {}

    def test_to_dict_with_options(self) -> None:
        """Test prefs with options."""
        prefs = OpenRouterProviderPrefs(
            sort="price",
            order=["anthropic", "openai"],
            ignore=["azure"],
            allow_fallbacks=False,
        )
        result = prefs.to_dict()

        assert result["sort"] == "price"
        assert result["order"] == ["anthropic", "openai"]
        assert result["ignore"] == ["azure"]
        assert result["allow_fallbacks"] is False


class TestGroqProvider:
    """Test enhanced GroqProvider."""

    def test_initialization(self) -> None:
        """Test provider initialization."""
        provider = GroqProvider(api_key="test-key", model_name="llama-70b")

        assert provider.PROVIDER_NAME == "groq"
        assert provider.COST_TIER == CostTier.FREE
        assert provider.SPEED_TIER == SpeedTier.INSTANT
        assert provider.model_name == "llama-3.3-70b-versatile"

    def test_headers_mapping(self) -> None:
        """Test Groq-specific header mapping."""
        provider = GroqProvider(api_key="test")
        mapping = provider._get_headers_mapping()

        assert mapping["requests_limit"] == "x-ratelimit-limit-requests"
        assert mapping["requests_remaining"] == "x-ratelimit-remaining-requests"
        assert mapping["tokens_limit"] == "x-ratelimit-limit-tokens"
        assert mapping["tokens_remaining"] == "x-ratelimit-remaining-tokens"
        assert mapping["retry_after"] == "retry-after"

    def test_is_not_available_without_key(self) -> None:
        """Test availability check."""
        with patch.dict("os.environ", {}, clear=True):
            provider = GroqProvider(api_key=None)
            assert provider.is_available() is False

    def test_model_info(self) -> None:
        """Test model info includes Groq-specific details."""
        provider = GroqProvider(api_key="test")
        info = provider.get_model_info()

        assert info["provider"] == "groq"
        assert info["cost_tier"] == "free"
        assert info["speed_tier"] == "instant"
        assert "requests_per_day" in info


class TestCerebrasProvider:
    """Test enhanced CerebrasProvider."""

    def test_initialization(self) -> None:
        """Test provider initialization."""
        provider = CerebrasProvider(api_key="test-key", model_name="llama-70b")

        assert provider.PROVIDER_NAME == "cerebras"
        assert provider.COST_TIER == CostTier.FREE
        assert provider.SPEED_TIER == SpeedTier.INSTANT
        assert provider.model_name == "llama-3.3-70b"

    def test_headers_mapping_day_minute(self) -> None:
        """Test Cerebras uses day/minute granularity headers."""
        provider = CerebrasProvider(api_key="test")
        mapping = provider._get_headers_mapping()

        assert "day" in mapping["requests_limit"]
        assert "minute" in mapping["tokens_limit"]

    def test_model_info(self) -> None:
        """Test model info includes tokens per day."""
        provider = CerebrasProvider(api_key="test")
        info = provider.get_model_info()

        assert "tokens_per_day" in info
        assert info["tokens_per_day"] == 1000000


class TestMistralProvider:
    """Test enhanced MistralProvider with budget tracking."""

    def test_initialization(self) -> None:
        """Test provider initialization."""
        provider = MistralProvider(api_key="test-key", model_name="large")

        assert provider.PROVIDER_NAME == "mistral"
        assert provider.COST_TIER == CostTier.FREE
        assert provider.model_name == "mistral-large-latest"

    def test_monthly_budget_tracking(self) -> None:
        """Test monthly budget starts at 1B."""
        provider = MistralProvider(api_key="test")

        assert provider.monthly_budget_remaining == 1_000_000_000
        assert provider.monthly_budget_utilization == 0.0

    def test_monthly_usage_update(self) -> None:
        """Test monthly usage tracking."""
        provider = MistralProvider(api_key="test")
        provider._update_monthly_usage(1000)

        assert provider._monthly_tokens_used == 1000
        assert provider.monthly_budget_remaining == 999_999_000

    def test_budget_exceeded_raises(self) -> None:
        """Test budget exceeded raises error."""
        provider = MistralProvider(api_key="test")
        provider._monthly_tokens_used = 999_999_999

        with pytest.raises(RuntimeError, match="budget exceeded"):
            provider._check_monthly_budget(estimated_tokens=10)

    def test_codestral_paid_tier(self) -> None:
        """Test Codestral is paid tier."""
        provider = MistralProvider(api_key="test", model_name="codestral")

        assert provider.COST_TIER == CostTier.LOW_COST

    def test_model_info_includes_budget(self) -> None:
        """Test model info includes monthly budget details."""
        provider = MistralProvider(api_key="test")
        info = provider.get_model_info()

        assert "tokens_per_month" in info
        assert "monthly_remaining" in info
        assert "monthly_utilization" in info


class TestOpenRouterProvider:
    """Test enhanced OpenRouterProvider with :floor optimization."""

    def test_initialization(self) -> None:
        """Test provider initialization."""
        provider = OpenRouterProvider(api_key="test-key", model_name="llama-70b")

        assert provider.PROVIDER_NAME == "openrouter"
        assert provider.model_name == "meta-llama/llama-3.3-70b-instruct"

    def test_floor_suffix_applied(self) -> None:
        """Test :floor suffix applied for cost optimization."""
        provider = OpenRouterProvider(api_key="test")
        model = provider._apply_cost_suffix("test-model", optimize_cost=True)

        assert model == "test-model:floor"

    def test_floor_suffix_not_duplicated(self) -> None:
        """Test :floor not duplicated if already present."""
        provider = OpenRouterProvider(api_key="test")
        model = provider._apply_cost_suffix("test-model:floor", optimize_cost=True)

        assert model == "test-model:floor"

    def test_nitro_suffix_preserved(self) -> None:
        """Test :nitro suffix preserved (not replaced with :floor)."""
        provider = OpenRouterProvider(api_key="test")
        model = provider._apply_cost_suffix("test-model:nitro", optimize_cost=True)

        assert model == "test-model:nitro"

    def test_floor_suffix_disabled(self) -> None:
        """Test :floor can be disabled."""
        provider = OpenRouterProvider(api_key="test")
        model = provider._apply_cost_suffix("test-model", optimize_cost=False)

        assert model == "test-model"

    def test_provider_preferences_in_request(self) -> None:
        """Test provider preferences included in request body."""
        prefs = OpenRouterProviderPrefs(sort="price", ignore=["azure"])
        provider = OpenRouterProvider(api_key="test", provider_prefs=prefs)

        body = provider._build_request_body(
            messages=[{"role": "user", "content": "test"}],
            max_tokens=100,
            temperature=0.7,
        )

        assert "provider" in body
        assert body["provider"]["sort"] == "price"
        assert body["provider"]["ignore"] == ["azure"]

    def test_free_model_cost_tier(self) -> None:
        """Test free models have FREE cost tier."""
        provider = OpenRouterProvider(api_key="test", model_name="llama-8b")

        assert provider.COST_TIER == CostTier.FREE

    def test_set_provider_preferences(self) -> None:
        """Test updating provider preferences."""
        provider = OpenRouterProvider(api_key="test")
        provider.set_provider_preferences(
            sort="latency", order=["anthropic"], allow_fallbacks=False
        )

        assert provider.provider_prefs.sort == "latency"
        assert provider.provider_prefs.order == ["anthropic"]
        assert provider.provider_prefs.allow_fallbacks is False


class TestProviderStats:
    """Test ProviderStats aggregation."""

    def test_avg_latency_empty(self) -> None:
        """Test average latency with no requests."""
        stats = ProviderStats()
        assert stats.avg_latency_ms == 0.0

    def test_avg_latency_calculation(self) -> None:
        """Test average latency calculation."""
        stats = ProviderStats(successful_requests=2, total_latency_ms=200.0)
        assert stats.avg_latency_ms == 100.0

    def test_success_rate(self) -> None:
        """Test success rate calculation."""
        stats = ProviderStats(total_requests=10, successful_requests=8, failed_requests=2)
        assert stats.success_rate == 0.8

    def test_tokens_per_dollar_free(self) -> None:
        """Test tokens per dollar for free tier."""
        stats = ProviderStats(
            total_input_tokens=1000000, total_output_tokens=500000, total_cost_usd=0.0
        )
        assert stats.tokens_per_dollar == float("inf")

    def test_tokens_per_dollar_paid(self) -> None:
        """Test tokens per dollar for paid tier."""
        stats = ProviderStats(
            total_input_tokens=1000000, total_output_tokens=500000, total_cost_usd=1.5
        )
        assert stats.tokens_per_dollar == 1000000.0


class TestPrometheusMetrics:
    """Test Prometheus metrics export."""

    def test_metrics_format(self) -> None:
        """Test Prometheus metrics format."""
        provider = GroqProvider(api_key="test")
        provider._stats.total_requests = 100
        provider._stats.successful_requests = 95

        metrics = provider.get_prometheus_metrics()

        assert "provider_requests_total" in metrics
        assert 'provider="groq"' in metrics
        assert "100" in metrics
        assert "provider_success_rate" in metrics


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
