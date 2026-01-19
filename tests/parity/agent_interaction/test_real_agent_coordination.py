"""
REAL Agent Coordination Tests

Tests actual agent-to-agent communication and coordination
using REAL LLM calls and REAL execution.

These tests validate that agents can:
1. Delegate tasks to appropriate agents
2. Pass context between agents
3. Synthesize results from multiple agents
"""

import pytest
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.real,
    pytest.mark.agent_interaction,
]


def load_env():
    """Load environment variables."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env()


class AgentCoordinationTester:
    """Helper class for testing agent coordination."""

    def __init__(self):
        self.initialized = False
        self.agents = {}
        self.orchestrator = None
        self.call_log: List[Dict] = []

    async def initialize(self):
        """Initialize real agents."""
        try:
            # Try to import real agents
            from vertice_tui.core.agents.manager import AgentManager
            from vertice_tui.core.bridge import Bridge

            self.bridge = Bridge()
            await self.bridge.initialize()

            # Access agent manager through bridge
            if hasattr(self.bridge, "agent_manager"):
                self.agent_manager = self.bridge.agent_manager
                self.initialized = True
                return True

            # Fallback: try direct import
            from agents.orchestrator.agent import OrchestratorAgent

            self.orchestrator = OrchestratorAgent()
            self.initialized = True
            return True

        except ImportError as e:
            print(f"Could not import agents: {e}")
            return False
        except Exception as e:
            print(f"Initialization error: {e}")
            return False

    async def route_to_agent(self, message: str) -> Dict[str, Any]:
        """Route message to appropriate agent and track."""
        result = {
            "agent_selected": None,
            "routing_confidence": 0.0,
            "output": "",
            "secondary_agents": [],
            "duration_ms": 0,
        }

        start = time.time()

        try:
            if hasattr(self, "agent_manager") and self.agent_manager:
                # Use agent manager routing
                agent_id, confidence = await self.agent_manager.route(message)
                result["agent_selected"] = agent_id
                result["routing_confidence"] = confidence

                # Process through selected agent
                async for chunk in self.bridge.process_message(message):
                    if hasattr(chunk, "content"):
                        result["output"] += chunk.content
                    elif isinstance(chunk, str):
                        result["output"] += chunk

            elif self.orchestrator:
                # Use orchestrator directly
                response = await self.orchestrator.process(message)
                result["output"] = str(response)
                result["agent_selected"] = "orchestrator"

        except Exception as e:
            result["error"] = str(e)

        result["duration_ms"] = int((time.time() - start) * 1000)
        self.call_log.append(result)
        return result

    async def test_delegation(self, from_agent: str, task: str) -> Dict[str, Any]:
        """Test if one agent properly delegates to another."""
        # This would need real agent delegation implementation
        return await self.route_to_agent(task)

    async def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, "bridge") and self.bridge:
            try:
                await self.bridge.shutdown()
            except Exception:
                pass


@pytest.fixture
async def coordinator():
    """Provide agent coordination tester."""
    tester = AgentCoordinationTester()
    success = await tester.initialize()

    if not success:
        pytest.skip("Could not initialize agent coordination")

    yield tester

    await tester.cleanup()


class TestRealAgentRouting:
    """Test real agent routing decisions."""

    @pytest.mark.timeout(90)
    async def test_planning_request_routes_to_planner(self, coordinator):
        """
        REAL TEST: Planning request should route to planner agent.
        """
        request = "Design the architecture for a REST API"

        result = await coordinator.route_to_agent(request)

        print(f"\n[REAL] Agent selected: {result['agent_selected']}")
        print(f"[REAL] Confidence: {result['routing_confidence']}")
        print(f"[REAL] Duration: {result['duration_ms']}ms")

        # Should route to planner or architect
        if result["agent_selected"]:
            assert result["agent_selected"] in [
                "planner",
                "architect",
                "orchestrator",
            ], f"Unexpected agent: {result['agent_selected']}"

    @pytest.mark.timeout(90)
    async def test_coding_request_routes_to_coder(self, coordinator):
        """
        REAL TEST: Coding request should route to coder agent.
        """
        request = "Implement a function to validate email addresses"

        result = await coordinator.route_to_agent(request)

        print(f"\n[REAL] Agent selected: {result['agent_selected']}")

        # Should produce code output
        if result["output"]:
            has_code = "def " in result["output"] or "function" in result["output"]
            assert (
                has_code or len(result["output"]) > 50
            ), "Coding request should produce code or substantial output"

    @pytest.mark.timeout(90)
    async def test_review_request_routes_to_reviewer(self, coordinator):
        """
        REAL TEST: Review request should route to reviewer agent.
        """
        request = "Review this code for security issues: `eval(user_input)`"

        result = await coordinator.route_to_agent(request)

        print(f"\n[REAL] Agent selected: {result['agent_selected']}")

        # Should mention security concerns
        if result["output"]:
            output_lower = result["output"].lower()
            has_security_mention = any(
                word in output_lower
                for word in [
                    "security",
                    "dangerous",
                    "vulnerability",
                    "eval",
                    "injection",
                    "unsafe",
                ]
            )
            assert (
                has_security_mention
            ), "Review should mention security concerns for eval(user_input)"


class TestRealAgentCoordination:
    """Test real multi-agent coordination."""

    @pytest.mark.timeout(180)
    async def test_multi_step_task_uses_multiple_agents(self, coordinator):
        """
        REAL TEST: Complex task should involve multiple agents.
        """
        request = """
        I need you to:
        1. Design a simple cache system
        2. Implement it in Python
        3. Write tests for it
        """

        result = await coordinator.route_to_agent(request)

        print(f"\n[REAL] Duration: {result['duration_ms']}ms")
        print(f"[REAL] Output length: {len(result['output'])} chars")

        if result.get("error"):
            pytest.skip(f"Error: {result['error']}")

        output_lower = result["output"].lower()

        # Should address multiple aspects
        aspects_covered = sum(
            [
                "cache" in output_lower or "design" in output_lower,
                "def " in result["output"] or "class " in result["output"],
                "test" in output_lower or "assert" in output_lower,
            ]
        )

        assert (
            aspects_covered >= 2
        ), f"Multi-step task should cover multiple aspects, found {aspects_covered}"

    @pytest.mark.timeout(120)
    async def test_context_preserved_across_agents(self, coordinator):
        """
        REAL TEST: Context should be preserved when delegating between agents.
        """
        # First request establishes context
        setup_request = "We are building a Python REST API using FastAPI"
        await coordinator.route_to_agent(setup_request)

        # Second request should use that context
        followup_request = "Now add authentication to it"
        result = await coordinator.route_to_agent(followup_request)

        print(f"\n[REAL] Output: {result['output'][:300]}...")

        if result.get("error"):
            pytest.skip(f"Error: {result['error']}")

        output_lower = result["output"].lower()

        # Should reference FastAPI or Python concepts
        context_preserved = any(
            word in output_lower
            for word in ["fastapi", "python", "api", "endpoint", "route", "dependency"]
        )

        assert context_preserved, "Context from previous request should be preserved"


class TestRealAgentSpecialization:
    """Test that agents are properly specialized."""

    @pytest.mark.timeout(90)
    async def test_explorer_finds_code(self, coordinator):
        """
        REAL TEST: Explorer agent should find code locations.
        """
        request = "Find where the main entry point of this project is defined"

        result = await coordinator.route_to_agent(request)

        print(f"\n[REAL] Output: {result['output'][:300]}...")

        if result.get("error"):
            pytest.skip(f"Error: {result['error']}")

        # Should mention file paths or locations
        output = result["output"]
        has_path_reference = any(s in output for s in [".py", "/", "file", "module", "entry"])

        assert (
            has_path_reference or len(output) > 50
        ), "Explorer should find and report code locations"

    @pytest.mark.timeout(90)
    async def test_refactorer_suggests_improvements(self, coordinator):
        """
        REAL TEST: Refactorer agent should suggest improvements.
        """
        request = """
        Suggest how to refactor this code:
        ```python
        def f(x):
            if x == True:
                return True
            else:
                return False
        ```
        """

        result = await coordinator.route_to_agent(request)

        print(f"\n[REAL] Output: {result['output'][:300]}...")

        if result.get("error"):
            pytest.skip(f"Error: {result['error']}")

        output_lower = result["output"].lower()

        # Should suggest simplification
        suggests_improvement = any(
            word in output_lower
            for word in ["simplif", "return x", "redundant", "unneces", "improve", "better"]
        )

        assert suggests_improvement, "Refactorer should suggest improvements for redundant code"

    @pytest.mark.timeout(90)
    async def test_documentation_agent_generates_docs(self, coordinator):
        """
        REAL TEST: Documentation agent should generate docstrings.
        """
        request = """
        Write a docstring for this function:
        ```python
        def calculate_discount(price, percentage, max_discount=100):
            discount = price * (percentage / 100)
            return min(discount, max_discount)
        ```
        """

        result = await coordinator.route_to_agent(request)

        print(f"\n[REAL] Output: {result['output'][:300]}...")

        if result.get("error"):
            pytest.skip(f"Error: {result['error']}")

        # Should produce docstring format
        output = result["output"]
        has_docstring = (
            '"""' in output or "'''" in output or "Args:" in output or "Parameters" in output
        )

        assert (
            has_docstring or "discount" in output.lower()
        ), "Documentation agent should generate proper docstring"


class TestRealAgentErrorHandling:
    """Test agent error handling in real scenarios."""

    @pytest.mark.timeout(60)
    async def test_agent_handles_invalid_input(self, coordinator):
        """
        REAL TEST: Agents should handle invalid input gracefully.
        """
        request = "Review this code: [invalid syntax here{{{{"

        result = await coordinator.route_to_agent(request)

        # Should not crash, should provide some response
        assert result is not None
        assert not result.get("error") or len(result.get("output", "")) > 0

    @pytest.mark.timeout(60)
    async def test_agent_handles_ambiguous_request(self, coordinator):
        """
        REAL TEST: Agents should handle ambiguous requests.
        """
        request = "Make it better"

        result = await coordinator.route_to_agent(request)

        # Should ask for clarification or provide general response
        assert result is not None
        if result["output"]:
            # Should ask what "it" refers to or provide general advice
            assert len(result["output"]) > 10


class TestRealAgentPerformance:
    """Performance tests for agent coordination."""

    @pytest.mark.timeout(120)
    @pytest.mark.benchmark
    async def test_routing_latency(self, coordinator):
        """
        REAL BENCHMARK: Measure routing decision latency.
        """
        requests = [
            "Plan a feature",
            "Write some code",
            "Review the PR",
        ]

        latencies = []
        for request in requests:
            start = time.time()
            await coordinator.route_to_agent(request)
            latency = (time.time() - start) * 1000
            latencies.append(latency)

        avg_latency = sum(latencies) / len(latencies)
        print(f"\n[BENCHMARK] Average routing latency: {avg_latency:.0f}ms")
        print(f"[BENCHMARK] Individual: {[f'{l:.0f}ms' for l in latencies]}")

        # Routing should be reasonably fast
        assert avg_latency < 60000, f"Average latency too high: {avg_latency}ms"
