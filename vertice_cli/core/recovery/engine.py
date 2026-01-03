"""
Error Recovery Engine - LLM-Assisted Diagnosis.

Constitutional compliance:
- Layer 4 (Execution): Verify-Fix-Execute loop
- P6 (Eficiência): Max 2 iterations with mandatory diagnosis
"""

import asyncio
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .types import ErrorCategory, RecoveryContext, RecoveryResult, RecoveryStrategy
from .retry_policy import RetryPolicy
from .circuit_breaker import RecoveryCircuitBreaker

logger = logging.getLogger(__name__)


# Error categorization patterns
ERROR_PATTERNS = {
    ErrorCategory.COMMAND_NOT_FOUND: ["command not found", "command not recognized"],
    ErrorCategory.SYNTAX: ["syntax", "parse"],
    ErrorCategory.PERMISSION: ["permission", "denied", "forbidden"],
    ErrorCategory.NOT_FOUND: ["not found", "does not exist", "no such"],
    ErrorCategory.TIMEOUT: ["timeout", "timed out"],
    ErrorCategory.TYPE_ERROR: ["type", "error"],
    ErrorCategory.VALUE_ERROR: ["value", "error"],
    ErrorCategory.NETWORK: ["network", "connection"],
}


class ErrorRecoveryEngine:
    """Error recovery engine with LLM-assisted diagnosis."""

    DIAGNOSTIC_SYSTEM_PROMPT = """You are an expert debugging assistant. Analyze errors and suggest precise fixes.

When analyzing an error:
1. Identify the ROOT CAUSE (not just symptoms)
2. Suggest a SPECIFIC correction
3. Consider the user's INTENT
4. Provide corrected tool call if possible

Format your response as:
DIAGNOSIS: [root cause analysis]
CORRECTION: [specific fix or alternative approach]
TOOL_CALL: [corrected JSON if applicable]

Be concise and actionable."""

    def __init__(
        self,
        llm_client: Any,
        max_attempts: int = 2,
        enable_learning: bool = True,
        enable_retry_policy: bool = True,
        enable_circuit_breaker: bool = True,
    ):
        """Initialize recovery engine.

        Args:
            llm_client: LLM client for diagnosis
            max_attempts: Maximum recovery attempts (P6: should be 2)
            enable_learning: Enable learning from recovery attempts
            enable_retry_policy: Enable exponential backoff + jitter (DAY 7)
            enable_circuit_breaker: Enable circuit breaker pattern (DAY 7)
        """
        self.llm = llm_client
        self.max_attempts = max_attempts
        self.enable_learning = enable_learning

        self.retry_policy = RetryPolicy() if enable_retry_policy else None
        self.circuit_breaker = RecoveryCircuitBreaker() if enable_circuit_breaker else None

        self.recovery_history: List[Dict[str, Any]] = []
        self.common_errors: Dict[str, int] = {}
        self.successful_fixes: Dict[str, List[str]] = {}

        logger.info(
            f"Initialized ErrorRecoveryEngine "
            f"(max_attempts={max_attempts}, learning={enable_learning}, "
            f"retry_policy={enable_retry_policy}, circuit_breaker={enable_circuit_breaker})"
        )

    def categorize_error(self, error: str) -> ErrorCategory:
        """Categorize error for recovery strategy."""
        error_lower = error.lower()

        for category, patterns in ERROR_PATTERNS.items():
            if category == ErrorCategory.TYPE_ERROR:
                if "type" in error_lower and "error" in error_lower:
                    return category
            elif category == ErrorCategory.VALUE_ERROR:
                if "value" in error_lower and "error" in error_lower:
                    return category
            elif any(p in error_lower for p in patterns):
                return category

        return ErrorCategory.UNKNOWN

    def determine_strategy(
        self, category: ErrorCategory, context: RecoveryContext
    ) -> RecoveryStrategy:
        """Determine recovery strategy based on error category."""
        if self.enable_learning and context.error in self.successful_fixes:
            return RecoveryStrategy.RETRY_MODIFIED

        strategy_map = {
            ErrorCategory.SYNTAX: RecoveryStrategy.RETRY_MODIFIED,
            ErrorCategory.PERMISSION: RecoveryStrategy.SUGGEST_PERMISSION,
            ErrorCategory.NOT_FOUND: RecoveryStrategy.RETRY_ALTERNATIVE,
            ErrorCategory.COMMAND_NOT_FOUND: RecoveryStrategy.SUGGEST_INSTALL,
            ErrorCategory.TIMEOUT: RecoveryStrategy.RETRY_MODIFIED,
            ErrorCategory.TYPE_ERROR: RecoveryStrategy.RETRY_MODIFIED,
            ErrorCategory.VALUE_ERROR: RecoveryStrategy.RETRY_MODIFIED,
            ErrorCategory.NETWORK: RecoveryStrategy.RETRY_ALTERNATIVE,
        }

        if category in strategy_map:
            return strategy_map[category]

        if context.attempt_number < context.max_attempts:
            return RecoveryStrategy.RETRY_MODIFIED
        return RecoveryStrategy.ESCALATE

    async def diagnose_error(
        self, context: RecoveryContext
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Use LLM to diagnose error and suggest fix (Constitutional P6: mandatory diagnosis)."""
        prompt = self._build_diagnostic_prompt(context)

        try:
            response = await self.llm.generate_async(
                messages=[
                    {"role": "system", "content": self.DIAGNOSTIC_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=500,
            )

            diagnosis_text = response.get("content", "")
            correction = self._parse_correction(diagnosis_text, context)

            return diagnosis_text, correction

        except Exception as e:
            logger.error(f"LLM diagnosis failed: {e}")
            return f"LLM diagnosis failed: {e}", None

    def _build_diagnostic_prompt(self, context: RecoveryContext) -> str:
        """Build diagnostic prompt for LLM."""
        previous = self._format_previous_commands(context.previous_commands)
        return f"""ERROR ANALYSIS REQUEST:

User Intent: {context.user_intent}

Failed Tool: {context.failed_tool}
Arguments: {context.failed_args}

Error: {context.error}
Category: {context.error_category.value}

Attempt: {context.attempt_number}/{context.max_attempts}

Recent Commands:
{previous}

Please diagnose the error and suggest a correction."""

    def _format_previous_commands(self, commands: List[Dict[str, Any]]) -> str:
        """Format previous commands for context."""
        if not commands:
            return "None"

        lines = []
        for i, cmd in enumerate(commands[-3:]):
            lines.append(f"{i+1}. {cmd.get('tool', 'unknown')}({cmd.get('args', {})})")

        return "\n".join(lines)

    def _parse_correction(
        self, diagnosis_text: str, context: RecoveryContext
    ) -> Optional[Dict[str, Any]]:
        """Parse LLM diagnosis for corrected tool call."""
        if "TOOL_CALL:" in diagnosis_text:
            try:
                start_pos = diagnosis_text.index("TOOL_CALL:") + len("TOOL_CALL:")
                json_start = diagnosis_text.index("{", start_pos)

                brace_count = 0
                json_end = json_start
                for i in range(json_start, len(diagnosis_text)):
                    if diagnosis_text[i] == "{":
                        brace_count += 1
                    elif diagnosis_text[i] == "}":
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = i + 1
                            break

                json_str = diagnosis_text[json_start:json_end]
                correction: Dict[str, Any] = json.loads(json_str)
                return correction
            except (ValueError, json.JSONDecodeError, IndexError) as e:
                logger.debug(f"Failed to extract JSON correction: {e}")

        try:
            json_match = re.search(r"\{[^}]+\}", diagnosis_text)
            if json_match:
                correction_data: Dict[str, Any] = json.loads(json_match.group())
                if "tool" in correction_data and "args" in correction_data:
                    return correction_data
        except (json.JSONDecodeError, AttributeError) as e:
            logger.debug(f"Failed to parse correction JSON: {e}")

        return None

    async def attempt_recovery(self, context: RecoveryContext) -> RecoveryResult:
        """Attempt error recovery (Constitutional Layer 4: Verify-Fix-Execute loop)."""
        logger.info(
            f"Starting recovery attempt {context.attempt_number}/{context.max_attempts} "
            f"for {context.failed_tool} (category: {context.error_category.value})"
        )

        if self.enable_learning:
            self.common_errors[context.error] = (
                self.common_errors.get(context.error, 0) + 1
            )

        strategy = self.determine_strategy(context.error_category, context)
        context.recovery_strategy = strategy

        logger.info(f"Recovery strategy: {strategy.value}")

        if strategy == RecoveryStrategy.ESCALATE:
            return RecoveryResult(
                success=False,
                recovered=False,
                attempts_used=context.attempt_number,
                final_error=context.error,
                escalation_reason="Cannot auto-recover, need human intervention",
            )

        if strategy == RecoveryStrategy.ABORT:
            return RecoveryResult(
                success=False,
                recovered=False,
                attempts_used=context.attempt_number,
                final_error=context.error,
                escalation_reason="Fatal error, cannot recover",
            )

        diagnosis, correction = await self.diagnose_error(context)
        context.diagnosis = diagnosis

        if not correction:
            return RecoveryResult(
                success=False,
                recovered=False,
                attempts_used=context.attempt_number,
                final_error=context.error,
                escalation_reason="LLM could not suggest correction",
            )

        context.suggested_fix = str(correction)

        return RecoveryResult(
            success=True,
            recovered=False,
            attempts_used=context.attempt_number,
            corrected_tool=correction.get("tool"),
            corrected_args=correction.get("args"),
            what_worked="LLM provided correction",
        )

    async def attempt_recovery_with_backoff(
        self, context: RecoveryContext, error: Exception
    ) -> RecoveryResult:
        """Attempt recovery with retry policy and circuit breaker (DAY 7 enhancement)."""
        if self.circuit_breaker:
            allowed, reason = self.circuit_breaker.should_allow_recovery()
            if not allowed:
                logger.warning(f"Circuit breaker prevented recovery: {reason}")
                return RecoveryResult(
                    success=False,
                    recovered=False,
                    attempts_used=context.attempt_number,
                    final_error=context.error,
                    escalation_reason=f"Circuit breaker OPEN: {reason}",
                )

        if self.retry_policy:
            should_retry = self.retry_policy.should_retry(
                context.attempt_number, context.max_attempts, error
            )

            if not should_retry:
                logger.info(f"Retry policy decided not to retry: {error}")
                return RecoveryResult(
                    success=False,
                    recovered=False,
                    attempts_used=context.attempt_number,
                    final_error=context.error,
                    escalation_reason="Retry policy rejected (permanent error detected)",
                )

            if context.attempt_number > 1:
                delay = self.retry_policy.get_delay(context.attempt_number)
                logger.info(f"Applying exponential backoff: {delay:.2f}s")
                await asyncio.sleep(delay)

        try:
            result = await self.attempt_recovery(context)

            if self.circuit_breaker:
                if result.success or result.corrected_args:
                    self.circuit_breaker.record_success()
                else:
                    self.circuit_breaker.record_failure()

            return result

        except Exception as e:
            logger.error(f"Recovery attempt failed with exception: {e}")

            if self.circuit_breaker:
                self.circuit_breaker.record_failure()

            return RecoveryResult(
                success=False,
                recovered=False,
                attempts_used=context.attempt_number,
                final_error=str(e),
                escalation_reason=f"Recovery raised exception: {e}",
            )

    def record_recovery_outcome(
        self, context: RecoveryContext, result: RecoveryResult, final_success: bool
    ) -> None:
        """Record recovery outcome for learning."""
        if not self.enable_learning:
            return

        record = {
            "timestamp": time.time(),
            "error": context.error,
            "category": context.error_category.value,
            "strategy": (
                context.recovery_strategy.value if context.recovery_strategy else None
            ),
            "diagnosis": context.diagnosis,
            "suggested_fix": context.suggested_fix,
            "attempts": result.attempts_used,
            "final_success": final_success,
        }

        self.recovery_history.append(record)

        if final_success and context.suggested_fix:
            if context.error not in self.successful_fixes:
                self.successful_fixes[context.error] = []

            self.successful_fixes[context.error].append(context.suggested_fix)
            logger.info(f"Recorded successful fix for: {context.error[:50]}...")

    def get_statistics(self) -> Dict[str, Any]:
        """Get recovery statistics."""
        stats: Dict[str, Any] = {}

        if not self.enable_learning:
            stats["learning_disabled"] = True
        else:
            total_attempts = len(self.recovery_history)
            successful_recoveries = sum(
                1 for r in self.recovery_history if r["final_success"]
            )

            stats.update(
                {
                    "total_recovery_attempts": total_attempts,
                    "successful_recoveries": successful_recoveries,
                    "success_rate": (
                        successful_recoveries / total_attempts
                        if total_attempts > 0
                        else 0.0
                    ),
                    "common_errors": dict(
                        sorted(
                            self.common_errors.items(), key=lambda x: x[1], reverse=True
                        )[:10]
                    ),
                    "learned_fixes": len(self.successful_fixes),
                }
            )

        if self.circuit_breaker:
            stats["circuit_breaker"] = self.circuit_breaker.get_status()

        return stats

    def get_circuit_breaker_status(self) -> Optional[Dict[str, Any]]:
        """Get circuit breaker status (DAY 7 enhancement)."""
        if self.circuit_breaker:
            return self.circuit_breaker.get_status()
        return None

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker to CLOSED state (DAY 7 enhancement)."""
        if self.circuit_breaker:
            self.circuit_breaker.reset()
            logger.info("Circuit breaker manually reset")
