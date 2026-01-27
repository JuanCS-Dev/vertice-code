"""
Observability Module for Vertice Agent Gateway.

Provides:
- OpenTelemetry integration with Google Cloud Trace
- Structured logging with trace correlation
- Metrics collection and export
- Request tracing middleware for FastAPI

Follows Google Cloud best practices for Python instrumentation (2026).
"""

from observability.tracing import (
    setup_opentelemetry,
    setup_structured_logging,
    get_tracer,
    get_meter,
    trace_async,
    create_span,
    TracingMiddleware,
)
from observability.feedback import (
    FeedbackService,
    FeedbackRecord,
    FeedbackType,
)
from observability.cost_tracker import (
    CostTracker,
    TokenUsage,
    estimate_cost_usd,
)

__all__ = [
    # Tracing
    "setup_opentelemetry",
    "setup_structured_logging",
    "get_tracer",
    "get_meter",
    "trace_async",
    "create_span",
    "TracingMiddleware",
    # Feedback
    "FeedbackService",
    "FeedbackRecord",
    "FeedbackType",
    # Cost tracking
    "CostTracker",
    "TokenUsage",
    "estimate_cost_usd",
]
