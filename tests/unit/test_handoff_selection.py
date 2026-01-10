"""
Tests for AgentSelector - Sprint 2 Refactoring.

Tests cover:
    - AgentSelector initialization and configuration
    - Agent selection by capabilities
    - Escalation chain logic
    - Edge cases and error handling
    - Priority and scoring mechanisms
"""

import pytest
from vertice_core.agents.handoff.selection import AgentSelector
from vertice_core.agents.router.types import AgentType
from vertice_core.agents.handoff.types import AgentCapability, EscalationChain, HandoffReason


class TestAgentSelectorInitialization:
    """Test AgentSelector initialization and configuration."""

    def test_initialization_with_capabilities_and_chains(self) -> None:
        """Test initialization with capabilities and escalation chains."""
        capabilities = {
            AgentType.ARCHITECT: AgentCapability(
                agent_type=AgentType.ARCHITECT,
                capabilities={"design", "plan"},
                priority=1,
            ),
            AgentType.EXECUTOR: AgentCapability(
                agent_type=AgentType.EXECUTOR,
                capabilities={"execute", "run"},
                priority=2,
            ),
        }

        chains = [
            EscalationChain(
                name="basic_chain",
                chain=[AgentType.ARCHITECT, AgentType.EXECUTOR],
            )
        ]

        selector = AgentSelector(capabilities, chains)

        assert selector.capabilities == capabilities
        assert selector.escalation_chains == chains

    def test_initialization_with_empty_capabilities(self) -> None:
        """Test initialization with empty capabilities."""
        selector = AgentSelector({}, [])

        assert selector.capabilities == {}
        assert selector.escalation_chains == []

    def test_initialization_with_none_values_raises_error(self) -> None:
        """Test that initialization with None values raises error."""
        with pytest.raises(AttributeError):
            AgentSelector(None, None)  # type: ignore


class TestAgentSelection:
    """Test agent selection by capabilities."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.capabilities = {
            AgentType.ARCHITECT: AgentCapability(
                agent_type=AgentType.ARCHITECT,
                capabilities={"design", "plan", "architecture"},
                priority=1,
                can_plan=True,
            ),
            AgentType.EXECUTOR: AgentCapability(
                agent_type=AgentType.EXECUTOR,
                capabilities={"execute", "run", "deploy"},
                priority=2,
                can_execute=True,
            ),
            AgentType.PLANNER: AgentCapability(
                agent_type=AgentType.PLANNER,
                capabilities={"plan", "schedule", "coordinate"},
                priority=3,
                can_plan=True,
            ),
            AgentType.SECURITY: AgentCapability(
                agent_type=AgentType.SECURITY,
                capabilities={"security", "audit", "encrypt"},
                priority=4,
                description="Security specialist",
            ),
        }

        self.chains = [
            EscalationChain(
                name="development_chain",
                chain=[AgentType.ARCHITECT, AgentType.PLANNER, AgentType.EXECUTOR],
            )
        ]

        self.selector = AgentSelector(self.capabilities, self.chains)

    def test_select_agent_single_capability_match(self) -> None:
        """Test selecting agent with single capability match."""
        result = self.selector.select_agent({"design"})

        assert result == AgentType.ARCHITECT

    def test_select_agent_multiple_capabilities_match(self) -> None:
        """Test selecting agent with multiple capability matches."""
        # Both ARCHITECT and PLANNER have "plan"
        result = self.selector.select_agent({"plan"})

        # Should select the one with highest priority (lowest number)
        assert result in [AgentType.ARCHITECT, AgentType.PLANNER]

    def test_select_agent_exact_capability_set(self) -> None:
        """Test selecting agent with exact capability set."""
        result = self.selector.select_agent({"execute", "run", "deploy"})

        assert result == AgentType.EXECUTOR

    def test_select_agent_no_match_returns_none(self) -> None:
        """Test that no match returns None."""
        result = self.selector.select_agent({"nonexistent_capability"})

        assert result is None

    def test_select_agent_empty_capabilities(self) -> None:
        """Test selecting with empty required capabilities."""
        result = self.selector.select_agent(set())

        # Should return some agent (implementation dependent)
        assert result is not None

    def test_select_agent_with_exclusion(self) -> None:
        """Test selecting agent with exclusion list."""
        # Exclude ARCHITECT, should get another agent
        result = self.selector.select_agent({"plan"}, exclude={AgentType.ARCHITECT})

        assert result == AgentType.PLANNER

    def test_select_agent_exclude_all_candidates(self) -> None:
        """Test selecting when all candidates are excluded."""
        result = self.selector.select_agent(
            {"design"},
            exclude={
                AgentType.ARCHITECT,
                AgentType.PLANNER,
                AgentType.EXECUTOR,
                AgentType.SECURITY,
            },
        )

        assert result is None

    def test_select_agent_prefer_escalation(self) -> None:
        """Test selecting with escalation preference."""
        # This might affect priority scoring
        result = self.selector.select_agent({"design"}, prefer_escalation=True)

        assert result is not None  # Should still select an agent

    def test_select_agent_priority_ordering(self) -> None:
        """Test that agents are selected by priority order."""
        # Both ARCHITECT (priority 1) and PLANNER (priority 3) have "plan"
        # ARCHITECT should be selected due to higher priority (lower number)
        result = self.selector.select_agent({"plan"})

        assert result == AgentType.ARCHITECT


class TestEscalationLogic:
    """Test escalation chain logic."""

    def setup_method(self) -> None:
        """Setup test fixtures."""
        self.capabilities = {
            AgentType.ARCHITECT: AgentCapability(
                agent_type=AgentType.ARCHITECT,
                capabilities={"design"},
                priority=1,
            ),
            AgentType.PLANNER: AgentCapability(
                agent_type=AgentType.PLANNER,
                capabilities={"plan"},
                priority=2,
            ),
            AgentType.EXECUTOR: AgentCapability(
                agent_type=AgentType.EXECUTOR,
                capabilities={"execute"},
                priority=3,
            ),
        }

        self.chains = [
            EscalationChain(
                name="development_chain",
                chain=[AgentType.ARCHITECT, AgentType.PLANNER, AgentType.EXECUTOR],
            ),
            EscalationChain(
                name="simple_chain",
                chain=[AgentType.ARCHITECT, AgentType.EXECUTOR],
            ),
        ]

        self.selector = AgentSelector(self.capabilities, self.chains)

    def test_get_escalation_target_basic(self) -> None:
        """Test getting basic escalation target."""
        target = self.selector.get_escalation_target(AgentType.ARCHITECT, HandoffReason.ESCALATION)

        assert target == AgentType.PLANNER  # Next in development_chain

    def test_get_escalation_target_last_in_chain(self) -> None:
        """Test escalation when agent is last in chain."""
        target = self.selector.get_escalation_target(AgentType.EXECUTOR, HandoffReason.ESCALATION)

        assert target is None  # No next agent

    def test_get_escalation_target_not_in_chain(self) -> None:
        """Test escalation for agent not in any chain."""
        # Add an agent not in chains
        self.capabilities[AgentType.SECURITY] = AgentCapability(
            agent_type=AgentType.SECURITY,
            capabilities={"security"},
            priority=4,
        )

        target = self.selector.get_escalation_target(AgentType.SECURITY, HandoffReason.ESCALATION)

        assert target is None  # Not in any chain

    def test_get_escalation_target_with_chain_name(self) -> None:
        """Test escalation with specific chain name."""
        target = self.selector.get_escalation_target(
            AgentType.ARCHITECT, HandoffReason.ESCALATION, chain_name="simple_chain"
        )

        assert target == AgentType.EXECUTOR  # Next in simple_chain

    def test_get_escalation_target_unknown_chain_name(self) -> None:
        """Test escalation with unknown chain name."""
        target = self.selector.get_escalation_target(
            AgentType.ARCHITECT, HandoffReason.ESCALATION, chain_name="unknown_chain"
        )

        assert target is None  # No matching chain

    def test_get_escalation_target_middle_of_chain(self) -> None:
        """Test escalation from middle of chain."""
        target = self.selector.get_escalation_target(AgentType.PLANNER, HandoffReason.ESCALATION)

        assert target == AgentType.EXECUTOR  # Next after PLANNER


class TestAgentCapabilityLogic:
    """Test agent capability matching logic."""

    def test_capability_can_handle_single_capability(self) -> None:
        """Test capability matching for single capability."""
        capability = AgentCapability(
            agent_type=AgentType.ARCHITECT,
            capabilities={"design", "plan"},
            priority=1,
        )

        assert capability.can_handle({"design"})
        assert capability.can_handle({"plan"})
        assert not capability.can_handle({"execute"})

    def test_capability_can_handle_multiple_capabilities(self) -> None:
        """Test capability matching for multiple capabilities."""
        capability = AgentCapability(
            agent_type=AgentType.EXECUTOR,
            capabilities={"execute", "run", "deploy"},
            priority=2,
        )

        assert capability.can_handle({"execute", "run"})
        assert capability.can_handle({"execute", "deploy"})
        assert capability.can_handle({"run", "deploy"})
        assert not capability.can_handle({"execute", "security"})  # Missing security

    def test_capability_can_handle_empty_set(self) -> None:
        """Test capability matching for empty capability set."""
        capability = AgentCapability(
            agent_type=AgentType.ARCHITECT,
            capabilities={"design", "plan"},
            priority=1,
        )

        assert capability.can_handle(set())  # Empty set should match

    def test_capability_can_handle_exact_match(self) -> None:
        """Test capability matching for exact set match."""
        capability = AgentCapability(
            agent_type=AgentType.SECURITY,
            capabilities={"security", "audit"},
            priority=3,
        )

        assert capability.can_handle({"security", "audit"})
        assert not capability.can_handle({"security", "audit", "extra"})  # Too many


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_select_agent_with_none_exclude(self) -> None:
        """Test selecting agent with None exclude parameter."""
        capabilities = {
            AgentType.ARCHITECT: AgentCapability(
                agent_type=AgentType.ARCHITECT,
                capabilities={"design"},
                priority=1,
            )
        }

        selector = AgentSelector(capabilities, [])

        # Should work with None exclude (converted to empty set)
        result = selector.select_agent({"design"}, exclude=None)

        assert result == AgentType.ARCHITECT

    def test_empty_capabilities_dict(self) -> None:
        """Test behavior with empty capabilities dictionary."""
        selector = AgentSelector({}, [])

        result = selector.select_agent({"any_capability"})

        assert result is None

    def test_capability_priority_scoring(self) -> None:
        """Test that priority affects selection order."""
        capabilities = {
            AgentType.ARCHITECT: AgentCapability(
                agent_type=AgentType.ARCHITECT,
                capabilities={"design"},
                priority=10,  # Lower priority
            ),
            AgentType.PLANNER: AgentCapability(
                agent_type=AgentType.PLANNER,
                capabilities={"design"},
                priority=1,  # Higher priority (lower number)
            ),
        }

        selector = AgentSelector(capabilities, [])

        result = selector.select_agent({"design"})

        # Should select PLANNER due to higher priority (lower number)
        assert result == AgentType.PLANNER

    def test_escalation_chains_empty(self) -> None:
        """Test escalation with empty chains list."""
        capabilities = {
            AgentType.ARCHITECT: AgentCapability(
                agent_type=AgentType.ARCHITECT,
                capabilities={"design"},
                priority=1,
            )
        }

        selector = AgentSelector(capabilities, [])

        target = selector.get_escalation_target(AgentType.ARCHITECT, HandoffReason.ESCALATION)

        assert target is None  # No chains available
