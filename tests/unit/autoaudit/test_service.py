"""
Tests for AutoAuditService.

Orchestration logic validation with mocks.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from vertice_tui.core.autoaudit.service import AutoAuditService
from vertice_tui.core.autoaudit.scenarios import AuditScenario, ScenarioCategory, Expectation


@pytest.fixture
def mock_app():
    app = MagicMock()
    app.router = MagicMock()
    app.router.dispatch = AsyncMock()
    app._handle_chat = AsyncMock()
    app.bridge = MagicMock()
    app.bridge.agents.available_agents = []
    app.bridge.tools.get_tool_count.return_value = 0
    app.bridge.history.get_context.return_value = []
    return app


@pytest.fixture
def mock_view():
    return MagicMock()


@pytest.fixture
def basic_scenario():
    return AuditScenario(
        id="test_001",
        category=ScenarioCategory.TOOLS,
        prompt="/test",
        expectations=[Expectation.HAS_RESPONSE],
        description="Test Scenario",
        timeout_seconds=0.1,
    )


@pytest.fixture
def service(mock_app, mock_view, basic_scenario):
    return AutoAuditService(mock_app, mock_view, [basic_scenario])


@pytest.mark.asyncio
async def test_successful_execution(service):
    """Test standard execution flow."""
    # Mock Validator to return success
    with patch("vertice_tui.core.autoaudit.service.ScenarioValidator") as MockVal:
        MockVal.validate.return_value = {Expectation.HAS_RESPONSE.value: True}

        report = await service.run()

        assert report is not None
        assert report.total_scenarios == 1
        assert report.passed == 1
        assert report.failed == 0
        assert report.success_rate == 100.0

        # Verify monitoring started/stopped
        # Note: can't easily check monitor calls as monitor is instantiated inside init,
        # but we can check if router was called since prompt starts with /
        service.app.router.dispatch.assert_called_once()


@pytest.mark.asyncio
async def test_failure_execution(service):
    """Test scenario failure."""
    with patch("vertice_tui.core.autoaudit.service.ScenarioValidator") as MockVal:
        # Validator returns False
        MockVal.validate.return_value = {Expectation.HAS_RESPONSE.value: False}
        MockVal.failure_reason.return_value = "No response"

        report = await service.run()

        assert report.passed == 0
        assert report.failed == 1
        assert report.results[0].error_message == "No response"


@pytest.mark.asyncio
async def test_timeout_handling(service):
    """Test timeout logic."""
    # Make scenario shorter
    service.scenarios[0].timeout_seconds = 0.01

    # Make handler slower
    async def slow(*args):
        await asyncio.sleep(0.05)

    service.app.router.dispatch = slow  # Because prompt is /test

    with patch("vertice_tui.core.autoaudit.service.ScenarioValidator"):
        report = await service.run()

        assert report.failed == 1
        assert "Timeout" in report.results[0].error_message


@pytest.mark.asyncio
async def test_critical_error_handling(service):
    """Test unhandled exception."""
    service.app.router.dispatch.side_effect = Exception("Boom")

    report = await service.run()

    assert report.critical_errors == 1
    assert "Boom" in report.results[0].error_message
    assert report.results[0].status == "CRITICAL_ERROR"


@pytest.mark.asyncio
async def test_vertex_diagnostic_routing(service):
    """Test special diagnostic routing."""
    service.scenarios[0].prompt = "__VERTEX_AI_DIAGNOSTIC__"

    # Mock _run_vertex_diagnostic
    # Since it's a method on self, we need to patch it on the instance or class
    with patch.object(service, "_run_vertex_diagnostic", new_callable=AsyncMock) as mock_diag:
        mock_diag.return_value = MagicMock(status="SUCCESS", latency_ms=10)

        await service.run()

        mock_diag.assert_called_once()
