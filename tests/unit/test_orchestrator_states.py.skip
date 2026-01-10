"""
Tests for Orchestrator State Implementations - Sprint 2 Refactoring.

Tests cover:
    - State machine behavior for each orchestrator state
    - State transitions and message yielding
    - Error handling and edge cases
    - Context updates and decision recording
    - Handoff logic and execution flow
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from vertice_core.agents.orchestrator.states import (
    state_initializing,
    state_gathering,
    state_routing,
    state_planning,
    state_executing,
    state_verifying,
    state_reviewing,
    state_handoff,
    state_error_recovery,
)
from vertice_core.agents.orchestrator.orchestrator import ActiveOrchestrator
from vertice_core.agents.context.unified import UnifiedContext
from vertice_core.agents.router.types import AgentType, RoutingDecision, TaskComplexity
from vertice_core.agents.orchestrator.types import OrchestratorState
from vertice_core.agents.orchestrator.models import ExecutionPlan, ExecutionStep, Handoff


class TestStateInitializing:
    """Test state_initializing function."""

    @pytest.mark.asyncio
    async def test_state_initializing_basic(self) -> None:
        """Test basic initialization state behavior."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Collect yielded messages
        messages = []
        async for message in state_initializing(orchestrator):
            messages.append(message)

        # Should yield initialization message
        assert len(messages) == 1
        assert "📋 Initializing context..." in messages[0]

        # Should transition to GATHERING
        assert orchestrator.state == OrchestratorState.GATHERING

    @pytest.mark.asyncio
    async def test_state_initializing_adds_thought(self) -> None:
        """Test that initialization adds thought to context."""
        context = UnifiedContext(user_request="Test request")
        orchestrator = ActiveOrchestrator(context)

        await state_initializing(orchestrator).__anext__()

        # Should have added a thought
        thoughts = context.get_thought_chain()
        assert len(thoughts) >= 1

        thought = thoughts[-1]
        assert thought.agent_id == "orchestrator"
        assert "Processing request: Test request" in thought.reasoning


class TestStateGathering:
    """Test state_gathering function."""

    @pytest.mark.asyncio
    async def test_state_gathering_basic(self) -> None:
        """Test basic gathering state behavior."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Collect yielded messages
        messages = []
        async for message in state_gathering(orchestrator):
            messages.append(message)

        # Should yield gathering message
        assert len(messages) == 1
        assert "🔍 Gathering context..." in messages[0]

        # Should transition to ROUTING
        assert orchestrator.state == OrchestratorState.ROUTING

    @pytest.mark.asyncio
    async def test_state_gathering_records_decision(self) -> None:
        """Test that gathering records a decision."""
        context = UnifiedContext(user_request="Test request")
        orchestrator = ActiveOrchestrator(context)

        await state_gathering(orchestrator).__anext__()

        # Should have recorded a decision
        decisions = context.get_decisions()
        assert len(decisions) >= 1

        decision = decisions[-1]
        assert "Context gathered for request" in decision.description


class TestStateRouting:
    """Test state_routing function."""

    @pytest.mark.asyncio
    async def test_state_routing_basic(self) -> None:
        """Test basic routing state behavior."""
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
            # Collect yielded messages
            messages = []
            async for message in state_routing(orchestrator):
                messages.append(message)

            # Should yield routing messages
            assert len(messages) > 0
            assert any("🎯 Routing" in msg for msg in messages)

            # Should transition to PLANNING
            assert orchestrator.state == OrchestratorState.PLANNING

    @pytest.mark.asyncio
    async def test_state_routing_with_low_confidence(self) -> None:
        """Test routing with low confidence decision."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Mock router to return low confidence decision
        mock_decision = RoutingDecision(
            route_name="architect",
            agent_type=AgentType.ARCHITECT,
            confidence=0.6,  # Below threshold
            reasoning="Uncertain routing",
        )

        with patch.object(orchestrator.router, "route", return_value=mock_decision):
            messages = []
            async for message in state_routing(orchestrator):
                messages.append(message)

            # Should still work but may have different messages
            assert len(messages) > 0

    @pytest.mark.asyncio
    async def test_state_routing_creates_execution_plan(self) -> None:
        """Test that routing creates an execution plan."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        mock_decision = RoutingDecision(
            route_name="architect",
            agent_type=AgentType.ARCHITECT,
            confidence=0.9,
            reasoning="Architecture task",
        )

        with patch.object(orchestrator.router, "route", return_value=mock_decision):
            await state_routing(orchestrator).__anext__()

            # Should have created an execution plan
            assert orchestrator.current_plan is not None
            assert isinstance(orchestrator.current_plan, ExecutionPlan)


class TestStatePlanning:
    """Test state_planning function."""

    @pytest.mark.asyncio
    async def test_state_planning_basic(self) -> None:
        """Test basic planning state behavior."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Create a mock plan
        mock_plan = ExecutionPlan(
            request_id="test-123",
            steps=[
                ExecutionStep(
                    step_id="step-1",
                    agent_type=AgentType.ARCHITECT,
                    description="Design calculator",
                    estimated_duration=300,
                )
            ],
        )
        orchestrator.current_plan = mock_plan

        # Collect yielded messages
        messages = []
        async for message in state_planning(orchestrator):
            messages.append(message)

        # Should yield planning messages
        assert len(messages) > 0
        assert any("📋 Planning" in msg for msg in messages)

        # Should transition to EXECUTING
        assert orchestrator.state == OrchestratorState.EXECUTING

    @pytest.mark.asyncio
    async def test_state_planning_complex_plan(self) -> None:
        """Test planning with complex multi-step plan."""
        context = UnifiedContext(user_request="Build full app")
        orchestrator = ActiveOrchestrator(context)

        # Create complex plan
        mock_plan = ExecutionPlan(
            request_id="test-123",
            steps=[
                ExecutionStep(
                    step_id="step-1",
                    agent_type=AgentType.ARCHITECT,
                    description="Design architecture",
                    estimated_duration=300,
                ),
                ExecutionStep(
                    step_id="step-2",
                    agent_type=AgentType.PLANNER,
                    description="Create detailed plan",
                    estimated_duration=200,
                ),
                ExecutionStep(
                    step_id="step-3",
                    agent_type=AgentType.EXECUTOR,
                    description="Implement features",
                    estimated_duration=600,
                ),
            ],
        )
        orchestrator.current_plan = mock_plan

        messages = []
        async for message in state_planning(orchestrator):
            messages.append(message)

        # Should handle complex plan
        assert len(messages) > 0
        assert orchestrator.state == OrchestratorState.EXECUTING


class TestStateExecuting:
    """Test state_executing function."""

    @pytest.mark.asyncio
    async def test_state_executing_basic(self) -> None:
        """Test basic executing state behavior."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Create a mock plan with one step
        mock_plan = ExecutionPlan(
            request_id="test-123",
            steps=[
                ExecutionStep(
                    step_id="step-1",
                    agent_type=AgentType.EXECUTOR,
                    description="Execute code",
                    estimated_duration=100,
                )
            ],
        )
        orchestrator.current_plan = mock_plan

        # Mock agent execution
        mock_agent = AsyncMock()
        mock_agent.execute_step.return_value = "✅ Code executed successfully"

        orchestrator.agents = {AgentType.EXECUTOR: mock_agent}

        # Collect yielded messages
        messages = []
        async for message in state_executing(orchestrator):
            messages.append(message)

        # Should yield execution messages
        assert len(messages) > 0
        assert any("⚡ Executing" in msg for msg in messages)

        # Should transition to VERIFYING
        assert orchestrator.state == OrchestratorState.VERIFYING

    @pytest.mark.asyncio
    async def test_state_executing_with_failures(self) -> None:
        """Test executing state with execution failures."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        mock_plan = ExecutionPlan(
            request_id="test-123",
            steps=[
                ExecutionStep(
                    step_id="step-1",
                    agent_type=AgentType.EXECUTOR,
                    description="Execute code",
                    estimated_duration=100,
                )
            ],
        )
        orchestrator.current_plan = mock_plan

        # Mock agent to fail
        mock_agent = AsyncMock()
        mock_agent.execute_step.side_effect = Exception("Execution failed")

        orchestrator.agents = {AgentType.EXECUTOR: mock_agent}

        messages = []
        async for message in state_executing(orchestrator):
            messages.append(message)

        # Should handle failure gracefully
        assert len(messages) > 0
        # May transition to error recovery or failed state


class TestStateVerifying:
    """Test state_verifying function."""

    @pytest.mark.asyncio
    async def test_state_verifying_basic(self) -> None:
        """Test basic verifying state behavior."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Collect yielded messages
        messages = []
        async for message in state_verifying(orchestrator):
            messages.append(message)

        # Should yield verification messages
        assert len(messages) > 0
        assert any("✅ Verifying" in msg for msg in messages)

        # Should transition to COMPLETED
        assert orchestrator.state == OrchestratorState.COMPLETED

    @pytest.mark.asyncio
    async def test_state_verifying_with_issues(self) -> None:
        """Test verifying state when issues are found."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Mock some errors in context
        context.record_error(error_message="Test failed", agent_id="verifier")

        messages = []
        async for message in state_verifying(orchestrator):
            messages.append(message)

        # Should still complete but may have different messages
        assert len(messages) > 0


class TestStateReviewing:
    """Test state_reviewing function."""

    @pytest.mark.asyncio
    async def test_state_reviewing_basic(self) -> None:
        """Test basic reviewing state behavior."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Collect yielded messages
        messages = []
        async for message in state_reviewing(orchestrator):
            messages.append(message)

        # Should yield review messages
        assert len(messages) > 0
        assert any("🔄 Reviewing" in msg for msg in messages)

        # Should transition to COMPLETED
        assert orchestrator.state == OrchestratorState.COMPLETED


class TestStateHandoff:
    """Test state_handoff function."""

    @pytest.mark.asyncio
    async def test_state_handoff_basic(self) -> None:
        """Test basic handoff state behavior."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Add a pending handoff
        handoff = Handoff(
            from_agent=AgentType.CHAT, to_agent=AgentType.ARCHITECT, reason="Need architecture help"
        )
        orchestrator.pending_handoffs = [handoff]

        # Collect yielded messages
        messages = []
        async for message in state_handoff(orchestrator):
            messages.append(message)

        # Should yield handoff messages
        assert len(messages) > 0
        assert any("🔄 Handoff" in msg for msg in messages)

        # Should transition to EXECUTING
        assert orchestrator.state == OrchestratorState.EXECUTING

    @pytest.mark.asyncio
    async def test_state_handoff_no_pending_handoffs(self) -> None:
        """Test handoff state with no pending handoffs."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # No pending handoffs
        orchestrator.pending_handoffs = []

        messages = []
        async for message in state_handoff(orchestrator):
            messages.append(message)

        # Should handle gracefully
        assert len(messages) > 0


class TestStateErrorRecovery:
    """Test state_error_recovery function."""

    @pytest.mark.asyncio
    async def test_state_error_recovery_basic(self) -> None:
        """Test basic error recovery state behavior."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        # Add some errors
        context.record_error(error_message="Test error", agent_id="executor")

        # Collect yielded messages
        messages = []
        async for message in state_error_recovery(orchestrator):
            messages.append(message)

        # Should yield error recovery messages
        assert len(messages) > 0
        assert any("🚨 Error Recovery" in msg for msg in messages)

        # Should transition back to EXECUTING or another state
        assert orchestrator.state in [
            OrchestratorState.EXECUTING,
            OrchestratorState.FAILED,
            OrchestratorState.COMPLETED,
        ]

    @pytest.mark.asyncio
    async def test_state_error_recovery_no_errors(self) -> None:
        """Test error recovery with no errors."""
        context = UnifiedContext(user_request="Build a calculator")
        orchestrator = ActiveOrchestrator(context)

        messages = []
        async for message in state_error_recovery(orchestrator):
            messages.append(message)

        # Should handle gracefully
        assert len(messages) > 0


class TestStateEdgeCases:
    """Test edge cases across states."""

    @pytest.mark.asyncio
    async def test_states_with_none_context(self) -> None:
        """Test state functions handle None context gracefully."""
        # This would normally cause errors, but testing error handling
        orchestrator = MagicMock()
        orchestrator.context = None
        orchestrator._transition_to = MagicMock()

        # Most state functions should handle None context gracefully
        # or raise appropriate errors
        with pytest.raises(AttributeError):
            async for _ in state_initializing(orchestrator):
                pass

    @pytest.mark.asyncio
    async def test_state_transitions_with_callbacks(self) -> None:
        """Test state transitions trigger callbacks."""
        context = UnifiedContext(user_request="Test")
        orchestrator = ActiveOrchestrator(context)

        callback_called = False

        def state_callback(old_state, new_state):
            nonlocal callback_called
            callback_called = True

        orchestrator.set_on_state_change(state_callback)

        await state_initializing(orchestrator).__anext__()

        # Callback should have been called during transition
        assert callback_called

    @pytest.mark.asyncio
    async def test_states_with_empty_agents_dict(self) -> None:
        """Test states handle empty agents dictionary."""
        context = UnifiedContext(user_request="Test")
        orchestrator = ActiveOrchestrator(context)
        orchestrator.agents = {}  # Empty agents

        # States should handle missing agents gracefully
        messages = []
        async for message in state_routing(orchestrator):
            messages.append(message)

        assert len(messages) > 0  # Should still produce messages
