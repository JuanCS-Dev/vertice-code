"""
Resilience Mixin - Unified resilience integration for agents.

Combines all resilience patterns:
- Retry with exponential backoff
- Circuit breaker isolation
- Rate limiting
- Provider fallback

References:
- AWS Architecture: Build Resilient Generative AI Agents
- https://aws.amazon.com/blogs/architecture/build-resilient-generative-ai-agents/
"""

from __future__ import annotations

import logging
from typing import TypeVar, Callable, Awaitable, Optional, Dict, Any, List
from functools import wraps

from .types import (
    RetryConfig,
    CircuitBreakerConfig,
    RateLimitConfig,
    FallbackConfig,
    ErrorContext,
    ResilienceError,
)
from .retry import RetryHandler
from .circuit_breaker import CircuitBreaker
from .rate_limiter import RateLimiter
from .fallback import FallbackHandler

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ResilienceMixin:
    """Mixin providing resilience capabilities to agents.

    Provides:
    - resilient_call(): Combined retry + circuit breaker + rate limiting
    - Per-provider circuit breakers
    - Unified health monitoring
    - Prometheus-compatible metrics

    Usage:
        class MyAgent(ResilienceMixin, BaseAgent):
            async def call_llm(self, prompt: str) -> str:
                return await self.resilient_call(
                    self._provider.chat,
                    prompt,
                    provider="openai",
                    estimated_tokens=500,
                )

    Or with decorator:
        @self.with_resilience(provider="openai")
        async def call_llm(self, prompt: str) -> str:
            return await self._provider.chat(prompt)
    """

    # Configuration (can be overridden by subclasses)
    RETRY_CONFIG = RetryConfig(max_retries=3, base_delay=1.0, jitter=0.1)
    CIRCUIT_CONFIG = CircuitBreakerConfig(failure_threshold=5, timeout=30.0)
    RATE_LIMIT_CONFIG = RateLimitConfig(requests_per_minute=60, tokens_per_minute=100000)

    def _init_resilience(self) -> None:
        """Initialize resilience components."""
        if hasattr(self, "_resilience_initialized"):
            return

        self._resilience_initialized = True

        # Components
        self._retry_handler = RetryHandler(
            config=self.RETRY_CONFIG,
            on_retry=self._on_retry_callback,
        )
        self._circuits: Dict[str, CircuitBreaker] = {}
        self._rate_limiters: Dict[str, RateLimiter] = {}
        self._fallback_handler: Optional[FallbackHandler] = None

        # Stats
        self._resilience_stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "retried_calls": 0,
            "circuit_opened": 0,
            "rate_limited": 0,
            "fallback_used": 0,
        }

    def _get_circuit(self, provider: str) -> CircuitBreaker:
        """Get or create circuit breaker for provider.

        Args:
            provider: Provider identifier

        Returns:
            CircuitBreaker for provider
        """
        self._init_resilience()

        if provider not in self._circuits:
            self._circuits[provider] = CircuitBreaker(
                name=provider, config=self.CIRCUIT_CONFIG
            )
        return self._circuits[provider]

    def _get_rate_limiter(self, provider: str) -> RateLimiter:
        """Get or create rate limiter for provider.

        Args:
            provider: Provider identifier

        Returns:
            RateLimiter for provider
        """
        self._init_resilience()

        if provider not in self._rate_limiters:
            self._rate_limiters[provider] = RateLimiter(
                config=self.RATE_LIMIT_CONFIG, name=provider
            )
        return self._rate_limiters[provider]

    async def _on_retry_callback(self, context: ErrorContext) -> None:
        """Callback invoked on retry attempts.

        Args:
            context: Error context from retry
        """
        self._init_resilience()
        self._resilience_stats["retried_calls"] += 1

        agent_id = getattr(self, "agent_id", "unknown")
        logger.debug(
            f"Agent {agent_id} retry: attempt={context.attempt}, "
            f"error={context.error}, category={context.category.value}"
        )

    async def resilient_call(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        provider: str = "default",
        estimated_tokens: int = 0,
        skip_circuit: bool = False,
        skip_rate_limit: bool = False,
        skip_retry: bool = False,
        **kwargs: Any,
    ) -> T:
        """Execute function with full resilience stack.

        Applies in order:
        1. Rate limiting (acquire tokens)
        2. Circuit breaker check
        3. Retry with exponential backoff

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            provider: Provider name for circuit/rate limit tracking
            estimated_tokens: Estimated tokens for rate limiting
            skip_circuit: Skip circuit breaker
            skip_rate_limit: Skip rate limiting
            skip_retry: Skip retry logic
            **kwargs: Keyword arguments for func

        Returns:
            Result from function

        Raises:
            ResilienceError: If all resilience mechanisms exhausted
        """
        self._init_resilience()
        self._resilience_stats["total_calls"] += 1

        # 1. Rate limiting
        if not skip_rate_limit:
            limiter = self._get_rate_limiter(provider)
            try:
                await limiter.acquire(estimated_tokens=estimated_tokens)
            except Exception:
                self._resilience_stats["rate_limited"] += 1
                raise

        # 2. Circuit breaker
        circuit = self._get_circuit(provider) if not skip_circuit else None

        # 3. Build execution chain
        async def execute_with_circuit() -> T:
            if circuit:
                return await circuit.execute(func, *args, **kwargs)
            return await func(*args, **kwargs)

        # 4. Execute with retry
        try:
            if skip_retry:
                result = await execute_with_circuit()
            else:
                result = await self._retry_handler.execute(execute_with_circuit)

            self._resilience_stats["successful_calls"] += 1

            # Record success for rate limiter
            if not skip_rate_limit:
                self._get_rate_limiter(provider).record_success()

            return result

        except Exception:
            self._resilience_stats["failed_calls"] += 1

            # Check if circuit opened
            if circuit and circuit.is_open:
                self._resilience_stats["circuit_opened"] += 1

            raise

    def with_resilience(
        self,
        provider: str = "default",
        estimated_tokens: int = 0,
        **resilience_kwargs: Any,
    ) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
        """Decorator to wrap function with resilience.

        Args:
            provider: Provider name
            estimated_tokens: Estimated tokens per call
            **resilience_kwargs: Additional kwargs for resilient_call

        Example:
            @self.with_resilience(provider="openai", estimated_tokens=500)
            async def generate(self, prompt: str) -> str:
                return await self._llm.chat(prompt)
        """

        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                return await self.resilient_call(
                    func,
                    *args,
                    provider=provider,
                    estimated_tokens=estimated_tokens,
                    **resilience_kwargs,
                    **kwargs,
                )

            return wrapper

        return decorator

    def setup_fallback(
        self,
        providers: List[str],
        provider_funcs: Dict[str, Callable[..., Awaitable[Any]]],
        parallel: bool = False,
    ) -> None:
        """Setup fallback handler with multiple providers.

        Args:
            providers: Ordered list of provider names
            provider_funcs: Mapping of name to function
            parallel: Use parallel fallback mode
        """
        self._init_resilience()

        config = FallbackConfig(providers=providers, parallel_fallback=parallel)

        self._fallback_handler = FallbackHandler(
            providers=providers,
            provider_funcs=provider_funcs,
            config=config,
        )

    async def call_with_fallback(self, *args: Any, **kwargs: Any) -> Any:
        """Execute with fallback across providers.

        Args:
            *args: Arguments for provider functions
            **kwargs: Keyword arguments for provider functions

        Returns:
            Result from first successful provider

        Raises:
            ResilienceError: If all providers fail
        """
        self._init_resilience()

        if not self._fallback_handler:
            raise ResilienceError("Fallback handler not configured. Call setup_fallback first.")

        result = await self._fallback_handler.execute(*args, **kwargs)

        if result.total_attempts > 1:
            self._resilience_stats["fallback_used"] += 1

        return result.value

    def get_resilience_stats(self) -> Dict[str, Any]:
        """Get resilience statistics.

        Returns:
            Dictionary with all resilience stats
        """
        self._init_resilience()

        stats = {**self._resilience_stats}

        # Add retry stats
        stats["retry"] = self._retry_handler.get_stats()

        # Add circuit stats
        stats["circuits"] = {
            name: circuit.get_stats() for name, circuit in self._circuits.items()
        }

        # Add rate limiter stats
        stats["rate_limiters"] = {
            name: limiter.get_stats() for name, limiter in self._rate_limiters.items()
        }

        # Add fallback stats if configured
        if self._fallback_handler:
            stats["fallback"] = self._fallback_handler.get_stats()

        return stats

    def get_prometheus_resilience_metrics(self) -> str:
        """Get Prometheus-formatted resilience metrics.

        Returns:
            Prometheus metrics string
        """
        self._init_resilience()

        agent_id = getattr(self, "agent_id", "unknown")
        lines = []

        # Basic counters
        total = self._resilience_stats["total_calls"]
        success = self._resilience_stats["successful_calls"]
        failed = self._resilience_stats["failed_calls"]
        retries = self._resilience_stats["retried_calls"]

        lines.append(f'resilience_calls_total{{agent="{agent_id}"}} {total}')
        lines.append(f'resilience_successes_total{{agent="{agent_id}"}} {success}')
        lines.append(f'resilience_failures_total{{agent="{agent_id}"}} {failed}')
        lines.append(f'resilience_retries_total{{agent="{agent_id}"}} {retries}')

        # Circuit breaker states
        state_map = {"closed": 0, "open": 1, "half_open": 2}
        for name, circuit in self._circuits.items():
            state_value = state_map.get(circuit.state.value, -1)
            lines.append(f'circuit_state{{agent="{agent_id}",provider="{name}"}} {state_value}')

        return "\n".join(lines)

    async def reset_resilience(self, provider: Optional[str] = None) -> None:
        """Reset resilience state.

        Args:
            provider: Specific provider to reset, or None for all
        """
        self._init_resilience()

        if provider:
            if provider in self._circuits:
                await self._circuits[provider].reset()
            if provider in self._rate_limiters:
                await self._rate_limiters[provider].reset()
        else:
            for circuit in self._circuits.values():
                await circuit.reset()
            for limiter in self._rate_limiters.values():
                await limiter.reset()

            self._resilience_stats = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "retried_calls": 0,
                "circuit_opened": 0,
                "rate_limited": 0,
                "fallback_used": 0,
            }

        logger.info(f"Resilience reset for provider={provider or 'all'}")
