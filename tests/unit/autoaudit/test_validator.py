"""
Tests for ScenarioValidator.

Scientific validation of audit expectations logic.
"""
import pytest
from unittest.mock import MagicMock

from vertice_tui.core.autoaudit.validator import ScenarioValidator
from vertice_tui.core.autoaudit.scenarios import Expectation
from vertice_tui.core.autoaudit.monitor import EventTrace


@pytest.fixture
def mock_monitor():
    """Mock StateMonitor."""
    return MagicMock()


def create_event(type: str, payload: dict = None) -> EventTrace:
    """Helper to create fake events."""
    return EventTrace(timestamp=0.0, event_type=type, payload=payload or {})


class TestScenarioValidator:
    def test_has_response(self, mock_monitor):
        """Expectation.HAS_RESPONSE requires >0 events."""
        # Case 1: Empty events -> Fail
        res = ScenarioValidator.validate([Expectation.HAS_RESPONSE], [], 1.0, mock_monitor)
        assert res[Expectation.HAS_RESPONSE.value] is False

        # Case 2: One event -> Pass
        events = [create_event("any")]
        res = ScenarioValidator.validate([Expectation.HAS_RESPONSE], events, 1.0, mock_monitor)
        assert res[Expectation.HAS_RESPONSE.value] is True

    def test_latency_checks(self, mock_monitor):
        """Latency checks."""
        # < 5s
        res = ScenarioValidator.validate([Expectation.LATENCY_UNDER_5S], [], 4.9, mock_monitor)
        assert res[Expectation.LATENCY_UNDER_5S.value] is True
        res = ScenarioValidator.validate([Expectation.LATENCY_UNDER_5S], [], 5.1, mock_monitor)
        assert res[Expectation.LATENCY_UNDER_5S.value] is False

        # < 10s
        res = ScenarioValidator.validate([Expectation.LATENCY_UNDER_10S], [], 9.9, mock_monitor)
        assert res[Expectation.LATENCY_UNDER_10S.value] is True
        res = ScenarioValidator.validate([Expectation.LATENCY_UNDER_10S], [], 10.1, mock_monitor)
        assert res[Expectation.LATENCY_UNDER_10S.value] is False

    def test_sse_events_complete(self, mock_monitor):
        """Depends on monitor query."""
        mock_monitor.has_event_type.return_value = True
        res = ScenarioValidator.validate([Expectation.SSE_EVENTS_COMPLETE], [], 1.0, mock_monitor)
        assert res[Expectation.SSE_EVENTS_COMPLETE.value] is True
        mock_monitor.has_event_type.assert_called_with("response.completed")

        mock_monitor.has_event_type.return_value = False
        res = ScenarioValidator.validate([Expectation.SSE_EVENTS_COMPLETE], [], 1.0, mock_monitor)
        assert res[Expectation.SSE_EVENTS_COMPLETE.value] is False

    def test_tool_use_file_read(self, mock_monitor):
        """Detect read_file usage."""
        # Pass
        events = [create_event("tool_call", {"tool_name": "read_file"})]
        res = ScenarioValidator.validate(
            [Expectation.TOOL_USE_FILE_READ], events, 1.0, mock_monitor
        )
        assert res[Expectation.TOOL_USE_FILE_READ.value] is True

        # Pass (alternative name)
        events = [create_event("tool_call", {"tool_name": "read_file_content"})]
        res = ScenarioValidator.validate(
            [Expectation.TOOL_USE_FILE_READ], events, 1.0, mock_monitor
        )
        assert res[Expectation.TOOL_USE_FILE_READ.value] is True

        # Fail (wrong tool)
        events = [create_event("tool_call", {"tool_name": "other_tool"})]
        res = ScenarioValidator.validate(
            [Expectation.TOOL_USE_FILE_READ], events, 1.0, mock_monitor
        )
        assert res[Expectation.TOOL_USE_FILE_READ.value] is False

        # Fail (no tool calls)
        res = ScenarioValidator.validate([Expectation.TOOL_USE_FILE_READ], [], 1.0, mock_monitor)
        assert res[Expectation.TOOL_USE_FILE_READ.value] is False

    def test_tool_use_bash(self, mock_monitor):
        """Detect run_command usage."""
        # Pass
        events = [create_event("tool_call", {"tool_name": "run_command"})]
        res = ScenarioValidator.validate([Expectation.TOOL_USE_BASH], events, 1.0, mock_monitor)
        assert res[Expectation.TOOL_USE_BASH.value] is True

        # Fail
        events = [create_event("tool_call", {"tool_name": "read_file"})]
        res = ScenarioValidator.validate([Expectation.TOOL_USE_BASH], events, 1.0, mock_monitor)
        assert res[Expectation.TOOL_USE_BASH.value] is False

    def test_dangerous_action(self, mock_monitor):
        """Block rm -rf."""
        # Safe
        events = [create_event("tool_call", {"tool_name": "run_command", "args": "ls -la"})]
        res = ScenarioValidator.validate(
            [Expectation.NO_DANGEROUS_ACTION], events, 1.0, mock_monitor
        )
        assert res[Expectation.NO_DANGEROUS_ACTION.value] is True

        # Dangerous
        events = [create_event("tool_call", {"tool_name": "run_command", "args": "rm -rf /"})]
        res = ScenarioValidator.validate(
            [Expectation.NO_DANGEROUS_ACTION], events, 1.0, mock_monitor
        )
        assert res[Expectation.NO_DANGEROUS_ACTION.value] is False

    def test_failure_reason(self):
        """Format failure message."""
        validations = {"check1": True, "check2": False, "check3": False}
        msg = ScenarioValidator.failure_reason(validations)
        assert "Falhou: check2, check3" in msg
