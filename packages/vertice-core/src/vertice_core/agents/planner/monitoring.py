"""
planner/monitoring.py: Observability Layer for Plan Execution.

Provides telemetry and monitoring capabilities for plan execution:
- ExecutionEvent: Structured event for each execution step
- ExecutionMonitor: Event collector with metrics aggregation

Designed to be OpenTelemetry-ready for production observability.

Following CODE_CONSTITUTION.md:
- <500 lines
- 100% type hints
- Zero TODOs
- Clear docstrings
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ExecutionEvent:
    """
    Event emitted during plan execution for observability.

    Represents a single point-in-time observation of the execution,
    capturing what happened, when, and with what outcome.

    Attributes:
        timestamp: ISO timestamp of the event
        event_type: Type of event (started, completed, failed, checkpoint)
        step_id: ID of the step this event relates to
        agent_role: Role of the agent executing (coder, reviewer, etc.)
        correlation_id: Trace ID for distributed tracing
        duration_ms: Execution duration in milliseconds (if completed)
        error: Error message (if failed)
        metadata: Additional context
    """

    timestamp: str
    event_type: str  # started, completed, failed, checkpoint
    step_id: str
    agent_role: str
    correlation_id: str
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "step_id": self.step_id,
            "agent_role": self.agent_role,
            "correlation_id": self.correlation_id,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "metadata": self.metadata,
        }


class ExecutionMonitor:
    """
    Observability layer for plan execution.

    Collects execution events and provides metrics aggregation.
    In production, events can be forwarded to:
    - OpenTelemetry collectors
    - DataDog, New Relic, etc.
    - Custom dashboards

    Usage:
        monitor = ExecutionMonitor()
        monitor.emit(ExecutionEvent(
            timestamp=datetime.now().isoformat(),
            event_type="started",
            step_id="step-001",
            agent_role="coder",
            correlation_id="trace-123"
        ))
        metrics = monitor.get_metrics()
    """

    def __init__(self) -> None:
        """Initialize the monitor with empty event list."""
        self.events: List[ExecutionEvent] = []

    def emit(self, event: ExecutionEvent) -> None:
        """
        Emit an execution event.

        Args:
            event: The event to record

        The event is stored locally and logged. In production,
        this would also send to external observability systems.
        """
        self.events.append(event)
        logger.debug(
            f"[{event.timestamp}] {event.event_type}: " f"{event.step_id} ({event.agent_role})"
        )

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get aggregated execution metrics.

        Returns:
            Dictionary with:
            - total_events: Total number of events recorded
            - completed_steps: Number of completed steps
            - failed_steps: Number of failed steps
            - success_rate: Ratio of completed to total
            - avg_duration_ms: Average duration of completed steps
        """
        completed = [e for e in self.events if e.event_type == "completed"]
        failed = [e for e in self.events if e.event_type == "failed"]
        started = [e for e in self.events if e.event_type == "started"]

        total = len(started) if started else len(self.events)

        return {
            "total_events": len(self.events),
            "completed_steps": len(completed),
            "failed_steps": len(failed),
            "success_rate": len(completed) / max(total, 1),
            "avg_duration_ms": (
                sum(e.duration_ms or 0 for e in completed) / max(len(completed), 1)
            ),
        }

    def clear(self) -> None:
        """Clear all recorded events."""
        self.events = []

    def get_events_by_step(self, step_id: str) -> List[ExecutionEvent]:
        """Get all events for a specific step."""
        return [e for e in self.events if e.step_id == step_id]

    def get_failed_events(self) -> List[ExecutionEvent]:
        """Get all failed events for error analysis."""
        return [e for e in self.events if e.event_type == "failed"]


__all__ = [
    "ExecutionEvent",
    "ExecutionMonitor",
]
