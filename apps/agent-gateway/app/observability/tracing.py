"""
OpenTelemetry Tracing Integration for Google Cloud Trace.

Implements the official Google Cloud Python instrumentation pattern (2026):
- OTLP export to Cloud Trace
- Structured logging with trace correlation
- FastAPI middleware for automatic request tracing
- Async decorator for tracing coroutines

References:
- https://cloud.google.com/trace/docs/setup/python-ot
- https://opentelemetry.io/docs/languages/python/
"""

from __future__ import annotations

import functools
import logging
import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar

logger = logging.getLogger(__name__)

# Type for decorated functions
F = TypeVar("F", bound=Callable[..., Any])

# OpenTelemetry imports (optional - graceful degradation)
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource, SERVICE_INSTANCE_ID
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.logging import LoggingInstrumentor

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not available - tracing disabled")

# Global instances
_tracer: Optional[Any] = None
_meter: Optional[Any] = None
_initialized = False


def setup_opentelemetry(
    service_name: str = "vertice-agent-gateway",
    service_version: str = "2026.1.0",
) -> bool:
    """
    Initialize OpenTelemetry with Google Cloud Trace export.

    Args:
        service_name: Name of the service for tracing
        service_version: Version of the service

    Returns:
        True if initialization successful
    """
    global _tracer, _meter, _initialized

    if _initialized:
        return True

    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry SDK not installed - tracing disabled")
        return False

    try:
        # Create resource with service metadata
        resource = Resource.create(
            attributes={
                "service.name": service_name,
                "service.version": service_version,
                SERVICE_INSTANCE_ID: f"worker-{os.getpid()}",
                "cloud.provider": "gcp",
                "cloud.platform": "gcp_cloud_run",
            }
        )

        # Set up tracer provider with OTLP export
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
        trace.set_tracer_provider(tracer_provider)
        _tracer = trace.get_tracer(service_name, service_version)

        # Set up meter provider for metrics
        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(),
            export_interval_millis=60000,  # Export every 60 seconds
        )
        meter_provider = MeterProvider(
            metric_readers=[metric_reader],
            resource=resource,
        )
        metrics.set_meter_provider(meter_provider)
        _meter = metrics.get_meter(service_name, service_version)

        _initialized = True
        logger.info(f"OpenTelemetry initialized for {service_name}")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        return False


class JsonFormatter(logging.Formatter):
    """
    JSON formatter for structured logging with Cloud Logging compatibility.

    Outputs logs in a format that Cloud Logging can parse with trace correlation.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with trace context."""
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add trace context if available
        if hasattr(record, "otelTraceID") and record.otelTraceID:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
            log_obj[
                "logging.googleapis.com/trace"
            ] = f"projects/{project_id}/traces/{record.otelTraceID}"
        if hasattr(record, "otelSpanID") and record.otelSpanID:
            log_obj["logging.googleapis.com/spanId"] = record.otelSpanID
        if hasattr(record, "otelTraceSampled"):
            log_obj["logging.googleapis.com/trace_sampled"] = record.otelTraceSampled

        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "otelTraceID",
                "otelSpanID",
                "otelTraceSampled",
                "message",
            ):
                log_obj[key] = value

        import json

        return json.dumps(log_obj)


def setup_structured_logging(level: int = logging.INFO) -> None:
    """
    Configure structured JSON logging with trace correlation.

    This enables Cloud Logging to correlate logs with traces automatically.
    """
    if OTEL_AVAILABLE:
        try:
            LoggingInstrumentor().instrument(set_logging_format=True)
        except Exception as e:
            logger.warning(f"Failed to instrument logging: {e}")

    # Set up JSON formatter
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers and add our JSON handler
    for existing_handler in root_logger.handlers[:]:
        root_logger.removeHandler(existing_handler)
    root_logger.addHandler(handler)

    logger.info("Structured logging configured with trace correlation")


def get_tracer() -> Optional[Any]:
    """Get the global tracer instance."""
    return _tracer


def get_meter() -> Optional[Any]:
    """Get the global meter instance."""
    return _meter


def trace_async(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable[[F], F]:
    """
    Decorator to trace async functions.

    Args:
        name: Span name (defaults to function name)
        attributes: Additional span attributes

    Example:
        @trace_async("process_request")
        async def process_request(prompt: str) -> str:
            ...
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            span_name = name or func.__name__

            if _tracer is None:
                return await func(*args, **kwargs)

            with _tracer.start_as_current_span(span_name) as span:
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)

                try:
                    result = await func(*args, **kwargs)
                    span.set_attribute("status", "success")
                    return result
                except Exception as e:
                    span.set_attribute("status", "error")
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise

        return wrapper  # type: ignore

    return decorator


@contextmanager
def create_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
):
    """
    Context manager to create a span.

    Args:
        name: Span name
        attributes: Span attributes

    Example:
        with create_span("database_query", {"query": "SELECT ..."}) as span:
            result = await db.execute(query)
            span.set_attribute("row_count", len(result))
    """
    if _tracer is None:
        yield None
        return

    with _tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        yield span


class TracingMiddleware:
    """
    FastAPI middleware for automatic request tracing.

    Adds trace context to all incoming requests and records:
    - Request method and path
    - Response status code
    - Request duration
    - User ID (if authenticated)
    """

    def __init__(self, app):
        """Initialize middleware with FastAPI app."""
        self.app = app

        if OTEL_AVAILABLE and _initialized:
            try:
                FastAPIInstrumentor.instrument_app(app)
                logger.info("FastAPI instrumented for tracing")
            except Exception as e:
                logger.warning(f"Failed to instrument FastAPI: {e}")

    async def __call__(self, scope, receive, send):
        """Process request through middleware."""
        await self.app(scope, receive, send)
