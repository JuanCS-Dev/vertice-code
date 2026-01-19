"""
Test Prometheus Event Bus Integration.

Verifies that PrometheusOrchestrator emits events correctly.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from prometheus.core.events import (
    PrometheusTaskReceived,
    PrometheusTaskCompleted,
    PrometheusTaskFailed,
)
from prometheus.core.orchestrator import PrometheusOrchestrator
from vertice_core.messaging.events import EventBus


@pytest.mark.asyncio
async def test_orchestrator_emits_start_and_complete_fast_mode():
    """Test event emission in fast mode."""
    # Setup
    mock_llm = AsyncMock()
    mock_llm.generate.return_value = "Mock Output"

    mock_bus = MagicMock(spec=EventBus)
    mock_bus.emit_sync = MagicMock()

    orchestrator = PrometheusOrchestrator(llm_client=mock_llm, event_bus=mock_bus)

    # Execute
    task = "Test Task"
    async for _ in orchestrator.execute(task, fast_mode=True):
        pass

    # Verify Start Event
    assert mock_bus.emit_sync.call_count >= 2  # Start + Complete

    # Check first call (Start)
    start_call = mock_bus.emit_sync.call_args_list[0]
    event = start_call[0][0]
    assert isinstance(event, PrometheusTaskReceived)
    assert event.data["request"] == task
    assert event.data["complexity"] == "simple"

    # Check last call (Complete)
    complete_call = mock_bus.emit_sync.call_args_list[-1]
    event = complete_call[0][0]
    assert isinstance(event, PrometheusTaskCompleted)
    assert event.data["result"] == "Mock Output"


@pytest.mark.asyncio
async def test_orchestrator_emits_failure():
    """Test event emission on failure."""
    # Setup
    mock_llm = AsyncMock()
    # Mocking internal method to fail
    orchestrator = PrometheusOrchestrator(llm_client=mock_llm, event_bus=MagicMock(spec=EventBus))
    # Force failure by mocking _execute_task_with_context
    orchestrator._execute_task_with_context = AsyncMock(side_effect=ValueError("Boom"))

    # Execute
    with pytest.raises(ValueError):
        async for _ in orchestrator.execute("Test", fast_mode=True):
            pass

    # Verify Failure Event
    mock_bus = orchestrator.event_bus
    # Should have Start + Fail
    failure_call = mock_bus.emit_sync.call_args_list[-1]
    event = failure_call[0][0]
    assert isinstance(event, PrometheusTaskFailed)
    assert event.data["error"] == "Boom"
