"""
Metrics Collector

Collects and aggregates metrics for AI agent observability.

References:
- OpenTelemetry Metrics specification
- GenAI semantic conventions for metrics
- arXiv:2401.02009 (LLM Observability)
- arXiv:2312.00752 (LLM Cost monitoring)
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .types import MetricType, MetricDefinition, ObservabilityConfig

logger = logging.getLogger(__name__)


@dataclass
class MetricPoint:
    """A single metric data point."""
    timestamp: float
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class Histogram:
    """Histogram metric with bucket aggregation."""
    name: str
    buckets: List[float] = field(default_factory=lambda: [
        0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0
    ])
    counts: Dict[float, int] = field(default_factory=dict)
    sum_value: float = 0.0
    count: int = 0

    def __post_init__(self):
        self.counts = {b: 0 for b in self.buckets}
        self.counts[float('inf')] = 0

    def observe(self, value: float) -> None:
        """Record a value in the histogram."""
        self.sum_value += value
        self.count += 1

        for bucket in self.buckets:
            if value <= bucket:
                self.counts[bucket] += 1
        self.counts[float('inf')] += 1

    def percentile(self, p: float) -> float:
        """Calculate approximate percentile from histogram."""
        if self.count == 0:
            return 0.0

        target_count = int(self.count * p / 100)
        cumulative = 0

        for bucket in sorted(self.buckets):
            cumulative += self.counts[bucket]
            if cumulative >= target_count:
                return bucket

        return self.buckets[-1]


class MetricsCollector:
    """
    Collects and aggregates AI agent metrics.

    Implements OpenTelemetry-compatible metric collection for:
    - LLM token usage and costs
    - Latency distributions
    - Error rates
    - Agent-specific metrics

    References:
    - https://opentelemetry.io/docs/specs/otel/metrics/
    """

    # Standard GenAI metrics following semantic conventions
    STANDARD_METRICS = [
        MetricDefinition(
            name="gen_ai.client.token.usage",
            metric_type=MetricType.COUNTER,
            description="Number of tokens used",
            unit="tokens",
            labels=["gen_ai.operation.name", "gen_ai.request.model", "token_type"],
        ),
        MetricDefinition(
            name="gen_ai.client.operation.duration",
            metric_type=MetricType.HISTOGRAM,
            description="Duration of GenAI operations",
            unit="ms",
            labels=["gen_ai.operation.name", "gen_ai.request.model"],
        ),
        MetricDefinition(
            name="gen_ai.server.request.duration",
            metric_type=MetricType.HISTOGRAM,
            description="Duration of requests to GenAI server",
            unit="ms",
            labels=["gen_ai.request.model", "server.address"],
        ),
        MetricDefinition(
            name="gen_ai.server.time_to_first_token",
            metric_type=MetricType.HISTOGRAM,
            description="Time to first token from streaming response",
            unit="ms",
            labels=["gen_ai.request.model"],
        ),
        MetricDefinition(
            name="agent.task.count",
            metric_type=MetricType.COUNTER,
            description="Number of agent tasks executed",
            unit="tasks",
            labels=["agent_id", "task_type", "status"],
        ),
        MetricDefinition(
            name="agent.tool.invocations",
            metric_type=MetricType.COUNTER,
            description="Number of tool invocations",
            unit="invocations",
            labels=["tool_name", "status"],
        ),
        MetricDefinition(
            name="agent.error.count",
            metric_type=MetricType.COUNTER,
            description="Number of agent errors",
            unit="errors",
            labels=["agent_id", "error_type"],
        ),
    ]

    def __init__(self, config: Optional[ObservabilityConfig] = None):
        """
        Initialize metrics collector.

        Args:
            config: Observability configuration
        """
        self._config = config or ObservabilityConfig()

        # Metric storage
        self._counters: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: Dict[str, Dict[str, Histogram]] = defaultdict(dict)

        # Time series for trending
        self._time_series: Dict[str, List[MetricPoint]] = defaultdict(list)

        # Initialize standard metrics
        self._init_standard_metrics()

        # Cost tracking
        self._token_costs: Dict[str, float] = {}  # model -> cost per 1K tokens

    def _init_standard_metrics(self) -> None:
        """Initialize standard GenAI metrics."""
        for metric in self.STANDARD_METRICS:
            if metric.metric_type == MetricType.HISTOGRAM:
                self._histograms[metric.name] = {}

    def increment_counter(
        self,
        name: str,
        value: float = 1.0,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            name: Metric name
            value: Increment value (default: 1)
            labels: Metric labels
        """
        label_key = self._labels_to_key(labels)
        self._counters[name][label_key] += value

        # Record time series
        self._time_series[name].append(MetricPoint(
            timestamp=time.time(),
            value=value,
            labels=labels or {},
        ))

    def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Set a gauge metric value.

        Args:
            name: Metric name
            value: Gauge value
            labels: Metric labels
        """
        label_key = self._labels_to_key(labels)
        self._gauges[name][label_key] = value

    def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record a histogram observation.

        Args:
            name: Metric name
            value: Observed value
            labels: Metric labels
        """
        label_key = self._labels_to_key(labels)

        if label_key not in self._histograms[name]:
            self._histograms[name][label_key] = Histogram(name=name)

        self._histograms[name][label_key].observe(value)

    def record_token_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        operation: str = "chat",
    ) -> None:
        """
        Record LLM token usage with optional cost calculation.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            operation: Operation type
        """
        # Record input tokens
        self.increment_counter(
            "gen_ai.client.token.usage",
            value=input_tokens,
            labels={
                "gen_ai.operation.name": operation,
                "gen_ai.request.model": model,
                "token_type": "input",
            },
        )

        # Record output tokens
        self.increment_counter(
            "gen_ai.client.token.usage",
            value=output_tokens,
            labels={
                "gen_ai.operation.name": operation,
                "gen_ai.request.model": model,
                "token_type": "output",
            },
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
        labels = {"gen_ai.operation.name": operation}
        if model:
            labels["gen_ai.request.model"] = model

        self.observe_histogram(
            "gen_ai.client.operation.duration",
            value=duration_ms,
            labels=labels,
        )

    def record_ttft(self, model: str, ttft_ms: float) -> None:
        """
        Record time to first token for streaming responses.

        Args:
            model: Model name
            ttft_ms: Time to first token in milliseconds
        """
        self.observe_histogram(
            "gen_ai.server.time_to_first_token",
            value=ttft_ms,
            labels={"gen_ai.request.model": model},
        )

    def record_tool_invocation(
        self,
        tool_name: str,
        success: bool,
        duration_ms: Optional[float] = None,
    ) -> None:
        """
        Record a tool invocation.

        Args:
            tool_name: Name of the tool
            success: Whether invocation was successful
            duration_ms: Optional duration
        """
        self.increment_counter(
            "agent.tool.invocations",
            labels={
                "tool_name": tool_name,
                "status": "success" if success else "error",
            },
        )

        if duration_ms is not None:
            self.observe_histogram(
                "agent.tool.duration",
                value=duration_ms,
                labels={"tool_name": tool_name},
            )

    def record_error(
        self,
        agent_id: str,
        error_type: str,
    ) -> None:
        """
        Record an agent error.

        Args:
            agent_id: Agent identifier
            error_type: Type of error
        """
        self.increment_counter(
            "agent.error.count",
            labels={
                "agent_id": agent_id,
                "error_type": error_type,
            },
        )

    def get_counter_value(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> float:
        """Get counter value."""
        label_key = self._labels_to_key(labels)
        return self._counters[name].get(label_key, 0.0)

    def get_gauge_value(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> float:
        """Get gauge value."""
        label_key = self._labels_to_key(labels)
        return self._gauges[name].get(label_key, 0.0)

    def get_histogram_stats(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, float]:
        """Get histogram statistics."""
        label_key = self._labels_to_key(labels)

        if name not in self._histograms or label_key not in self._histograms[name]:
            return {"count": 0, "sum": 0.0, "p50": 0.0, "p90": 0.0, "p99": 0.0}

        hist = self._histograms[name][label_key]
        return {
            "count": hist.count,
            "sum": hist.sum_value,
            "mean": hist.sum_value / hist.count if hist.count > 0 else 0.0,
            "p50": hist.percentile(50),
            "p90": hist.percentile(90),
            "p99": hist.percentile(99),
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics summary."""
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: {
                    label: {
                        "count": h.count,
                        "sum": h.sum_value,
                        "mean": h.sum_value / h.count if h.count > 0 else 0.0,
                    }
                    for label, h in label_hists.items()
                }
                for name, label_hists in self._histograms.items()
            },
        }

    def _labels_to_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Convert labels dict to a hashable key."""
        if not labels:
            return ""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    def clear(self) -> None:
        """Clear all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()
        self._time_series.clear()
