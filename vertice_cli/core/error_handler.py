"""
Error Escalation Handler - Tiered recovery with escalation.

Implements Claude Code-style error recovery with progressive escalation:
1. Retry - Same parameters
2. Adjust - Modified parameters
3. Fallback - Alternative provider/tool
4. Decompose - Break into smaller subtasks
5. Human - Request user intervention

Reference: HEROIC_IMPLEMENTATION_PLAN.md Sprint 3.1
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Generic

logger = logging.getLogger(__name__)


class EscalationLevel(str, Enum):
    """Escalation levels in order of severity."""
    RETRY = "retry"
    ADJUST = "adjust"
    FALLBACK = "fallback"
    DECOMPOSE = "decompose"
    HUMAN = "human"


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ExecutionContext:
    """Context for error recovery."""
    operation: str
    args: Dict[str, Any] = field(default_factory=dict)
    attempt: int = 0
    max_retries: int = 3
    provider: Optional[str] = None
    tool: Optional[str] = None
    original_error: Optional[Exception] = None
    history: List[str] = field(default_factory=list)


@dataclass
class Recovery:
    """Result of a recovery attempt."""
    success: bool
    result: Any = None
    strategy_used: EscalationLevel = EscalationLevel.RETRY
    attempts: int = 0
    message: str = ""


class UnrecoverableError(Exception):
    """Error that cannot be recovered from."""
    pass


class ErrorEscalationHandler:
    """
    Tiered error recovery with escalation hierarchy.

    Key principles:
    - Try least disruptive recovery first
    - Escalate only when current level fails
    - Track success/failure for calibration
    - Provide clear feedback at each level

    Usage:
        handler = ErrorEscalationHandler()

        async def my_operation(ctx):
            # do something risky
            pass

        result = await handler.execute_with_recovery(
            operation=my_operation,
            context=ExecutionContext(operation="my_operation", args={...})
        )
    """

    ESCALATION_LEVELS = [
        (EscalationLevel.RETRY, "Retry with same parameters"),
        (EscalationLevel.ADJUST, "Retry with adjusted parameters"),
        (EscalationLevel.FALLBACK, "Use fallback provider/tool"),
        (EscalationLevel.DECOMPOSE, "Break task into smaller subtasks"),
        (EscalationLevel.HUMAN, "Request human intervention"),
    ]

    def __init__(
        self,
        fallback_providers: Optional[List[str]] = None,
        human_callback: Optional[Callable[[str, Exception], str]] = None,
        decompose_callback: Optional[Callable[[str], List[str]]] = None,
    ):
        """
        Initialize error escalation handler.

        Args:
            fallback_providers: List of fallback provider names
            human_callback: Callback for human intervention (sync or async)
            decompose_callback: Callback to decompose task into subtasks
        """
        self.fallback_providers = fallback_providers or []
        self.human_callback = human_callback
        self.decompose_callback = decompose_callback
        self._recovery_history: List[Dict[str, Any]] = []

    async def handle_error(
        self,
        error: Exception,
        context: ExecutionContext,
        execute_fn: Callable[[ExecutionContext], Any],
    ) -> Recovery:
        """
        Handle error with escalation hierarchy.

        Args:
            error: The exception that occurred
            context: Execution context
            execute_fn: Function to retry execution

        Returns:
            Recovery result
        """
        context.original_error = error
        context.history.append(f"Error: {type(error).__name__}: {str(error)[:100]}")

        for level_idx, (level, description) in enumerate(self.ESCALATION_LEVELS):
            logger.info(f"[Escalation] Level {level_idx + 1}: {description}")
            context.history.append(f"Trying: {level.value}")

            try:
                if level == EscalationLevel.RETRY:
                    result = await self._retry(execute_fn, context)
                elif level == EscalationLevel.ADJUST:
                    result = await self._retry_adjusted(execute_fn, context, error)
                elif level == EscalationLevel.FALLBACK:
                    result = await self._use_fallback(execute_fn, context)
                elif level == EscalationLevel.DECOMPOSE:
                    result = await self._decompose_and_retry(execute_fn, context)
                elif level == EscalationLevel.HUMAN:
                    result = await self._request_human_help(context, error)
                else:
                    continue

                if result is not None:
                    recovery = Recovery(
                        success=True,
                        result=result,
                        strategy_used=level,
                        attempts=context.attempt,
                        message=f"Recovered at level {level.value}",
                    )
                    self._record_recovery(context, recovery)
                    return recovery

            except Exception as e:
                logger.warning(f"[Escalation] Level {level.value} failed: {e}")
                context.history.append(f"Failed: {level.value} - {str(e)[:50]}")
                continue

        # All levels exhausted
        raise UnrecoverableError(
            f"All recovery strategies failed for {context.operation}: {error}"
        )

    async def execute_with_recovery(
        self,
        operation: Callable[[ExecutionContext], Any],
        context: ExecutionContext,
    ) -> Recovery:
        """
        Execute operation with automatic error recovery.

        Args:
            operation: The operation to execute
            context: Execution context

        Returns:
            Recovery result with operation result or failure info
        """
        try:
            result = await self._safe_call(operation, context)
            return Recovery(
                success=True,
                result=result,
                strategy_used=EscalationLevel.RETRY,
                attempts=1,
                message="Succeeded on first attempt",
            )
        except Exception as e:
            return await self.handle_error(e, context, operation)

    async def _safe_call(
        self, func: Callable, context: ExecutionContext
    ) -> Any:
        """Safely call function (sync or async)."""
        context.attempt += 1
        result = func(context)
        if asyncio.iscoroutine(result):
            return await result
        return result

    async def _retry(
        self,
        execute_fn: Callable[[ExecutionContext], Any],
        context: ExecutionContext,
    ) -> Any:
        """Retry with same parameters."""
        if context.attempt >= context.max_retries:
            raise Exception(f"Max retries ({context.max_retries}) exceeded")

        # Exponential backoff
        wait_time = min(2 ** context.attempt, 30)
        logger.debug(f"[Retry] Waiting {wait_time}s before attempt {context.attempt + 1}")
        await asyncio.sleep(wait_time)

        return await self._safe_call(execute_fn, context)

    async def _retry_adjusted(
        self,
        execute_fn: Callable[[ExecutionContext], Any],
        context: ExecutionContext,
        error: Exception,
    ) -> Any:
        """Retry with adjusted parameters based on error type."""
        error_type = type(error).__name__
        error_msg = str(error).lower()

        # Adjust parameters based on error
        adjustments = self._get_adjustments(error_type, error_msg, context)

        if not adjustments:
            raise Exception("No adjustments applicable for this error")

        # Apply adjustments
        for key, value in adjustments.items():
            context.args[key] = value
            context.history.append(f"Adjusted: {key}={value}")

        logger.info(f"[Adjust] Applied adjustments: {adjustments}")
        return await self._safe_call(execute_fn, context)

    def _get_adjustments(
        self,
        error_type: str,
        error_msg: str,
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Get parameter adjustments based on error."""
        adjustments: Dict[str, Any] = {}

        # Token limit errors
        if "token" in error_msg or "context" in error_msg:
            current_tokens = context.args.get("max_tokens", 4096)
            adjustments["max_tokens"] = int(current_tokens * 0.7)
            adjustments["truncate_context"] = True

        # Timeout errors
        if "timeout" in error_msg or "timed out" in error_msg:
            current_timeout = context.args.get("timeout", 30)
            adjustments["timeout"] = min(current_timeout * 2, 300)

        # Rate limit errors
        if "rate" in error_msg and "limit" in error_msg:
            adjustments["delay_before_call"] = 5.0
            adjustments["reduce_batch_size"] = True

        # Model errors
        if "model" in error_msg and ("not found" in error_msg or "unavailable" in error_msg):
            adjustments["use_fallback_model"] = True

        return adjustments

    async def _use_fallback(
        self,
        execute_fn: Callable[[ExecutionContext], Any],
        context: ExecutionContext,
    ) -> Any:
        """Use fallback provider or tool."""
        if not self.fallback_providers:
            raise Exception("No fallback providers configured")

        # Find next unused fallback
        used_providers = [
            h for h in context.history
            if h.startswith("Provider:")
        ]

        for provider in self.fallback_providers:
            if f"Provider: {provider}" not in used_providers:
                context.provider = provider
                context.history.append(f"Provider: {provider}")
                logger.info(f"[Fallback] Trying provider: {provider}")
                return await self._safe_call(execute_fn, context)

        raise Exception("All fallback providers exhausted")

    async def _decompose_and_retry(
        self,
        execute_fn: Callable[[ExecutionContext], Any],
        context: ExecutionContext,
    ) -> Any:
        """Break task into smaller subtasks and retry each."""
        if not self.decompose_callback:
            raise Exception("No decompose callback configured")

        # Get subtasks from callback
        operation_desc = context.args.get("description", context.operation)
        subtasks = self.decompose_callback(operation_desc)

        if not subtasks or len(subtasks) <= 1:
            raise Exception("Task cannot be decomposed further")

        logger.info(f"[Decompose] Split into {len(subtasks)} subtasks")
        context.history.append(f"Decomposed into {len(subtasks)} subtasks")

        # Execute subtasks
        results = []
        for i, subtask in enumerate(subtasks):
            subtask_context = ExecutionContext(
                operation=f"{context.operation}_subtask_{i}",
                args={**context.args, "description": subtask},
                max_retries=context.max_retries,
                provider=context.provider,
            )

            try:
                result = await self._safe_call(execute_fn, subtask_context)
                results.append(result)
            except Exception as e:
                logger.warning(f"[Decompose] Subtask {i} failed: {e}")
                # Continue with other subtasks
                results.append(None)

        # Return combined results if majority succeeded
        success_count = sum(1 for r in results if r is not None)
        if success_count > len(results) // 2:
            return {"subtasks": results, "success_rate": success_count / len(results)}

        raise Exception(f"Only {success_count}/{len(results)} subtasks succeeded")

    async def _request_human_help(
        self,
        context: ExecutionContext,
        error: Exception,
    ) -> Any:
        """Request human intervention."""
        if not self.human_callback:
            raise Exception("No human callback configured")

        message = (
            f"Error in {context.operation}:\n"
            f"{type(error).__name__}: {error}\n\n"
            f"History:\n" + "\n".join(f"  - {h}" for h in context.history[-5:])
        )

        logger.info("[Human] Requesting human intervention")
        context.history.append("Requested human help")

        # Call human callback (may be async)
        result = self.human_callback(message, error)
        if asyncio.iscoroutine(result):
            result = await result

        return result

    def _record_recovery(self, context: ExecutionContext, recovery: Recovery) -> None:
        """Record recovery for statistics."""
        self._recovery_history.append({
            "operation": context.operation,
            "strategy": recovery.strategy_used.value,
            "attempts": recovery.attempts,
            "timestamp": datetime.now().isoformat(),
            "success": recovery.success,
        })

    def get_stats(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        if not self._recovery_history:
            return {"total": 0, "by_strategy": {}}

        by_strategy: Dict[str, int] = {}
        for record in self._recovery_history:
            strategy = record["strategy"]
            by_strategy[strategy] = by_strategy.get(strategy, 0) + 1

        return {
            "total": len(self._recovery_history),
            "success_rate": sum(1 for r in self._recovery_history if r["success"]) / len(self._recovery_history),
            "by_strategy": by_strategy,
            "avg_attempts": sum(r["attempts"] for r in self._recovery_history) / len(self._recovery_history),
        }


class EnhancedCircuitBreaker:
    """
    Circuit breaker with gradual recovery.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Failing, requests are blocked
    - HALF_OPEN: Testing recovery, limited requests allowed

    Usage:
        breaker = EnhancedCircuitBreaker(failure_threshold=5)

        async def risky_call():
            return await api.call()

        result = await breaker.call(risky_call)
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        success_threshold: int = 3,
        name: str = "default",
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            success_threshold: Successes in half-open to close circuit
            name: Identifier for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.name = name

        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time: Optional[float] = None
        self._success_count_in_half_open = 0
        self._total_calls = 0
        self._total_failures = 0

    @property
    def state(self) -> CircuitState:
        """Get current state."""
        return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (blocking requests)."""
        return self._state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    async def call(
        self,
        func: Callable[[], Any],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute function through circuit breaker.

        Args:
            func: Function to call (sync or async)
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitOpenError: If circuit is open
        """
        self._total_calls += 1

        # Check if we should attempt recovery
        if self._state == CircuitState.OPEN:
            if self._should_attempt_recovery():
                logger.info(f"[CircuitBreaker:{self.name}] Entering HALF_OPEN state")
                self._state = CircuitState.HALF_OPEN
                self._success_count_in_half_open = 0
            else:
                raise CircuitOpenError(
                    f"Circuit {self.name} is open. "
                    f"Wait {self._time_until_recovery():.0f}s"
                )

        try:
            # Execute function
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result

            self._on_success()
            return result

        except Exception as e:
            self._on_failure(e)
            raise

    def _should_attempt_recovery(self) -> bool:
        """Check if enough time has passed for recovery attempt."""
        if self._last_failure_time is None:
            return True

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.recovery_timeout

    def _time_until_recovery(self) -> float:
        """Get time remaining until recovery attempt."""
        if self._last_failure_time is None:
            return 0

        elapsed = time.time() - self._last_failure_time
        return max(0, self.recovery_timeout - elapsed)

    def _on_success(self) -> None:
        """Handle successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count_in_half_open += 1
            logger.debug(
                f"[CircuitBreaker:{self.name}] Success in HALF_OPEN "
                f"({self._success_count_in_half_open}/{self.success_threshold})"
            )

            if self._success_count_in_half_open >= self.success_threshold:
                logger.info(f"[CircuitBreaker:{self.name}] Closing circuit (recovered)")
                self._state = CircuitState.CLOSED
                self._failures = 0
        else:
            # Decay failures on success
            self._failures = max(0, self._failures - 1)

    def _on_failure(self, error: Exception) -> None:
        """Handle failed call."""
        self._failures += 1
        self._total_failures += 1
        self._last_failure_time = time.time()

        logger.warning(
            f"[CircuitBreaker:{self.name}] Failure #{self._failures}: "
            f"{type(error).__name__}"
        )

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens the circuit
            logger.info(f"[CircuitBreaker:{self.name}] Reopening circuit (failure in HALF_OPEN)")
            self._state = CircuitState.OPEN
            self._success_count_in_half_open = 0

        elif self._failures >= self.failure_threshold:
            logger.warning(f"[CircuitBreaker:{self.name}] Opening circuit (threshold reached)")
            self._state = CircuitState.OPEN

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._last_failure_time = None
        self._success_count_in_half_open = 0
        logger.info(f"[CircuitBreaker:{self.name}] Reset to CLOSED")

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failures": self._failures,
            "total_calls": self._total_calls,
            "total_failures": self._total_failures,
            "failure_rate": self._total_failures / self._total_calls if self._total_calls > 0 else 0,
            "time_until_recovery": self._time_until_recovery() if self._state == CircuitState.OPEN else 0,
        }


class CircuitOpenError(Exception):
    """Raised when attempting to call through an open circuit."""
    pass


# Singleton instances
_default_handler: Optional[ErrorEscalationHandler] = None
_circuit_breakers: Dict[str, EnhancedCircuitBreaker] = {}


def get_escalation_handler() -> ErrorEscalationHandler:
    """Get or create the default escalation handler."""
    global _default_handler
    if _default_handler is None:
        _default_handler = ErrorEscalationHandler()
    return _default_handler


def get_circuit_breaker(name: str = "default") -> EnhancedCircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = EnhancedCircuitBreaker(name=name)
    return _circuit_breakers[name]


def reset_all_circuits() -> None:
    """Reset all circuit breakers."""
    for breaker in _circuit_breakers.values():
        breaker.reset()
