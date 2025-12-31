"""
Phase 6.1 Tests - Core Agent Integration

Tests for CoreAgentAdapter, OrchestratorIntegration, and AgentManager updates.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, AsyncIterator, Dict, List, Optional


# =============================================================================
# FIXTURES
# =============================================================================


class MockCoreAgent:
    """Mock core agent with typical mixin patterns."""

    def __init__(self) -> None:
        self._approval_callback: Optional[Any] = None
        self._notify_callback: Optional[Any] = None
        self.execute_called = False
        self.execute_request: Optional[str] = None

    async def execute(self, request: str, stream: bool = False) -> AsyncIterator[str]:
        self.execute_called = True
        self.execute_request = request
        yield "Starting...\n"
        yield "Processing...\n"
        yield "Done.\n"

    def check_autonomy(self, operation: str) -> tuple[bool, Optional[Any]]:
        if "dangerous" in operation.lower():
            return (False, {"id": "approval-1", "operation": operation})
        return (True, None)

    def get_status(self) -> Dict[str, Any]:
        return {"status": "ready", "type": "MockCoreAgent"}


class MockCoreAgentNoStream:
    """Mock core agent without streaming support."""

    async def execute(self, request: str) -> str:
        return f"Result for: {request}"


@pytest.fixture
def mock_core_agent() -> MockCoreAgent:
    return MockCoreAgent()


@pytest.fixture
def mock_llm_client() -> MagicMock:
    client = MagicMock()
    client.is_available = True

    async def mock_stream(message: str, system_prompt: str = "") -> AsyncIterator[str]:
        yield "Fallback response"

    client.stream = mock_stream
    return client


# =============================================================================
# CORE AGENT CONTEXT TESTS
# =============================================================================


class TestCoreAgentContext:
    """Tests for CoreAgentContext dataclass."""

    def test_default_values(self) -> None:
        from tui.core.agents.core_adapter import CoreAgentContext

        ctx = CoreAgentContext()
        assert ctx.autonomy_level == "L1"
        assert ctx.approval_callback is None
        assert ctx.notify_callback is None
        assert ctx.history_context is None
        assert ctx.enable_deep_think is True
        assert ctx.enable_darwin_godel is False
        assert ctx.extra_config == {}

    def test_custom_values(self) -> None:
        from tui.core.agents.core_adapter import CoreAgentContext

        callback = MagicMock()
        ctx = CoreAgentContext(
            autonomy_level="L2",
            approval_callback=callback,
            enable_darwin_godel=True,
        )
        assert ctx.autonomy_level == "L2"
        assert ctx.approval_callback is callback
        assert ctx.enable_darwin_godel is True


# =============================================================================
# CORE AGENT ADAPTER TESTS
# =============================================================================


class TestCoreAgentAdapter:
    """Tests for CoreAgentAdapter."""

    def test_init(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test_agent")
        assert adapter.agent_name == "test_agent"
        assert adapter.core_agent is mock_core_agent
        assert adapter._mixin_activated is False

    def test_name_property(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test_agent")
        assert adapter.name == "test_agent"

    def test_activate_mixins(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter, CoreAgentContext

        adapter = CoreAgentAdapter(mock_core_agent, "test_agent")
        callback = MagicMock()
        ctx = CoreAgentContext(approval_callback=callback)

        adapter._activate_mixins(ctx)

        assert adapter._mixin_activated is True
        assert mock_core_agent._approval_callback is callback

    def test_activate_mixins_only_once(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter, CoreAgentContext

        adapter = CoreAgentAdapter(mock_core_agent, "test_agent")
        callback1 = MagicMock()
        callback2 = MagicMock()

        adapter._activate_mixins(CoreAgentContext(approval_callback=callback1))
        adapter._activate_mixins(CoreAgentContext(approval_callback=callback2))

        # First callback should be kept
        assert mock_core_agent._approval_callback is callback1

    def test_estimate_complexity_simple(self) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(MagicMock(), "test")

        # Short request = SIMPLE (word count < 10)
        result = adapter._estimate_complexity("Fix bug")
        # Result should be SIMPLE enum, verify by checking name
        assert result.name == "SIMPLE"

    def test_estimate_complexity_moderate(self) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(MagicMock(), "test")

        # Medium request = MODERATE (word count >= 10 and < 50)
        request = " ".join(["word"] * 20)
        result = adapter._estimate_complexity(request)
        assert result.name == "MODERATE"

    def test_estimate_complexity_complex(self) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(MagicMock(), "test")

        # Request with 50+ words + architecture keyword = COMPLEX
        # Need >= 50 words for the keyword check to apply
        words = " ".join(["word"] * 48) + " architecture design system"
        assert len(words.split()) >= 50  # Verify we have enough words
        result = adapter._estimate_complexity(words)
        assert result.name == "COMPLEX"

    def test_normalize_chunk_string(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test")
        assert adapter._normalize_chunk("hello") == "hello"

    def test_normalize_chunk_object_with_text(
        self, mock_core_agent: MockCoreAgent
    ) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test")

        class ChunkWithText:
            text = "hello from object"

        assert adapter._normalize_chunk(ChunkWithText()) == "hello from object"

    def test_normalize_chunk_dict_with_text(
        self, mock_core_agent: MockCoreAgent
    ) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test")
        assert adapter._normalize_chunk({"text": "hello"}) == "hello"

    def test_normalize_chunk_dict_with_content(
        self, mock_core_agent: MockCoreAgent
    ) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test")
        assert adapter._normalize_chunk({"content": "hello"}) == "hello"

    @pytest.mark.asyncio
    async def test_execute_streaming(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test")

        chunks: List[str] = []
        async for chunk in adapter.execute_streaming("Test task"):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert "Starting" in chunks[0]
        assert mock_core_agent.execute_called is True

    @pytest.mark.asyncio
    async def test_execute_sync(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test")
        result = await adapter.execute("Test task")

        assert "Starting" in result
        assert "Done" in result

    def test_check_autonomy_allowed(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test")
        allowed, approval = adapter.check_autonomy("safe operation")

        assert allowed is True
        assert approval is None

    def test_check_autonomy_denied(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test")
        allowed, approval = adapter.check_autonomy("dangerous operation")

        assert allowed is False
        assert approval is not None

    def test_get_status(self, mock_core_agent: MockCoreAgent) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test_agent")
        status = adapter.get_status()

        assert status["adapter_name"] == "test_agent"
        assert status["mixin_activated"] is False
        assert status["core_agent_type"] == "MockCoreAgent"
        assert "core_status" in status

    def test_get_pending_approvals_empty(
        self, mock_core_agent: MockCoreAgent
    ) -> None:
        from tui.core.agents.core_adapter import CoreAgentAdapter

        adapter = CoreAgentAdapter(mock_core_agent, "test")
        assert adapter.get_pending_approvals() == []


# =============================================================================
# ORCHESTRATOR INTEGRATION TESTS
# =============================================================================


class TestOrchestrationContext:
    """Tests for OrchestrationContext dataclass."""

    def test_default_values(self) -> None:
        from tui.core.agents.orchestrator_integration import OrchestrationContext

        ctx = OrchestrationContext()
        assert ctx.request_id == ""
        assert ctx.autonomy_level == "L1"
        assert ctx.approval_pending is False
        assert ctx.sub_tasks == []
        assert ctx.executed_tasks == []
        assert ctx.history == []


class TestOrchestratorIntegration:
    """Tests for OrchestratorIntegration."""

    @pytest.fixture
    def mock_agent_manager(self, mock_llm_client: MagicMock) -> MagicMock:
        manager = MagicMock()
        manager.llm_client = mock_llm_client

        async def mock_get_agent(name: str) -> Optional[Any]:
            if name == "orchestrator_core":
                return None  # Simulate unavailable
            return MagicMock()

        manager.get_agent = mock_get_agent

        async def mock_invoke(
            name: str, task: str, context: Optional[Dict[str, Any]] = None
        ) -> AsyncIterator[str]:
            yield f"[{name}] Processing: {task}\n"
            yield f"[{name}] Done.\n"

        manager.invoke = mock_invoke
        return manager

    def test_init(self, mock_agent_manager: MagicMock) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)
        assert integration.agent_manager is mock_agent_manager
        assert integration._orchestrator is None
        assert integration._approval_queue == []

    @pytest.mark.asyncio
    async def test_execute_fallback_when_no_orchestrator(
        self, mock_agent_manager: MagicMock
    ) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)

        chunks: List[str] = []
        async for chunk in integration.execute_orchestrated("Test task"):
            chunks.append(chunk)

        combined = "".join(chunks)
        assert "Fallback" in combined
        assert "planner" in combined.lower()

    def test_set_autonomy_level_valid(
        self, mock_agent_manager: MagicMock
    ) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)

        assert integration.set_autonomy_level("L0") is True
        assert integration._context.autonomy_level == "L0"

        assert integration.set_autonomy_level("l2") is True
        assert integration._context.autonomy_level == "L2"

    def test_set_autonomy_level_invalid(
        self, mock_agent_manager: MagicMock
    ) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)
        original = integration._context.autonomy_level

        assert integration.set_autonomy_level("L5") is False
        assert integration._context.autonomy_level == original

    def test_approve_pending(self, mock_agent_manager: MagicMock) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)
        integration._approval_queue.append({
            "id": "approval-0",
            "operation": "delete files",
            "status": "pending"
        })

        result = integration.approve("approval-0", "admin")

        assert result is True
        assert integration._approval_queue[0]["status"] == "approved"
        assert integration._approval_queue[0]["approved_by"] == "admin"

    def test_approve_not_found(self, mock_agent_manager: MagicMock) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)
        result = integration.approve("nonexistent", "admin")
        assert result is False

    def test_reject_pending(self, mock_agent_manager: MagicMock) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)
        integration._approval_queue.append({
            "id": "approval-0",
            "operation": "delete files",
            "status": "pending"
        })

        result = integration.reject("approval-0", "user")

        assert result is True
        assert integration._approval_queue[0]["status"] == "rejected"

    def test_get_pending_approvals(self, mock_agent_manager: MagicMock) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)
        integration._approval_queue = [
            {"id": "a1", "status": "pending"},
            {"id": "a2", "status": "approved"},
            {"id": "a3", "status": "pending"},
        ]

        pending = integration.get_pending_approvals()
        assert len(pending) == 2
        assert all(a["status"] == "pending" for a in pending)

    def test_get_status(self, mock_agent_manager: MagicMock) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)
        integration._approval_queue.append({"id": "a1", "status": "pending"})
        integration._context.executed_tasks.append("task1")

        status = integration.get_status()

        assert status["orchestrator_available"] is False
        assert status["pending_approvals"] == 1
        assert status["executed_tasks"] == 1

    def test_clear_history(self, mock_agent_manager: MagicMock) -> None:
        from tui.core.agents.orchestrator_integration import OrchestratorIntegration

        integration = OrchestratorIntegration(mock_agent_manager)
        integration._context.history = ["a", "b", "c"]
        integration._context.executed_tasks = ["t1", "t2"]
        integration._approval_queue = [{"id": "a1"}]

        integration.clear_history()

        assert integration._context.history == []
        assert integration._context.executed_tasks == []
        assert integration._approval_queue == []


# =============================================================================
# AGENT MANAGER INTEGRATION TESTS
# =============================================================================


class TestAgentManagerCoreIntegration:
    """Tests for AgentManager with is_core detection."""

    def test_core_agent_detection(self) -> None:
        from tui.core.agents.registry import AGENT_REGISTRY

        core_agents = [
            name for name, info in AGENT_REGISTRY.items() if info.is_core
        ]

        assert "orchestrator_core" in core_agents
        assert "coder_core" in core_agents
        assert "reviewer_core" in core_agents
        assert len(core_agents) >= 6

    def test_cli_agent_not_core(self) -> None:
        from tui.core.agents.registry import AGENT_REGISTRY

        cli_agents = ["planner", "executor", "explorer", "architect"]
        for name in cli_agents:
            if name in AGENT_REGISTRY:
                assert AGENT_REGISTRY[name].is_core is False


# =============================================================================
# SUMMARY
# =============================================================================


def test_phase6_1_summary() -> None:
    """Summary test ensuring all Phase 6.1 components exist."""
    # CoreAgentAdapter
    from tui.core.agents.core_adapter import CoreAgentAdapter, CoreAgentContext

    assert CoreAgentAdapter is not None
    assert CoreAgentContext is not None

    # OrchestratorIntegration
    from tui.core.agents.orchestrator_integration import (
        OrchestratorIntegration,
        OrchestrationContext,
    )

    assert OrchestratorIntegration is not None
    assert OrchestrationContext is not None

    # Exports from __init__
    from tui.core.agents import (
        CoreAgentAdapter as CA,
        CoreAgentContext as CC,
        OrchestratorIntegration as OI,
        OrchestrationContext as OC,
    )

    assert CA is CoreAgentAdapter
    assert CC is CoreAgentContext
    assert OI is OrchestratorIntegration
    assert OC is OrchestrationContext
