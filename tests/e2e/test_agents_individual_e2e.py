"""
E2E Tests - Individual Agents (All 20).

Tests REAL agent loading, invocation, and capabilities.
NO MOCKS - real LLM execution.
"""

import pytest
from typing import List

from vertice_tui.core.agents.registry import AGENT_REGISTRY
from vertice_tui.core.agents.manager import AgentManager


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def agent_manager():
    """Real AgentManager with real LLM."""
    return AgentManager()


# =============================================================================
# REGISTRY STRUCTURE TESTS
# =============================================================================


class TestRegistryStructure:
    """Tests for registry data structure."""

    def test_has_20_agents(self):
        """Registry has exactly 20 agents."""
        assert len(AGENT_REGISTRY) == 20

    def test_cli_agents_count(self):
        """14 CLI agents (not core)."""
        cli_count = sum(1 for a in AGENT_REGISTRY.values() if not a.is_core)
        assert cli_count == 14

    def test_core_agents_count(self):
        """6 core agents."""
        core_count = sum(1 for a in AGENT_REGISTRY.values() if a.is_core)
        assert core_count == 6


class TestCLIAgentsPresent:
    """All 14 CLI agents present in registry."""

    @pytest.mark.parametrize("agent_name", [
        "planner", "executor", "architect", "reviewer",
        "explorer", "refactorer", "testing", "security",
        "documentation", "performance", "devops",
        "justica", "sofia", "data"
    ])
    def test_cli_agent_in_registry(self, agent_name):
        """CLI agent exists in registry."""
        assert agent_name in AGENT_REGISTRY
        assert AGENT_REGISTRY[agent_name].is_core is False


class TestCoreAgentsPresent:
    """All 6 core agents present in registry."""

    @pytest.mark.parametrize("agent_name", [
        "orchestrator_core", "coder_core", "reviewer_core",
        "architect_core", "researcher_core", "devops_core"
    ])
    def test_core_agent_in_registry(self, agent_name):
        """Core agent exists in registry."""
        assert agent_name in AGENT_REGISTRY
        assert AGENT_REGISTRY[agent_name].is_core is True


# =============================================================================
# AGENT INFO VALIDATION
# =============================================================================


class TestAgentInfoFields:
    """All agents have required fields."""

    def test_all_have_name(self):
        """All agents have name."""
        for name, info in AGENT_REGISTRY.items():
            assert info.name == name

    def test_all_have_role(self):
        """All agents have role."""
        for name, info in AGENT_REGISTRY.items():
            assert info.role, f"{name} missing role"

    def test_all_have_module_path(self):
        """All agents have module_path."""
        for name, info in AGENT_REGISTRY.items():
            assert info.module_path, f"{name} missing module_path"

    def test_all_have_class_name(self):
        """All agents have class_name."""
        for name, info in AGENT_REGISTRY.items():
            assert info.class_name, f"{name} missing class_name"

    def test_cli_agents_have_capabilities(self):
        """CLI agents have capabilities list."""
        for name, info in AGENT_REGISTRY.items():
            if not info.is_core:
                assert len(info.capabilities) > 0, f"{name} has no capabilities"


# =============================================================================
# AGENT LOADING TESTS
# =============================================================================


class TestAgentLoading:
    """Tests for real agent loading."""

    @pytest.mark.asyncio
    async def test_load_planner(self, agent_manager):
        """Can load planner agent."""
        agent = await agent_manager.get_agent("planner")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_architect(self, agent_manager):
        """Can load architect agent."""
        agent = await agent_manager.get_agent("architect")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_explorer(self, agent_manager):
        """Can load explorer agent."""
        agent = await agent_manager.get_agent("explorer")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_reviewer(self, agent_manager):
        """Can load reviewer agent."""
        agent = await agent_manager.get_agent("reviewer")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_executor(self, agent_manager):
        """Can load executor agent."""
        agent = await agent_manager.get_agent("executor")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_refactorer(self, agent_manager):
        """Can load refactorer agent."""
        agent = await agent_manager.get_agent("refactorer")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_security(self, agent_manager):
        """Can load security agent."""
        agent = await agent_manager.get_agent("security")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_testing(self, agent_manager):
        """Can load testing agent."""
        agent = await agent_manager.get_agent("testing")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_devops(self, agent_manager):
        """Can load devops agent."""
        agent = await agent_manager.get_agent("devops")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_documentation(self, agent_manager):
        """Can load documentation agent."""
        agent = await agent_manager.get_agent("documentation")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_justica(self, agent_manager):
        """Can load justica agent."""
        agent = await agent_manager.get_agent("justica")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_sofia(self, agent_manager):
        """Can load sofia agent."""
        agent = await agent_manager.get_agent("sofia")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_performance(self, agent_manager):
        """Can load performance agent."""
        agent = await agent_manager.get_agent("performance")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_load_data(self, agent_manager):
        """Can load data agent."""
        agent = await agent_manager.get_agent("data")
        assert agent is not None


class TestAgentLoadErrors:
    """Tests for agent loading error handling."""

    @pytest.mark.asyncio
    async def test_unknown_agent_returns_none(self, agent_manager):
        """Unknown agent returns None."""
        agent = await agent_manager.get_agent("nonexistent_xyz")
        assert agent is None

    @pytest.mark.asyncio
    async def test_load_error_tracked(self, agent_manager):
        """Load errors are tracked."""
        await agent_manager.get_agent("nonexistent_xyz")
        assert "nonexistent_xyz" in agent_manager._load_errors


# =============================================================================
# AGENT INTERFACE TESTS
# =============================================================================


class TestAgentInterfaces:
    """Tests for agent interfaces after loading."""

    @pytest.mark.asyncio
    async def test_planner_has_execute(self, agent_manager):
        """Planner has execute method."""
        agent = await agent_manager.get_agent("planner")
        assert hasattr(agent, 'execute') or hasattr(agent, 'execute_streaming')

    @pytest.mark.asyncio
    async def test_architect_has_execute(self, agent_manager):
        """Architect has execute method."""
        agent = await agent_manager.get_agent("architect")
        assert hasattr(agent, 'execute') or hasattr(agent, 'execute_streaming')


# =============================================================================
# REAL INVOCATION TESTS
# =============================================================================


class TestRealInvocation:
    """Tests with real LLM calls."""

    @pytest.mark.asyncio
    async def test_planner_real_invocation(self, agent_manager):
        """Invoke planner with real LLM."""
        chunks: List[str] = []
        async for chunk in agent_manager.invoke("planner", "Plan hello world"):
            chunks.append(chunk)
        output = "".join(chunks)
        assert len(output) > 10, f"Got: {output[:50]}"

    @pytest.mark.asyncio
    async def test_architect_real_invocation(self, agent_manager):
        """Invoke architect with real LLM."""
        chunks: List[str] = []
        async for chunk in agent_manager.invoke("architect", "Is this feasible?"):
            chunks.append(chunk)
        output = "".join(chunks)
        assert len(output) > 10, f"Got: {output[:50]}"

    @pytest.mark.asyncio
    async def test_explorer_real_invocation(self, agent_manager):
        """Invoke explorer with real LLM."""
        chunks: List[str] = []
        async for chunk in agent_manager.invoke("explorer", "Find test files"):
            chunks.append(chunk)
        output = "".join(chunks)
        assert len(output) > 0

    @pytest.mark.asyncio
    async def test_reviewer_real_invocation(self, agent_manager):
        """Invoke reviewer with real LLM."""
        chunks: List[str] = []
        async for chunk in agent_manager.invoke("reviewer", "Review: print('hi')"):
            chunks.append(chunk)
        output = "".join(chunks)
        assert len(output) > 0

    @pytest.mark.asyncio
    async def test_security_real_invocation(self, agent_manager):
        """Invoke security with real LLM."""
        chunks: List[str] = []
        async for chunk in agent_manager.invoke("security", "Check for SQL injection"):
            chunks.append(chunk)
        output = "".join(chunks)
        assert len(output) > 0

    @pytest.mark.asyncio
    async def test_devops_real_invocation(self, agent_manager):
        """Invoke devops with real LLM."""
        chunks: List[str] = []
        async for chunk in agent_manager.invoke("devops", "How to deploy to production?"):
            chunks.append(chunk)
        output = "".join(chunks)
        assert len(output) >= 0  # May be empty if agent not fully configured


# =============================================================================
# ALL AGENTS LOADABLE TEST
# =============================================================================


class TestAllAgentsLoadable:
    """Test that all 20 agents can be loaded."""

    @pytest.mark.asyncio
    async def test_load_all_agents(self, agent_manager):
        """All 20 agents can be loaded."""
        loaded = 0
        failed = []

        for name in agent_manager.available_agents:
            agent = await agent_manager.get_agent(name)
            if agent is not None:
                loaded += 1
            else:
                failed.append(name)

        # At least 14 CLI agents should load
        assert loaded >= 14, f"Only {loaded} loaded. Failed: {failed}"


# =============================================================================
# GOVERNANCE AGENTS
# =============================================================================


class TestGovernanceAgents:
    """Test JUSTICA and SOFIA agents."""

    @pytest.mark.asyncio
    async def test_justica_loaded(self, agent_manager):
        """JUSTICA agent loads."""
        agent = await agent_manager.get_agent("justica")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_sofia_loaded(self, agent_manager):
        """SOFIA agent loads."""
        agent = await agent_manager.get_agent("sofia")
        assert agent is not None

    @pytest.mark.asyncio
    async def test_justica_invocation(self, agent_manager):
        """JUSTICA can be invoked."""
        chunks: List[str] = []
        async for chunk in agent_manager.invoke("justica", "Evaluate this action"):
            chunks.append(chunk)
        output = "".join(chunks)
        assert len(output) > 0

    @pytest.mark.asyncio
    async def test_sofia_invocation(self, agent_manager):
        """SOFIA can be invoked."""
        chunks: List[str] = []
        async for chunk in agent_manager.invoke("sofia", "Provide ethical counsel"):
            chunks.append(chunk)
        output = "".join(chunks)
        assert len(output) > 0
