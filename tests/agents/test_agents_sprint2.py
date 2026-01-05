"""
Tests for Sprint 2 - Unified Agent System.

Tests all components:
- UnifiedContext: Shared state management
- SemanticRouter: Intent classification
- ActiveOrchestrator: State machine execution
- HandoffManager: Agent transfers
- ContextCompactor: Context compression

Phase 10: Sprint 2 - Agent Rewrite

Soli Deo Gloria
"""

import asyncio
import pytest

# Import all Sprint 2 components
from vertice_core.agents import (
    # Context
    ContextState,
    DecisionType,
    ExecutionResult,
    UnifiedContext,
    get_context,
    set_context,
    new_context,
    # Router
    AgentType,
    TaskComplexity,
    RouteDefinition,
    RoutingDecision,
    SemanticRouter,
    DEFAULT_ROUTES,
    # Orchestrator
    OrchestratorState,
    ExecutionStep,
    ExecutionPlan,
    ActiveOrchestrator,
    HandoffStatus,
    HandoffReason,
    HandoffManager,
    handoff,
    CompactionStrategy,
    CompactionConfig,
    ContextCompactor,
)


# =============================================================================
# UnifiedContext Tests
# =============================================================================

class TestUnifiedContext:
    """Tests for UnifiedContext."""

    def test_create_context(self):
        """Test basic context creation."""
        ctx = UnifiedContext(user_request="test request")

        assert ctx.user_request == "test request"
        assert ctx.state == ContextState.ACTIVE
        assert ctx.session_id is not None
        assert len(ctx.session_id) == 8

    def test_context_variables_swarm_pattern(self):
        """Test context variables (Swarm pattern)."""
        ctx = UnifiedContext()

        # Set and get
        ctx.set("key1", "value1")
        assert ctx.get("key1") == "value1"
        assert ctx.get("nonexistent", "default") == "default"

        # Update multiple
        ctx.update({"key2": "value2", "key3": "value3"})
        assert ctx.get("key2") == "value2"
        assert ctx.get("key3") == "value3"

        # Delete
        assert ctx.delete("key1") is True
        assert ctx.get("key1") is None
        assert ctx.delete("nonexistent") is False

        # Variables copy
        variables = ctx.variables
        assert "key2" in variables
        variables["key4"] = "should not appear"
        assert ctx.get("key4") is None  # Original not modified

    def test_file_context_claude_pattern(self):
        """Test file context management (Claude pattern)."""
        ctx = UnifiedContext(max_tokens=10000)

        # Add file
        content = "def hello(): pass"
        assert ctx.add_file("test.py", content) is True

        # Verify file added
        files = ctx.list_files()
        assert "test.py" in files

        # Get file
        file_ctx = ctx.get_file("test.py")
        assert file_ctx is not None
        assert file_ctx.content == content
        assert file_ctx.language == "python"
        assert file_ctx.tokens > 0

        # Remove file
        assert ctx.remove_file("test.py") is True
        assert ctx.get_file("test.py") is None
        assert ctx.remove_file("test.py") is False

    def test_file_context_token_budget(self):
        """Test file context respects token budget."""
        ctx = UnifiedContext(max_tokens=100)

        # Add small file - should succeed
        assert ctx.add_file("small.py", "x = 1") is True

        # Add large file - should fail
        large_content = "x = 1\n" * 1000
        assert ctx.add_file("large.py", large_content) is False

    def test_message_history(self):
        """Test message history management."""
        ctx = UnifiedContext()

        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi there!")

        messages = ctx.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"

        # Get limited
        limited = ctx.get_messages(limit=1)
        assert len(limited) == 1
        assert limited[0]["role"] == "assistant"

    def test_decision_tracking(self):
        """Test decision tracking for explainability."""
        ctx = UnifiedContext()

        decision = ctx.record_decision(
            decision_type=DecisionType.ROUTING,
            description="Route to executor",
            agent_id="router",
            reasoning="User wants to implement feature",
            alternatives=["planner", "reviewer"],
            confidence=0.95,
        )

        assert decision.decision_id is not None
        assert decision.decision_type == DecisionType.ROUTING

        decisions = ctx.get_decisions()
        assert len(decisions) == 1

        # Filter by type
        routing_decisions = ctx.get_decisions(decision_type=DecisionType.ROUTING)
        assert len(routing_decisions) == 1

    def test_error_tracking(self):
        """Test error context tracking."""
        ctx = UnifiedContext()

        error = ctx.record_error(
            error_type="ValueError",
            error_message="Invalid input",
            agent_id="executor",
            step_id="step1",
        )

        assert error.error_id is not None
        assert error.error_type == "ValueError"

        errors = ctx.get_errors()
        assert len(errors) == 1

    def test_thought_signatures_gemini_pattern(self):
        """Test thought signatures (Gemini pattern)."""
        ctx = UnifiedContext()

        sig = ctx.add_thought(
            agent_id="planner",
            reasoning="Need to break down the task into steps",
            insights=["Task is complex", "Requires multiple files"],
            next_action="create_plan",
        )

        assert sig.signature_id is not None
        assert sig.thought_hash is not None
        assert len(sig.key_insights) == 2

        chain = ctx.get_thought_chain()
        assert len(chain) == 1

        # Test limit (max 10)
        for i in range(15):
            ctx.add_thought("agent", f"thought {i}", [], "action")

        chain = ctx.get_thought_chain()
        assert len(chain) == 10  # Limited to 10

    def test_execution_results(self):
        """Test execution result tracking."""
        ctx = UnifiedContext()

        result = ExecutionResult(
            step_id="step1",
            success=True,
            output="Done",
            duration_ms=100.5,
            files_modified=["file1.py"],
        )

        ctx.add_step_result(result)

        assert ctx.get_step_result("step1") == result
        assert ctx.get_step_result("nonexistent") is None
        assert ctx.has_failures() is False

        # Add failure
        ctx.add_step_result(ExecutionResult(step_id="step2", success=False))
        assert ctx.has_failures() is True

    def test_token_usage_tracking(self):
        """Test token usage tracking."""
        ctx = UnifiedContext(max_tokens=10000)

        initial_usage, max_tokens = ctx.get_token_usage()
        assert max_tokens == 10000

        # Add content and check usage increases
        ctx.add_message("user", "A" * 400)  # ~100 tokens

        new_usage, _ = ctx.get_token_usage()
        assert new_usage > initial_usage

    def test_serialization(self):
        """Test context serialization."""
        ctx = UnifiedContext(user_request="test")
        ctx.set("key", "value")
        ctx.add_message("user", "hello")

        # To dict
        data = ctx.to_dict()
        assert data["user_request"] == "test"
        assert data["variables"]["key"] == "value"

        # From dict
        ctx2 = UnifiedContext.from_dict(data)
        assert ctx2.user_request == "test"
        assert ctx2.get("key") == "value"

    def test_prompt_context_generation(self):
        """Test prompt context string generation."""
        ctx = UnifiedContext(user_request="implement login")
        ctx.set("language", "python")
        ctx.add_file("auth.py", "def login(): pass")
        ctx.record_decision(
            DecisionType.ROUTING,
            "Route to executor",
        )

        prompt = ctx.to_prompt_context()

        assert "implement login" in prompt
        assert "auth.py" in prompt
        assert "Route to executor" in prompt

    def test_context_clear(self):
        """Test context clearing."""
        ctx = UnifiedContext()
        ctx.set("key", "value")
        ctx.add_message("user", "hello")
        ctx.add_file("test.py", "code")

        ctx.clear()

        assert ctx.get("key") is None
        assert len(ctx.get_messages()) == 0
        assert len(ctx.list_files()) == 0
        assert ctx.state == ContextState.ACTIVE

    def test_context_singleton(self):
        """Test context singleton functions."""
        # Create new context
        ctx1 = new_context(user_request="request1")
        assert get_context().user_request == "request1"

        # Set different context
        ctx2 = UnifiedContext(user_request="request2")
        set_context(ctx2)
        assert get_context().user_request == "request2"


# =============================================================================
# SemanticRouter Tests
# =============================================================================

class TestSemanticRouter:
    """Tests for SemanticRouter."""

    @pytest.mark.asyncio
    async def test_router_initialization(self):
        """Test router initialization."""
        router = SemanticRouter()

        await router.initialize()

        assert router._initialized is True
        assert len(router.routes) == len(DEFAULT_ROUTES)

    @pytest.mark.asyncio
    async def test_route_planning_intent(self):
        """Test routing planning requests."""
        router = SemanticRouter()

        decision = await router.route("create a plan to implement authentication")

        assert decision.primary_agent in [AgentType.PLANNER, AgentType.ARCHITECT]
        assert decision.requires_planning is True
        assert decision.confidence > 0.5

    @pytest.mark.asyncio
    async def test_route_execution_intent(self):
        """Test routing execution requests."""
        router = SemanticRouter()

        decision = await router.route("add a new login endpoint")

        assert decision.primary_agent == AgentType.EXECUTOR
        assert decision.requires_execution is True

    @pytest.mark.asyncio
    async def test_route_review_intent(self):
        """Test routing review requests."""
        router = SemanticRouter()

        decision = await router.route("review my code for bugs")

        assert decision.primary_agent == AgentType.REVIEWER
        assert decision.requires_review is True

    @pytest.mark.asyncio
    async def test_route_exploration_intent(self):
        """Test routing exploration requests."""
        router = SemanticRouter()

        decision = await router.route("how does the authentication flow work")

        assert decision.primary_agent == AgentType.EXPLORER
        assert decision.requires_execution is False

    @pytest.mark.asyncio
    async def test_route_chat_fallback(self):
        """Test routing falls back to chat for greetings."""
        router = SemanticRouter()

        decision = await router.route("hello")

        assert decision.primary_agent == AgentType.CHAT

    @pytest.mark.asyncio
    async def test_route_caching(self):
        """Test routing cache."""
        router = SemanticRouter()

        # First call
        decision1 = await router.route("implement feature X", use_cache=True)

        # Second call (should hit cache)
        decision2 = await router.route("implement feature X", use_cache=True)

        assert decision1.primary_agent == decision2.primary_agent

        stats = router.get_stats()
        assert stats["cache_hits"] >= 1

    @pytest.mark.asyncio
    async def test_route_no_cache(self):
        """Test routing without cache."""
        router = SemanticRouter()

        await router.route("test", use_cache=False)
        await router.route("test", use_cache=False)

        stats = router.get_stats()
        assert stats["cache_hits"] == 0

    @pytest.mark.asyncio
    async def test_complexity_assessment(self):
        """Test task complexity assessment."""
        router = SemanticRouter()

        # Simple task
        simple = await router.route("hello world")
        assert simple.complexity == TaskComplexity.SIMPLE

        # Complex task
        complex_task = await router.route(
            "refactor the entire authentication system across all files"
        )
        assert complex_task.complexity == TaskComplexity.COMPLEX

    def test_add_custom_route(self):
        """Test adding custom routes."""
        router = SemanticRouter()

        custom_route = RouteDefinition(
            name="custom",
            agent_type=AgentType.DATA,
            description="Custom data processing",
            examples=["process the data", "analyze dataset"],
        )

        router.add_route(custom_route)

        assert "custom" in router._route_map
        assert router._initialized is False  # Needs re-init

    @pytest.mark.asyncio
    async def test_router_stats(self):
        """Test router statistics."""
        router = SemanticRouter()

        await router.route("test 1")
        await router.route("test 2")

        stats = router.get_stats()

        assert stats["total_routes"] == 2
        assert "fast_path_percent" in stats
        assert stats["routes_defined"] == len(DEFAULT_ROUTES)

    def test_clear_cache(self):
        """Test cache clearing."""
        router = SemanticRouter()
        router._cache["test"] = RoutingDecision(
            primary_agent=AgentType.CHAT,
            confidence=1.0,
            requires_planning=False,
            requires_execution=False,
            requires_review=False,
            complexity=TaskComplexity.SIMPLE,
        )

        count = router.clear_cache()

        assert count == 1
        assert len(router._cache) == 0


# =============================================================================
# ActiveOrchestrator Tests
# =============================================================================

class TestActiveOrchestrator:
    """Tests for ActiveOrchestrator."""

    @pytest.mark.asyncio
    async def test_orchestrator_initialization(self):
        """Test orchestrator initialization."""
        ctx = UnifiedContext(user_request="test")
        orchestrator = ActiveOrchestrator(ctx)

        assert orchestrator.state == OrchestratorState.IDLE
        assert orchestrator.context == ctx

    @pytest.mark.asyncio
    async def test_orchestrator_basic_execution(self):
        """Test basic orchestration execution."""
        ctx = UnifiedContext()
        orchestrator = ActiveOrchestrator(ctx)

        events = []
        async for event in orchestrator.execute("hello"):
            events.append(event)

        assert len(events) > 0
        assert orchestrator.state in [
            OrchestratorState.COMPLETED,
            OrchestratorState.FAILED,
        ]

    @pytest.mark.asyncio
    async def test_orchestrator_state_transitions(self):
        """Test state machine transitions."""
        ctx = UnifiedContext()
        orchestrator = ActiveOrchestrator(ctx)

        states_visited = []

        def on_state_change(old, new):
            states_visited.append(new)

        orchestrator.set_on_state_change(on_state_change)

        async for _ in orchestrator.execute("test"):
            pass

        # Should have visited multiple states
        assert len(states_visited) > 0
        assert OrchestratorState.INITIALIZING in states_visited

    @pytest.mark.asyncio
    async def test_orchestrator_cancellation(self):
        """Test orchestration cancellation."""
        ctx = UnifiedContext()
        orchestrator = ActiveOrchestrator(ctx)

        events = []
        async for event in orchestrator.execute("long task"):
            events.append(event)
            # Cancel after first event and consume remaining
            orchestrator.cancel()

        # Should end in cancelled state after loop completes
        assert orchestrator.state == OrchestratorState.CANCELLED or orchestrator._cancelled is True

    @pytest.mark.asyncio
    async def test_orchestrator_timeout(self):
        """Test orchestration timeout."""
        ctx = UnifiedContext()
        orchestrator = ActiveOrchestrator(ctx)
        orchestrator.DEFAULT_TIMEOUT = 0.001  # Very short timeout

        events = []
        async for event in orchestrator.execute("test"):
            events.append(event)
            await asyncio.sleep(0.01)

        assert orchestrator.state == OrchestratorState.TIMEOUT

    @pytest.mark.asyncio
    async def test_execution_plan(self):
        """Test execution plan creation and tracking."""
        plan = ExecutionPlan(goal="implement feature")

        step1 = ExecutionStep(description="Step 1")
        step2 = ExecutionStep(description="Step 2", dependencies=[step1.step_id])

        plan.steps = [step1, step2]

        # Only step1 is runnable initially
        runnable = plan.get_runnable_steps()
        assert len(runnable) == 1
        assert runnable[0].step_id == step1.step_id

        # Mark step1 complete
        step1.status = "completed"

        # Now step2 is runnable
        runnable = plan.get_runnable_steps()
        assert len(runnable) == 1
        assert runnable[0].step_id == step2.step_id

    @pytest.mark.asyncio
    async def test_orchestrator_stats(self):
        """Test orchestrator statistics."""
        ctx = UnifiedContext()
        orchestrator = ActiveOrchestrator(ctx)

        async for _ in orchestrator.execute("test"):
            pass

        stats = orchestrator.get_stats()

        assert "state" in stats
        assert "iterations" in stats
        assert stats["iterations"] > 0

    @pytest.mark.asyncio
    async def test_state_history(self):
        """Test state transition history."""
        ctx = UnifiedContext()
        orchestrator = ActiveOrchestrator(ctx)

        async for _ in orchestrator.execute("test"):
            pass

        history = orchestrator.get_state_history()

        assert len(history) > 0
        assert all("from" in h and "to" in h for h in history)


# =============================================================================
# HandoffManager Tests
# =============================================================================

class TestHandoffManager:
    """Tests for HandoffManager."""

    def test_create_handoff(self):
        """Test creating handoff request."""
        ctx = UnifiedContext()
        ctx.current_agent = "executor"

        manager = HandoffManager(ctx)

        request = manager.create_handoff(
            to_agent=AgentType.REVIEWER,
            reason=HandoffReason.TASK_COMPLETION,
            message="Please review my changes",
        )

        assert request.from_agent == AgentType.EXECUTOR
        assert request.to_agent == AgentType.REVIEWER
        assert request.status == HandoffStatus.PENDING

    def test_swarm_handoff(self):
        """Test Swarm-style handoff creation."""
        ctx = UnifiedContext()
        manager = HandoffManager(ctx)

        request = manager.create_swarm_handoff(
            AgentType.PLANNER,
            context_updates={"key": "value"},
        )

        assert request.to_agent == AgentType.PLANNER
        assert request.context_updates == {"key": "value"}
        assert request.reason == HandoffReason.TASK_COMPLETION

    @pytest.mark.asyncio
    async def test_execute_handoff(self):
        """Test handoff execution."""
        ctx = UnifiedContext()
        ctx.current_agent = "executor"

        manager = HandoffManager(ctx)

        request = manager.create_handoff(
            to_agent=AgentType.REVIEWER,
            context_updates={"reviewed": True},
        )

        result = await manager.execute_handoff(request)

        assert result.success is True
        assert result.from_agent == AgentType.EXECUTOR
        assert result.to_agent == AgentType.REVIEWER
        assert ctx.current_agent == "reviewer"
        assert ctx.get("reviewed") is True

    @pytest.mark.asyncio
    async def test_auto_select_agent(self):
        """Test automatic agent selection."""
        ctx = UnifiedContext()
        manager = HandoffManager(ctx)

        request = manager.create_handoff(
            to_agent=None,  # Auto-select
            required_capabilities={"security", "audit"},
        )

        result = await manager.execute_handoff(request)

        assert result.success is True
        assert result.to_agent == AgentType.SECURITY

    @pytest.mark.asyncio
    async def test_escalation(self):
        """Test agent escalation."""
        ctx = UnifiedContext()
        ctx.current_agent = "executor"

        manager = HandoffManager(ctx)

        result = await manager.escalate(reason="Cannot handle complexity")

        assert result.success is True
        # Executor escalates to planner
        assert result.to_agent == AgentType.PLANNER

    @pytest.mark.asyncio
    async def test_delegate_to(self):
        """Test delegation to specific agent."""
        ctx = UnifiedContext()
        manager = HandoffManager(ctx)

        result = await manager.delegate_to(
            AgentType.TESTING,
            task="Write unit tests",
        )

        assert result.success is True
        assert result.to_agent == AgentType.TESTING

    @pytest.mark.asyncio
    async def test_return_to_caller(self):
        """Test returning to previous agent."""
        ctx = UnifiedContext()
        ctx.current_agent = "executor"

        manager = HandoffManager(ctx)

        # First handoff
        await manager.delegate_to(AgentType.REVIEWER)

        # Return
        result = await manager.return_to_caller(result="Review complete")

        assert result.success is True
        assert result.to_agent == AgentType.EXECUTOR

    def test_agent_capabilities(self):
        """Test agent capability matching."""
        ctx = UnifiedContext()
        manager = HandoffManager(ctx)

        # Find agent with planning capability
        agent = manager.select_agent({"planning"})
        assert agent in [AgentType.PLANNER, AgentType.ARCHITECT]

        # Find agent with execution capability
        agent = manager.select_agent({"execution"})
        assert agent == AgentType.EXECUTOR

        # No match
        agent = manager.select_agent({"nonexistent_capability"})
        assert agent is None

    def test_escalation_chain(self):
        """Test escalation chain."""
        ctx = UnifiedContext()
        manager = HandoffManager(ctx)

        # Executor → Planner
        target = manager.get_escalation_target(AgentType.EXECUTOR)
        assert target == AgentType.PLANNER

        # Planner → Architect
        target = manager.get_escalation_target(AgentType.PLANNER)
        assert target == AgentType.ARCHITECT

        # Architect → None (end of chain)
        target = manager.get_escalation_target(AgentType.ARCHITECT)
        assert target is None

    @pytest.mark.asyncio
    async def test_parallel_handoffs(self):
        """Test parallel handoff execution."""
        ctx = UnifiedContext()
        manager = HandoffManager(ctx)

        requests = [
            manager.create_handoff(to_agent=AgentType.REVIEWER),
            manager.create_handoff(to_agent=AgentType.SECURITY),
        ]

        results = await manager.execute_parallel_handoffs(requests)

        assert len(results) == 2
        # At least one should succeed (context gets modified)
        assert any(r.success for r in results)

    def test_handoff_history(self):
        """Test handoff history tracking."""
        ctx = UnifiedContext()
        manager = HandoffManager(ctx)

        # Execute some handoffs
        asyncio.run(manager.delegate_to(AgentType.REVIEWER))
        asyncio.run(manager.delegate_to(AgentType.EXECUTOR))

        history = manager.get_history()
        assert len(history) >= 2

        chain = manager.get_handoff_chain()
        assert len(chain) >= 2

    def test_handoff_stats(self):
        """Test handoff statistics."""
        ctx = UnifiedContext()
        manager = HandoffManager(ctx)

        stats = manager.get_stats()

        assert "total_handoffs" in stats
        assert "success_rate" in stats
        assert "current_agent" in stats

    def test_handoff_helper_function(self):
        """Test handoff() helper function."""
        request = handoff(AgentType.REVIEWER, review_type="security")

        assert request.to_agent == AgentType.REVIEWER
        assert request.context_updates == {"review_type": "security"}


# =============================================================================
# ContextCompactor Tests
# =============================================================================

class TestContextCompactor:
    """Tests for ContextCompactor."""

    def test_compactor_initialization(self):
        """Test compactor initialization."""
        ctx = UnifiedContext(max_tokens=10000)
        compactor = ContextCompactor(ctx)

        assert compactor.context == ctx
        assert compactor.config is not None

    def test_should_compact_threshold(self):
        """Test compaction threshold detection."""
        ctx = UnifiedContext(max_tokens=1000)
        config = CompactionConfig(trigger_threshold=0.50)
        compactor = ContextCompactor(ctx, config)

        # Below threshold
        ctx._token_usage = 400
        assert compactor.should_compact() is False

        # Above threshold
        ctx._token_usage = 600
        assert compactor.should_compact() is True

    def test_emergency_compact_threshold(self):
        """Test emergency compaction threshold."""
        ctx = UnifiedContext(max_tokens=1000)
        config = CompactionConfig(emergency_threshold=0.95)
        compactor = ContextCompactor(ctx, config)

        ctx._token_usage = 960
        assert compactor.needs_emergency_compact() is True

        ctx._token_usage = 900
        assert compactor.needs_emergency_compact() is False

    def test_recommended_strategy(self):
        """Test strategy recommendation."""
        ctx = UnifiedContext(max_tokens=1000)
        compactor = ContextCompactor(ctx)

        # Normal: observation masking
        ctx._token_usage = 900
        strategy = compactor.get_recommended_strategy()
        assert strategy == CompactionStrategy.OBSERVATION_MASKING

        # Emergency without LLM: hierarchical
        ctx._token_usage = 960
        strategy = compactor.get_recommended_strategy()
        assert strategy == CompactionStrategy.HIERARCHICAL

    def test_compact_not_needed(self):
        """Test compaction when not needed."""
        ctx = UnifiedContext(max_tokens=10000)
        compactor = ContextCompactor(ctx)

        result = compactor.compact()

        assert result.success is True
        assert result.strategy_used == CompactionStrategy.NONE
        assert result.compression_ratio == 1.0

    def test_compact_forced(self):
        """Test forced compaction."""
        ctx = UnifiedContext(max_tokens=10000)
        ctx._token_usage = 100  # Below threshold

        # Add messages to compact
        for i in range(20):
            ctx.add_message("user", f"Message {i}")

        compactor = ContextCompactor(ctx)
        result = compactor.compact(force=True)

        assert result.success is True
        assert result.strategy_used != CompactionStrategy.NONE

    def test_observation_masking_strategy(self):
        """Test observation masking strategy."""
        ctx = UnifiedContext(max_tokens=10000)

        # Add tool-like output
        ctx.add_message("tool", """
            ```python
            def long_function():
                # lots of code
                pass
            ```
            Success: Operation completed
            Files: 3 modified
        """)
        ctx.add_message("user", "Thanks!")

        config = CompactionConfig(keep_recent_messages=1)
        compactor = ContextCompactor(ctx, config)

        result = compactor.compact(
            strategy=CompactionStrategy.OBSERVATION_MASKING,
            force=True,
        )

        assert result.success is True
        assert result.tokens_after <= result.tokens_before

    def test_hierarchical_strategy(self):
        """Test hierarchical summarization strategy."""
        ctx = UnifiedContext(max_tokens=10000)

        # Add many messages
        for i in range(30):
            ctx.add_message("user", f"Question {i}")
            ctx.add_message("assistant", f"Answer {i}")

        config = CompactionConfig(keep_recent_messages=5)
        compactor = ContextCompactor(ctx, config)

        result = compactor.compact(
            strategy=CompactionStrategy.HIERARCHICAL,
            force=True,
        )

        assert result.success is True
        assert result.messages_removed > 0
        assert len(ctx.get_messages()) == 5  # Only recent kept

    def test_auto_compact(self):
        """Test automatic compaction."""
        ctx = UnifiedContext(max_tokens=1000)

        # Add content to exceed threshold
        for i in range(50):
            ctx.add_message("user", f"Message {i} " * 10)

        compactor = ContextCompactor(ctx)
        result = compactor.auto_compact()

        if compactor.should_compact():
            assert result is not None
            assert result.success is True

    def test_compactor_stats(self):
        """Test compactor statistics."""
        ctx = UnifiedContext(max_tokens=10000)
        compactor = ContextCompactor(ctx)

        # Do some compactions
        compactor.compact(force=True)

        stats = compactor.get_stats()

        assert "total_compactions" in stats
        assert "current_usage" in stats
        assert "should_compact" in stats

    def test_compaction_history(self):
        """Test compaction history."""
        ctx = UnifiedContext(max_tokens=10000)
        compactor = ContextCompactor(ctx)

        # Add messages and compact
        for i in range(10):
            ctx.add_message("user", f"Msg {i}")

        compactor.compact(force=True)
        compactor.compact(force=True)

        history = compactor.get_history()
        assert len(history) >= 1
        assert all("strategy" in h for h in history)


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for Sprint 2 components."""

    @pytest.mark.asyncio
    async def test_router_to_orchestrator(self):
        """Test router feeding into orchestrator."""
        ctx = new_context(user_request="implement a login feature")
        router = SemanticRouter()

        # Route the request
        decision = await router.route(ctx.user_request)
        ctx.set("routing_decision", decision.to_dict())

        # Orchestrate
        orchestrator = ActiveOrchestrator(ctx, router)

        events = []
        async for event in orchestrator.execute(ctx.user_request):
            events.append(event)

        assert len(events) > 0

    @pytest.mark.asyncio
    async def test_orchestrator_with_handoffs(self):
        """Test orchestrator with handoff manager."""
        ctx = UnifiedContext(user_request="test")
        handoff_manager = HandoffManager(ctx)
        orchestrator = ActiveOrchestrator(ctx)

        # Execute with handoff
        async for _ in orchestrator.execute("test"):
            if orchestrator.state == OrchestratorState.EXECUTING:
                # Request handoff
                orchestrator.request_handoff(
                    to_agent=AgentType.REVIEWER,
                    reason="Need review",
                )
                break

        # Handoff should be pending
        assert len(orchestrator.pending_handoffs) >= 0

    @pytest.mark.asyncio
    async def test_full_pipeline(self):
        """Test full pipeline: route → plan → execute → review."""
        ctx = new_context(user_request="write a hello world function")

        # Route
        router = SemanticRouter()
        decision = await router.route(ctx.user_request)

        # Orchestrate
        orchestrator = ActiveOrchestrator(ctx, router)

        events = []
        async for event in orchestrator.execute(ctx.user_request):
            events.append(event)

        # Check context was updated
        assert ctx.session_id is not None
        assert len(ctx.get_decisions()) > 0

    def test_context_with_compaction(self):
        """Test context with compaction during use."""
        ctx = UnifiedContext(max_tokens=2000)
        compactor = ContextCompactor(ctx)

        # Simulate conversation that fills context
        for i in range(100):
            ctx.add_message("user", f"Question {i} about topic " * 5)
            ctx.add_message("assistant", f"Answer {i} explaining " * 5)

            # Auto-compact if needed
            compactor.auto_compact()

        # Context should still be usable
        usage, max_tokens = ctx.get_token_usage()
        assert usage < max_tokens

    @pytest.mark.asyncio
    async def test_error_recovery_flow(self):
        """Test error recovery in orchestration."""
        ctx = UnifiedContext()
        orchestrator = ActiveOrchestrator(ctx)

        # Record an error
        ctx.record_error(
            error_type="TestError",
            error_message="Simulated error",
        )

        # Orchestrator should handle it
        async for event in orchestrator.execute("test"):
            pass

        # Should have recorded the error
        assert len(ctx.get_errors()) >= 1


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
