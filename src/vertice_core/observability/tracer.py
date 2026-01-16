"""
Agent Tracer

OpenTelemetry-compatible tracer for AI agent operations.

References:
- OpenTelemetry GenAI Semantic Conventions (2025)
- OTEL Agent Spans specification
- arXiv:2401.02009 (LLM Observability patterns)
"""

from __future__ import annotations

import logging
import random
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from .types import (
    AgentSpan,
    LLMSpan,
    ToolSpan,
    TraceContext,
    SpanKind,
    ObservabilityConfig,
)

logger = logging.getLogger(__name__)


class AgentTracer:
    """
    Tracer for AI agent operations following OpenTelemetry GenAI conventions.

    Implements hierarchical span tracking:
    - Agent spans (top-level operations)
    - LLM spans (model calls)
    - Tool spans (tool executions)
    - Retrieval spans (RAG operations)

    References:
    - https://opentelemetry.io/docs/specs/semconv/gen-ai/
    """

    def __init__(self, config: Optional[ObservabilityConfig] = None):
        """
        Initialize tracer.

        Args:
            config: Observability configuration
        """
        self._config = config or ObservabilityConfig()
        self._active_spans: Dict[str, AgentSpan] = {}
        self._completed_spans: List[AgentSpan] = []
        self._llm_spans: List[LLMSpan] = []
        self._tool_spans: List[ToolSpan] = []
        self._current_context: Optional[TraceContext] = None
        self._sampling_stats = {"sampled": 0, "dropped": 0}

    def _should_sample(self, is_error: bool = False) -> bool:
        """
        Decide whether to sample this trace (P1-5).

        Implements head-based + tail-based sampling:
        - Head-based: Sample X% of all traces (configurable)
        - Tail-based: Always sample errors (100%)

        Args:
            is_error: Whether this is an error trace

        Returns:
            True if trace should be sampled

        Reference:
            https://www.groundcover.com/opentelemetry/opentelemetry-metrics
        """
        if not self._config.sampling_enabled:
            return True  # Sampling disabled - sample everything

        # Tail-based: Always sample errors
        if is_error and self._config.tail_sample_errors:
            self._sampling_stats["sampled"] += 1
            return True

        # Head-based: Sample based on rate
        if random.random() < self._config.head_sample_rate:
            self._sampling_stats["sampled"] += 1
            return True

        self._sampling_stats["dropped"] += 1
        return False

    @contextmanager
    def start_agent_span(
        self,
        operation_name: str,
        agent_id: str,
        agent_name: Optional[str] = None,
        description: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Generator[AgentSpan, None, None]:
        """
        Start an agent span following GenAI semantic conventions.

        Args:
            operation_name: gen_ai.operation.name (e.g., "chat", "task")
            agent_id: gen_ai.agent.id
            agent_name: gen_ai.agent.name
            description: gen_ai.agent.description
            attributes: Additional span attributes

        Yields:
            AgentSpan for the operation
        """
        # Create or get trace context
        if self._current_context is None:
            self._current_context = TraceContext()

        span = AgentSpan(
            trace_id=self._current_context.trace_id,
            parent_span_id=self._current_context.span_id,
            gen_ai_system=self._config.service_name,
            gen_ai_operation_name=operation_name,
            gen_ai_agent_id=agent_id,
            gen_ai_agent_name=agent_name or agent_id,
            gen_ai_agent_description=description or "",
        )

        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)

        # Track active span
        self._active_spans[span.span_id] = span
        old_context = self._current_context
        self._current_context = self._current_context.child()

        span.add_event("span_started", {"operation": operation_name})

        try:
            yield span
            span.end(status_code="OK")
        except Exception as e:
            span.end(status_code="ERROR", message=str(e))
            span.add_event(
                "exception",
                {
                    "exception.type": type(e).__name__,
                    "exception.message": str(e),
                },
            )
            raise
        finally:
            # Cleanup
            del self._active_spans[span.span_id]

            # Sampling decision (P1-5)
            is_error = span.status_code == "ERROR"
            if self._should_sample(is_error=is_error):
                self._completed_spans.append(span)
            # If not sampled, span is dropped (not stored)

            self._current_context = old_context

            logger.debug(
                f"[Tracer] Agent span completed: {operation_name} "
                f"({span.duration_ms:.1f}ms, status={span.status_code})"
            )

    @contextmanager
    def start_llm_span(
        self,
        model: str,
        operation: str = "chat",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> Generator[LLMSpan, None, None]:
        """
        Start an LLM span for model calls.

        Args:
            model: gen_ai.request.model
            operation: gen_ai.operation.name
            max_tokens: gen_ai.request.max_tokens
            temperature: gen_ai.request.temperature

        Yields:
            LLMSpan for the model call
        """
        span = LLMSpan(
            parent_span_id=self._current_context.span_id if self._current_context else None,
            gen_ai_operation_name=operation,
            gen_ai_request_model=model,
            gen_ai_request_max_tokens=max_tokens,
            gen_ai_request_temperature=temperature,
        )

        try:
            yield span
            span.end(status_code="OK")
        except Exception as e:
            span.end(status_code="ERROR")
            span.error_type = type(e).__name__
            raise
        finally:
            self._llm_spans.append(span)

            logger.debug(
                f"[Tracer] LLM span completed: {model} "
                f"({span.duration_ms:.1f}ms, tokens={span.gen_ai_usage_total_tokens})"
            )

    @contextmanager
    def start_tool_span(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Generator[ToolSpan, None, None]:
        """
        Start a tool execution span.

        Args:
            tool_name: Name of the tool being executed
            parameters: Tool parameters (may be redacted for privacy)

        Yields:
            ToolSpan for the tool execution
        """
        span = ToolSpan(
            parent_span_id=self._current_context.span_id if self._current_context else None,
            tool_name=tool_name,
            tool_parameters=parameters or {} if self._config.trace_tool_results else {},
        )

        try:
            yield span
            span.end(status_code="OK")
        except Exception as e:
            span.end(status_code="ERROR", error=str(e))
            raise
        finally:
            self._tool_spans.append(span)

            logger.debug(
                f"[Tracer] Tool span completed: {tool_name} "
                f"({span.duration_ms:.1f}ms, status={span.status_code})"
            )

    def get_current_trace_id(self) -> Optional[str]:
        """Get current trace ID."""
        return self._current_context.trace_id if self._current_context else None

    def get_current_span_id(self) -> Optional[str]:
        """Get current span ID."""
        return self._current_context.span_id if self._current_context else None

    def add_event_to_current_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add event to the current active span."""
        if self._current_context and self._active_spans:
            # Find the active span for current context
            for span in self._active_spans.values():
                if span.span_id == self._current_context.parent_span_id:
                    span.add_event(name, attributes)
                    break

    def set_attribute(self, key: str, value: Any) -> None:
        """Set attribute on current span."""
        if self._current_context and self._active_spans:
            for span in self._active_spans.values():
                if span.span_id == self._current_context.parent_span_id:
                    span.set_attribute(key, value)
                    break

    def get_trace_stats(self) -> Dict[str, Any]:
        """Get tracing statistics."""
        total_agent_spans = len(self._completed_spans)
        total_llm_spans = len(self._llm_spans)
        total_tool_spans = len(self._tool_spans)

        avg_agent_duration = (
            sum(s.duration_ms for s in self._completed_spans) / total_agent_spans
            if total_agent_spans
            else 0.0
        )
        avg_llm_duration = (
            sum(s.duration_ms for s in self._llm_spans) / total_llm_spans
            if total_llm_spans
            else 0.0
        )
        total_tokens = sum(s.gen_ai_usage_total_tokens for s in self._llm_spans)

        error_count = sum(1 for s in self._completed_spans if s.status_code == "ERROR")

        # Calculate sampling metrics
        total_traces = self._sampling_stats["sampled"] + self._sampling_stats["dropped"]
        sample_rate_actual = (
            self._sampling_stats["sampled"] / total_traces if total_traces > 0 else 0.0
        )

        return {
            "total_agent_spans": total_agent_spans,
            "total_llm_spans": total_llm_spans,
            "total_tool_spans": total_tool_spans,
            "avg_agent_duration_ms": avg_agent_duration,
            "avg_llm_duration_ms": avg_llm_duration,
            "total_tokens_used": total_tokens,
            "error_count": error_count,
            "error_rate": error_count / total_agent_spans if total_agent_spans else 0.0,
            "active_spans": len(self._active_spans),  # Number of currently active spans
            # Sampling metrics (P1-5)
            "sampling_enabled": self._config.sampling_enabled,
            "traces_sampled": self._sampling_stats["sampled"],
            "traces_dropped": self._sampling_stats["dropped"],
            "sample_rate_actual": sample_rate_actual,
            "sample_rate_configured": self._config.head_sample_rate,
        }

    def export_spans(self) -> List[Dict[str, Any]]:
        """Export all spans in OTLP-compatible format."""
        spans = []

        for span in self._completed_spans:
            spans.append(span.to_dict())

        for span in self._llm_spans:
            spans.append(span.to_dict())

        for span in self._tool_spans:
            spans.append(
                {
                    "spanId": span.span_id,
                    "parentSpanId": span.parent_span_id,
                    "name": f"tool.{span.tool_name}",
                    "kind": SpanKind.TOOL.value,
                    "attributes": {
                        "tool.name": span.tool_name,
                    },
                    "status": {"code": span.status_code},
                }
            )

        return spans

    def clear(self) -> None:
        """Clear all trace data."""
        self._active_spans.clear()
        self._completed_spans.clear()
        self._llm_spans.clear()
        self._tool_spans.clear()
        self._current_context = None
