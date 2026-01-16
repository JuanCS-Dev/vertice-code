"""
Fallback Handler - Multi-provider fallback orchestration.

Implements best practices:
- Ordered provider chain with priority
- Parallel fallback option (first success wins)
- Provider health tracking
- Automatic recovery detection

References:
- https://www.gocodeo.com/post/error-recovery-and-fallback-strategies
- https://www.ravchat.com/resilient-llm-build-fault-integration
- resilient-llm library patterns
"""

from __future__ import annotations

import asyncio
import logging
from typing import TypeVar, Callable, Awaitable, Optional, List, Dict, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
from functools import wraps

from .types import FallbackConfig, ErrorCategory, ResilienceError
from .circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class ProviderStatus:
    """Health status for a provider."""

    name: str
    is_healthy: bool = True
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    total_requests: int = 0
    total_failures: int = 0
    circuit: Optional[CircuitBreaker] = None


@dataclass
class FallbackResult:
    """Result from fallback execution."""

    value: Any
    provider_used: str
    providers_tried: List[str]
    total_attempts: int
    elapsed_time: float


class FallbackHandler:
    """Orchestrates fallback across multiple providers.

    Features:
    - Ordered provider chain with configurable priority
    - Per-provider circuit breakers
    - Health tracking and automatic recovery
    - Parallel fallback mode (first success wins)

    Example:
        fallback = FallbackHandler(
            providers=["groq", "openai", "anthropic"],
            provider_funcs={
                "groq": groq_client.chat,
                "openai": openai_client.chat,
                "anthropic": anthropic_client.chat,
            }
        )

        result = await fallback.execute(prompt="Hello")
    """

    def __init__(
        self,
        providers: List[str],
        provider_funcs: Optional[Dict[str, Callable[..., Awaitable[Any]]]] = None,
        config: Optional[FallbackConfig] = None,
        enable_circuits: bool = True,
    ) -> None:
        """Initialize fallback handler.

        Args:
            providers: Ordered list of provider names
            provider_funcs: Mapping of provider name to async function
            config: Fallback configuration
            enable_circuits: Enable per-provider circuit breakers
        """
        self.providers = providers
        self.provider_funcs = provider_funcs or {}
        self.config = config or FallbackConfig(providers=providers)
        self.enable_circuits = enable_circuits

        # Provider status tracking
        self._provider_status: Dict[str, ProviderStatus] = {}
        for provider in providers:
            status = ProviderStatus(name=provider)
            if enable_circuits:
                status.circuit = CircuitBreaker(name=f"fallback_{provider}")
            self._provider_status[provider] = status

        # Stats
        self._stats = {
            "total_executions": 0,
            "fallback_used": 0,
            "all_failed": 0,
        }

    def register_provider(
        self,
        name: str,
        func: Callable[..., Awaitable[Any]],
        priority: Optional[int] = None,
    ) -> None:
        """Register a provider function.

        Args:
            name: Provider name
            func: Async function to call
            priority: Position in provider list (None = append)
        """
        self.provider_funcs[name] = func

        if name not in self._provider_status:
            status = ProviderStatus(name=name)
            if self.enable_circuits:
                status.circuit = CircuitBreaker(name=f"fallback_{name}")
            self._provider_status[name] = status

        if name not in self.providers:
            if priority is not None:
                self.providers.insert(priority, name)
            else:
                self.providers.append(name)

    def get_healthy_providers(self) -> List[str]:
        """Get list of currently healthy providers.

        Returns:
            List of healthy provider names in priority order
        """
        healthy = []
        for provider in self.providers:
            status = self._provider_status.get(provider)
            if status and status.is_healthy:
                # Check circuit breaker
                if status.circuit and status.circuit.is_open:
                    continue
                healthy.append(provider)
        return healthy

    async def _call_provider(
        self,
        provider: str,
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[bool, Any, Optional[Exception]]:
        """Call a single provider.

        Args:
            provider: Provider name
            *args: Arguments for provider function
            **kwargs: Keyword arguments for provider function

        Returns:
            Tuple of (success, result, error)
        """
        status = self._provider_status.get(provider)
        func = self.provider_funcs.get(provider)

        if not func:
            return False, None, ValueError(f"Provider '{provider}' not registered")

        if not status:
            return False, None, ValueError(f"Provider '{provider}' status not found")

        status.total_requests += 1

        try:
            # Use circuit breaker if enabled
            if status.circuit:
                result = await asyncio.wait_for(
                    status.circuit.execute(func, *args, **kwargs),
                    timeout=self.config.timeout_per_provider,
                )
            else:
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout_per_provider,
                )

            # Record success
            status.is_healthy = True
            status.last_success = datetime.utcnow()
            status.consecutive_failures = 0

            return True, result, None

        except Exception as e:
            # Record failure
            status.total_failures += 1
            status.consecutive_failures += 1
            status.last_failure = datetime.utcnow()

            # Mark unhealthy after threshold
            if status.consecutive_failures >= 3:
                status.is_healthy = False

            logger.warning(f"Provider '{provider}' failed: {e}")
            return False, None, e

    async def execute(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> FallbackResult:
        """Execute with fallback through providers.

        Args:
            *args: Arguments for provider functions
            **kwargs: Keyword arguments for provider functions

        Returns:
            FallbackResult with value and metadata

        Raises:
            ResilienceError: If all providers fail
        """
        import time

        start = time.monotonic()
        self._stats["total_executions"] += 1

        providers_tried: List[str] = []
        last_error: Optional[Exception] = None

        if self.config.parallel_fallback:
            result = await self._execute_parallel(*args, **kwargs)
            if result is not None:
                return result
        else:
            # Sequential fallback
            for provider in self.providers:
                providers_tried.append(provider)

                success, result, error = await self._call_provider(provider, *args, **kwargs)

                if success:
                    if len(providers_tried) > 1:
                        self._stats["fallback_used"] += 1

                    return FallbackResult(
                        value=result,
                        provider_used=provider,
                        providers_tried=providers_tried,
                        total_attempts=len(providers_tried),
                        elapsed_time=time.monotonic() - start,
                    )

                last_error = error

        # All providers failed
        self._stats["all_failed"] += 1

        raise ResilienceError(
            f"All providers failed. Tried: {providers_tried}. " f"Last error: {last_error}",
            category=ErrorCategory.PERMANENT,
        )

    async def _execute_parallel(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[FallbackResult]:
        """Execute providers in parallel, return first success.

        Args:
            *args: Arguments for provider functions
            **kwargs: Keyword arguments for provider functions

        Returns:
            FallbackResult or None if all failed
        """
        import time

        start = time.monotonic()
        healthy = self.get_healthy_providers()

        if not healthy:
            return None

        # Create tasks for all healthy providers
        tasks = {
            provider: asyncio.create_task(self._call_provider(provider, *args, **kwargs))
            for provider in healthy
        }

        done: set = set()
        pending = set(tasks.values())

        while pending:
            done_now, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            done.update(done_now)

            for task in done_now:
                # Find which provider this task belongs to
                provider = next((p for p, t in tasks.items() if t == task), None)
                if provider is None:
                    continue

                success, result, _ = task.result()
                if success:
                    # Cancel remaining tasks
                    for t in pending:
                        t.cancel()

                    return FallbackResult(
                        value=result,
                        provider_used=provider,
                        providers_tried=healthy,
                        total_attempts=len(done),
                        elapsed_time=time.monotonic() - start,
                    )

        return None

    def fallback(
        self,
        func: Optional[Callable[..., Awaitable[T]]] = None,
    ) -> Callable[..., Awaitable[T]]:
        """Decorator to wrap function with fallback logic.

        Note: This registers the decorated function as the primary provider.

        Example:
            @handler.fallback
            async def call_llm(prompt: str) -> str:
                return await primary_provider.chat(prompt)
        """

        def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            # Register as primary if not already registered
            primary = self.providers[0] if self.providers else "primary"
            if primary not in self.provider_funcs:
                self.provider_funcs[primary] = fn

            @wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> T:
                result = await self.execute(*args, **kwargs)
                return result.value

            return wrapper

        if func is not None:
            return decorator(func)
        return decorator

    def get_stats(self) -> Dict[str, Any]:
        """Get fallback handler statistics.

        Returns:
            Dictionary with stats
        """
        provider_stats = {
            name: {
                "is_healthy": status.is_healthy,
                "total_requests": status.total_requests,
                "total_failures": status.total_failures,
                "consecutive_failures": status.consecutive_failures,
                "last_success": status.last_success,
                "last_failure": status.last_failure,
            }
            for name, status in self._provider_status.items()
        }

        return {
            **self._stats,
            "providers": provider_stats,
            "healthy_providers": self.get_healthy_providers(),
            "fallback_rate": (
                self._stats["fallback_used"] / self._stats["total_executions"]
                if self._stats["total_executions"] > 0
                else 0.0
            ),
        }

    async def reset_provider(self, provider: str) -> None:
        """Reset a provider's health status.

        Args:
            provider: Provider name to reset
        """
        if provider in self._provider_status:
            status = self._provider_status[provider]
            status.is_healthy = True
            status.consecutive_failures = 0
            if status.circuit:
                await status.circuit.reset()
            logger.info(f"Provider '{provider}' reset")
