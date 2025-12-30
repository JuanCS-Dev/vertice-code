"""
Observability Mixin

Mixin providing observability capabilities to agents.

References:
- OpenTelemetry GenAI Semantic Conventions
- arXiv:2401.02009 (LLM Observability)
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional

from .types import ObservabilityConfig
from .tracer import AgentTracer
from .metrics import MetricsCollector
from .exporter import SpanExporter, MetricsExporter

logger = logging.getLogger(__name__)


class ObservabilityMixin:
    """
    Mixin providing observability capabilities to agents.

    Adds:
    - Distributed tracing with OpenTelemetry conventions
    - Metrics collection and aggregation
    - Export to various backends
    """

    def _init_observability(
        self,
        config: Optional[ObservabilityConfig] = None,
        traces_path: Optional[Path] = None,
        metrics_path: Optional[Path] = None,
    ) -> None:
        """
        Initialize observability system.

        Args:
            config: Observability configuration
            traces_path: Path for trace export
            metrics_path: Path for metrics export
        """
        self._observability_config = config or ObservabilityConfig()
        self._tracer = AgentTracer(self._observability_config)
        self._metrics = MetricsCollector(self._observability_config)
        self._span_exporter = SpanExporter(self._observability_config, traces_path)
        self._metrics_exporter = MetricsExporter(self._observability_config, metrics_path)
        self._observability_initialized = True

        logger.info("[Observability] Initialized OpenTelemetry-compatible observability")

    @contextmanager
    def trace_operation(
        self,
        operation_name: str,
        agent_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Generator[Any, None, None]:
        """
        Trace an agent operation.

        Args:
            operation_name: Name of the operation
            agent_id: Agent identifier
            attributes: Additional span attributes

        Yields:
            Span context for the operation
        """
        if not hasattr(self, "_tracer"):
            self._init_observability()

        effective_agent_id = agent_id or getattr(self, "agent_id", "unknown")

        with self._tracer.start_agent_span(
            operation_name=operation_name,
            agent_id=effective_agent_id,
            attributes=attributes,
        ) as span:
            yield span

    @contextmanager
    def trace_llm_call(
        self,
        model: str,
        operation: str = "chat",
        **kwargs,
    ) -> Generator[Any, None, None]:
        """
        Trace an LLM API call.

        Args:
            model: Model name
            operation: Operation type
            **kwargs: Additional LLM parameters

        Yields:
            LLM span for recording token usage
        """
        if not hasattr(self, "_tracer"):
            self._init_observability()

        with self._tracer.start_llm_span(
            model=model,
            operation=operation,
            max_tokens=kwargs.get("max_tokens"),
            temperature=kwargs.get("temperature"),
        ) as span:
            yield span

    @contextmanager
    def trace_tool(
        self,
        tool_name: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Generator[Any, None, None]:
        """
        Trace a tool execution.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters

        Yields:
            Tool span
        """
        if not hasattr(self, "_tracer"):
            self._init_observability()

        start_time = time.perf_counter()

        with self._tracer.start_tool_span(
            tool_name=tool_name,
            parameters=parameters,
        ) as span:
            try:
                yield span
                duration_ms = (time.perf_counter() - start_time) * 1000
                self._metrics.record_tool_invocation(tool_name, success=True, duration_ms=duration_ms)
            except Exception:
                duration_ms = (time.perf_counter() - start_time) * 1000
                self._metrics.record_tool_invocation(tool_name, success=False, duration_ms=duration_ms)
                raise

    def record_tokens(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str = "chat",
    ) -> None:
        """
        Record token usage.

        Args:
            model: Model name
            input_tokens: Input token count
            output_tokens: Output token count
            operation: Operation type
        """
        if not hasattr(self, "_metrics"):
            self._init_observability()

        self._metrics.record_token_usage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            operation=operation,
        )

    def record_latency(
        self,
        operation: str,
        duration_ms: float,
        model: Optional[str] = None,
    ) -> None:
        """
        Record operation latency.

        Args:
            operation: Operation name
            duration_ms: Duration in milliseconds
            model: Optional model name
        """
        if not hasattr(self, "_metrics"):
            self._init_observability()

        self._metrics.record_latency(
            operation=operation,
            duration_ms=duration_ms,
            model=model,
        )

    def record_error(
        self,
        error_type: str,
        agent_id: Optional[str] = None,
    ) -> None:
        """
        Record an error.

        Args:
            error_type: Type of error
            agent_id: Agent identifier
        """
        if not hasattr(self, "_metrics"):
            self._init_observability()

        effective_agent_id = agent_id or getattr(self, "agent_id", "unknown")
        self._metrics.record_error(effective_agent_id, error_type)

    def add_trace_event(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add event to current trace span.

        Args:
            name: Event name
            attributes: Event attributes
        """
        if hasattr(self, "_tracer"):
            self._tracer.add_event_to_current_span(name, attributes)

    def set_trace_attribute(self, key: str, value: Any) -> None:
        """
        Set attribute on current trace span.

        Args:
            key: Attribute key
            value: Attribute value
        """
        if hasattr(self, "_tracer"):
            self._tracer.set_attribute(key, value)

    def get_observability_stats(self) -> Dict[str, Any]:
        """Get observability statistics."""
        if not hasattr(self, "_observability_initialized"):
            return {"initialized": False}

        return {
            "initialized": True,
            "traces": self._tracer.get_trace_stats(),
            "metrics": self._metrics.get_all_metrics(),
        }

    def export_traces(self) -> bool:
        """Export collected traces."""
        if not hasattr(self, "_span_exporter"):
            return False

        spans = self._tracer.export_spans()
        return self._span_exporter.export(spans)

    def export_metrics(self) -> bool:
        """Export collected metrics."""
        if not hasattr(self, "_metrics_exporter"):
            return False

        metrics = self._metrics.get_all_metrics()
        return self._metrics_exporter.export([metrics])

    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        if not hasattr(self, "_metrics_exporter"):
            return ""

        metrics = self._metrics.get_all_metrics()
        return self._metrics_exporter.to_prometheus_format(metrics)

    def shutdown_observability(self) -> None:
        """Shutdown observability system and flush data."""
        if hasattr(self, "_span_exporter"):
            self.export_traces()
            self._span_exporter.shutdown()

        if hasattr(self, "_metrics_exporter"):
            self.export_metrics()
            self._metrics_exporter.shutdown()
