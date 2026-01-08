"""
Error Tracking and Recovery System for Vertice TUI.

Tracks errors, aggregates patterns, and provides recovery suggestions
for improved system resilience and debugging.
"""

import time
import threading
import hashlib
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import logging


@dataclass
class ErrorEvent:
    """Represents a single error event."""

    timestamp: float
    component: str
    operation: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    correlation_id: Optional[str] = None

    @property
    def error_signature(self) -> str:
        """Generate a signature for error pattern matching."""
        signature_parts = [
            self.component,
            self.operation,
            self.error_type,
            self.error_message[:100],  # First 100 chars
        ]
        return hashlib.md5("|".join(signature_parts).encode()).hexdigest()


@dataclass
class ErrorPattern:
    """Represents an aggregated error pattern."""

    signature: str
    component: str
    operation: str
    error_type: str
    first_occurrence: float
    last_occurrence: float
    occurrences: int = 0
    messages: List[str] = field(default_factory=list)
    recovery_suggestions: List[str] = field(default_factory=list)
    impact_score: float = 0.0  # 0-1, higher = more severe

    @property
    def frequency_per_hour(self) -> float:
        """Calculate error frequency per hour."""
        duration_hours = (self.last_occurrence - self.first_occurrence) / 3600
        return self.occurrences / max(duration_hours, 1) if duration_hours > 0 else self.occurrences

    @property
    def severity_level(self) -> str:
        """Determine severity level based on frequency and impact."""
        if self.frequency_per_hour > 10 or self.impact_score > 0.8:
            return "critical"
        elif self.frequency_per_hour > 1 or self.impact_score > 0.5:
            return "high"
        elif self.frequency_per_hour > 0.1 or self.impact_score > 0.2:
            return "medium"
        else:
            return "low"


class RecoveryStrategy:
    """Recovery strategy for error patterns."""

    def __init__(
        self,
        name: str,
        condition: Callable[[ErrorPattern], bool],
        action: Callable[[ErrorPattern], Any],
        cooldown_seconds: int = 300,
    ):
        self.name = name
        self.condition = condition
        self.action = action
        self.cooldown_seconds = cooldown_seconds
        self.last_executed: Optional[float] = None

    def should_execute(self, pattern: ErrorPattern) -> bool:
        """Check if recovery strategy should be executed."""
        if not self.condition(pattern):
            return False

        if self.last_executed and (time.time() - self.last_executed) < self.cooldown_seconds:
            return False

        return True

    def execute(self, pattern: ErrorPattern) -> Any:
        """Execute the recovery strategy."""
        try:
            result = self.action(pattern)
            self.last_executed = time.time()
            return result
        except Exception as e:
            logging.error(f"Recovery strategy {self.name} failed: {e}")
            return None


class ErrorTracker:
    """Central error tracking and recovery system."""

    def __init__(self, max_patterns: int = 1000, pattern_ttl_hours: int = 24):
        self.max_patterns = max_patterns
        self.pattern_ttl_hours = pattern_ttl_hours
        self.errors: List[ErrorEvent] = []
        self.patterns: Dict[str, ErrorPattern] = {}
        self._lock = threading.RLock()

        # Recovery strategies
        self.recovery_strategies: List[RecoveryStrategy] = []
        self._setup_default_strategies()

    def _setup_default_strategies(self):
        """Setup default recovery strategies."""

        # Strategy 1: High-frequency LLM errors - suggest fallback
        def llm_high_freq_condition(pattern: ErrorPattern) -> bool:
            return (
                pattern.component == "llm"
                and pattern.severity_level in ["critical", "high"]
                and pattern.frequency_per_hour > 5
            )

        def llm_fallback_action(pattern: ErrorPattern) -> str:
            return f"Consider switching to alternative LLM provider. Pattern: {pattern.signature}"

        self.recovery_strategies.append(
            RecoveryStrategy(
                "llm_fallback_suggestion",
                llm_high_freq_condition,
                llm_fallback_action,
                cooldown_seconds=1800,  # 30 minutes
            )
        )

        # Strategy 2: Tool execution failures - suggest tool validation
        def tool_failure_condition(pattern: ErrorPattern) -> bool:
            return (
                pattern.component == "tool"
                and pattern.error_type in ["ToolExecutionError", "TimeoutError"]
                and pattern.occurrences > 3
            )

        def tool_validation_action(pattern: ErrorPattern) -> str:
            return f"Validate tool configuration and permissions. Pattern: {pattern.signature}"

        self.recovery_strategies.append(
            RecoveryStrategy(
                "tool_validation_suggestion",
                tool_failure_condition,
                tool_validation_action,
                cooldown_seconds=900,  # 15 minutes
            )
        )

        # Strategy 3: Memory issues - suggest cleanup
        def memory_condition(pattern: ErrorPattern) -> bool:
            return (
                "memory" in " ".join(pattern.messages).lower()
                or "MemoryError" in pattern.error_type
            ) and pattern.occurrences > 1

        def memory_cleanup_action(pattern: ErrorPattern) -> str:
            return "Consider clearing caches or restarting to free memory"

        self.recovery_strategies.append(
            RecoveryStrategy(
                "memory_cleanup_suggestion",
                memory_condition,
                memory_cleanup_action,
                cooldown_seconds=3600,  # 1 hour
            )
        )

    def track_error(
        self,
        component: str,
        operation: str,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> ErrorEvent:
        """Track a new error event."""
        with self._lock:
            event = ErrorEvent(
                timestamp=time.time(),
                component=component,
                operation=operation,
                error_type=error.__class__.__name__,
                error_message=str(error),
                stack_trace=self._get_stack_trace(error),
                context=context or {},
                correlation_id=correlation_id,
            )

            self.errors.append(event)
            self._update_pattern(event)

            # Check for recovery strategies
            pattern = self.patterns.get(event.error_signature)
            if pattern:
                self._check_recovery_strategies(pattern)

            # Cleanup old errors and patterns
            self._cleanup_old_data()

            return event

    def _update_pattern(self, event: ErrorEvent):
        """Update or create error pattern."""
        signature = event.error_signature

        if signature not in self.patterns:
            self.patterns[signature] = ErrorPattern(
                signature=signature,
                component=event.component,
                operation=event.operation,
                error_type=event.error_type,
                first_occurrence=event.timestamp,
                last_occurrence=event.timestamp,
                messages=[event.error_message],
                recovery_suggestions=self._generate_recovery_suggestions(event),
            )
        else:
            pattern = self.patterns[signature]
            pattern.last_occurrence = event.timestamp
            pattern.occurrences += 1

            # Keep only last 10 messages for pattern
            if event.error_message not in pattern.messages:
                pattern.messages.append(event.error_message)
                pattern.messages = pattern.messages[-10:]

            # Update impact score based on error characteristics
            pattern.impact_score = min(
                1.0, pattern.impact_score + self._calculate_error_impact(event)
            )

    def _generate_recovery_suggestions(self, event: ErrorEvent) -> List[str]:
        """Generate recovery suggestions based on error characteristics."""
        suggestions = []

        if "timeout" in event.error_message.lower():
            suggestions.append("Increase timeout values or check network connectivity")

        if "permission" in event.error_message.lower() or "access" in event.error_message.lower():
            suggestions.append("Check file permissions and access rights")

        if "memory" in event.error_message.lower():
            suggestions.append("Monitor memory usage and consider cleanup")

        if "connection" in event.error_message.lower():
            suggestions.append("Check network connectivity and API endpoints")

        if "authentication" in event.error_message.lower():
            suggestions.append("Verify API keys and authentication credentials")

        return suggestions or ["Check logs for more details"]

    def _calculate_error_impact(self, event: ErrorEvent) -> float:
        """Calculate impact score for error (0-1)."""
        impact = 0.1  # Base impact

        # Component criticality
        critical_components = {"llm", "auth", "bridge"}
        if event.component in critical_components:
            impact += 0.3

        # Error type severity
        severe_errors = {"AuthenticationError", "ConnectionError", "TimeoutError"}
        if event.error_type in severe_errors:
            impact += 0.2

        # Message indicators
        if any(word in event.error_message.lower() for word in ["critical", "fatal", "emergency"]):
            impact += 0.3

        return min(1.0, impact)

    def _check_recovery_strategies(self, pattern: ErrorPattern):
        """Check and execute applicable recovery strategies."""
        for strategy in self.recovery_strategies:
            if strategy.should_execute(pattern):
                try:
                    result = strategy.execute(pattern)
                    if result:
                        logging.info(f"Recovery strategy executed: {strategy.name} - {result}")
                except Exception as e:
                    logging.error(f"Recovery strategy failed: {strategy.name} - {e}")

    def _cleanup_old_data(self):
        """Clean up old error data and patterns."""
        cutoff_time = time.time() - (self.pattern_ttl_hours * 3600)

        # Remove old patterns
        old_patterns = [
            sig for sig, pattern in self.patterns.items() if pattern.last_occurrence < cutoff_time
        ]
        for sig in old_patterns:
            del self.patterns[sig]

        # Keep only last 10000 errors
        if len(self.errors) > 10000:
            self.errors = self.errors[-5000:]

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        with self._lock:
            total_errors = len(self.errors)
            if not total_errors:
                return {"total_errors": 0, "patterns": 0, "most_common": {}}

            # Most common error types
            error_types = Counter(event.error_type for event in self.errors)
            most_common = dict(error_types.most_common(5))

            # Pattern stats
            pattern_stats = {
                "total_patterns": len(self.patterns),
                "critical_patterns": sum(
                    1 for p in self.patterns.values() if p.severity_level == "critical"
                ),
                "high_patterns": sum(
                    1 for p in self.patterns.values() if p.severity_level == "high"
                ),
            }

            return {
                "total_errors": total_errors,
                "time_range_hours": (time.time() - min(e.timestamp for e in self.errors)) / 3600
                if self.errors
                else 0,
                "most_common_error_types": most_common,
                "pattern_stats": pattern_stats,
                "patterns": [
                    {
                        "signature": p.signature[:8],
                        "component": p.component,
                        "operation": p.operation,
                        "severity": p.severity_level,
                        "occurrences": p.occurrences,
                        "frequency_per_hour": round(p.frequency_per_hour, 2),
                    }
                    for p in sorted(
                        self.patterns.values(), key=lambda x: x.occurrences, reverse=True
                    )[:10]
                ],
            }

    def _get_stack_trace(self, error: Exception) -> Optional[str]:
        """Get stack trace from exception."""
        import traceback

        try:
            return "".join(traceback.format_exception(type(error), error, error.__traceback__))
        except:
            return None


# Global error tracker instance
_error_tracker = ErrorTracker()
_component_loggers = {}


def get_error_tracker() -> ErrorTracker:
    """Get global error tracker instance."""
    return _error_tracker


def get_component_logger(component: str) -> logging.Logger:
    """Get or create component-specific logger."""
    if component not in _component_loggers:
        logger = logging.getLogger(f"vertice.{component}")
        _component_loggers[component] = logger
    return _component_loggers[component]


def track_error(
    component: str,
    operation: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> ErrorEvent:
    """Convenience function to track an error."""
    return _error_tracker.track_error(component, operation, error, context, correlation_id)
