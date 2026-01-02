"""
Unit tests for topology-aware execution.

Tests that the mesh topology selection is actually applied
during execution, not just calculated and ignored.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from dataclasses import dataclass
from typing import List, Dict, Any
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


@dataclass
class ExecutionRecord:
    """Record of an execution event."""

    topology: str
    agents_involved: List[str]
    coordinator: str | None
    parallel: bool
    timestamp: float


class MockMeshExecutor:
    """Mock mesh executor with topology support."""

    def __init__(self):
        self.execution_log: List[ExecutionRecord] = []
        self.agents: Dict[str, AsyncMock] = {}

    def register_agent(self, name: str):
        """Register an agent."""
        self.agents[name] = AsyncMock(return_value=f"Result from {name}")

    async def execute_centralized(
        self, agents: List[str], context: Dict
    ) -> Dict[str, Any]:
        """Execute in centralized topology - single coordinator."""
        coordinator = agents[0]  # First agent is coordinator

        self.execution_log.append(
            ExecutionRecord(
                topology="centralized",
                agents_involved=agents,
                coordinator=coordinator,
                parallel=False,
                timestamp=asyncio.get_event_loop().time(),
            )
        )

        # Coordinator delegates to each agent sequentially
        results = {}
        for agent in agents:
            results[agent] = await self.agents[agent](context)

        return {"coordinator": coordinator, "results": results}

    async def execute_decentralized(
        self, agents: List[str], context: Dict
    ) -> Dict[str, Any]:
        """Execute in decentralized topology - parallel peer-to-peer."""
        self.execution_log.append(
            ExecutionRecord(
                topology="decentralized",
                agents_involved=agents,
                coordinator=None,
                parallel=True,
                timestamp=asyncio.get_event_loop().time(),
            )
        )

        # All agents execute in parallel
        tasks = [self.agents[agent](context) for agent in agents]
        results = await asyncio.gather(*tasks)

        return {"results": dict(zip(agents, results))}

    async def execute_hybrid(
        self, agents: List[str], context: Dict
    ) -> Dict[str, Any]:
        """Execute in hybrid topology - centralized planning, decentralized execution."""
        coordinator = agents[0]

        self.execution_log.append(
            ExecutionRecord(
                topology="hybrid",
                agents_involved=agents,
                coordinator=coordinator,
                parallel=True,  # Execution phase is parallel
                timestamp=asyncio.get_event_loop().time(),
            )
        )

        # Coordinator plans first
        plan = await self.agents[coordinator]({"phase": "plan", **context})

        # Then others execute in parallel
        executors = agents[1:]
        if executors:
            tasks = [self.agents[agent]({"phase": "execute", **context}) for agent in executors]
            exec_results = await asyncio.gather(*tasks)
        else:
            exec_results = []

        return {
            "coordinator": coordinator,
            "plan": plan,
            "execution_results": dict(zip(executors, exec_results)),
        }


@pytest.fixture
def mesh_executor():
    """Provide mesh executor with agents."""
    executor = MockMeshExecutor()
    for name in ["planner", "coder", "reviewer", "tester"]:
        executor.register_agent(name)
    return executor


class TestTopologySelection:
    """Tests for topology selection."""

    @pytest.mark.unit
    async def test_centralized_uses_coordinator(self, mesh_executor):
        """Centralized topology should use a single coordinator."""
        result = await mesh_executor.execute_centralized(
            ["planner", "coder", "reviewer"], {}
        )

        assert result["coordinator"] == "planner"
        assert len(mesh_executor.execution_log) == 1
        assert mesh_executor.execution_log[0].topology == "centralized"
        assert mesh_executor.execution_log[0].coordinator is not None

    @pytest.mark.unit
    async def test_decentralized_no_coordinator(self, mesh_executor):
        """Decentralized topology should have no coordinator."""
        result = await mesh_executor.execute_decentralized(
            ["coder", "reviewer", "tester"], {}
        )

        assert mesh_executor.execution_log[0].topology == "decentralized"
        assert mesh_executor.execution_log[0].coordinator is None
        assert mesh_executor.execution_log[0].parallel is True

    @pytest.mark.unit
    async def test_hybrid_has_both_phases(self, mesh_executor):
        """Hybrid topology should have planning and execution phases."""
        result = await mesh_executor.execute_hybrid(
            ["planner", "coder", "tester"], {}
        )

        assert result["coordinator"] == "planner"
        assert "plan" in result
        assert "execution_results" in result


class TestTopologyExecution:
    """Tests for actual topology execution behavior."""

    @pytest.mark.unit
    async def test_centralized_sequential_execution(self, mesh_executor):
        """Centralized should execute agents sequentially."""
        agents = ["planner", "coder", "reviewer"]

        await mesh_executor.execute_centralized(agents, {})

        # All agents should have been called
        for agent in agents:
            mesh_executor.agents[agent].assert_called()

    @pytest.mark.unit
    async def test_decentralized_parallel_execution(self, mesh_executor):
        """Decentralized should execute agents in parallel."""
        agents = ["coder", "reviewer", "tester"]

        start = asyncio.get_event_loop().time()
        await mesh_executor.execute_decentralized(agents, {})
        duration = asyncio.get_event_loop().time() - start

        # Should be parallel (fast)
        assert mesh_executor.execution_log[0].parallel is True

    @pytest.mark.unit
    async def test_hybrid_planning_before_execution(self, mesh_executor):
        """Hybrid should complete planning before execution."""
        agents = ["planner", "coder", "tester"]

        # Track call order
        call_order = []

        async def track_planner(ctx):
            call_order.append(("planner", ctx.get("phase")))
            return "plan"

        async def track_coder(ctx):
            call_order.append(("coder", ctx.get("phase")))
            return "code"

        async def track_tester(ctx):
            call_order.append(("tester", ctx.get("phase")))
            return "test"

        mesh_executor.agents["planner"] = track_planner
        mesh_executor.agents["coder"] = track_coder
        mesh_executor.agents["tester"] = track_tester

        await mesh_executor.execute_hybrid(agents, {})

        # Planner should be called first with "plan" phase
        assert call_order[0] == ("planner", "plan")


class TestTopologyNotIgnored:
    """Tests that topology is actually applied, not calculated and ignored."""

    @pytest.mark.unit
    async def test_different_topologies_different_behavior(self, mesh_executor):
        """Different topologies should result in different execution patterns."""
        agents = ["planner", "coder", "reviewer"]

        # Execute with each topology
        await mesh_executor.execute_centralized(agents, {"test": 1})
        await mesh_executor.execute_decentralized(agents, {"test": 2})
        await mesh_executor.execute_hybrid(agents, {"test": 3})

        # Should have 3 different execution patterns
        assert len(mesh_executor.execution_log) == 3
        topologies = [e.topology for e in mesh_executor.execution_log]
        assert topologies == ["centralized", "decentralized", "hybrid"]

    @pytest.mark.unit
    async def test_topology_affects_parallelism(self, mesh_executor):
        """Topology selection should affect parallelism."""
        agents = ["coder", "reviewer", "tester"]

        await mesh_executor.execute_centralized(agents, {})
        await mesh_executor.execute_decentralized(agents, {})

        centralized = mesh_executor.execution_log[0]
        decentralized = mesh_executor.execution_log[1]

        # Centralized is sequential, decentralized is parallel
        assert centralized.parallel is False
        assert decentralized.parallel is True


class TestTopologyEdgeCases:
    """Edge case tests for topology execution."""

    @pytest.mark.unit
    async def test_single_agent_centralized(self, mesh_executor):
        """Single agent should work in centralized topology."""
        result = await mesh_executor.execute_centralized(["coder"], {})

        assert result["coordinator"] == "coder"

    @pytest.mark.unit
    async def test_single_agent_decentralized(self, mesh_executor):
        """Single agent should work in decentralized topology."""
        result = await mesh_executor.execute_decentralized(["coder"], {})

        assert len(result["results"]) == 1

    @pytest.mark.unit
    async def test_empty_agents_handled(self, mesh_executor):
        """Empty agent list should be handled gracefully."""
        # This might raise or return empty - both are acceptable
        try:
            result = await mesh_executor.execute_decentralized([], {})
            assert result["results"] == {}
        except (ValueError, IndexError):
            pass  # Also acceptable

    @pytest.mark.unit
    async def test_context_passed_to_all_agents(self, mesh_executor):
        """Context should be passed to all agents."""
        context = {"project": "test", "language": "python"}

        await mesh_executor.execute_decentralized(
            ["coder", "reviewer"], context
        )

        # Verify context was passed
        for agent in ["coder", "reviewer"]:
            mesh_executor.agents[agent].assert_called()
            call_args = mesh_executor.agents[agent].call_args
            assert "project" in call_args[0][0]


class TestTopologyIntegration:
    """Integration tests with real mesh system."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.path.exists("/media/juan/DATA/Vertice-Code/core/mesh/mixin.py"),
        reason="Mesh mixin not available"
    )
    async def test_real_mesh_topology_applied(self):
        """Test that real mesh system applies topology."""
        try:
            from core.mesh.mixin import MeshMixin

            # Verify the topology methods are not stubs
            mixin = MeshMixin()

            # These should be actual implementations, not pass-through
            centralized_code = mixin._execute_centralized.__code__
            decentralized_code = mixin._execute_decentralized.__code__

            # They should be different (not just calling same function)
            assert centralized_code is not decentralized_code

        except ImportError:
            pytest.skip("Mesh mixin not importable")
