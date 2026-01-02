"""
Error Escalation Handler - Tiered recovery with escalation.

Implements Claude Code-style error recovery with progressive escalation:
1. Retry - Same parameters
2. Adjust - Modified parameters
3. Fallback - Alternative provider/tool
4. Decompose - Break into smaller subtasks
5. Human - Request user intervention

Reference: HEROIC_IMPLEMENTATION_PLAN.md Sprint 3.1
Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .types import (
    DecomposeCallback,
    EscalationLevel,
    ExecutionContext,
    HumanCallback,
    Recovery,
    UnrecoverableError,
)

logger = logging.getLogger(__name__)


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
        human_callback: Optional[HumanCallback] = None,
        decompose_callback: Optional[DecomposeCallback] = None,
    ) -> None:
        """
        Initialize error escalation handler.

        Args:
            fallback_providers: List of fallback provider names
            human_callback: Callback for human intervention
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
                result = await self._execute_level(level, execute_fn, context, error)
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

        raise UnrecoverableError(
            f"All recovery strategies failed for {context.operation}: {error}"
        )

    async def _execute_level(
        self,
        level: EscalationLevel,
        execute_fn: Callable[[ExecutionContext], Any],
        context: ExecutionContext,
        error: Exception,
    ) -> Any:
        """Execute a specific escalation level."""
        if level == EscalationLevel.RETRY:
            return await self._retry(execute_fn, context)
        elif level == EscalationLevel.ADJUST:
            return await self._retry_adjusted(execute_fn, context, error)
        elif level == EscalationLevel.FALLBACK:
            return await self._use_fallback(execute_fn, context)
        elif level == EscalationLevel.DECOMPOSE:
            return await self._decompose_and_retry(execute_fn, context)
        elif level == EscalationLevel.HUMAN:
            return await self._request_human_help(context, error)
        return None

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
        adjustments = self._get_adjustments(error, context)

        if not adjustments:
            raise Exception("No adjustments applicable for this error")

        for key, value in adjustments.items():
            context.args[key] = value
            context.history.append(f"Adjusted: {key}={value}")

        logger.info(f"[Adjust] Applied adjustments: {adjustments}")
        return await self._safe_call(execute_fn, context)

    def _get_adjustments(
        self,
        error: Exception,
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Get parameter adjustments based on error."""
        adjustments: Dict[str, Any] = {}
        error_msg = str(error).lower()

        if "token" in error_msg or "context" in error_msg:
            current_tokens = context.args.get("max_tokens", 4096)
            adjustments["max_tokens"] = int(current_tokens * 0.7)
            adjustments["truncate_context"] = True

        if "timeout" in error_msg or "timed out" in error_msg:
            current_timeout = context.args.get("timeout", 30)
            adjustments["timeout"] = min(current_timeout * 2, 300)

        if "rate" in error_msg and "limit" in error_msg:
            adjustments["delay_before_call"] = 5.0

        return adjustments

    async def _use_fallback(
        self,
        execute_fn: Callable[[ExecutionContext], Any],
        context: ExecutionContext,
    ) -> Any:
        """Use fallback provider or tool."""
        if not self.fallback_providers:
            raise Exception("No fallback providers configured")

        used = [h for h in context.history if h.startswith("Provider:")]

        for provider in self.fallback_providers:
            if f"Provider: {provider}" not in used:
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

        operation_desc = context.args.get("description", context.operation)
        subtasks = self.decompose_callback(operation_desc)

        if not subtasks or len(subtasks) <= 1:
            raise Exception("Task cannot be decomposed further")

        logger.info(f"[Decompose] Split into {len(subtasks)} subtasks")

        results = []
        for i, subtask in enumerate(subtasks):
            subtask_ctx = ExecutionContext(
                operation=f"{context.operation}_sub_{i}",
                args={**context.args, "description": subtask},
                max_retries=context.max_retries,
                provider=context.provider,
            )
            try:
                result = await self._safe_call(execute_fn, subtask_ctx)
                results.append(result)
            except Exception:
                results.append(None)

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

        total = len(self._recovery_history)
        success_count = sum(1 for r in self._recovery_history if r["success"])

        return {
            "total": total,
            "success_rate": success_count / total,
            "by_strategy": by_strategy,
            "avg_attempts": sum(r["attempts"] for r in self._recovery_history) / total,
        }


# Singleton instance
_default_handler: Optional[ErrorEscalationHandler] = None


def get_escalation_handler() -> ErrorEscalationHandler:
    """Get or create the default escalation handler."""
    global _default_handler
    if _default_handler is None:
        _default_handler = ErrorEscalationHandler()
    return _default_handler
