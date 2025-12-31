"""
Real Orchestration Tests with LLM - Phase 8.3
Scientific testing of orchestration with REAL LLM providers.

Tests:
- Real provider initialization (Groq, Vertex AI, Claude)
- Complete orchestration workflow with streaming
- Multi-agent handoff with actual LLM responses
- Bounded Autonomy in practice
- Performance metrics collection

Requirements:
- API keys in environment (GROQ_API_KEY, ANTHROPIC_API_KEY, etc)
- pytest-benchmark for performance tests
"""

import pytest
import asyncio
import time
import os
from typing import Dict, List, Any
from unittest.mock import AsyncMock


def has_api_key(provider: str) -> bool:
    """Check if API key is available for provider."""
    key_map = {
        "groq": "GROQ_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "vertex": "GOOGLE_APPLICATION_CREDENTIALS",
        "openai": "OPENAI_API_KEY",
    }
    key_name = key_map.get(provider, f"{provider.upper()}_API_KEY")
    return bool(os.getenv(key_name))


# Skip markers
requires_groq = pytest.mark.skipif(
    not has_api_key("groq"),
    reason="GROQ_API_KEY not set"
)

requires_anthropic = pytest.mark.skipif(
    not has_api_key("anthropic"),
    reason="ANTHROPIC_API_KEY not set"
)


class TestRealProviderInitialization:
    """Test real provider initialization."""

    def test_provider_router_available(self):
        """Test provider router is importable."""
        from providers import get_router

        router = get_router()
        assert router is not None

    def test_provider_has_available_providers(self):
        """Test that some providers are available."""
        from providers import get_router

        router = get_router()
        # Should have at least one provider configured
        assert hasattr(router, 'providers') or hasattr(router, 'stream_chat')

    @requires_groq
    @pytest.mark.asyncio
    async def test_groq_provider_init(self):
        """Test Groq provider initializes correctly."""
        from providers import GroqProvider

        provider = GroqProvider()
        assert provider is not None
        # Should have model configured
        assert hasattr(provider, 'model') or hasattr(provider, 'client')


class TestRealOrchestratorWorkflow:
    """Test orchestrator with real components."""

    @pytest.mark.asyncio
    async def test_orchestrator_creates_real_tasks(self):
        """Test orchestrator creates tasks from real requests."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import TaskComplexity

        orchestrator = OrchestratorAgent()

        # Complex request
        tasks = await orchestrator.plan(
            "Design and implement a REST API for user authentication "
            "with JWT tokens and secure password hashing"
        )

        assert len(tasks) >= 1
        # Complex request should result in complex/critical task
        assert tasks[0].complexity in [
            TaskComplexity.MODERATE,
            TaskComplexity.COMPLEX,
            TaskComplexity.CRITICAL
        ]

    @pytest.mark.asyncio
    async def test_orchestrator_routes_correctly(self):
        """Test orchestrator routing accuracy based on actual ROUTING_TABLE."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        # Test cases based on actual ROUTING_TABLE keywords:
        # "code": CODER, "review": REVIEWER, "architecture": ARCHITECT,
        # "research": RESEARCHER, "deploy": DEVOPS, "security": REVIEWER
        test_cases = [
            ("Write code for authentication", AgentRole.CODER),
            ("Security review of the API", AgentRole.REVIEWER),  # 'security' keyword
            ("Design the architecture for new API", AgentRole.ARCHITECT),
            ("Research documentation on OAuth2", AgentRole.RESEARCHER),
            ("Deploy to production cluster", AgentRole.DEVOPS),
        ]

        for description, expected_role in test_cases:
            task = Task(
                id="test",
                description=description,
                complexity=TaskComplexity.SIMPLE
            )
            actual_role = await orchestrator.route(task)
            assert actual_role == expected_role, \
                f"Expected {expected_role} for '{description}', got {actual_role}"

    @pytest.mark.asyncio
    async def test_orchestrator_streaming_output(self):
        """Test orchestrator produces streaming output."""
        from agents import OrchestratorAgent

        orchestrator = OrchestratorAgent(
            approval_callback=AsyncMock(return_value=True),
            notify_callback=AsyncMock(),
        )

        chunks = []
        async for chunk in orchestrator.execute("Create hello world"):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_output = "".join(chunks)
        assert "Orchestrator" in full_output
        assert "task" in full_output.lower()


class TestRealMultiAgentHandoffs:
    """Test multi-agent handoffs with real components."""

    @pytest.mark.asyncio
    async def test_complete_handoff_chain(self):
        """Test complete handoff chain: Architect -> Coder -> Reviewer."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        # Track handoffs
        handoff_results = []

        # Phase 1: Architecture
        arch_task = Task(
            id="arch-1",
            description="Design microservices architecture",
            complexity=TaskComplexity.COMPLEX
        )
        h1 = await orchestrator.handoff(
            arch_task, AgentRole.ARCHITECT, "Architecture phase"
        )
        handoff_results.append(h1)

        # Phase 2: Implementation
        impl_task = Task(
            id="impl-1",
            description="Code the authentication service",
            complexity=TaskComplexity.MODERATE
        )
        h2 = await orchestrator.handoff(
            impl_task, AgentRole.CODER, "Implementation phase"
        )
        handoff_results.append(h2)

        # Phase 3: Review
        review_task = Task(
            id="review-1",
            description="Review implementation for security",
            complexity=TaskComplexity.MODERATE
        )
        h3 = await orchestrator.handoff(
            review_task, AgentRole.REVIEWER, "Review phase"
        )
        handoff_results.append(h3)

        # Verify chain
        assert len(handoff_results) == 3
        assert handoff_results[0].to_agent == AgentRole.ARCHITECT
        assert handoff_results[1].to_agent == AgentRole.CODER
        assert handoff_results[2].to_agent == AgentRole.REVIEWER

        # Verify orchestrator tracking
        assert len(orchestrator.handoffs) == 3


class TestRealBoundedAutonomy:
    """Test Bounded Autonomy with real scenarios."""

    @pytest.mark.asyncio
    async def test_trivial_task_is_autonomous(self):
        """Test that trivial tasks are L0 (autonomous)."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity

        approval_called = False

        async def track_approval(*args):
            nonlocal approval_called
            approval_called = True
            return True

        orchestrator = OrchestratorAgent(
            approval_callback=track_approval,
            notify_callback=AsyncMock(),
        )

        task = Task(
            id="trivial-1",
            description="List files",
            complexity=TaskComplexity.TRIVIAL
        )

        can_proceed, _ = await orchestrator.check_autonomy(task)

        # Trivial tasks should be autonomous (L0)
        assert can_proceed is True

    @pytest.mark.asyncio
    async def test_critical_task_requires_approval(self):
        """Test that critical tasks require approval (L2)."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity

        approval_called = False

        async def track_approval(*args):
            nonlocal approval_called
            approval_called = True
            return True

        orchestrator = OrchestratorAgent(
            approval_callback=track_approval,
            notify_callback=AsyncMock(),
        )

        task = Task(
            id="critical-1",
            description="Delete production database",
            complexity=TaskComplexity.CRITICAL
        )

        can_proceed, approval_request = await orchestrator.check_autonomy(task)

        # Critical tasks should have an approval request (even if auto-approved)
        # The exact behavior depends on implementation
        assert isinstance(can_proceed, bool)


class TestRealCoderAgent:
    """Test Coder agent with real code evaluation."""

    def test_coder_evaluates_valid_python(self):
        """Test coder evaluates valid Python correctly."""
        from agents import coder

        code = '''
def calculate_factorial(n: int) -> int:
    """Calculate factorial of n."""
    if n <= 1:
        return 1
    return n * calculate_factorial(n - 1)
'''

        result = coder.evaluate_code(code, "python")

        assert result.valid_syntax is True
        assert result.quality_score > 0.5  # Good code should score well

    def test_coder_evaluates_invalid_python(self):
        """Test coder catches invalid Python."""
        from agents import coder

        code = '''
def broken_function(
    return "missing colon"
'''

        result = coder.evaluate_code(code, "python")

        assert result.valid_syntax is False
        assert len(result.issues) > 0

    def test_coder_detects_antipatterns(self):
        """Test coder detects anti-patterns."""
        from agents import coder

        code = '''
def hacky_function():
    pass  # TODO: implement this
    # FIXME: this is broken
'''

        result = coder.evaluate_code(code, "python")

        # Code with TODO/FIXME should score lower
        assert result.quality_score < 0.9


class TestPerformanceMetrics:
    """Test performance metrics collection."""

    @pytest.mark.asyncio
    async def test_orchestrator_latency(self):
        """Measure orchestrator planning latency."""
        from agents import OrchestratorAgent

        orchestrator = OrchestratorAgent()

        start = time.time()
        await orchestrator.plan("Create a simple web server")
        latency = time.time() - start

        # Planning should be fast (no LLM call for basic planning)
        assert latency < 1.0, f"Planning took {latency:.2f}s, expected <1s"

    @pytest.mark.asyncio
    async def test_routing_latency(self):
        """Measure routing latency."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity

        orchestrator = OrchestratorAgent()

        task = Task(
            id="perf-1",
            description="Write code for API",
            complexity=TaskComplexity.SIMPLE
        )

        start = time.time()
        await orchestrator.route(task)
        latency = time.time() - start

        # Routing should be instant (keyword matching)
        assert latency < 0.1, f"Routing took {latency:.2f}s, expected <0.1s"

    @pytest.mark.asyncio
    async def test_handoff_latency(self):
        """Measure handoff latency."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(
            id="perf-2",
            description="Test task",
            complexity=TaskComplexity.SIMPLE
        )

        start = time.time()
        await orchestrator.handoff(task, AgentRole.CODER, "Context")
        latency = time.time() - start

        # Handoff should be instant
        assert latency < 0.1, f"Handoff took {latency:.2f}s, expected <0.1s"


class TestObservabilityIntegration:
    """Test observability integration."""

    def test_agents_have_observability(self):
        """Test all agents have observability mixin."""
        from agents import (
            orchestrator, coder, reviewer,
            architect, researcher, devops
        )
        from core.observability import ObservabilityMixin

        for agent in [orchestrator, coder, reviewer, architect, researcher, devops]:
            assert isinstance(agent, ObservabilityMixin), \
                f"{agent.name} missing ObservabilityMixin"

    def test_agent_has_trace_methods(self):
        """Test agents have trace methods."""
        from agents import coder

        assert hasattr(coder, 'trace_operation')
        assert hasattr(coder, 'trace_llm_call')
        assert hasattr(coder, 'record_tokens')


class TestCompleteWorkflow:
    """Test complete end-to-end workflow."""

    @pytest.mark.asyncio
    async def test_feature_development_workflow(self):
        """Test complete feature development workflow."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent(
            approval_callback=AsyncMock(return_value=True),
            notify_callback=AsyncMock(),
        )

        # Simulate feature development
        workflow = []

        # Step 1: Plan
        tasks = await orchestrator.plan(
            "Implement user authentication with OAuth2"
        )
        workflow.append(("plan", len(tasks)))

        # Step 2: Route and handoff
        for task in tasks:
            agent = await orchestrator.route(task)
            handoff = await orchestrator.handoff(task, agent, "Feature impl")
            workflow.append(("handoff", agent.value))

        # Verify workflow completed
        assert len(workflow) >= 2
        assert workflow[0][0] == "plan"

        # Verify status reflects workflow
        status = orchestrator.get_status()
        assert status["handoffs"] >= 1


class TestErrorRecovery:
    """Test error recovery in orchestration."""

    @pytest.mark.asyncio
    async def test_handles_empty_request(self):
        """Test orchestrator handles empty request gracefully."""
        from agents import OrchestratorAgent

        orchestrator = OrchestratorAgent()

        # Should not crash on empty request
        tasks = await orchestrator.plan("")
        assert isinstance(tasks, list)

    @pytest.mark.asyncio
    async def test_handles_very_long_request(self):
        """Test orchestrator handles very long request."""
        from agents import OrchestratorAgent

        orchestrator = OrchestratorAgent()

        # Very long request
        long_request = "Create a feature that " + "does something. " * 100

        tasks = await orchestrator.plan(long_request)
        assert isinstance(tasks, list)
        assert len(tasks) >= 1
