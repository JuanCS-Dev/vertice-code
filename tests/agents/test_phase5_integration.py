"""
Phase 5 Integration Tests

Verifies all 6 agents have proper mixin integration after Phase 5.

Tests:
- BaseAgent with ObservabilityMixin for all agents
- Specialized mixins (DarwinGodel, BoundedAutonomy, DeepThink, etc.)
- Agent instantiation and capability verification
"""

from __future__ import annotations

from agents.coder.agent import CoderAgent
from agents.orchestrator.agent import OrchestratorAgent
from agents.reviewer.agent import ReviewerAgent
from agents.architect.agent import ArchitectAgent
from agents.researcher.agent import ResearcherAgent
from agents.devops.agent import DevOpsAgent


class TestBaseAgentIntegration:
    """Test all agents inherit from BaseAgent with ObservabilityMixin."""

    def test_coder_has_observability(self) -> None:
        """CoderAgent has ObservabilityMixin methods."""
        agent = CoderAgent()
        assert hasattr(agent, "trace_operation")
        assert hasattr(agent, "record_tokens")
        assert hasattr(agent, "record_latency")
        assert hasattr(agent, "record_error")
        assert hasattr(agent, "export_traces")
        assert hasattr(agent, "get_prometheus_metrics")

    def test_orchestrator_has_observability(self) -> None:
        """OrchestratorAgent has ObservabilityMixin methods."""
        agent = OrchestratorAgent()
        assert hasattr(agent, "trace_operation")
        assert hasattr(agent, "record_tokens")
        assert hasattr(agent, "record_latency")

    def test_reviewer_has_observability(self) -> None:
        """ReviewerAgent has ObservabilityMixin methods."""
        agent = ReviewerAgent()
        assert hasattr(agent, "trace_operation")
        assert hasattr(agent, "record_tokens")

    def test_architect_has_observability(self) -> None:
        """ArchitectAgent has ObservabilityMixin methods."""
        agent = ArchitectAgent()
        assert hasattr(agent, "trace_operation")
        assert hasattr(agent, "record_tokens")

    def test_researcher_has_observability(self) -> None:
        """ResearcherAgent has ObservabilityMixin methods."""
        agent = ResearcherAgent()
        assert hasattr(agent, "trace_operation")
        assert hasattr(agent, "record_tokens")

    def test_devops_has_observability(self) -> None:
        """DevOpsAgent has ObservabilityMixin methods."""
        agent = DevOpsAgent()
        assert hasattr(agent, "trace_operation")
        assert hasattr(agent, "record_tokens")


class TestDarwinGodelIntegration:
    """Test CoderAgent has DarwinGodelMixin capabilities."""

    def test_coder_has_evolution_methods(self) -> None:
        """CoderAgent can evolve via Darwin Gödel pattern."""
        agent = CoderAgent()
        assert hasattr(agent, "get_archive")
        assert hasattr(agent, "evolve")
        assert hasattr(agent, "get_current_variant")
        assert hasattr(agent, "get_evolution_stats")
        assert hasattr(agent, "get_lineage")

    def test_coder_archive_initialization(self) -> None:
        """CoderAgent initializes evolution archive on demand."""
        agent = CoderAgent()
        archive = agent.get_archive()
        assert isinstance(archive, list)

    def test_coder_variant_access(self) -> None:
        """CoderAgent can access current variant."""
        agent = CoderAgent()
        variant = agent.get_current_variant()
        assert variant is not None
        assert hasattr(variant, "id")
        assert hasattr(variant, "generation")


class TestBoundedAutonomyIntegration:
    """Test OrchestratorAgent has BoundedAutonomyMixin capabilities."""

    def test_orchestrator_has_autonomy_methods(self) -> None:
        """OrchestratorAgent has bounded autonomy methods."""
        agent = OrchestratorAgent()
        assert hasattr(agent, "check_autonomy")
        assert hasattr(agent, "get_autonomy_level")
        assert hasattr(agent, "classify_operation")
        assert hasattr(agent, "approve")
        assert hasattr(agent, "reject")
        assert hasattr(agent, "get_pending_approvals")

    def test_orchestrator_autonomy_rules(self) -> None:
        """OrchestratorAgent has autonomy rules defined."""
        agent = OrchestratorAgent()
        assert hasattr(agent, "AUTONOMY_RULES")
        assert "deploy_production" in agent.AUTONOMY_RULES
        assert "read_file" in agent.AUTONOMY_RULES

    def test_orchestrator_classifies_operations(self) -> None:
        """OrchestratorAgent classifies operations correctly."""
        agent = OrchestratorAgent()
        assert agent.classify_operation("read file") == "format_code"
        assert agent.classify_operation("deploy to production") == "deploy_production"
        assert agent.classify_operation("refactor code") == "refactor_code"


class TestDeepThinkIntegration:
    """Test ReviewerAgent has DeepThinkMixin capabilities."""

    def test_reviewer_has_deep_think_methods(self) -> None:
        """ReviewerAgent has deep think review capability."""
        agent = ReviewerAgent()
        assert hasattr(agent, "deep_think_review")
        assert hasattr(agent, "_stage_static_analysis")
        assert hasattr(agent, "_stage_deep_reasoning")
        assert hasattr(agent, "_stage_critique")
        assert hasattr(agent, "_stage_validation")

    def test_reviewer_has_security_checks(self) -> None:
        """ReviewerAgent has security check patterns."""
        agent = ReviewerAgent()
        assert hasattr(agent, "SECURITY_CHECKS")
        assert len(agent.SECURITY_CHECKS) > 0


class TestThreeLoopsIntegration:
    """Test ArchitectAgent has ThreeLoopsMixin capabilities."""

    def test_architect_has_three_loops_methods(self) -> None:
        """ArchitectAgent has three loops pattern methods."""
        agent = ArchitectAgent()
        assert hasattr(agent, "classify_decision")
        assert hasattr(agent, "select_loop")

    def test_architect_classifies_decisions(self) -> None:
        """ArchitectAgent classifies architectural decisions."""
        agent = ArchitectAgent()
        context = agent.classify_decision("simple formatting change")
        assert context is not None


class TestAgenticRAGIntegration:
    """Test ResearcherAgent has AgenticRAGMixin capabilities."""

    def test_researcher_has_rag_methods(self) -> None:
        """ResearcherAgent has agentic RAG methods."""
        agent = ResearcherAgent()
        assert hasattr(agent, "agentic_research")
        assert hasattr(agent, "quick_lookup")
        assert hasattr(agent, "_classify_complexity")
        assert hasattr(agent, "_select_strategy")
        assert hasattr(agent, "_route_query")

    def test_researcher_has_doc_sources(self) -> None:
        """ResearcherAgent has documentation sources configured."""
        agent = ResearcherAgent()
        assert hasattr(agent, "DOC_SOURCES")
        assert "python" in agent.DOC_SOURCES
        assert "javascript" in agent.DOC_SOURCES


class TestIncidentHandlerIntegration:
    """Test DevOpsAgent has IncidentHandlerMixin capabilities."""

    def test_devops_has_incident_methods(self) -> None:
        """DevOpsAgent has incident handling methods."""
        agent = DevOpsAgent()
        assert hasattr(agent, "investigate_incident")
        assert hasattr(agent, "get_topology")
        assert hasattr(agent, "get_incident_metrics")

    def test_devops_has_templates(self) -> None:
        """DevOpsAgent has CI/CD templates."""
        agent = DevOpsAgent()
        assert hasattr(agent, "TEMPLATES")
        assert "github-actions" in agent.TEMPLATES
        assert "dockerfile" in agent.TEMPLATES


class TestAgentStatus:
    """Test all agents have proper status methods."""

    def test_all_agents_have_get_status(self) -> None:
        """All agents have get_status method."""
        agents = [
            CoderAgent(),
            OrchestratorAgent(),
            ReviewerAgent(),
            ArchitectAgent(),
            ResearcherAgent(),
            DevOpsAgent(),
        ]
        for agent in agents:
            assert hasattr(agent, "get_status")
            status = agent.get_status()
            assert isinstance(status, dict)
            assert "name" in status

    def test_all_agents_have_name(self) -> None:
        """All agents have name attribute."""
        expected_names = ["coder", "orchestrator", "reviewer", "architect", "researcher", "devops"]
        agents = [
            CoderAgent(),
            OrchestratorAgent(),
            ReviewerAgent(),
            ArchitectAgent(),
            ResearcherAgent(),
            DevOpsAgent(),
        ]
        for agent, name in zip(agents, expected_names):
            assert agent.name == name
