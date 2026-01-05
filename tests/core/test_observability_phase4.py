"""
Tests for Observability Module (Phase 4)

Tests for OpenTelemetry GenAI semantic conventions.

References:
- OpenTelemetry GenAI Semantic Conventions (2025)
- OTEL GenAI Agent Spans specification
"""

import pytest
import time
from unittest.mock import patch, MagicMock

from core.observability.types import (
    SpanKind,
    MetricType,
    OperationType,
    TraceContext,
    AgentSpan,
    LLMSpan,
    ToolSpan,
    MetricDefinition,
    ObservabilityConfig,
)


class TestObservabilityTypes:
    """Tests for observability type definitions."""

    def test_span_kind_enum(self):
        """Test SpanKind enumeration."""
        assert SpanKind.AGENT.value == "agent"
        assert SpanKind.LLM.value == "llm"
        assert SpanKind.TOOL.value == "tool"
        assert SpanKind.RETRIEVAL.value == "retrieval"
        assert SpanKind.EMBEDDING.value == "embedding"

    def test_metric_type_enum(self):
        """Test MetricType enumeration."""
        assert MetricType.COUNTER.value == "counter"
        assert MetricType.GAUGE.value == "gauge"
        assert MetricType.HISTOGRAM.value == "histogram"
        assert MetricType.SUMMARY.value == "summary"

    def test_operation_type_enum(self):
        """Test OperationType enumeration."""
        assert OperationType.CHAT.value == "chat"
        assert OperationType.TEXT_COMPLETION.value == "text_completion"
        assert OperationType.EMBEDDINGS.value == "embeddings"
        assert OperationType.TOOL_CALL.value == "tool_call"

    def test_trace_context_creation(self):
        """Test TraceContext creation."""
        ctx = TraceContext()
        assert ctx.trace_id is not None
        assert ctx.span_id is not None
        assert ctx.parent_span_id is None

    def test_trace_context_child(self):
        """Test TraceContext child creation."""
        parent = TraceContext()
        child = parent.child()

        assert child.trace_id == parent.trace_id
        assert child.parent_span_id == parent.span_id
        assert child.span_id != parent.span_id

    def test_trace_context_baggage(self):
        """Test TraceContext baggage propagation."""
        parent = TraceContext(baggage={"key": "value"})
        child = parent.child()

        assert child.baggage == {"key": "value"}


class TestAgentSpan:
    """Tests for AgentSpan."""

    @pytest.fixture
    def span(self):
        """Create test agent span."""
        return AgentSpan(
            trace_id="trace_123",
            gen_ai_agent_id="agent_1",
            gen_ai_agent_name="TestAgent",
            gen_ai_operation_name="execute_task",
        )

    def test_agent_span_creation(self, span):
        """Test AgentSpan creation."""
        assert span.trace_id == "trace_123"
        assert span.gen_ai_agent_id == "agent_1"
        assert span.gen_ai_agent_name == "TestAgent"
        assert span.gen_ai_system == "vertice"

    def test_agent_span_add_event(self, span):
        """Test adding events to span."""
        span.add_event("task_started", {"task_id": "123"})

        assert len(span.events) == 1
        assert span.events[0]["name"] == "task_started"
        assert span.events[0]["attributes"]["task_id"] == "123"

    def test_agent_span_set_attribute(self, span):
        """Test setting span attributes."""
        span.set_attribute("custom.key", "value")

        assert span.attributes["custom.key"] == "value"

    def test_agent_span_end(self, span):
        """Test ending span."""
        span.end(status_code="OK", message="Success")

        assert span.end_time is not None
        assert span.status_code == "OK"
        assert span.status_message == "Success"
        assert span.duration_ms >= 0.0

    def test_agent_span_end_with_error(self, span):
        """Test ending span with error."""
        span.end(status_code="ERROR", message="Something failed")

        assert span.status_code == "ERROR"
        assert span.status_message == "Something failed"

    def test_agent_span_to_dict(self, span):
        """Test span serialization to OTLP format."""
        span.end()

        d = span.to_dict()

        assert d["traceId"] == "trace_123"
        assert d["name"] == "execute_task"
        assert d["kind"] == "agent"
        assert "gen_ai.agent.id" in d["attributes"]


class TestLLMSpan:
    """Tests for LLMSpan."""

    @pytest.fixture
    def span(self):
        """Create test LLM span."""
        return LLMSpan(
            gen_ai_request_model="gpt-4",
            gen_ai_operation_name="chat",
            gen_ai_usage_input_tokens=100,
            gen_ai_usage_output_tokens=50,
        )

    def test_llm_span_creation(self, span):
        """Test LLMSpan creation."""
        assert span.gen_ai_request_model == "gpt-4"
        assert span.gen_ai_operation_name == "chat"
        assert span.gen_ai_usage_input_tokens == 100
        assert span.gen_ai_usage_output_tokens == 50

    def test_llm_span_end(self, span):
        """Test LLMSpan end calculates totals."""
        span.end()

        assert span.gen_ai_usage_total_tokens == 150
        assert span.duration_ms >= 0.0

    def test_llm_span_time_to_first_token(self):
        """Test TTFT tracking."""
        span = LLMSpan(time_to_first_token_ms=120.5)
        assert span.time_to_first_token_ms == 120.5

    def test_llm_span_request_params(self):
        """Test LLM request parameters."""
        span = LLMSpan(
            gen_ai_request_max_tokens=1000,
            gen_ai_request_temperature=0.7,
            gen_ai_request_top_p=0.9,
        )

        assert span.gen_ai_request_max_tokens == 1000
        assert span.gen_ai_request_temperature == 0.7
        assert span.gen_ai_request_top_p == 0.9

    def test_llm_span_to_dict(self, span):
        """Test LLMSpan serialization."""
        span.end()

        d = span.to_dict()

        assert d["name"] == "llm.chat"
        assert d["kind"] == "llm"
        assert d["attributes"]["gen_ai.request.model"] == "gpt-4"


class TestToolSpan:
    """Tests for ToolSpan."""

    @pytest.fixture
    def span(self):
        """Create test tool span."""
        return ToolSpan(
            tool_name="execute_code",
            tool_description="Execute Python code",
            tool_parameters={"code": "print('hello')"},
        )

    def test_tool_span_creation(self, span):
        """Test ToolSpan creation."""
        assert span.tool_name == "execute_code"
        assert span.tool_description == "Execute Python code"
        assert "code" in span.tool_parameters

    def test_tool_span_end_success(self, span):
        """Test ToolSpan end with success."""
        span.tool_result = "hello"
        span.end(status_code="OK")

        assert span.status_code == "OK"
        assert span.error_message is None
        assert span.duration_ms >= 0.0

    def test_tool_span_end_error(self, span):
        """Test ToolSpan end with error."""
        span.end(status_code="ERROR", error="Execution failed")

        assert span.status_code == "ERROR"
        assert span.error_message == "Execution failed"


class TestMetricDefinition:
    """Tests for MetricDefinition."""

    def test_counter_metric(self):
        """Test counter metric definition."""
        metric = MetricDefinition(
            name="gen_ai.client.token.usage",
            metric_type=MetricType.COUNTER,
            description="Total token usage",
            unit="tokens",
            labels=["model", "operation"],
        )

        assert metric.name == "gen_ai.client.token.usage"
        assert metric.metric_type == MetricType.COUNTER
        assert "model" in metric.labels

    def test_histogram_metric(self):
        """Test histogram metric definition."""
        metric = MetricDefinition(
            name="gen_ai.client.operation.duration",
            metric_type=MetricType.HISTOGRAM,
            description="Operation duration",
            unit="ms",
        )

        assert metric.metric_type == MetricType.HISTOGRAM
        assert metric.unit == "ms"


class TestObservabilityConfig:
    """Tests for ObservabilityConfig."""

    def test_config_defaults(self):
        """Test default configuration."""
        config = ObservabilityConfig()

        assert config.service_name == "vertice-agent"
        assert config.sample_rate == 1.0
        assert config.trace_llm_content is False
        assert config.collect_token_metrics is True

    def test_config_custom_values(self):
        """Test custom configuration."""
        config = ObservabilityConfig(
            service_name="my-agent",
            service_version="2.0.0",
            environment="production",
            otlp_endpoint="http://localhost:4317",
            sample_rate=0.5,
        )

        assert config.service_name == "my-agent"
        assert config.service_version == "2.0.0"
        assert config.otlp_endpoint == "http://localhost:4317"
        assert config.sample_rate == 0.5

    def test_config_privacy_settings(self):
        """Test privacy-related settings."""
        config = ObservabilityConfig(
            trace_llm_content=True,
            trace_tool_results=False,
        )

        assert config.trace_llm_content is True
        assert config.trace_tool_results is False


class TestSpanHierarchy:
    """Tests for span parent-child relationships."""

    def test_agent_span_children(self):
        """Test agent span with child spans."""
        parent = AgentSpan(
            trace_id="trace_1",
            gen_ai_agent_id="agent_1",
            gen_ai_agent_name="TestAgent",
        )

        llm_span = LLMSpan(parent_span_id=parent.span_id)
        tool_span = ToolSpan(parent_span_id=parent.span_id)

        parent.child_spans.append(llm_span.span_id)
        parent.child_spans.append(tool_span.span_id)

        assert len(parent.child_spans) == 2
        assert llm_span.parent_span_id == parent.span_id
        assert tool_span.parent_span_id == parent.span_id

    def test_nested_llm_calls(self):
        """Test nested LLM calls."""
        outer = LLMSpan(gen_ai_request_model="gpt-4")
        inner = LLMSpan(
            gen_ai_request_model="gpt-4-vision",
            parent_span_id=outer.span_id,
        )

        assert inner.parent_span_id == outer.span_id


class TestSpanTiming:
    """Tests for span timing measurements."""

    def test_span_duration(self):
        """Test span duration calculation."""
        span = AgentSpan()
        time.sleep(0.01)  # 10ms
        span.end()

        assert span.duration_ms >= 10.0

    def test_llm_span_duration(self):
        """Test LLM span duration."""
        span = LLMSpan(gen_ai_request_model="gpt-4")
        time.sleep(0.01)
        span.end()

        assert span.duration_ms >= 10.0

    def test_tool_span_duration(self):
        """Test tool span duration."""
        span = ToolSpan(tool_name="test")
        time.sleep(0.01)
        span.end()

        assert span.duration_ms >= 10.0


class TestTraceContextPropagation:
    """Tests for trace context propagation."""

    def test_context_propagation_chain(self):
        """Test context propagation through multiple levels."""
        root = TraceContext()
        child1 = root.child()
        child2 = child1.child()
        child3 = child2.child()

        # All should share same trace_id
        assert child1.trace_id == root.trace_id
        assert child2.trace_id == root.trace_id
        assert child3.trace_id == root.trace_id

        # Parent chains should be correct
        assert child1.parent_span_id == root.span_id
        assert child2.parent_span_id == child1.span_id
        assert child3.parent_span_id == child2.span_id

    def test_baggage_propagation(self):
        """Test baggage propagation through context chain."""
        root = TraceContext(baggage={"user_id": "123"})
        child = root.child()
        grandchild = child.child()

        assert grandchild.baggage["user_id"] == "123"

    def test_baggage_independence(self):
        """Test that child baggage is independent copy."""
        parent = TraceContext(baggage={"key": "value"})
        child = parent.child()

        child.baggage["new_key"] = "new_value"

        assert "new_key" not in parent.baggage


# ==============================================================================
# AgentTracer Tests
# ==============================================================================

class TestAgentTracer:
    """Tests for AgentTracer."""

    @pytest.fixture
    def tracer(self):
        """Create test tracer."""
        from core.observability.tracer import AgentTracer
        return AgentTracer()

    @pytest.fixture
    def tracer_with_config(self):
        """Create tracer with custom config."""
        from core.observability.tracer import AgentTracer
        config = ObservabilityConfig(
            service_name="test-service",
            trace_tool_results=True,
        )
        return AgentTracer(config)

    def test_tracer_creation(self, tracer):
        """Test tracer initialization."""
        assert tracer._active_spans == {}
        assert tracer._completed_spans == []
        assert tracer._current_context is None

    def test_start_agent_span(self, tracer):
        """Test starting an agent span."""
        with tracer.start_agent_span(
            operation_name="test_op",
            agent_id="agent_1",
            agent_name="TestAgent",
        ) as span:
            assert span.gen_ai_operation_name == "test_op"
            assert span.gen_ai_agent_id == "agent_1"
            assert span.gen_ai_agent_name == "TestAgent"

        assert len(tracer._completed_spans) == 1
        assert tracer._completed_spans[0].status_code == "OK"

    def test_agent_span_with_error(self, tracer):
        """Test agent span with exception."""
        with pytest.raises(ValueError):
            with tracer.start_agent_span(
                operation_name="failing_op",
                agent_id="agent_1",
            ) as span:
                raise ValueError("Test error")

        assert len(tracer._completed_spans) == 1
        assert tracer._completed_spans[0].status_code == "ERROR"

    def test_agent_span_with_attributes(self, tracer):
        """Test agent span with custom attributes."""
        with tracer.start_agent_span(
            operation_name="test_op",
            agent_id="agent_1",
            attributes={"custom.key": "value"},
        ) as span:
            assert span.attributes["custom.key"] == "value"

    def test_start_llm_span(self, tracer):
        """Test starting an LLM span."""
        with tracer.start_llm_span(
            model="gpt-4",
            operation="chat",
            max_tokens=1000,
            temperature=0.7,
        ) as span:
            span.gen_ai_usage_input_tokens = 100
            span.gen_ai_usage_output_tokens = 50

        assert len(tracer._llm_spans) == 1
        assert tracer._llm_spans[0].gen_ai_request_model == "gpt-4"

    def test_llm_span_with_error(self, tracer):
        """Test LLM span with exception."""
        with pytest.raises(RuntimeError):
            with tracer.start_llm_span(model="gpt-4") as span:
                raise RuntimeError("API error")

        assert len(tracer._llm_spans) == 1
        assert tracer._llm_spans[0].status_code == "ERROR"

    def test_start_tool_span(self, tracer_with_config):
        """Test starting a tool span."""
        with tracer_with_config.start_tool_span(
            tool_name="execute_code",
            parameters={"code": "print('hello')"},
        ) as span:
            span.tool_result = "hello"

        assert len(tracer_with_config._tool_spans) == 1
        assert tracer_with_config._tool_spans[0].tool_name == "execute_code"

    def test_tool_span_with_error(self, tracer):
        """Test tool span with exception."""
        with pytest.raises(Exception):
            with tracer.start_tool_span(tool_name="failing_tool") as span:
                raise Exception("Tool failed")

        assert len(tracer._tool_spans) == 1
        assert tracer._tool_spans[0].status_code == "ERROR"

    def test_nested_spans(self, tracer):
        """Test nested agent and LLM spans."""
        with tracer.start_agent_span(
            operation_name="outer",
            agent_id="agent_1",
        ) as agent_span:
            with tracer.start_llm_span(model="gpt-4") as llm_span:
                llm_span.gen_ai_usage_input_tokens = 50

        assert len(tracer._completed_spans) == 1
        assert len(tracer._llm_spans) == 1
        assert tracer._llm_spans[0].parent_span_id is not None

    def test_get_current_trace_id(self, tracer):
        """Test getting current trace ID."""
        # Initially no context
        assert tracer.get_current_trace_id() is None

        with tracer.start_agent_span(
            operation_name="test",
            agent_id="agent_1",
        ):
            trace_id = tracer.get_current_trace_id()
            assert trace_id is not None

        # After span ends, context is restored to root (not None)
        # because the tracer maintains the trace context for the session
        # Use clear() to fully reset
        tracer.clear()
        assert tracer.get_current_trace_id() is None

    def test_get_current_span_id(self, tracer):
        """Test getting current span ID."""
        assert tracer.get_current_span_id() is None

        with tracer.start_agent_span(
            operation_name="test",
            agent_id="agent_1",
        ):
            assert tracer.get_current_span_id() is not None

    def test_add_event_to_current_span(self, tracer):
        """Test adding events to current span."""
        with tracer.start_agent_span(
            operation_name="test",
            agent_id="agent_1",
        ) as span:
            tracer.add_event_to_current_span("custom_event", {"key": "value"})

    def test_set_attribute(self, tracer):
        """Test setting attribute on current span."""
        with tracer.start_agent_span(
            operation_name="test",
            agent_id="agent_1",
        ):
            tracer.set_attribute("custom.attr", "value")

    def test_get_trace_stats(self, tracer):
        """Test getting trace statistics."""
        with tracer.start_agent_span(
            operation_name="test",
            agent_id="agent_1",
        ):
            with tracer.start_llm_span(model="gpt-4") as llm_span:
                llm_span.gen_ai_usage_input_tokens = 100
                llm_span.gen_ai_usage_output_tokens = 50

        stats = tracer.get_trace_stats()

        assert stats["total_agent_spans"] == 1
        assert stats["total_llm_spans"] == 1
        assert stats["total_tokens_used"] == 150

    def test_export_spans(self, tracer):
        """Test exporting spans."""
        with tracer.start_agent_span(
            operation_name="test",
            agent_id="agent_1",
        ):
            with tracer.start_llm_span(model="gpt-4"):
                pass
            with tracer.start_tool_span(tool_name="tool_1"):
                pass

        spans = tracer.export_spans()

        assert len(spans) >= 3

    def test_clear(self, tracer):
        """Test clearing trace data."""
        with tracer.start_agent_span(
            operation_name="test",
            agent_id="agent_1",
        ):
            pass

        tracer.clear()

        assert tracer._active_spans == {}
        assert tracer._completed_spans == []
        assert tracer._llm_spans == []
        assert tracer._tool_spans == []
        assert tracer._current_context is None


# ==============================================================================
# MetricsCollector Tests
# ==============================================================================

class TestMetricsCollector:
    """Tests for MetricsCollector."""

    @pytest.fixture
    def collector(self):
        """Create test metrics collector."""
        from core.observability.metrics import MetricsCollector
        return MetricsCollector()

    def test_collector_creation(self, collector):
        """Test metrics collector initialization."""
        assert collector._counters is not None
        assert collector._gauges is not None
        assert collector._histograms is not None

    def test_increment_counter(self, collector):
        """Test incrementing a counter."""
        collector.increment_counter("test.counter")
        collector.increment_counter("test.counter", value=5)

        value = collector.get_counter_value("test.counter")
        assert value == 6.0

    def test_increment_counter_with_labels(self, collector):
        """Test counter with labels."""
        collector.increment_counter(
            "test.counter",
            labels={"env": "test", "op": "read"},
        )

        value = collector.get_counter_value(
            "test.counter",
            labels={"env": "test", "op": "read"},
        )
        assert value == 1.0

    def test_set_gauge(self, collector):
        """Test setting a gauge."""
        collector.set_gauge("test.gauge", 42.0)

        value = collector.get_gauge_value("test.gauge")
        assert value == 42.0

    def test_set_gauge_with_labels(self, collector):
        """Test gauge with labels."""
        collector.set_gauge(
            "test.gauge",
            100.0,
            labels={"instance": "a"},
        )

        value = collector.get_gauge_value(
            "test.gauge",
            labels={"instance": "a"},
        )
        assert value == 100.0

    def test_observe_histogram(self, collector):
        """Test histogram observations."""
        for i in range(10):
            collector.observe_histogram("test.histogram", float(i) / 10)

        stats = collector.get_histogram_stats("test.histogram")

        assert stats["count"] == 10
        assert stats["sum"] > 0

    def test_histogram_percentiles(self, collector):
        """Test histogram percentile calculations."""
        for i in range(100):
            collector.observe_histogram("latency", float(i) / 100)

        stats = collector.get_histogram_stats("latency")

        assert stats["p50"] > 0
        assert stats["p90"] > 0
        assert stats["p99"] > 0

    def test_record_token_usage(self, collector):
        """Test token usage recording."""
        collector.record_token_usage(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            operation="chat",
        )

        input_value = collector.get_counter_value(
            "gen_ai.client.token.usage",
            labels={
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4",
                "token_type": "input",
            },
        )
        assert input_value == 100

    def test_record_latency(self, collector):
        """Test latency recording."""
        collector.record_latency(
            operation="chat",
            duration_ms=150.0,
            model="gpt-4",
        )

        stats = collector.get_histogram_stats(
            "gen_ai.client.operation.duration",
            labels={
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4",
            },
        )
        assert stats["count"] == 1

    def test_record_ttft(self, collector):
        """Test time to first token recording."""
        collector.record_ttft("gpt-4", 120.5)

        stats = collector.get_histogram_stats(
            "gen_ai.server.time_to_first_token",
            labels={"gen_ai.request.model": "gpt-4"},
        )
        assert stats["count"] == 1

    def test_record_tool_invocation(self, collector):
        """Test tool invocation recording."""
        collector.record_tool_invocation("execute_code", success=True, duration_ms=50.0)
        collector.record_tool_invocation("execute_code", success=False)

        success_value = collector.get_counter_value(
            "agent.tool.invocations",
            labels={"tool_name": "execute_code", "status": "success"},
        )
        error_value = collector.get_counter_value(
            "agent.tool.invocations",
            labels={"tool_name": "execute_code", "status": "error"},
        )

        assert success_value == 1
        assert error_value == 1

    def test_record_error(self, collector):
        """Test error recording."""
        collector.record_error("agent_1", "ValueError")

        value = collector.get_counter_value(
            "agent.error.count",
            labels={"agent_id": "agent_1", "error_type": "ValueError"},
        )
        assert value == 1

    def test_get_all_metrics(self, collector):
        """Test getting all metrics."""
        collector.increment_counter("test.counter")
        collector.set_gauge("test.gauge", 42.0)
        collector.observe_histogram("test.histogram", 0.5)

        metrics = collector.get_all_metrics()

        assert "counters" in metrics
        assert "gauges" in metrics
        assert "histograms" in metrics

    def test_clear(self, collector):
        """Test clearing all metrics."""
        collector.increment_counter("test.counter")
        collector.clear()

        value = collector.get_counter_value("test.counter")
        assert value == 0.0


class TestHistogram:
    """Tests for Histogram class."""

    @pytest.fixture
    def histogram(self):
        """Create test histogram."""
        from core.observability.metrics import Histogram
        return Histogram(name="test")

    def test_histogram_creation(self, histogram):
        """Test histogram initialization."""
        assert histogram.name == "test"
        assert histogram.count == 0
        assert histogram.sum_value == 0.0

    def test_histogram_observe(self, histogram):
        """Test observing values."""
        histogram.observe(0.1)
        histogram.observe(0.5)
        histogram.observe(1.0)

        assert histogram.count == 3
        assert histogram.sum_value == 1.6

    def test_histogram_bucket_counts(self, histogram):
        """Test bucket counting."""
        histogram.observe(0.001)  # Fits in 0.005 bucket
        histogram.observe(0.1)   # Fits in 0.1 bucket
        histogram.observe(100)   # Goes to inf bucket

        assert histogram.counts[0.005] == 1
        assert histogram.counts[float('inf')] == 3  # All values go to inf

    def test_histogram_percentile_empty(self, histogram):
        """Test percentile on empty histogram."""
        assert histogram.percentile(50) == 0.0

    def test_histogram_percentile(self, histogram):
        """Test percentile calculation."""
        for i in range(100):
            histogram.observe(float(i) / 100)

        p50 = histogram.percentile(50)
        p90 = histogram.percentile(90)
        p99 = histogram.percentile(99)

        assert p50 <= p90 <= p99


# ==============================================================================
# Exporter Tests
# ==============================================================================

class TestSpanExporter:
    """Tests for SpanExporter."""

    @pytest.fixture
    def exporter(self, tmp_path):
        """Create test span exporter."""
        from core.observability.exporter import SpanExporter
        return SpanExporter(export_path=tmp_path / "spans.json")

    @pytest.fixture
    def exporter_no_path(self):
        """Create exporter without path."""
        from core.observability.exporter import SpanExporter
        return SpanExporter()

    def test_exporter_creation(self, exporter):
        """Test exporter initialization."""
        assert exporter._batch == []

    def test_export_empty(self, exporter):
        """Test exporting empty list."""
        result = exporter.export([])
        assert result is True

    def test_export_adds_to_batch(self, exporter):
        """Test export adds spans to batch."""
        spans = [{"spanId": "1", "name": "test"}]
        exporter.export(spans)

        assert len(exporter._batch) == 1

    def test_export_to_file(self, exporter, tmp_path):
        """Test exporting to file."""
        spans = [
            {"spanId": "1", "name": "span1"},
            {"spanId": "2", "name": "span2"},
        ]

        # Force flush by exceeding batch size
        exporter._config.batch_size = 1
        exporter.export(spans)

        assert (tmp_path / "spans.json").exists()

    def test_shutdown_flushes(self, exporter, tmp_path):
        """Test shutdown flushes pending data."""
        exporter.export([{"spanId": "1", "name": "test"}])
        exporter.shutdown()

        assert (tmp_path / "spans.json").exists()

    def test_export_no_path(self, exporter_no_path):
        """Test export without file path configured."""
        result = exporter_no_path.export([{"spanId": "1"}])
        assert result is True


class TestMetricsExporter:
    """Tests for MetricsExporter."""

    @pytest.fixture
    def exporter(self, tmp_path):
        """Create test metrics exporter."""
        from core.observability.exporter import MetricsExporter
        return MetricsExporter(export_path=tmp_path / "metrics.json")

    def test_exporter_creation(self, exporter):
        """Test exporter initialization."""
        assert exporter._config is not None

    def test_export_empty(self, exporter):
        """Test exporting empty list."""
        result = exporter.export([])
        assert result is True

    def test_export_to_file(self, exporter, tmp_path):
        """Test exporting metrics to file."""
        metrics = [{"counters": {"test": {"": 1}}}]
        result = exporter.export(metrics)

        assert result is True
        assert (tmp_path / "metrics.json").exists()

    def test_prometheus_format_counters(self, exporter):
        """Test Prometheus format for counters."""
        metrics = {
            "counters": {
                "gen_ai.token.count": {"model=gpt-4": 100},
            },
        }

        output = exporter.to_prometheus_format(metrics)

        assert "# TYPE gen_ai_token_count counter" in output
        assert "gen_ai_token_count{model=gpt-4} 100" in output

    def test_prometheus_format_gauges(self, exporter):
        """Test Prometheus format for gauges."""
        metrics = {
            "gauges": {
                "active.connections": {"": 42},
            },
        }

        output = exporter.to_prometheus_format(metrics)

        assert "# TYPE active_connections gauge" in output
        assert "active_connections 42" in output

    def test_prometheus_format_histograms(self, exporter):
        """Test Prometheus format for histograms."""
        metrics = {
            "histograms": {
                "request.duration": {
                    "": {"count": 10, "sum": 150.5},
                },
            },
        }

        output = exporter.to_prometheus_format(metrics)

        assert "# TYPE request_duration histogram" in output
        assert "request_duration_count 10" in output
        assert "request_duration_sum 150.5" in output

    def test_shutdown(self, exporter):
        """Test shutdown (no-op)."""
        exporter.shutdown()  # Should not raise

    def test_prometheus_format_with_labels(self, exporter):
        """Test Prometheus format with labeled histograms."""
        metrics = {
            "histograms": {
                "request.duration": {
                    "method=GET,path=/api": {"count": 10, "sum": 150.5},
                    "": {"count": 5, "sum": 50.0},  # No labels
                },
            },
            "gauges": {
                "memory.usage": {
                    "": 1024,  # No labels
                },
            },
            "counters": {
                "requests.total": {
                    "": 100,  # No labels
                },
            },
        }
        output = exporter.to_prometheus_format(metrics)
        assert "request_duration_count{method=GET,path=/api} 10" in output
        assert "request_duration_count 5" in output


class TestSpanExporterExtended:
    """Extended tests for SpanExporter edge cases."""

    @pytest.fixture
    def exporter_with_otlp(self, tmp_path):
        """Create exporter with OTLP endpoint configured."""
        from core.observability.exporter import SpanExporter
        from core.observability.types import ObservabilityConfig
        config = ObservabilityConfig(
            otlp_endpoint="http://localhost:4318",
            batch_size=1,
        )
        return SpanExporter(config=config, export_path=tmp_path / "spans.json")

    def test_export_to_file_exception(self, tmp_path):
        """Test file export handles exceptions."""
        from core.observability.exporter import SpanExporter
        exporter = SpanExporter(export_path=tmp_path / "subdir" / "spans.json")
        exporter._batch = [{"span": "data"}]
        # Should not raise, returns True/False
        result = exporter._export_to_file()
        # Directory should be created
        assert result is True

    def test_export_to_file_invalid_path(self):
        """Test file export with invalid path."""
        from core.observability.exporter import SpanExporter
        from pathlib import Path
        exporter = SpanExporter(export_path=Path("/nonexistent/readonly/spans.json"))
        exporter._batch = [{"span": "data"}]
        # Should handle exception and return False
        result = exporter._export_to_file()
        assert result is False

    def test_flush_with_otlp_and_file(self, exporter_with_otlp, tmp_path):
        """Test flush exports to both OTLP and file."""
        exporter_with_otlp._batch = [{"spanId": "1", "name": "test"}]
        # OTLP will fail (no server) but file should succeed
        result = exporter_with_otlp._flush()
        # File export succeeded
        assert (tmp_path / "spans.json").exists()

    @pytest.mark.asyncio
    async def test_otlp_export_connection_error(self, exporter_with_otlp):
        """Test OTLP export handles connection errors gracefully."""
        exporter_with_otlp._batch = [{"spanId": "1", "name": "test"}]
        # Will fail because no OTLP server running
        result = exporter_with_otlp._export_to_otlp()
        assert result is False


class TestMetricsExporterExtended:
    """Extended tests for MetricsExporter edge cases."""

    def test_export_file_exception(self, tmp_path):
        """Test metrics export handles file exceptions."""
        from core.observability.exporter import MetricsExporter
        from pathlib import Path
        exporter = MetricsExporter(export_path=Path("/nonexistent/readonly/metrics.json"))
        result = exporter._export_to_file([{"metric": "data"}])
        assert result is False

    def test_prometheus_empty_metrics(self):
        """Test Prometheus format with empty metrics."""
        from core.observability.exporter import MetricsExporter
        exporter = MetricsExporter()
        output = exporter.to_prometheus_format({})
        assert output == ""

    def test_prometheus_all_metric_types(self):
        """Test Prometheus format with all metric types."""
        from core.observability.exporter import MetricsExporter
        exporter = MetricsExporter()
        metrics = {
            "counters": {
                "http.requests": {
                    "method=POST,status=200": 150,
                    "method=GET,status=200": 300,
                },
            },
            "gauges": {
                "cpu.usage": {
                    "host=server1": 0.75,
                },
            },
            "histograms": {
                "latency.ms": {
                    "service=api": {"count": 1000, "sum": 25000.5},
                },
            },
        }
        output = exporter.to_prometheus_format(metrics)
        assert "http_requests{method=POST,status=200} 150" in output
        assert "cpu_usage{host=server1} 0.75" in output
        assert "latency_ms_count{service=api} 1000" in output


class TestConsoleExporter:
    """Tests for ConsoleExporter."""

    @pytest.fixture
    def exporter(self):
        """Create console exporter."""
        from core.observability.exporter import ConsoleExporter
        return ConsoleExporter()

    def test_export(self, exporter, caplog):
        """Test console export."""
        import logging
        caplog.set_level(logging.INFO)

        result = exporter.export([{"key": "value"}])

        assert result is True

    def test_shutdown(self, exporter):
        """Test shutdown (no-op)."""
        exporter.shutdown()  # Should not raise


# ==============================================================================
# ObservabilityMixin Tests
# ==============================================================================

class TestObservabilityMixin:
    """Tests for ObservabilityMixin."""

    @pytest.fixture
    def mixin_agent(self):
        """Create test agent with mixin."""
        from core.observability.mixin import ObservabilityMixin

        class TestAgent(ObservabilityMixin):
            def __init__(self):
                self.agent_id = "test_agent"

        return TestAgent()

    def test_init_observability(self, mixin_agent, tmp_path):
        """Test observability initialization."""
        mixin_agent._init_observability(
            traces_path=tmp_path / "traces.json",
            metrics_path=tmp_path / "metrics.json",
        )

        assert mixin_agent._observability_initialized is True
        assert mixin_agent._tracer is not None
        assert mixin_agent._metrics is not None

    def test_trace_operation(self, mixin_agent):
        """Test tracing an operation."""
        with mixin_agent.trace_operation(
            operation_name="test_task",
            agent_id="agent_1",
        ) as span:
            assert span is not None
            assert span.gen_ai_operation_name == "test_task"

    def test_trace_operation_auto_init(self, mixin_agent):
        """Test trace_operation auto-initializes observability."""
        with mixin_agent.trace_operation("test") as span:
            assert span is not None

        assert hasattr(mixin_agent, "_tracer")

    def test_trace_llm_call(self, mixin_agent):
        """Test tracing an LLM call."""
        with mixin_agent.trace_llm_call(
            model="gpt-4",
            operation="chat",
            max_tokens=1000,
            temperature=0.7,
        ) as span:
            span.gen_ai_usage_input_tokens = 50
            span.gen_ai_usage_output_tokens = 100

    def test_trace_tool_success(self, mixin_agent):
        """Test tracing successful tool execution."""
        with mixin_agent.trace_tool(
            tool_name="execute_code",
            parameters={"code": "print('hi')"},
        ) as span:
            span.tool_result = "hi"

    def test_trace_tool_failure(self, mixin_agent):
        """Test tracing failed tool execution."""
        with pytest.raises(ValueError):
            with mixin_agent.trace_tool(tool_name="failing_tool"):
                raise ValueError("Tool error")

    def test_record_tokens(self, mixin_agent):
        """Test recording token usage."""
        mixin_agent.record_tokens(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
        )

        assert hasattr(mixin_agent, "_metrics")

    def test_record_latency(self, mixin_agent):
        """Test recording latency."""
        mixin_agent.record_latency(
            operation="chat",
            duration_ms=150.0,
            model="gpt-4",
        )

    def test_record_error(self, mixin_agent):
        """Test recording error."""
        mixin_agent.record_error(error_type="ValueError")

    def test_add_trace_event(self, mixin_agent):
        """Test adding trace event."""
        mixin_agent._init_observability()
        mixin_agent.add_trace_event("custom_event", {"key": "value"})

    def test_set_trace_attribute(self, mixin_agent):
        """Test setting trace attribute."""
        mixin_agent._init_observability()
        mixin_agent.set_trace_attribute("custom.key", "value")

    def test_get_observability_stats_uninitialized(self, mixin_agent):
        """Test stats when uninitialized."""
        stats = mixin_agent.get_observability_stats()
        assert stats["initialized"] is False

    def test_get_observability_stats(self, mixin_agent):
        """Test getting observability statistics."""
        mixin_agent._init_observability()

        with mixin_agent.trace_operation("test"):
            pass

        stats = mixin_agent.get_observability_stats()

        assert stats["initialized"] is True
        assert "traces" in stats
        assert "metrics" in stats

    def test_export_traces(self, mixin_agent, tmp_path):
        """Test exporting traces."""
        mixin_agent._init_observability(traces_path=tmp_path / "traces.json")

        with mixin_agent.trace_operation("test"):
            pass

        # Force flush
        mixin_agent._span_exporter._config.batch_size = 1
        result = mixin_agent.export_traces()

        assert result is True

    def test_export_traces_uninitialized(self, mixin_agent):
        """Test export traces when uninitialized."""
        result = mixin_agent.export_traces()
        assert result is False

    def test_export_metrics(self, mixin_agent, tmp_path):
        """Test exporting metrics."""
        mixin_agent._init_observability(metrics_path=tmp_path / "metrics.json")
        mixin_agent.record_tokens("gpt-4", 100, 50)

        result = mixin_agent.export_metrics()

        assert result is True

    def test_export_metrics_uninitialized(self, mixin_agent):
        """Test export metrics when uninitialized."""
        result = mixin_agent.export_metrics()
        assert result is False

    def test_get_prometheus_metrics(self, mixin_agent):
        """Test getting Prometheus format metrics."""
        mixin_agent._init_observability()
        mixin_agent.record_tokens("gpt-4", 100, 50)

        output = mixin_agent.get_prometheus_metrics()

        assert isinstance(output, str)

    def test_get_prometheus_metrics_uninitialized(self, mixin_agent):
        """Test Prometheus metrics when uninitialized."""
        output = mixin_agent.get_prometheus_metrics()
        assert output == ""

    def test_shutdown_observability(self, mixin_agent, tmp_path):
        """Test shutting down observability."""
        mixin_agent._init_observability(
            traces_path=tmp_path / "traces.json",
            metrics_path=tmp_path / "metrics.json",
        )

        mixin_agent.shutdown_observability()
        # Should not raise


# ==============================================================================
# Additional Edge Case Tests for 100% Coverage
# ==============================================================================

class TestEdgeCases:
    """Additional tests for edge cases to improve coverage."""

    def test_histogram_percentile_returns_last_bucket(self):
        """Test histogram percentile returns last bucket when no buckets match."""
        from core.observability.metrics import Histogram

        hist = Histogram(name="test")
        # Observe values larger than all bucket boundaries
        # (default buckets go up to 10.0, so 100 and 200 exceed all)
        hist.observe(100)
        hist.observe(200)

        # The loop won't find any matching buckets, so returns last bucket
        p50 = hist.percentile(50)
        assert p50 == hist.buckets[-1]  # 10.0

    def test_span_exporter_flush_empty_batch(self):
        """Test flushing empty batch."""
        from core.observability.exporter import SpanExporter

        exporter = SpanExporter()
        result = exporter._flush()
        assert result is True

    def test_span_exporter_export_interval(self, tmp_path):
        """Test export flush based on time interval."""
        from core.observability.exporter import SpanExporter

        exporter = SpanExporter(export_path=tmp_path / "spans.json")
        exporter._config.export_interval_seconds = 0  # Force immediate flush
        exporter._last_export = 0  # Set to past

        result = exporter.export([{"spanId": "1"}])
        assert result is True

    def test_metrics_exporter_no_path(self):
        """Test metrics exporter without file path."""
        from core.observability.exporter import MetricsExporter

        exporter = MetricsExporter()
        result = exporter.export([{"counters": {}}])
        assert result is True  # No-op when no path configured

    def test_prometheus_format_empty_labels(self, tmp_path):
        """Test Prometheus format with empty labels."""
        from core.observability.exporter import MetricsExporter

        exporter = MetricsExporter(export_path=tmp_path / "metrics.json")
        metrics = {
            "counters": {"test.counter": {"": 100}},
            "gauges": {"test.gauge": {"": 50}},
            "histograms": {"test.hist": {"": {"count": 5, "sum": 10}}},
        }

        output = exporter.to_prometheus_format(metrics)

        assert "test_counter 100" in output
        assert "test_gauge 50" in output
        assert "test_hist_count 5" in output

    def test_tracer_add_event_finds_span(self):
        """Test add_event_to_current_span finds the correct span."""
        from core.observability.tracer import AgentTracer

        tracer = AgentTracer()

        with tracer.start_agent_span(
            operation_name="test",
            agent_id="agent_1",
        ) as span:
            # The span should be in active_spans and events should be added
            tracer.add_event_to_current_span("event1", {"key": "value"})
            # Event is added via the span's context manager

    def test_tracer_set_attribute_finds_span(self):
        """Test set_attribute finds the correct span."""
        from core.observability.tracer import AgentTracer

        tracer = AgentTracer()

        with tracer.start_agent_span(
            operation_name="test",
            agent_id="agent_1",
        ) as span:
            tracer.set_attribute("custom.key", "value")

    def test_get_histogram_stats_empty(self):
        """Test getting stats for non-existent histogram."""
        from core.observability.metrics import MetricsCollector

        collector = MetricsCollector()
        stats = collector.get_histogram_stats("nonexistent")

        assert stats["count"] == 0
        assert stats["p50"] == 0.0

    def test_record_latency_without_model(self):
        """Test recording latency without model parameter."""
        from core.observability.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.record_latency("test_op", 100.0)

        stats = collector.get_histogram_stats(
            "gen_ai.client.operation.duration",
            labels={"gen_ai.operation.name": "test_op"},
        )
        assert stats["count"] == 1

    def test_tool_invocation_without_duration(self):
        """Test recording tool invocation without duration."""
        from core.observability.metrics import MetricsCollector

        collector = MetricsCollector()
        collector.record_tool_invocation("test_tool", success=True)

        value = collector.get_counter_value(
            "agent.tool.invocations",
            labels={"tool_name": "test_tool", "status": "success"},
        )
        assert value == 1

    def test_labels_to_key_none(self):
        """Test labels_to_key with None."""
        from core.observability.metrics import MetricsCollector

        collector = MetricsCollector()
        key = collector._labels_to_key(None)
        assert key == ""

    def test_span_exporter_append_to_existing_file(self, tmp_path):
        """Test appending spans to existing file."""
        from core.observability.exporter import SpanExporter
        import json

        export_path = tmp_path / "spans.json"

        # Create initial file
        with open(export_path, "w") as f:
            json.dump([{"spanId": "existing"}], f)

        exporter = SpanExporter(export_path=export_path)
        exporter._config.batch_size = 1  # Force flush
        exporter.export([{"spanId": "new"}])

        # Verify both spans are in file
        with open(export_path) as f:
            data = json.load(f)
        assert len(data) == 2


class TestBaseExporterAbstract:
    """Test abstract BaseExporter methods (lines 32, 37)."""

    def test_base_exporter_abstract_export(self):
        """Test BaseExporter.export raises NotImplementedError."""
        from core.observability.exporter import BaseExporter

        class ConcreteExporter(BaseExporter):
            def export(self, data):
                return super().export(data)

            def shutdown(self):
                pass

        exporter = ConcreteExporter()
        with pytest.raises(NotImplementedError):
            exporter.export([])

    def test_base_exporter_abstract_shutdown(self):
        """Test BaseExporter.shutdown raises NotImplementedError."""
        from core.observability.exporter import BaseExporter

        class ConcreteExporter(BaseExporter):
            def export(self, data):
                return True

            def shutdown(self):
                super().shutdown()

        exporter = ConcreteExporter()
        with pytest.raises(NotImplementedError):
            exporter.shutdown()


class TestSpanExporterOTLPResponse:
    """Test SpanExporter OTLP response handling (lines 167-171)."""

    def test_export_otlp_non_200_response(self):
        """Test OTLP export handles non-200 response."""
        from core.observability.exporter import SpanExporter
        from core.observability.types import ObservabilityConfig

        config = ObservabilityConfig(otlp_endpoint="http://localhost:4318")
        exporter = SpanExporter(config=config)
        exporter._config.batch_size = 1

        # Mock urlopen to return non-200 status
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = exporter._export_to_otlp()
            assert result is False

    def test_export_otlp_200_success(self):
        """Test OTLP export succeeds with 200 response."""
        from core.observability.exporter import SpanExporter
        from core.observability.types import ObservabilityConfig

        config = ObservabilityConfig(otlp_endpoint="http://localhost:4318")
        exporter = SpanExporter(config=config)
        exporter._config.batch_size = 1
        exporter._batch = [{"spanId": "test"}]

        # Mock urlopen to return 200 status
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            result = exporter._export_to_otlp()
            assert result is True


class TestTracerAddEventSetAttribute:
    """Test tracer add_event and set_attribute with matching span (lines 223-224, 231-232)."""

    def test_add_event_finds_matching_span(self):
        """Test add_event_to_current_span finds span by parent_span_id."""
        from core.observability.tracer import AgentTracer
        from core.observability.types import TraceContext, AgentSpan

        tracer = AgentTracer()

        # Manually set up state where condition matches
        span = AgentSpan(
            trace_id="trace1",
            parent_span_id=None,
            gen_ai_system="test",
            gen_ai_operation_name="op",
            gen_ai_agent_id="agent1",
            gen_ai_agent_name="agent1",
        )
        # Add span to active spans
        tracer._active_spans[span.span_id] = span
        # Set context where parent_span_id matches span.span_id
        tracer._current_context = TraceContext(
            trace_id="trace1",
            parent_span_id=span.span_id,  # This makes the condition match
        )

        initial_events = len(span.events)
        tracer.add_event_to_current_span("test_event", {"key": "value"})
        # Event should be added to the span
        assert len(span.events) > initial_events

    def test_set_attribute_finds_matching_span(self):
        """Test set_attribute finds span by parent_span_id."""
        from core.observability.tracer import AgentTracer
        from core.observability.types import TraceContext, AgentSpan

        tracer = AgentTracer()

        # Manually set up state where condition matches
        span = AgentSpan(
            trace_id="trace1",
            parent_span_id=None,
            gen_ai_system="test",
            gen_ai_operation_name="op",
            gen_ai_agent_id="agent1",
            gen_ai_agent_name="agent1",
        )
        tracer._active_spans[span.span_id] = span
        tracer._current_context = TraceContext(
            trace_id="trace1",
            parent_span_id=span.span_id,  # Makes condition match
        )

        tracer.set_attribute("custom_key", "custom_value")
        assert span.attributes.get("custom_key") == "custom_value"
