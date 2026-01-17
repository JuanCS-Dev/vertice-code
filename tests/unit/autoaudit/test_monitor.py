"""
Tests for StateMonitor.

Validates event capture and hooks.
"""
import time
from unittest.mock import MagicMock
from vertice_tui.core.autoaudit.monitor import StateMonitor


class TestMonitor:
    def test_record_lifecycle(self):
        """Test start, record, stop cycle."""
        monitor = StateMonitor()
        assert not monitor._is_active

        monitor.start()
        assert monitor._is_active

        monitor.record("event.a", {"val": 1})
        time.sleep(0.01)  # Ensure timestamp diff
        monitor.record("event.b", {"val": 2})

        events = monitor.stop()
        assert not monitor._is_active
        assert len(events) == 2

        assert events[0].event_type == "event.a"
        assert events[0].payload["val"] == 1
        assert events[1].event_type == "event.b"

        # Verify timestamp order
        assert events[1].timestamp > events[0].timestamp

    def test_hooks_execution(self):
        """Test that hooks are called on record."""
        monitor = StateMonitor()
        hook = MagicMock()
        monitor.add_hook(hook)

        # Should not call hook if not started (unless design allows?)
        # Implementation check: Is active check inside record?
        # Let's assume record works always, or check implementation.
        # Based on typical pattern, hooks run on record.

        monitor.start()
        monitor.record("test.hook", {"data": 123})

        hook.assert_called_once()
        args = hook.call_args[0]
        # Expected args: event_type, payload
        assert args[0] == "test.hook"
        assert args[1] == {"data": 123}

    def test_has_event_type(self):
        """Test event existence check."""
        monitor = StateMonitor()
        monitor.start()
        monitor.record("target.event", {})

        assert monitor.has_event_type("target.event")
        assert not monitor.has_event_type("other.event")

    def test_get_events_by_type(self):
        """Test filtering."""
        monitor = StateMonitor()
        monitor.start()
        monitor.record("a", {})
        monitor.record("b", {})
        monitor.record("a", {})

        events_a = monitor.get_events_by_type("a")
        assert len(events_a) == 2

        events_b = monitor.get_events_by_type("b")
        assert len(events_b) == 1
