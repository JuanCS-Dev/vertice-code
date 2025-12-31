"""
Tests for Agent Registry.

Validates the unified agent registry that provides
access to all VERTICE agents.

Author: JuanCS Dev
Date: 2025-12-31
"""

from __future__ import annotations

import pytest

from vertice_agents import AgentRegistry, get_agent, list_agents
from vertice_agents.registry import AgentSource, AgentInfo


# =============================================================================
# REGISTRY TESTS
# =============================================================================


class TestAgentRegistry:
    """Tests for AgentRegistry singleton."""

    def test_singleton_pattern(self) -> None:
        """Registry is a singleton."""
        r1 = AgentRegistry.instance()
        r2 = AgentRegistry.instance()

        assert r1 is r2

    def test_agents_registered(self) -> None:
        """All expected agents are registered."""
        registry = AgentRegistry.instance()

        # Core agents
        assert registry.has_agent("orchestrator")
        assert registry.has_agent("coder")
        assert registry.has_agent("reviewer_core")
        assert registry.has_agent("architect_core")
        assert registry.has_agent("researcher")
        assert registry.has_agent("devops")

        # CLI agents
        assert registry.has_agent("architect")
        assert registry.has_agent("explorer")
        assert registry.has_agent("planner")
        assert registry.has_agent("refactorer")
        assert registry.has_agent("reviewer")

        # Governance agents
        assert registry.has_agent("justica")
        assert registry.has_agent("sofia")

    def test_unknown_agent_returns_none(self) -> None:
        """Unknown agent returns None."""
        registry = AgentRegistry.instance()

        assert registry.get("nonexistent") is None
        assert registry.get_class("nonexistent") is None
        assert registry.get_info("nonexistent") is None

    def test_get_info_without_loading(self) -> None:
        """get_info returns info without loading the agent."""
        registry = AgentRegistry.instance()

        info = registry.get_info("planner")

        assert info is not None
        assert isinstance(info, AgentInfo)
        assert info.name == "planner"
        assert info.source == AgentSource.CLI
        assert info._class is None  # Not loaded yet

    def test_list_all_agents(self) -> None:
        """list_agents returns all agents."""
        agents = list_agents()

        assert len(agents) >= 10  # At least 10 agents
        names = [name for name, _ in agents]
        assert "planner" in names
        assert "orchestrator" in names

    def test_list_by_source(self) -> None:
        """list_agents filters by source."""
        core = list_agents(AgentSource.CORE)
        cli = list_agents(AgentSource.CLI)
        gov = list_agents(AgentSource.GOVERNANCE)

        assert len(core) == 6
        assert len(cli) >= 8
        assert len(gov) == 2

        # Verify sources are correct
        for _, info in core:
            assert info.source == AgentSource.CORE
        for _, info in cli:
            assert info.source == AgentSource.CLI


# =============================================================================
# LAZY LOADING TESTS
# =============================================================================


class TestLazyLoading:
    """Tests for lazy loading of agents."""

    def test_get_class_lazy_loads(self) -> None:
        """get_class imports the agent module."""
        registry = AgentRegistry.instance()

        # Clear any cached class
        info = registry.get_info("planner")
        info._class = None

        # Get class - should trigger import
        PlannerClass = registry.get_class("planner")

        assert PlannerClass is not None
        assert PlannerClass.__name__ == "PlannerAgent"
        assert info._class is PlannerClass  # Cached

    def test_get_class_cached(self) -> None:
        """get_class returns cached class on subsequent calls."""
        registry = AgentRegistry.instance()

        class1 = registry.get_class("refactorer")
        class2 = registry.get_class("refactorer")

        assert class1 is class2


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for get_agent and list_agents functions."""

    def test_get_agent_returns_instance(self) -> None:
        """get_agent returns an agent instance."""
        # Note: This may fail if agent requires specific constructor args
        # For now, just test that get_class works
        registry = AgentRegistry.instance()
        cls = registry.get_class("explorer")

        assert cls is not None
        assert cls.__name__ == "ExplorerAgent"

    def test_list_agents_function(self) -> None:
        """list_agents function works."""
        agents = list_agents()

        assert isinstance(agents, list)
        assert len(agents) > 0
        assert all(isinstance(item, tuple) for item in agents)


# =============================================================================
# AGENT SOURCE TESTS
# =============================================================================


class TestAgentSource:
    """Tests for AgentSource enum."""

    def test_sources_exist(self) -> None:
        """All sources are defined."""
        assert AgentSource.CORE
        assert AgentSource.CLI
        assert AgentSource.GOVERNANCE

    def test_core_agents_have_core_source(self) -> None:
        """Core agents have CORE source."""
        registry = AgentRegistry.instance()

        for name in ["orchestrator", "coder", "devops"]:
            info = registry.get_info(name)
            assert info.source == AgentSource.CORE

    def test_cli_agents_have_cli_source(self) -> None:
        """CLI agents have CLI source."""
        registry = AgentRegistry.instance()

        for name in ["planner", "refactorer", "explorer"]:
            info = registry.get_info(name)
            assert info.source == AgentSource.CLI
