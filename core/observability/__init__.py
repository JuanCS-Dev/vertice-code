"""
Observability Module

OpenTelemetry-based observability for AI agents following GenAI Semantic Conventions.

References:
- OpenTelemetry GenAI Semantic Conventions (2025)
- OTEL GenAI Agent Spans specification
- arXiv:2401.02009 (LLM Observability patterns)
- arXiv:2312.00752 (LLM Cost monitoring)
- Prometheus metrics specification
"""

from .types import (
    SpanKind,
    MetricType,
    OperationType,
    AgentSpan,
    LLMSpan,
    ToolSpan,
    MetricDefinition,
    TraceContext,
    ObservabilityConfig,
)
from .tracer import AgentTracer
from .metrics import MetricsCollector, Histogram
from .exporter import SpanExporter, MetricsExporter, ConsoleExporter
from .mixin import ObservabilityMixin

__all__ = [
    # Types
    "SpanKind",
    "MetricType",
    "OperationType",
    "AgentSpan",
    "LLMSpan",
    "ToolSpan",
    "MetricDefinition",
    "TraceContext",
    "ObservabilityConfig",
    # Core
    "AgentTracer",
    "MetricsCollector",
    "Histogram",
    "SpanExporter",
    "MetricsExporter",
    "ConsoleExporter",
    "ObservabilityMixin",
]
