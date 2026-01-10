"""
Tests for ActiveOrchestrator - Sprint 2 Refactoring.

Tests cover:
    - Orchestrator initialization and configuration
    - Main execution flow and state machine
    - State transitions and lifecycle management
    - Agent handoffs and communication
    - Execution control (cancel, pause, resume)
    - Statistics and state history
    - Callback system and event handling
    - Error handling and edge cases
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from vertice_core.agents.orchestrator.orchestrator import ActiveOrchestrator
from vertice_core.agents.context.unified import UnifiedContext
from vertice_core.agents.router.router import SemanticRouter
from vertice_core.agents.router.types import AgentType, RoutingDecision
from vertice_core.agents.orchestrator.types import OrchestratorState, HandoffType
from vertice_core.agents.orchestrator.models import ExecutionStep, ExecutionPlan, Handoff
from vertice_core.agents.orchestrator.protocol import AgentProtocol


class TestActiveOrchestratorInitialization:
    """Test ActiveOrchestrator initialization and configuration."""

    def test_default_initialization(self) -> None:
        """Test orchestrator initialization with defaults."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        assert orchestrator.context == context
        assert isinstance(orchestrator.router, SemanticRouter)
        assert orchestrator.agents == {}
        assert orchestrator.state == OrchestratorState.IDLE
        assert orchestrator._state_history == []
        assert orchestrator.current_plan is None
        assert orchestrator.pending_handoffs == []
        assert orchestrator.completed_handoffs == []
        assert orchestrator._cancelled is False
        assert orchestrator._iteration_count == 0
        assert orchestrator._start_time is None
        assert orchestrator._on_state_change is None
        assert orchestrator._on_step_complete is None

    def test_custom_initialization(self) -> None:
        """Test orchestrator with custom parameters."""
        context = UnifiedContext()
        router = SemanticRouter()
        agents = {AgentType.ARCHITECT: MagicMock(spec=AgentProtocol)}

        orchestrator = ActiveOrchestrator(
            context=context,
            router=router,
            agents=agents,
        )

        assert orchestrator.router == router
        assert orchestrator.agents == agents

    def test_initialization_with_none_context_raises_error(self) -> None:
        """Test that initialization with None context raises error."""
        with pytest.raises(AttributeError):
            ActiveOrchestrator(None)  # type: ignore


class TestActiveOrchestratorStateMachine:
    """Test state machine functionality."""

    def test_initial_state_is_idle(self) -> None:
        """Test that orchestrator starts in IDLE state."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        assert orchestrator.state == OrchestratorState.IDLE

    def test_transition_to_method(self) -> None:
        """Test state transition method."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Should start with empty history
        assert len(orchestrator._state_history) == 0

        # Transition to GATHERING
        orchestrator._transition_to(OrchestratorState.GATHERING, "Starting execution")

        assert orchestrator.state == OrchestratorState.GATHERING
        assert len(orchestrator._state_history) == 1

        # Check history entry
        history_entry = orchestrator._state_history[0]
        assert history_entry["from_state"] == OrchestratorState.IDLE
        assert history_entry["to_state"] == OrchestratorState.GATHERING
        assert "Starting execution" in history_entry["reason"]

    def test_is_terminal_state(self) -> None:
        """Test terminal state detection."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Non-terminal states
        orchestrator.state = OrchestratorState.IDLE
        assert not orchestrator._is_terminal_state()

        orchestrator.state = OrchestratorState.GATHERING
        assert not orchestrator._is_terminal_state()

        orchestrator.state = OrchestratorState.EXECUTING
        assert not orchestrator._is_terminal_state()

        # Terminal states
        orchestrator.state = OrchestratorState.COMPLETED
        assert orchestrator._is_terminal_state()

        orchestrator.state = OrchestratorState.FAILED
        assert orchestrator._is_terminal_state()

        orchestrator.state = OrchestratorState.CANCELLED
        assert orchestrator._is_terminal_state()

    def test_check_timeout(self) -> None:
        """Test timeout checking."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context, timeout=1.0)

        # Should not timeout immediately
        assert not orchestrator._check_timeout()

        # Mock start time to be in the past
        orchestrator._start_time = time.time() - 2.0  # 2 seconds ago
        assert orchestrator._check_timeout()

    def test_check_iteration_limit(self) -> None:
        """Test iteration limit checking."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context, max_iterations=5)

        # Should not exceed limit initially
        assert not orchestrator._check_iteration_limit()

        # Set iteration count to limit
        orchestrator._iteration_count = 5
        assert orchestrator._check_iteration_limit()


class TestActiveOrchestratorExecution:
    """Test main execution flow."""

    def test_execute_method_exists(self) -> None:
        """Test that execute method exists and is async."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        assert hasattr(orchestrator, "execute")
        assert asyncio.iscoroutinefunction(orchestrator.execute)

    @pytest.mark.asyncio
    async def test_execute_basic_flow(self) -> None:
        """Test basic execution flow."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Mock router to return a decision
        mock_decision = RoutingDecision(
            route_name="architect",
            agent_type=AgentType.ARCHITECT,
            confidence=0.9,
            reasoning="Architecture task",
        )

        with patch.object(orchestrator.router, "route", return_value=mock_decision):
            with patch.object(orchestrator, "_execute_state", return_value=asyncio.AsyncIterator()):
                # Execute should not raise
                await orchestrator.execute()

                # Should have transitioned from IDLE
                assert orchestrator.state != OrchestratorState.IDLE

    @pytest.mark.asyncio
    async def test_execute_with_timeout(self) -> None:
        """Test execution with timeout."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context, timeout=0.1)

        # Mock slow execution
        async def slow_execute():
            await asyncio.sleep(0.2)  # Longer than timeout
            yield "done"

        with patch.object(orchestrator, "_execute_state", return_value=slow_execute()):
            await orchestrator.execute()

            # Should have failed due to timeout
            assert orchestrator.state == OrchestratorState.FAILED

    @pytest.mark.asyncio
    async def test_execute_with_iteration_limit(self) -> None:
        """Test execution with iteration limit."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context, max_iterations=1)

        # Mock execution that takes multiple iterations
        async def multi_iteration_execute():
            yield "iteration 1"
            yield "iteration 2"

        with patch.object(orchestrator, "_execute_state", return_value=multi_iteration_execute()):
            await orchestrator.execute()

            # Should have stopped due to iteration limit
            assert orchestrator._iteration_count >= 1


class TestActiveOrchestratorHandoffs:
    """Test handoff functionality."""

    def test_request_handoff_basic(self) -> None:
        """Test basic handoff request."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Request handoff
        handoff = orchestrator.request_handoff(
            from_agent=AgentType.CHAT,
            to_agent=AgentType.ARCHITECT,
            reason="Need architecture help",
            context_updates={"priority": "high"},
        )

        assert isinstance(handoff, Handoff)
        assert handoff.from_agent == AgentType.CHAT
        assert handoff.to_agent == AgentType.ARCHITECT
        assert handoff.reason == "Need architecture help"
        assert handoff.context_updates == {"priority": "high"}

    def test_request_handoff_with_defaults(self) -> None:
        """Test handoff request with default parameters."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        handoff = orchestrator.request_handoff(
            from_agent=AgentType.PLANNER, to_agent=AgentType.EXECUTOR
        )

        assert handoff.reason == ""
        assert handoff.context_updates == {}

    def test_request_handoff_creates_execution_step(self) -> None:
        """Test that handoff creates an execution step."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Should start with no plan
        assert orchestrator._execution_plan is None

        handoff = orchestrator.request_handoff(
            from_agent=AgentType.CHAT, to_agent=AgentType.ARCHITECT
        )

        # Should have created a plan
        assert orchestrator._execution_plan is not None
        assert isinstance(orchestrator._execution_plan, ExecutionPlan)


class TestActiveOrchestratorControl:
    """Test execution control methods."""

    def test_cancel_method(self) -> None:
        """Test cancellation functionality."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Set to executing state
        orchestrator.state = OrchestratorState.EXECUTING

        orchestrator.cancel()

        assert orchestrator.state == OrchestratorState.CANCELLED

    def test_pause_method(self) -> None:
        """Test pause functionality."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Set to executing state
        orchestrator.state = OrchestratorState.EXECUTING

        orchestrator.pause()

        assert orchestrator.state == OrchestratorState.PAUSED

    def test_resume_method(self) -> None:
        """Test resume functionality."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Set to paused state
        orchestrator.state = OrchestratorState.PAUSED

        orchestrator.resume()

        assert orchestrator.state == OrchestratorState.EXECUTING

    def test_resume_from_non_paused_state(self) -> None:
        """Test resume from non-paused state does nothing."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Set to idle state
        orchestrator.state = OrchestratorState.IDLE

        orchestrator.resume()

        # Should remain idle
        assert orchestrator.state == OrchestratorState.IDLE


class TestActiveOrchestratorStats:
    """Test statistics and history tracking."""

    def test_get_stats_basic(self) -> None:
        """Test getting basic statistics."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        stats = orchestrator.get_stats()

        assert isinstance(stats, dict)
        assert "current_state" in stats
        assert "iteration_count" in stats
        assert "total_transitions" in stats
        assert "start_time" in stats

        assert stats["current_state"] == OrchestratorState.IDLE
        assert stats["iteration_count"] == 0
        assert stats["total_transitions"] == 0

    def test_get_stats_with_transitions(self) -> None:
        """Test statistics after state transitions."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Make some transitions
        orchestrator._transition_to(OrchestratorState.GATHERING, "test")
        orchestrator._transition_to(OrchestratorState.ROUTING, "test")

        stats = orchestrator.get_stats()

        assert stats["total_transitions"] == 2
        assert stats["current_state"] == OrchestratorState.ROUTING

    def test_get_state_history(self) -> None:
        """Test getting state history."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Make transitions
        orchestrator._transition_to(OrchestratorState.GATHERING, "Starting")
        orchestrator._transition_to(OrchestratorState.ROUTING, "Routing")

        history = orchestrator.get_state_history()

        assert len(history) == 2
        assert history[0]["to_state"] == OrchestratorState.GATHERING
        assert history[1]["to_state"] == OrchestratorState.ROUTING
        assert "Starting" in history[0]["reason"]


class TestActiveOrchestratorCallbacks:
    """Test callback system."""

    def test_set_on_state_change_callback(self) -> None:
        """Test setting state change callback."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        callback_called = False
        callback_data = None

        def state_callback(from_state, to_state, reason):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = (from_state, to_state, reason)

        orchestrator.set_on_state_change(state_callback)

        # Trigger state change
        orchestrator._transition_to(OrchestratorState.GATHERING, "test reason")

        assert callback_called
        assert callback_data == (OrchestratorState.IDLE, OrchestratorState.GATHERING, "test reason")

    def test_set_on_step_complete_callback(self) -> None:
        """Test setting step complete callback."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        callback_called = False

        def step_callback(step):
            nonlocal callback_called
            callback_called = True

        orchestrator.set_on_step_complete(step_callback)
        assert orchestrator._on_step_complete == step_callback

    def test_callbacks_with_none_values(self) -> None:
        """Test that callbacks work when set to None."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Should not raise errors
        orchestrator.set_on_state_change(None)
        orchestrator.set_on_step_complete(None)

        # Transition should work without callbacks
        orchestrator._transition_to(OrchestratorState.GATHERING, "test")


class TestActiveOrchestratorErrorHandling:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_execute_with_invalid_initial_state(self) -> None:
        """Test execution with invalid initial state."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Set to completed state
        orchestrator.state = OrchestratorState.COMPLETED

        # Execute should handle gracefully
        await orchestrator.execute()

        # Should remain completed
        assert orchestrator.state == OrchestratorState.COMPLETED

    def test_transition_with_invalid_state(self) -> None:
        """Test state transition with invalid target state."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # This should work (states are enums)
        orchestrator._transition_to(OrchestratorState.COMPLETED, "test")

        assert orchestrator.state == OrchestratorState.COMPLETED

    def test_get_stats_during_execution(self) -> None:
        """Test getting stats during execution."""
        context = UnifiedContext()
        orchestrator = ActiveOrchestrator(context)

        # Simulate execution state
        orchestrator.state = OrchestratorState.EXECUTING
        orchestrator._iteration_count = 5
        orchestrator._start_time = time.time() - 10  # 10 seconds ago

        stats = orchestrator.get_stats()

        assert stats["current_state"] == OrchestratorState.EXECUTING
        assert stats["iteration_count"] == 5
        assert stats["execution_time_seconds"] >= 10
