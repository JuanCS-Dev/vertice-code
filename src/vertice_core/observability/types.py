"""
Observability Types

Type definitions following OpenTelemetry GenAI Semantic Conventions.

References:
- https://opentelemetry.io/docs/specs/semconv/gen-ai/
- GenAI Agent Spans specification (2025)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
import uuid


class SpanKind(str, Enum):
    """OpenTelemetry span kinds for GenAI operations."""

    AGENT = "agent"  # Top-level agent operation
    TASK = "task"  # Sub-task within agent
    LLM = "llm"  # LLM call
    TOOL = "tool"  # Tool execution
    RETRIEVAL = "retrieval"  # RAG retrieval
    EMBEDDING = "embedding"  # Embedding generation
    CHAIN = "chain"  # Chain of operations


class MetricType(str, Enum):
    """Types of metrics collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class OperationType(str, Enum):
    """GenAI operation types per semantic conventions."""

    CHAT = "chat"
    TEXT_COMPLETION = "text_completion"
    EMBEDDINGS = "embeddings"
    TOOL_CALL = "tool_call"
    AGENT_INVOKE = "agent_invoke"
    RETRIEVAL = "retrieval"


@dataclass
class TraceContext:
    """Distributed tracing context."""

    trace_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None
    baggage: Dict[str, str] = field(default_factory=dict)

    def child(self) -> TraceContext:
        """Create child context."""
        return TraceContext(
            trace_id=self.trace_id,
            parent_span_id=self.span_id,
            baggage=dict(self.baggage),
        )


@dataclass
class AgentSpan:
    """
    Agent span following OpenTelemetry GenAI semantic conventions.

    Attributes follow gen_ai.* namespace.
    """

    # Core identifiers
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    trace_id: str = ""
    parent_span_id: Optional[str] = None

    # GenAI semantic attributes
    gen_ai_system: str = "vertice"  # gen_ai.system
    gen_ai_operation_name: str = ""  # gen_ai.operation.name
    gen_ai_agent_id: str = ""  # gen_ai.agent.id
    gen_ai_agent_name: str = ""  # gen_ai.agent.name
    gen_ai_agent_description: str = ""  # gen_ai.agent.description

    # Timing
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    duration_ms: float = 0.0

    # Status
    status_code: str = "UNSET"  # UNSET, OK, ERROR
    status_message: str = ""

    # Events and attributes
    events: List[Dict[str, Any]] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)

    # Child spans
    child_spans: List[str] = field(default_factory=list)

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        self.events.append(
            {
                "name": name,
                "timestamp": datetime.now().isoformat(),
                "attributes": attributes or {},
            }
        )

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def end(self, status_code: str = "OK", message: str = "") -> None:
        """End the span."""
        self.end_time = datetime.now().isoformat()
        self.status_code = status_code
        self.status_message = message

        # Calculate duration
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        self.duration_ms = (end - start).total_seconds() * 1000

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OTLP-compatible dictionary."""
        return {
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "parentSpanId": self.parent_span_id,
            "name": self.gen_ai_operation_name,
            "kind": SpanKind.AGENT.value,
            "startTimeUnixNano": self.start_time,
            "endTimeUnixNano": self.end_time,
            "attributes": {
                "gen_ai.system": self.gen_ai_system,
                "gen_ai.operation.name": self.gen_ai_operation_name,
                "gen_ai.agent.id": self.gen_ai_agent_id,
                "gen_ai.agent.name": self.gen_ai_agent_name,
                **self.attributes,
            },
            "status": {
                "code": self.status_code,
                "message": self.status_message,
            },
            "events": self.events,
        }


@dataclass
class LLMSpan:
    """
    LLM call span with GenAI semantic conventions.

    Captures token usage, model info, and request/response details.
    """

    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None

    # GenAI LLM attributes
    gen_ai_operation_name: str = "chat"  # gen_ai.operation.name
    gen_ai_request_model: str = ""  # gen_ai.request.model
    gen_ai_response_model: str = ""  # gen_ai.response.model
    gen_ai_request_max_tokens: Optional[int] = None
    gen_ai_request_temperature: Optional[float] = None
    gen_ai_request_top_p: Optional[float] = None

    # Token usage
    gen_ai_usage_input_tokens: int = 0  # gen_ai.usage.input_tokens
    gen_ai_usage_output_tokens: int = 0  # gen_ai.usage.output_tokens
    gen_ai_usage_total_tokens: int = 0

    # Response info
    gen_ai_response_finish_reasons: List[str] = field(default_factory=list)

    # Timing
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    duration_ms: float = 0.0
    time_to_first_token_ms: Optional[float] = None

    # Status
    status_code: str = "UNSET"
    error_type: Optional[str] = None

    def end(self, status_code: str = "OK") -> None:
        """End the span and calculate duration."""
        self.end_time = datetime.now().isoformat()
        self.status_code = status_code
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        self.duration_ms = (end - start).total_seconds() * 1000
        self.gen_ai_usage_total_tokens = (
            self.gen_ai_usage_input_tokens + self.gen_ai_usage_output_tokens
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to OTLP-compatible dictionary."""
        return {
            "spanId": self.span_id,
            "parentSpanId": self.parent_span_id,
            "name": f"llm.{self.gen_ai_operation_name}",
            "kind": SpanKind.LLM.value,
            "attributes": {
                "gen_ai.operation.name": self.gen_ai_operation_name,
                "gen_ai.request.model": self.gen_ai_request_model,
                "gen_ai.response.model": self.gen_ai_response_model,
                "gen_ai.usage.input_tokens": self.gen_ai_usage_input_tokens,
                "gen_ai.usage.output_tokens": self.gen_ai_usage_output_tokens,
            },
            "status": {"code": self.status_code},
        }


@dataclass
class ToolSpan:
    """Tool execution span."""

    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    parent_span_id: Optional[str] = None

    # Tool attributes
    tool_name: str = ""
    tool_description: str = ""
    tool_parameters: Dict[str, Any] = field(default_factory=dict)
    tool_result: Optional[Any] = None

    # Timing
    start_time: str = field(default_factory=lambda: datetime.now().isoformat())
    end_time: Optional[str] = None
    duration_ms: float = 0.0

    # Status
    status_code: str = "UNSET"
    error_message: Optional[str] = None

    def end(self, status_code: str = "OK", error: Optional[str] = None) -> None:
        """End the span."""
        self.end_time = datetime.now().isoformat()
        self.status_code = status_code
        self.error_message = error
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        self.duration_ms = (end - start).total_seconds() * 1000


@dataclass
class MetricDefinition:
    """Definition of a metric to collect."""

    name: str
    metric_type: MetricType
    description: str = ""
    unit: str = ""
    labels: List[str] = field(default_factory=list)


@dataclass
class ObservabilityConfig:
    """Configuration for observability system."""

    service_name: str = "vertice-agent"
    service_version: str = "1.0.0"
    environment: str = "development"

    # Export settings
    otlp_endpoint: Optional[str] = None
    export_interval_seconds: int = 60
    batch_size: int = 100

    # Sampling (P1-5 - Optimized for production scale)
    sampling_enabled: bool = True
    head_sample_rate: float = 0.1  # 10% head-based sampling (production)
    tail_sample_errors: bool = True  # Always sample errors (100%)
    sample_rate: float = 1.0  # Legacy: 1.0 = 100% sampling (dev/test)

    # Feature flags
    trace_llm_content: bool = False  # Privacy: don't trace prompts by default
    trace_tool_results: bool = True
    collect_token_metrics: bool = True
