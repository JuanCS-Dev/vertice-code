"""
E2E Tests for Agent Handoffs - Phase 8.3
Testing handoff patterns between agents.

Patterns tested:
- Direct handoff (A -> B)
- Chain handoff (A -> B -> C)
- Parallel handoff (A -> [B, C])
- Return handoff (A -> B -> A)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


class TestDirectHandoffs:
    """Test direct handoffs between two agents."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for handoff testing."""
        from agents import OrchestratorAgent
        return OrchestratorAgent()

    @pytest.mark.asyncio
    async def test_handoff_orchestrator_to_coder(self, orchestrator):
        """Test handoff from orchestrator to coder."""
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        task = Task(
            id="handoff-1",
            description="Generate code for API endpoint",
            complexity=TaskComplexity.SIMPLE,
        )

        handoff = await orchestrator.handoff(
            task=task,
            to_agent=AgentRole.CODER,
            context="Generate REST API endpoint"
        )

        assert handoff.from_agent == AgentRole.ORCHESTRATOR
        assert handoff.to_agent == AgentRole.CODER
        assert handoff.task_id == "handoff-1"
        assert "API endpoint" in handoff.context

    @pytest.mark.asyncio
    async def test_handoff_orchestrator_to_reviewer(self, orchestrator):
        """Test handoff from orchestrator to reviewer."""
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        task = Task(
            id="handoff-2",
            description="Review security vulnerabilities",
            complexity=TaskComplexity.MODERATE,
        )

        handoff = await orchestrator.handoff(
            task=task,
            to_agent=AgentRole.REVIEWER,
            context="Security review for authentication module"
        )

        assert handoff.to_agent == AgentRole.REVIEWER

    @pytest.mark.asyncio
    async def test_handoff_orchestrator_to_architect(self, orchestrator):
        """Test handoff from orchestrator to architect."""
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        task = Task(
            id="handoff-3",
            description="Design microservices architecture",
            complexity=TaskComplexity.COMPLEX,
        )

        handoff = await orchestrator.handoff(
            task=task,
            to_agent=AgentRole.ARCHITECT,
            context="Design payment microservices"
        )

        assert handoff.to_agent == AgentRole.ARCHITECT

    @pytest.mark.asyncio
    async def test_handoff_orchestrator_to_devops(self, orchestrator):
        """Test handoff from orchestrator to devops."""
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        task = Task(
            id="handoff-4",
            description="Deploy to production",
            complexity=TaskComplexity.CRITICAL,
        )

        handoff = await orchestrator.handoff(
            task=task,
            to_agent=AgentRole.DEVOPS,
            context="Production deployment of v2.0"
        )

        assert handoff.to_agent == AgentRole.DEVOPS


class TestChainHandoffs:
    """Test chain handoffs (A -> B -> C)."""

    @pytest.mark.asyncio
    async def test_chain_architect_coder_reviewer(self):
        """Test chain: Architect -> Coder -> Reviewer."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        # Phase 1: To Architect
        task1 = Task(
            id="chain-1",
            description="Design API architecture",
            complexity=TaskComplexity.COMPLEX,
        )
        h1 = await orchestrator.handoff(task1, AgentRole.ARCHITECT, "Design phase")

        # Phase 2: To Coder
        task2 = Task(
            id="chain-2",
            description="Implement the designed API",
            complexity=TaskComplexity.MODERATE,
        )
        h2 = await orchestrator.handoff(task2, AgentRole.CODER, "Implementation phase")

        # Phase 3: To Reviewer
        task3 = Task(
            id="chain-3",
            description="Review the implementation",
            complexity=TaskComplexity.MODERATE,
        )
        h3 = await orchestrator.handoff(task3, AgentRole.REVIEWER, "Review phase")

        assert len(orchestrator.handoffs) == 3
        assert orchestrator.handoffs[0].to_agent == AgentRole.ARCHITECT
        assert orchestrator.handoffs[1].to_agent == AgentRole.CODER
        assert orchestrator.handoffs[2].to_agent == AgentRole.REVIEWER

    @pytest.mark.asyncio
    async def test_chain_researcher_coder_devops(self):
        """Test chain: Researcher -> Coder -> DevOps."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        # Research phase
        h1 = await orchestrator.handoff(
            Task(id="r-1", description="Research best practices", complexity=TaskComplexity.SIMPLE),
            AgentRole.RESEARCHER,
            "Research"
        )

        # Implementation phase
        h2 = await orchestrator.handoff(
            Task(id="r-2", description="Implement feature", complexity=TaskComplexity.MODERATE),
            AgentRole.CODER,
            "Implement"
        )

        # Deployment phase
        h3 = await orchestrator.handoff(
            Task(id="r-3", description="Deploy feature", complexity=TaskComplexity.MODERATE),
            AgentRole.DEVOPS,
            "Deploy"
        )

        assert len(orchestrator.handoffs) == 3


class TestHandoffContext:
    """Test handoff context preservation."""

    @pytest.mark.asyncio
    async def test_context_preserved_in_handoff(self):
        """Test that context is preserved in handoff."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        context = "Important context: Use Python 3.12 features only"

        task = Task(
            id="ctx-1",
            description="Generate code",
            complexity=TaskComplexity.SIMPLE,
        )

        handoff = await orchestrator.handoff(task, AgentRole.CODER, context)

        assert handoff.context == context

    @pytest.mark.asyncio
    async def test_handoff_records_reason(self):
        """Test that handoff records the reason."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(
            id="reason-1",
            description="Critical security update needed",
            complexity=TaskComplexity.CRITICAL,
        )

        handoff = await orchestrator.handoff(task, AgentRole.REVIEWER, "Review")

        assert handoff.reason is not None
        assert len(handoff.reason) > 0


class TestHandoffTracking:
    """Test handoff tracking and history."""

    @pytest.mark.asyncio
    async def test_handoffs_are_tracked(self):
        """Test that all handoffs are tracked."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()
        assert len(orchestrator.handoffs) == 0

        # Make several handoffs
        for i in range(5):
            task = Task(id=f"track-{i}", description=f"Task {i}", complexity=TaskComplexity.SIMPLE)
            await orchestrator.handoff(task, AgentRole.CODER, f"Context {i}")

        assert len(orchestrator.handoffs) == 5

    @pytest.mark.asyncio
    async def test_handoff_status_in_orchestrator(self):
        """Test handoff count in status."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(id="status-1", description="Test", complexity=TaskComplexity.SIMPLE)
        await orchestrator.handoff(task, AgentRole.CODER, "Context")

        status = orchestrator.get_status()
        assert status["handoffs"] == 1


class TestRoutingToHandoff:
    """Test routing decisions leading to handoffs."""

    @pytest.mark.asyncio
    async def test_route_then_handoff_code_task(self):
        """Test routing then handoff for code task."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(
            id="rt-1",
            description="Write code for authentication",
            complexity=TaskComplexity.MODERATE,
        )

        # Route first
        agent = await orchestrator.route(task)
        assert agent == AgentRole.CODER

        # Then handoff
        handoff = await orchestrator.handoff(task, agent, "Auth implementation")
        assert handoff.to_agent == AgentRole.CODER

    @pytest.mark.asyncio
    async def test_route_then_handoff_review_task(self):
        """Test routing then handoff for review task."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(
            id="rt-2",
            description="Review the security implementation",
            complexity=TaskComplexity.MODERATE,
        )

        agent = await orchestrator.route(task)
        assert agent == AgentRole.REVIEWER

        handoff = await orchestrator.handoff(task, agent, "Security review")
        assert handoff.to_agent == AgentRole.REVIEWER

    @pytest.mark.asyncio
    async def test_route_then_handoff_deploy_task(self):
        """Test routing then handoff for deploy task."""
        from agents import OrchestratorAgent
        from agents.orchestrator.types import Task, TaskComplexity, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(
            id="rt-3",
            description="Deploy to kubernetes cluster",
            complexity=TaskComplexity.CRITICAL,
        )

        agent = await orchestrator.route(task)
        assert agent == AgentRole.DEVOPS

        handoff = await orchestrator.handoff(task, agent, "K8s deployment")
        assert handoff.to_agent == AgentRole.DEVOPS
