"""
Tests for OrchestratorAgent.

Sprint 5: Test coverage for agents module.
Tests the Anthropic Orchestrator-Worker pattern implementation.
"""

import pytest

from agents.orchestrator.agent import OrchestratorAgent
from agents.orchestrator.types import (
    AgentRole,
    Task,
    TaskComplexity,
)


class TestOrchestratorInit:
    """Tests for OrchestratorAgent initialization."""

    def test_create_orchestrator(self):
        """Test creating orchestrator instance."""
        orchestrator = OrchestratorAgent()

        assert orchestrator.name == "orchestrator"
        assert orchestrator.role == AgentRole.ORCHESTRATOR
        assert orchestrator.agents == {}
        assert not orchestrator._agents_initialized

    def test_lazy_agent_initialization(self):
        """Test that agents are initialized lazily."""
        orchestrator = OrchestratorAgent()

        # Agents should not be initialized yet
        assert len(orchestrator.agents) == 0
        assert not orchestrator._agents_initialized

        # Calling _ensure_agents should initialize them
        orchestrator._ensure_agents()

        assert orchestrator._agents_initialized
        assert len(orchestrator.agents) == 5  # 5 specialized agents
        assert AgentRole.CODER in orchestrator.agents
        assert AgentRole.REVIEWER in orchestrator.agents
        assert AgentRole.ARCHITECT in orchestrator.agents
        assert AgentRole.RESEARCHER in orchestrator.agents
        assert AgentRole.DEVOPS in orchestrator.agents

    def test_ensure_agents_idempotent(self):
        """Test that _ensure_agents is idempotent."""
        orchestrator = OrchestratorAgent()

        # First call
        orchestrator._ensure_agents()
        first_agents = orchestrator.agents.copy()

        # Second call should not reinitialize
        orchestrator._ensure_agents()

        assert orchestrator.agents == first_agents


class TestRouting:
    """Tests for task routing."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for testing."""
        return OrchestratorAgent()

    @pytest.mark.asyncio
    async def test_route_code_task(self, orchestrator):
        """Test routing code-related tasks to coder."""
        task = Task(id="1", description="Write code for authentication")
        role = await orchestrator.route(task)
        assert role == AgentRole.CODER

    @pytest.mark.asyncio
    async def test_route_review_task(self, orchestrator):
        """Test routing review tasks to reviewer."""
        task = Task(id="2", description="Review the pull request")
        role = await orchestrator.route(task)
        assert role == AgentRole.REVIEWER

    @pytest.mark.asyncio
    async def test_route_architecture_task(self, orchestrator):
        """Test routing architecture tasks to architect."""
        task = Task(id="3", description="Design system architecture")
        role = await orchestrator.route(task)
        assert role == AgentRole.ARCHITECT

    @pytest.mark.asyncio
    async def test_route_research_task(self, orchestrator):
        """Test routing research tasks to researcher."""
        task = Task(id="4", description="Research best practices")
        role = await orchestrator.route(task)
        assert role == AgentRole.RESEARCHER

    @pytest.mark.asyncio
    async def test_route_deploy_task(self, orchestrator):
        """Test routing deployment tasks to devops."""
        task = Task(id="5", description="Deploy to production")
        role = await orchestrator.route(task)
        assert role == AgentRole.DEVOPS

    @pytest.mark.asyncio
    async def test_route_default_to_coder(self, orchestrator):
        """Test that unknown tasks default to coder."""
        task = Task(id="6", description="Do something random")
        role = await orchestrator.route(task)
        assert role == AgentRole.CODER


class TestComplexityAnalysis:
    """Tests for complexity analysis."""

    @pytest.fixture
    def orchestrator(self):
        return OrchestratorAgent()

    @pytest.mark.asyncio
    async def test_simple_complexity(self, orchestrator):
        """Test simple request detection."""
        complexity = await orchestrator._analyze_complexity("Fix bug")
        assert complexity == TaskComplexity.SIMPLE

    @pytest.mark.asyncio
    async def test_moderate_complexity(self, orchestrator):
        """Test moderate request detection."""
        request = (
            "Implement a function that validates user input and returns appropriate error messages"
        )
        complexity = await orchestrator._analyze_complexity(request)
        assert complexity == TaskComplexity.MODERATE

    @pytest.mark.asyncio
    async def test_complex_architecture(self, orchestrator):
        """Test complex architecture request detection."""
        # Note: Complexity logic:
        # - < 10 words → SIMPLE
        # - < 50 words → MODERATE
        # - >= 50 words + "architecture"/"design" → COMPLEX
        # - >= 50 words + "production"/"security" → CRITICAL

        # Short request (< 10 words) → SIMPLE
        short_request = "Design a microservices architecture"
        complexity = await orchestrator._analyze_complexity(short_request)
        assert complexity == TaskComplexity.SIMPLE

        # Long request with architecture keyword → COMPLEX
        long_request = " ".join(["word"] * 51) + " architecture design system"
        complexity = await orchestrator._analyze_complexity(long_request)
        assert complexity == TaskComplexity.COMPLEX

    @pytest.mark.asyncio
    async def test_critical_production(self, orchestrator):
        """Test critical production request detection."""
        # Short security request gets SIMPLE (< 10 words)
        short_request = "Fix security bug"
        complexity = await orchestrator._analyze_complexity(short_request)
        assert complexity == TaskComplexity.SIMPLE

        # Long request with production/security keyword gets CRITICAL
        long_request = " ".join(["word"] * 51) + " production security deployment"
        complexity = await orchestrator._analyze_complexity(long_request)
        assert complexity == TaskComplexity.CRITICAL


class TestHandoff:
    """Tests for handoff functionality."""

    @pytest.fixture
    def orchestrator(self):
        return OrchestratorAgent()

    @pytest.mark.asyncio
    async def test_handoff_creates_record(self, orchestrator):
        """Test that handoff creates a record."""
        task = Task(id="1", description="Test task")

        handoff = await orchestrator.handoff(task, AgentRole.CODER, "Test context")

        assert handoff.from_agent == AgentRole.ORCHESTRATOR
        assert handoff.to_agent == AgentRole.CODER
        assert handoff.context == "Test context"
        assert handoff.task_id == "1"

    @pytest.mark.asyncio
    async def test_handoff_stored_in_list(self, orchestrator):
        """Test that handoffs are stored."""
        task = Task(id="1", description="Test task")

        assert len(orchestrator.handoffs) == 0

        await orchestrator.handoff(task, AgentRole.CODER, "Context 1")
        await orchestrator.handoff(task, AgentRole.REVIEWER, "Context 2")

        assert len(orchestrator.handoffs) == 2


class TestPlanning:
    """Tests for task planning."""

    @pytest.fixture
    def orchestrator(self):
        return OrchestratorAgent()

    @pytest.mark.asyncio
    async def test_plan_creates_tasks(self, orchestrator):
        """Test that plan creates tasks."""
        tasks = await orchestrator.plan("Implement user authentication")

        assert len(tasks) >= 1
        assert all(isinstance(t, Task) for t in tasks)

    @pytest.mark.asyncio
    async def test_plan_assigns_complexity(self, orchestrator):
        """Test that plan assigns complexity to tasks."""
        tasks = await orchestrator.plan("Simple fix")

        for task in tasks:
            assert task.complexity is not None


class TestStatus:
    """Tests for status reporting."""

    def test_get_status(self):
        """Test status retrieval."""
        orchestrator = OrchestratorAgent()

        status = orchestrator.get_status()

        assert "name" in status
        assert status["name"] == "orchestrator"
        assert "role" in status
        assert "active_tasks" in status
        assert "completed_tasks" in status
        assert "handoffs" in status
        assert "pending_approvals" in status


class TestModelRouting:
    """Tests for model routing based on complexity."""

    def test_model_routing_config(self):
        """Test model routing configuration exists."""
        assert OrchestratorAgent.MODEL_ROUTING is not None

        # Check expected mappings
        assert TaskComplexity.TRIVIAL in OrchestratorAgent.MODEL_ROUTING
        assert TaskComplexity.SIMPLE in OrchestratorAgent.MODEL_ROUTING
        assert TaskComplexity.COMPLEX in OrchestratorAgent.MODEL_ROUTING
        assert TaskComplexity.CRITICAL in OrchestratorAgent.MODEL_ROUTING

    def test_trivial_uses_fast_model(self):
        """Test that trivial tasks use fast model."""
        model = OrchestratorAgent.MODEL_ROUTING[TaskComplexity.TRIVIAL]
        assert model == "groq"

    def test_critical_uses_premium_model(self):
        """Test that critical tasks use premium model."""
        model = OrchestratorAgent.MODEL_ROUTING[TaskComplexity.CRITICAL]
        assert model == "claude"


class TestRoutingTable:
    """Tests for routing table configuration."""

    def test_routing_table_defined(self):
        """Test routing table is properly defined."""
        assert OrchestratorAgent.ROUTING_TABLE is not None
        assert len(OrchestratorAgent.ROUTING_TABLE) > 0

    def test_key_keywords_mapped(self):
        """Test that key keywords are mapped."""
        table = OrchestratorAgent.ROUTING_TABLE

        assert table["code"] == AgentRole.CODER
        assert table["review"] == AgentRole.REVIEWER
        assert table["architecture"] == AgentRole.ARCHITECT
        assert table["research"] == AgentRole.RESEARCHER
        assert table["deploy"] == AgentRole.DEVOPS


class TestExecution:
    """Tests for task execution."""

    @pytest.fixture
    def orchestrator(self):
        return OrchestratorAgent()

    @pytest.mark.asyncio
    async def test_execute_yields_progress(self, orchestrator):
        """Test that execute yields progress messages."""
        chunks = []
        async for chunk in orchestrator.execute("Write hello world", stream=True):
            chunks.append(chunk)

        # Should have some output
        assert len(chunks) > 0

        # Should mention orchestrator
        full_output = "".join(chunks)
        assert "Orchestrator" in full_output

    @pytest.mark.asyncio
    async def test_execute_processes_all_tasks(self, orchestrator):
        """Test that execute processes all planned tasks."""
        chunks = []
        async for chunk in orchestrator.execute("Simple task", stream=True):
            chunks.append(chunk)

        full_output = "".join(chunks)

        # Should indicate completion
        assert "completed" in full_output.lower() or "processed" in full_output.lower()
