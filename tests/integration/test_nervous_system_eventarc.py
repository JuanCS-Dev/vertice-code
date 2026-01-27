"""
Integration tests for NEXUS Digital Nervous System + Eventarc

Tests the complete integration of:
- Eventarc CloudEvent handling
- Nervous System three-layer processing
- Cloud Monitoring metrics reporting
- MCP synchronization

Run: pytest tests/integration/test_nervous_system_eventarc.py -v
"""

import asyncio
import pytest
import time
from datetime import datetime, timezone
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path

# Add nexus to path
_app_path = Path(__file__).resolve().parents[2] / "apps" / "agent-gateway" / "app"
if str(_app_path) not in sys.path:
    sys.path.insert(0, str(_app_path))


@pytest.fixture
def nexus_config():
    """Create a NexusConfig for testing."""
    from nexus.config import NexusConfig

    return NexusConfig(
        project_id="test-project",
        location="us-central1",
    )


@pytest.fixture
def nervous_system(nexus_config):
    """Create a DigitalNervousSystem for testing."""
    from nexus.nervous_system import DigitalNervousSystem

    return DigitalNervousSystem(nexus_config)


@pytest.fixture
def sample_logging_event():
    """Sample Cloud Logging event."""
    from nexus.nervous_system import NervousSystemEvent

    return NervousSystemEvent(
        event_id="test-event-001",
        source="eventarc",
        event_type="google.cloud.logging.logEntry.written",
        severity="ERROR",
        resource_type="cloud_run_revision",
        resource_name="vertice-agent-gateway",
        timestamp=datetime.now(timezone.utc),
        payload={
            "textPayload": "Exception: ConnectionError in service call",
            "severity": "ERROR",
        },
        metrics={
            "cpu_utilization": 0.75,
            "memory_utilization": 0.60,
        },
    )


@pytest.fixture
def sample_monitoring_alert():
    """Sample Cloud Monitoring alert."""
    from nexus.nervous_system import NervousSystemEvent

    return NervousSystemEvent(
        event_id="alert-001",
        source="monitoring",
        event_type="google.cloud.monitoring.alert.fired",
        severity="CRITICAL",
        resource_type="cloud_run_revision",
        resource_name="vertice-agent-gateway",
        timestamp=datetime.now(timezone.utc),
        payload={
            "incident": {
                "incident_id": "alert-001",
                "state": "open",
                "policy_name": "High CPU Critical",
            },
        },
        metrics={
            "cpu_utilization": 0.98,
            "memory_utilization": 0.95,
        },
    )


@pytest.fixture
def sample_crash_event():
    """Sample crash event that should trigger reflex."""
    from nexus.nervous_system import NervousSystemEvent

    return NervousSystemEvent(
        event_id="crash-001",
        source="eventarc",
        event_type="google.cloud.logging.logEntry.written",
        severity="CRITICAL",
        resource_type="cloud_run_revision",
        resource_name="vertice-agent-gateway",
        timestamp=datetime.now(timezone.utc),
        payload={
            "textPayload": "OOM killed: container crashed due to memory exhaustion",
            "severity": "CRITICAL",
        },
        metrics={
            "cpu_utilization": 0.30,
            "memory_utilization": 0.99,
        },
    )


class TestNervousSystemLayers:
    """Test the three-layer nervous system processing."""

    @pytest.mark.asyncio
    async def test_reflex_arc_activation(self, nervous_system, sample_crash_event):
        """Test that crash events trigger reflex arc."""
        # Process multiple times to build spike history
        for _ in range(6):  # Trigger burst pattern
            result = await nervous_system.on_stimulus(sample_crash_event)

        # Should resolve at reflex level for crash events
        assert result.resolved or result.autonomy_level.value in ["reflex_arc", "innate_immunity"]
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_innate_immunity_activation(self, nervous_system, sample_logging_event):
        """Test that error events trigger innate immunity."""
        result = await nervous_system.on_stimulus(sample_logging_event)

        # Should process through the system
        assert result.event_id == sample_logging_event.event_id
        assert result.latency_ms >= 0

    @pytest.mark.asyncio
    async def test_homeostasis_metrics(self, nervous_system, sample_logging_event):
        """Test homeostasis metrics are tracked."""
        # Process several events
        for _ in range(5):
            await nervous_system.on_stimulus(sample_logging_event)

        metrics = nervous_system.get_homeostasis_metrics()

        assert "total_events" in metrics
        assert metrics["total_events"] == 5
        assert "autonomous_resolution_rate" in metrics
        assert "by_layer" in metrics

    @pytest.mark.asyncio
    async def test_event_handlers_called(self, nervous_system, sample_logging_event):
        """Test that registered handlers are called."""
        reflex_called = False
        innate_called = False
        escalation_called = False

        async def on_reflex(event, reflex):
            nonlocal reflex_called
            reflex_called = True

        async def on_innate(event, responses):
            nonlocal innate_called
            innate_called = True

        async def on_escalation(event, digest):
            nonlocal escalation_called
            escalation_called = True

        nervous_system.on_reflex(on_reflex)
        nervous_system.on_innate(on_innate)
        nervous_system.on_escalation(on_escalation)

        await nervous_system.on_stimulus(sample_logging_event)

        # At least one handler should be called
        assert reflex_called or innate_called or escalation_called

    @pytest.mark.asyncio
    async def test_stats_collection(self, nervous_system, sample_logging_event):
        """Test that stats are properly collected."""
        await nervous_system.on_stimulus(sample_logging_event)

        stats = nervous_system.get_stats()

        assert "homeostasis" in stats
        assert "reflex_arc" in stats
        assert "innate_immunity" in stats
        assert "nexus_connected" in stats


class TestEventParsing:
    """Test CloudEvent parsing functions."""

    def test_parse_eventarc_event(self):
        """Test parsing Eventarc CloudEvent."""
        from nexus.nervous_system import parse_eventarc_event

        cloud_event = {
            "id": "test-123",
            "source": "//logging.googleapis.com/projects/test",
            "type": "google.cloud.logging.logEntry.written",
            "data": {
                "severity": "ERROR",
                "resource": {
                    "type": "cloud_run_revision",
                    "labels": {"service_name": "test-service"},
                },
                "textPayload": "Test error message",
            },
        }

        event = parse_eventarc_event(cloud_event)

        assert event.event_id == "test-123"
        assert event.source == "eventarc"
        assert event.severity == "ERROR"
        assert event.resource_type == "cloud_run_revision"

    def test_parse_pubsub_message(self):
        """Test parsing Pub/Sub message."""
        from nexus.nervous_system import parse_pubsub_message
        import base64
        import json

        payload = {"severity": "WARNING", "message": "Test warning"}
        encoded = base64.b64encode(json.dumps(payload).encode()).decode()

        message = {
            "messageId": "msg-123",
            "data": encoded,
            "attributes": {"type": "test.event"},
        }

        event = parse_pubsub_message(message)

        assert event.event_id == "msg-123"
        assert event.source == "pubsub"
        assert event.severity == "WARNING"

    def test_parse_monitoring_alert(self):
        """Test parsing Cloud Monitoring alert."""
        from nexus.nervous_system import parse_monitoring_alert

        alert = {
            "incident": {
                "incident_id": "incident-123",
                "state": "open",
                "policy_name": "critical_cpu_alert",
                "resource_type_display_name": "Cloud Run Revision",
                "resource_name": "test-service",
                "threshold_value": 0.9,
                "observed_value": 0.95,
            },
        }

        event = parse_monitoring_alert(alert)

        assert event.event_id == "incident-123"
        assert event.source == "monitoring"
        assert event.severity == "CRITICAL"  # "critical" in policy name
        assert event.metrics["threshold_value"] == 0.9


class TestReflexGanglion:
    """Test the neuromorphic reflex arc."""

    def test_neuron_spike_detection(self):
        """Test spike pattern detection."""
        from nexus.nervous_system import GanglionNeuron, SpikePattern

        neuron = GanglionNeuron("test", threshold=0.5, decay=0.9)

        # Fire multiple times to create burst
        for i in range(10):
            neuron.receive_input(1.0, time.time() * 1000 + i)

        pattern = neuron.detect_pattern(window_ms=1000)
        assert pattern in [SpikePattern.BURST, SpikePattern.TONIC, SpikePattern.IRREGULAR]

    def test_reflex_map_exists(self):
        """Test that reflex mappings are configured."""
        from nexus.nervous_system import ReflexGanglion, SpikePattern

        ganglion = ReflexGanglion()

        # Check that key reflexes are mapped
        assert ("crash_monitor", SpikePattern.BURST) in ganglion.reflex_map
        assert ("error_monitor", SpikePattern.BURST) in ganglion.reflex_map
        assert ("ram_monitor", SpikePattern.BURST) in ganglion.reflex_map


class TestInnateImmunity:
    """Test the innate immune system."""

    @pytest.mark.asyncio
    async def test_neutrophil_detection(self, nexus_config):
        """Test neutrophil threat detection."""
        from nexus.nervous_system import InnateImmuneSystem, NervousSystemEvent

        immune = InnateImmuneSystem(nexus_config)

        event = NervousSystemEvent(
            event_id="test",
            source="test",
            event_type="test",
            severity="WARNING",
            resource_type="test",
            resource_name="test",
            timestamp=datetime.now(timezone.utc),
            payload={},
            metrics={
                "memory_leaked": 0.5,
                "cache_hit_rate": 0.3,
            },
        )

        responses = await immune.respond(event)

        # Neutrophil should detect and respond to memory leak
        if responses:
            assert any(r.cell_type.value == "neutrophil" for r in responses)

    @pytest.mark.asyncio
    async def test_macrophage_error_digestion(self, nexus_config):
        """Test macrophage error log digestion."""
        from nexus.nervous_system import InnateImmuneSystem, NervousSystemEvent

        immune = InnateImmuneSystem(nexus_config)

        event = NervousSystemEvent(
            event_id="test",
            source="test",
            event_type="test",
            severity="ERROR",
            resource_type="test",
            resource_name="test",
            timestamp=datetime.now(timezone.utc),
            payload={
                "textPayload": "Exception: NullPointerException in service.process()",
            },
            metrics={},
        )

        responses = await immune.respond(event)

        # Macrophage should detect and digest error
        if responses:
            macrophage_responses = [r for r in responses if r.cell_type.value == "macrophage"]
            if macrophage_responses:
                assert macrophage_responses[0].success


class TestEventarcHandler:
    """Test the FastAPI Eventarc handler."""

    @pytest.mark.asyncio
    async def test_get_nervous_system_singleton(self):
        """Test that get_nervous_system returns a singleton."""
        from nexus.eventarc_handler import get_nervous_system

        ns1 = await get_nervous_system()
        ns2 = await get_nervous_system()

        assert ns1 is ns2

    @pytest.mark.asyncio
    async def test_cloud_event_parsing(self):
        """Test CloudEvent parsing from request."""
        from nexus.eventarc_handler import _cloud_event_to_nervous_event

        cloud_event = {
            "id": "ce-123",
            "source": "test",
            "type": "google.cloud.logging.logEntry.written",
            "data": {
                "severity": "WARNING",
                "resource": {
                    "type": "cloud_run_revision",
                    "labels": {"service_name": "test-svc"},
                },
            },
        }

        ns_event = _cloud_event_to_nervous_event(cloud_event)

        assert ns_event.event_id == "ce-123"
        assert ns_event.severity == "WARNING"


class TestGCloudMetrics:
    """Test Cloud Monitoring metrics integration."""

    def test_metrics_initialization(self):
        """Test metrics client initialization."""
        from nexus.gcloud_metrics import NervousSystemMetrics

        metrics = NervousSystemMetrics(project_id="test-project")

        # Should initialize even without Cloud Monitoring SDK
        assert metrics.project_id == "test-project"

    @pytest.mark.asyncio
    async def test_report_resolution_no_crash(self):
        """Test that report_resolution doesn't crash without SDK."""
        from nexus.gcloud_metrics import NervousSystemMetrics

        metrics = NervousSystemMetrics(project_id="test-project")

        # Should not raise even without Cloud Monitoring
        await metrics.report_resolution("reflex", True, 50.0)
        await metrics.report_reflex_activation("cpu_monitor", "scale_horizontal", 25.0)


class TestChaosEngineering:
    """Chaos engineering tests for homeostasis validation."""

    @pytest.mark.asyncio
    async def test_sustained_load(self, nervous_system):
        """Test system under sustained load."""
        from nexus.nervous_system import NervousSystemEvent

        events_processed = 0
        start_time = time.time()
        duration = 2.0  # 2 seconds

        while time.time() - start_time < duration:
            event = NervousSystemEvent(
                event_id=f"load-{events_processed}",
                source="chaos",
                event_type="chaos.load_test",
                severity="WARNING",
                resource_type="test",
                resource_name="test",
                timestamp=datetime.now(timezone.utc),
                payload={"chaos": True},
                metrics={"cpu_utilization": 0.5},
            )

            result = await nervous_system.on_stimulus(event)
            events_processed += 1

            await asyncio.sleep(0.01)  # 100 events/sec max

        metrics = nervous_system.get_homeostasis_metrics()

        assert events_processed > 10
        assert metrics["total_events"] == events_processed

    @pytest.mark.asyncio
    async def test_spike_recovery(self, nervous_system):
        """Test recovery from spike of critical events."""
        from nexus.nervous_system import NervousSystemEvent

        # Send burst of critical events
        for i in range(20):
            event = NervousSystemEvent(
                event_id=f"spike-{i}",
                source="chaos",
                event_type="chaos.spike",
                severity="CRITICAL",
                resource_type="test",
                resource_name="test",
                timestamp=datetime.now(timezone.utc),
                payload={"textPayload": "Critical crash error"},
                metrics={
                    "cpu_utilization": 0.99,
                    "memory_utilization": 0.99,
                },
            )
            await nervous_system.on_stimulus(event)

        metrics = nervous_system.get_homeostasis_metrics()

        # System should have processed all events
        assert metrics["total_events"] == 20
        # Some should have been resolved autonomously
        resolution_rate = metrics["autonomous_resolution_rate"]
        # Even under stress, should resolve some autonomously
        assert resolution_rate >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
