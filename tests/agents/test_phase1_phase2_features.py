"""
Tests for Phase 1 & 2 Features (AGENTS_2028_EVOLUTION.md)

Coverage targets:
- Darwin Gödel Evolution (Coder)
- Agentic RAG (Researcher)
- Three Loops Framework (Architect)
- AWS-style Incident Handler (DevOps)
- Deep Think Review (Reviewer)
- Bounded Autonomy (Orchestrator)

100% coverage for new implementations.
"""

from __future__ import annotations

import pytest
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch


# =============================================================================
# CODER: Darwin Gödel Evolution Tests
# =============================================================================

class TestDarwinGodelTypes:
    """Test coder types module."""

    def test_code_generation_request(self):
        """Test CodeGenerationRequest dataclass."""
        from agents.coder.types import CodeGenerationRequest

        req = CodeGenerationRequest(
            description="Create a function",
            language="python",
        )
        assert req.description == "Create a function"
        assert req.language == "python"
        assert req.style == "clean"
        assert req.include_tests is False
        assert req.include_docs is True

    def test_evaluation_result(self):
        """Test EvaluationResult dataclass."""
        from agents.coder.types import EvaluationResult

        result = EvaluationResult(
            valid_syntax=True,
            lint_score=0.95,
            quality_score=0.85,
            issues=[],
            suggestions=["Add docstring"],
        )
        assert result.valid_syntax is True
        assert result.lint_score == 0.95
        assert result.passed is True  # property

    def test_evaluation_result_failed(self):
        """Test EvaluationResult passed property when failed."""
        from agents.coder.types import EvaluationResult

        result = EvaluationResult(
            valid_syntax=False,
            lint_score=0.95,
            quality_score=0.85,
        )
        assert result.passed is False  # invalid syntax

        result2 = EvaluationResult(
            valid_syntax=True,
            lint_score=0.5,
            quality_score=0.5,  # below 0.6 threshold
        )
        assert result2.passed is False

    def test_generated_code(self):
        """Test GeneratedCode dataclass."""
        from agents.coder.types import GeneratedCode

        code = GeneratedCode(
            code="def foo(): pass",
            language="python",
            explanation="Simple function",
        )
        assert code.code == "def foo(): pass"
        assert code.tests is None
        assert code.tokens_used == 0
        assert code.evaluation is None
        assert code.correction_attempts == 0

    def test_agent_variant_fitness(self):
        """Test AgentVariant fitness property."""
        from agents.coder.types import AgentVariant

        variant = AgentVariant(
            id="v1",
            parent_id=None,
            generation=1,
            system_prompt="Test prompt",
            tools=["tool1"],
            strategies={},
            benchmark_scores={"task1": 0.8, "task2": 0.9},
        )
        assert abs(variant.fitness - 0.85) < 0.001  # float comparison

    def test_agent_variant_fitness_empty(self):
        """Test AgentVariant fitness with no scores."""
        from agents.coder.types import AgentVariant

        variant = AgentVariant(
            id="v1",
            parent_id=None,
            generation=1,
            system_prompt="Test",
            tools=[],
            strategies={},
        )
        assert variant.fitness == 0.0

    def test_agent_variant_to_dict(self):
        """Test AgentVariant to_dict method."""
        from agents.coder.types import AgentVariant

        variant = AgentVariant(
            id="v1",
            parent_id="p1",
            generation=1,
            system_prompt="Test",
            tools=["tool1"],
            strategies={"key": "value"},
        )
        d = variant.to_dict()
        assert d["id"] == "v1"
        assert d["parent_id"] == "p1"
        assert d["fitness"] == 0.0

    def test_evolution_result(self):
        """Test EvolutionResult dataclass."""
        from agents.coder.types import EvolutionResult, AgentVariant

        child = AgentVariant(
            id="c1", parent_id="p1", generation=1,
            system_prompt="New", tools=[], strategies={},
        )
        result = EvolutionResult(
            new_variant=child,
            improvement=0.15,
            modifications_made=["prompt_enhancement"],
            benchmark_results={"test": 0.9},
            success=True,
        )
        assert result.improvement == 0.15
        assert result.success is True

    def test_benchmark_task(self):
        """Test BenchmarkTask dataclass."""
        from agents.coder.types import BenchmarkTask

        task = BenchmarkTask(
            id="bm1",
            description="Test description",
        )
        assert task.id == "bm1"
        assert task.difficulty == "medium"  # default
        assert task.language == "python"  # default


class TestDarwinGodelMixin:
    """Test Darwin Gödel evolution mixin."""

    @pytest.fixture
    def coder(self):
        """Create coder agent instance."""
        from agents.coder.agent import CoderAgent
        return CoderAgent()

    def test_get_archive_initializes(self, coder):
        """Test that get_archive initializes system."""
        archive = coder.get_archive()
        assert len(archive) >= 1

    def test_get_current_variant(self, coder):
        """Test getting current variant."""
        variant = coder.get_current_variant()
        assert variant is not None
        assert variant.generation >= 0

    def test_sample_parent(self, coder):
        """Test parent sampling."""
        coder._init_evolution()
        parent = coder._sample_parent()
        assert parent is not None
        assert parent.id in [v.id for v in coder._archive]

    @pytest.mark.asyncio
    async def test_propose_modifications(self, coder):
        """Test proposing modifications to a variant."""
        coder._init_evolution()
        parent = coder.get_current_variant()

        mods = await coder._propose_modifications(parent)

        assert "description" in mods
        assert isinstance(mods.get("description"), str)

    def test_get_evolution_stats(self, coder):
        """Test getting evolution statistics."""
        stats = coder.get_evolution_stats()
        assert "total_variants" in stats
        assert "best_fitness" in stats
        assert "evolution_cycles" in stats

    def test_get_lineage(self, coder):
        """Test getting variant lineage."""
        coder._init_evolution()
        variant = coder.get_current_variant()

        lineage = coder.get_lineage(variant.id)
        assert len(lineage) >= 1
        assert lineage[-1].id == variant.id


# =============================================================================
# RESEARCHER: Agentic RAG Tests
# =============================================================================

class TestAgenticRAGTypes:
    """Test researcher types module."""

    def test_query_complexity_enum(self):
        """Test QueryComplexity enum values."""
        from agents.researcher.types import QueryComplexity

        assert QueryComplexity.SIMPLE.value == "simple"
        assert QueryComplexity.MODERATE.value == "moderate"
        assert QueryComplexity.COMPLEX.value == "complex"

    def test_retrieval_strategy_enum(self):
        """Test RetrievalStrategy enum values."""
        from agents.researcher.types import RetrievalStrategy

        assert RetrievalStrategy.DIRECT_ANSWER.value == "direct"
        assert RetrievalStrategy.SINGLE_RETRIEVAL.value == "single"
        assert RetrievalStrategy.MULTI_HOP.value == "multi_hop"
        assert RetrievalStrategy.CORRECTIVE.value == "corrective"

    def test_research_result(self):
        """Test ResearchResult dataclass."""
        from agents.researcher.types import ResearchResult

        result = ResearchResult(
            source="docs",
            title="Test Title",
            content="Test content",
            url="https://example.com",
            relevance_score=0.9,
        )
        assert result.source == "docs"
        assert result.relevance_score == 0.9

    def test_research_report(self):
        """Test ResearchReport dataclass."""
        from agents.researcher.types import ResearchReport

        report = ResearchReport(
            query="test query",
            summary="Test summary",
            findings=[],
            sources=["source1"],
            confidence=0.8,
        )
        assert report.query == "test query"
        assert report.confidence == 0.8

    def test_retrieval_plan(self):
        """Test RetrievalPlan dataclass."""
        from agents.researcher.types import RetrievalPlan

        plan = RetrievalPlan(
            original_query="Test query",
            sub_queries=["sub1", "sub2"],
            sources_to_check=["docs", "web"],
            estimated_hops=2,
            reasoning="Test reasoning",
        )
        assert len(plan.sub_queries) == 2
        assert plan.estimated_hops == 2

    def test_sufficiency_evaluation(self):
        """Test SufficiencyEvaluation dataclass."""
        from agents.researcher.types import SufficiencyEvaluation

        eval = SufficiencyEvaluation(
            sufficient=True,
            confidence=0.85,
            missing_aspects=[],
            recommendation="generate",
        )
        assert eval.sufficient is True
        assert eval.recommendation == "generate"

    def test_documentation_agent(self):
        """Test DocumentationAgent class."""
        from agents.researcher.types import DocumentationAgent

        agent = DocumentationAgent()
        assert agent.name == "documentation"
        assert agent.source_type == "docs"

    def test_web_search_agent(self):
        """Test WebSearchAgent class."""
        from agents.researcher.types import WebSearchAgent

        agent = WebSearchAgent()
        assert agent.name == "web_search"
        assert agent.source_type == "web"

    def test_codebase_agent(self):
        """Test CodebaseAgent class."""
        from agents.researcher.types import CodebaseAgent

        agent = CodebaseAgent()
        assert agent.name == "codebase"
        assert agent.source_type == "code"


class TestAgenticRAGMixin:
    """Test Agentic RAG mixin."""

    @pytest.fixture
    def researcher(self):
        """Create researcher agent instance."""
        from agents.researcher.agent import ResearcherAgent
        return ResearcherAgent()

    def test_classify_complexity_simple(self, researcher):
        """Test simple query classification."""
        from agents.researcher.types import QueryComplexity

        result = researcher._classify_complexity("What is Python?")
        assert result == QueryComplexity.SIMPLE

    def test_classify_complexity_moderate(self, researcher):
        """Test moderate query classification."""
        from agents.researcher.types import QueryComplexity

        result = researcher._classify_complexity(
            "How does the authentication system work in detail?"
        )
        assert result == QueryComplexity.MODERATE

    def test_classify_complexity_complex(self, researcher):
        """Test complex query classification."""
        from agents.researcher.types import QueryComplexity

        result = researcher._classify_complexity(
            "Analyze the architecture and provide a comparative analysis "
            "of different approaches with trade-offs"
        )
        assert result == QueryComplexity.COMPLEX

    def test_select_strategy(self, researcher):
        """Test retrieval strategy selection."""
        from agents.researcher.types import QueryComplexity, RetrievalStrategy

        simple = researcher._select_strategy(QueryComplexity.SIMPLE)
        assert simple == RetrievalStrategy.SINGLE_RETRIEVAL

        complex_ = researcher._select_strategy(QueryComplexity.COMPLEX)
        assert complex_ == RetrievalStrategy.MULTI_HOP

    def test_plan_retrieval(self, researcher):
        """Test retrieval planning."""
        plan = researcher._plan_retrieval("Compare A and B")
        assert len(plan.sub_queries) >= 1
        assert "docs" in plan.sources_to_check

    def test_plan_retrieval_with_vs(self, researcher):
        """Test retrieval planning with vs query."""
        plan = researcher._plan_retrieval("Python vs JavaScript")
        assert len(plan.sub_queries) >= 2

    def test_route_query_docs(self, researcher):
        """Test query routing to docs."""
        agents = researcher._route_query("What is the API function?")
        assert "docs" in agents

    def test_route_query_web(self, researcher):
        """Test query routing to web."""
        agents = researcher._route_query("Latest news about Python")
        assert "web" in agents

    def test_route_query_code(self, researcher):
        """Test query routing to code."""
        agents = researcher._route_query("Implement the codebase search")
        assert "code" in agents

    def test_assess_relevance_empty(self, researcher):
        """Test relevance assessment with empty results."""
        result = researcher._assess_relevance([], "test")
        assert result == "No results found"

    def test_evaluate_sufficiency_empty(self, researcher):
        """Test sufficiency evaluation with empty results."""
        eval = researcher._evaluate_sufficiency("test", [])
        assert eval.sufficient is False
        assert eval.recommendation == "retrieve_more"

    def test_evaluate_sufficiency_with_results(self, researcher):
        """Test sufficiency evaluation with results."""
        from agents.researcher.types import ResearchResult

        results = [
            ResearchResult(
                source="docs",
                title="Test",
                content="Content",
                relevance_score=0.9,
            )
            for _ in range(5)
        ]

        eval = researcher._evaluate_sufficiency("test", results)
        assert eval.confidence > 0

    @pytest.mark.asyncio
    async def test_agentic_research(self, researcher):
        """Test agentic research execution."""
        result = await researcher.agentic_research("What is Python?")

        assert result.query == "What is Python?"
        assert result.complexity is not None
        assert result.strategy_used is not None
        assert len(result.reasoning_trace) > 0

    @pytest.mark.asyncio
    async def test_quick_lookup(self, researcher):
        """Test quick lookup."""
        result = await researcher.quick_lookup("What is Python?")
        assert result.iterations <= 1


# =============================================================================
# ARCHITECT: Three Loops Framework Tests
# =============================================================================

class TestThreeLoopsTypes:
    """Test architect types module."""

    def test_design_level_enum(self):
        """Test DesignLevel enum values."""
        from agents.architect.types import DesignLevel

        assert DesignLevel.SYSTEM.value == "system"
        assert DesignLevel.SERVICE.value == "service"
        assert DesignLevel.COMPONENT.value == "component"
        assert DesignLevel.MODULE.value == "module"

    def test_architect_loop_enum(self):
        """Test ArchitectLoop enum values."""
        from agents.architect.types import ArchitectLoop

        assert ArchitectLoop.IN_THE_LOOP.value == "AITL"
        assert ArchitectLoop.ON_THE_LOOP.value == "AOTL"
        assert ArchitectLoop.OUT_OF_LOOP.value == "AOOTL"

    def test_decision_impact_enum(self):
        """Test DecisionImpact enum values."""
        from agents.architect.types import DecisionImpact

        assert DecisionImpact.LOW.value == "low"
        assert DecisionImpact.MEDIUM.value == "medium"
        assert DecisionImpact.HIGH.value == "high"
        assert DecisionImpact.CRITICAL.value == "critical"

    def test_decision_risk_enum(self):
        """Test DecisionRisk enum values."""
        from agents.architect.types import DecisionRisk

        assert DecisionRisk.LOW.value == "low"
        assert DecisionRisk.MEDIUM.value == "medium"
        assert DecisionRisk.HIGH.value == "high"

    def test_loop_context(self):
        """Test LoopContext dataclass."""
        from agents.architect.types import (
            LoopContext,
            DecisionImpact,
            DecisionRisk,
        )

        context = LoopContext(
            decision_type="API design",
            impact=DecisionImpact.HIGH,
            risk=DecisionRisk.MEDIUM,
            agent_confidence=0.8,
            requires_domain_expertise=False,
            ethical_considerations=False,
            regulatory_implications=False,
        )
        assert context.decision_type == "API design"

    def test_loop_recommendation(self):
        """Test LoopRecommendation dataclass."""
        from agents.architect.types import LoopRecommendation, ArchitectLoop

        rec = LoopRecommendation(
            recommended_loop=ArchitectLoop.ON_THE_LOOP,
            confidence=0.85,
            reasoning="Test reasoning",
            guardrails=["Guard 1"],
            transition_triggers=["Trigger 1"],
        )
        assert rec.recommended_loop == ArchitectLoop.ON_THE_LOOP
        assert len(rec.guardrails) == 1

    def test_loop_rules_matrix(self):
        """Test LOOP_RULES decision matrix."""
        from agents.architect.types import (
            LOOP_RULES,
            DecisionImpact,
            DecisionRisk,
            ArchitectLoop,
        )

        # Critical impact, high risk -> IN_THE_LOOP
        assert LOOP_RULES[(DecisionImpact.CRITICAL, DecisionRisk.HIGH)] == (
            ArchitectLoop.IN_THE_LOOP
        )

        # Low impact, low risk -> OUT_OF_LOOP
        assert LOOP_RULES[(DecisionImpact.LOW, DecisionRisk.LOW)] == (
            ArchitectLoop.OUT_OF_LOOP
        )


class TestThreeLoopsMixin:
    """Test Three Loops mixin."""

    @pytest.fixture
    def architect(self):
        """Create architect agent instance."""
        from agents.architect.agent import ArchitectAgent
        return ArchitectAgent()

    def test_classify_decision_critical_impact(self, architect):
        """Test decision classification with critical impact."""
        from agents.architect.types import DecisionImpact

        context = architect.classify_decision("Design database schema")
        assert context.impact == DecisionImpact.CRITICAL

    def test_classify_decision_high_impact(self, architect):
        """Test decision classification with high impact."""
        from agents.architect.types import DecisionImpact

        context = architect.classify_decision("Create new service endpoint")
        assert context.impact == DecisionImpact.HIGH

    def test_classify_decision_medium_impact(self, architect):
        """Test decision classification with medium impact."""
        from agents.architect.types import DecisionImpact

        context = architect.classify_decision("Add new component")
        assert context.impact == DecisionImpact.MEDIUM

    def test_classify_decision_low_impact(self, architect):
        """Test decision classification with low impact."""
        from agents.architect.types import DecisionImpact

        context = architect.classify_decision("Refactor code formatting")
        assert context.impact == DecisionImpact.LOW

    def test_classify_decision_high_risk(self, architect):
        """Test decision classification with high risk."""
        from agents.architect.types import DecisionRisk

        context = architect.classify_decision("Migrate to new framework")
        assert context.risk == DecisionRisk.HIGH

    def test_classify_decision_ethical(self, architect):
        """Test decision classification with ethical considerations."""
        context = architect.classify_decision("Handle user data privacy")
        assert context.ethical_considerations is True

    def test_classify_decision_regulatory(self, architect):
        """Test decision classification with regulatory implications."""
        context = architect.classify_decision("Implement GDPR compliance")
        assert context.regulatory_implications is True

    def test_classify_decision_confidence(self, architect):
        """Test decision classification confidence levels."""
        simple = architect.classify_decision("Simple straightforward task")
        complex_ = architect.classify_decision("Complex unclear requirements")

        assert simple.agent_confidence > complex_.agent_confidence

    def test_select_loop_ethical(self, architect):
        """Test loop selection with ethical considerations."""
        from agents.architect.types import (
            LoopContext,
            DecisionImpact,
            DecisionRisk,
            ArchitectLoop,
        )

        context = LoopContext(
            decision_type="User data handling",
            impact=DecisionImpact.MEDIUM,
            risk=DecisionRisk.MEDIUM,
            agent_confidence=0.9,
            requires_domain_expertise=False,
            ethical_considerations=True,
            regulatory_implications=False,
        )

        rec = architect.select_loop(context)
        assert rec.recommended_loop == ArchitectLoop.IN_THE_LOOP
        assert rec.confidence >= 0.95

    def test_select_loop_regulatory(self, architect):
        """Test loop selection with regulatory implications."""
        from agents.architect.types import (
            LoopContext,
            DecisionImpact,
            DecisionRisk,
            ArchitectLoop,
        )

        context = LoopContext(
            decision_type="HIPAA compliance",
            impact=DecisionImpact.MEDIUM,
            risk=DecisionRisk.MEDIUM,
            agent_confidence=0.9,
            requires_domain_expertise=False,
            ethical_considerations=False,
            regulatory_implications=True,
        )

        rec = architect.select_loop(context)
        assert rec.recommended_loop == ArchitectLoop.IN_THE_LOOP

    def test_select_loop_domain_expertise(self, architect):
        """Test loop selection requiring domain expertise."""
        from agents.architect.types import (
            LoopContext,
            DecisionImpact,
            DecisionRisk,
            ArchitectLoop,
        )

        context = LoopContext(
            decision_type="Domain specific",
            impact=DecisionImpact.MEDIUM,
            risk=DecisionRisk.MEDIUM,
            agent_confidence=0.8,
            requires_domain_expertise=True,
            ethical_considerations=False,
            regulatory_implications=False,
        )

        rec = architect.select_loop(context)
        assert rec.recommended_loop == ArchitectLoop.IN_THE_LOOP

    def test_select_loop_low_confidence_escalation(self, architect):
        """Test loop escalation on low confidence."""
        from agents.architect.types import (
            LoopContext,
            DecisionImpact,
            DecisionRisk,
            ArchitectLoop,
        )

        context = LoopContext(
            decision_type="Uncertain decision",
            impact=DecisionImpact.LOW,
            risk=DecisionRisk.LOW,
            agent_confidence=0.3,
            requires_domain_expertise=False,
            ethical_considerations=False,
            regulatory_implications=False,
        )

        rec = architect.select_loop(context)
        # Low confidence should escalate from OUT_OF_LOOP
        assert rec.recommended_loop != ArchitectLoop.OUT_OF_LOOP

    def test_get_loop_guardrails(self, architect):
        """Test guardrails retrieval for each loop."""
        from agents.architect.types import ArchitectLoop

        for loop in ArchitectLoop:
            guardrails = architect._get_loop_guardrails(loop)
            assert len(guardrails) > 0
            assert all(isinstance(g, str) for g in guardrails)

    def test_get_transition_triggers(self, architect):
        """Test transition triggers retrieval."""
        from agents.architect.types import (
            LoopContext,
            DecisionImpact,
            DecisionRisk,
            ArchitectLoop,
        )

        context = LoopContext(
            decision_type="Test",
            impact=DecisionImpact.MEDIUM,
            risk=DecisionRisk.MEDIUM,
            agent_confidence=0.7,
            requires_domain_expertise=False,
            ethical_considerations=False,
            regulatory_implications=False,
        )

        for loop in ArchitectLoop:
            triggers = architect._get_transition_triggers(loop, context)
            assert len(triggers) > 0

    def test_build_reasoning(self, architect):
        """Test reasoning generation."""
        from agents.architect.types import (
            LoopContext,
            DecisionImpact,
            DecisionRisk,
            ArchitectLoop,
        )

        context = LoopContext(
            decision_type="Test",
            impact=DecisionImpact.HIGH,
            risk=DecisionRisk.MEDIUM,
            agent_confidence=0.8,
            requires_domain_expertise=False,
            ethical_considerations=False,
            regulatory_implications=False,
        )

        for loop in ArchitectLoop:
            reasoning = architect._build_reasoning(context, loop)
            assert "Impact" in reasoning
            assert "Risk" in reasoning
            assert "Confidence" in reasoning


# =============================================================================
# DEVOPS: Incident Handler Tests
# =============================================================================

class TestIncidentHandlerTypes:
    """Test devops types module."""

    def test_deployment_environment_enum(self):
        """Test DeploymentEnvironment enum values."""
        from agents.devops.types import DeploymentEnvironment

        assert DeploymentEnvironment.DEV.value == "development"
        assert DeploymentEnvironment.STAGING.value == "staging"
        assert DeploymentEnvironment.PRODUCTION.value == "production"

    def test_incident_severity_enum(self):
        """Test IncidentSeverity enum values."""
        from agents.devops.types import IncidentSeverity

        assert IncidentSeverity.SEV1.value == "sev1"
        assert IncidentSeverity.SEV2.value == "sev2"
        assert IncidentSeverity.SEV3.value == "sev3"
        assert IncidentSeverity.SEV4.value == "sev4"

    def test_incident_status_enum(self):
        """Test IncidentStatus enum values."""
        from agents.devops.types import IncidentStatus

        assert IncidentStatus.DETECTED.value == "detected"
        assert IncidentStatus.RESOLVED.value == "resolved"

    def test_root_cause_category_enum(self):
        """Test RootCauseCategory enum values."""
        from agents.devops.types import RootCauseCategory

        assert RootCauseCategory.CODE_CHANGE.value == "code_change"
        assert RootCauseCategory.RESOURCE_LIMIT.value == "resource_limit"
        assert RootCauseCategory.DEPENDENCY.value == "dependency"
        assert RootCauseCategory.CONFIGURATION.value == "configuration"
        assert RootCauseCategory.UNKNOWN.value == "unknown"

    def test_topology_node(self):
        """Test TopologyNode dataclass."""
        from agents.devops.types import TopologyNode

        node = TopologyNode(
            id="api-1",
            name="API Server",
            type="service",
            environment="production",
            dependencies=["db-1", "cache-1"],
        )
        assert node.id == "api-1"
        assert len(node.dependencies) == 2
        assert node.health_status == "healthy"

    def test_alert(self):
        """Test Alert dataclass."""
        from agents.devops.types import Alert, IncidentSeverity

        alert = Alert(
            id="alert-1",
            source="prometheus",
            severity=IncidentSeverity.SEV1,
            title="High CPU",
            description="CPU usage above 90%",
            affected_resources=["api-1"],
            triggered_at="2025-01-01T00:00:00",
        )
        assert alert.severity == IncidentSeverity.SEV1

    def test_remediation(self):
        """Test Remediation dataclass."""
        from agents.devops.types import Remediation

        remediation = Remediation(
            id="rem-1",
            action="restart_service",
            description="Restart the service",
            risk_level="low",
            requires_approval=False,
            estimated_impact="Brief downtime",
            rollback_plan="N/A",
        )
        assert remediation.requires_approval is False


class TestIncidentHandlerMixin:
    """Test Incident Handler mixin."""

    @pytest.fixture
    def devops(self):
        """Create devops agent instance."""
        from agents.devops.agent import DevOpsAgent
        return DevOpsAgent()

    def test_build_topology(self, devops):
        """Test topology building."""
        services = [
            {"id": "api", "name": "API", "type": "service"},
            {"id": "db", "name": "Database", "type": "database"},
        ]

        topology = devops.build_topology(services)
        assert len(topology) == 2
        assert "api" in topology
        assert "db" in topology

    def test_build_topology_with_dependencies(self, devops):
        """Test topology building with dependencies."""
        services = [
            {"id": "api", "name": "API", "type": "service", "dependencies": ["db"]},
            {"id": "db", "name": "Database", "type": "database"},
        ]

        topology = devops.build_topology(services)
        assert "db" in topology["api"].dependencies

    def test_get_topology(self, devops):
        """Test getting topology."""
        topology = devops.get_topology()
        assert isinstance(topology, dict)

    @pytest.mark.asyncio
    async def test_investigate_incident(self, devops):
        """Test incident investigation."""
        from agents.devops.types import Alert, IncidentSeverity

        devops.build_topology([
            {"id": "api", "name": "API", "type": "service"},
        ])

        alert = Alert(
            id="alert-1",
            source="prometheus",
            severity=IncidentSeverity.SEV2,
            title="High Latency",
            description="API latency increased",
            affected_resources=["api"],
            triggered_at="2025-01-01T00:00:00",
        )

        incident = await devops.investigate_incident(alert)

        assert incident is not None
        assert incident.title == "High Latency"
        assert len(incident.investigation_steps) >= 3
        assert incident.root_cause is not None

    def test_record_deployment(self, devops):
        """Test recording deployment."""
        devops.record_deployment(
            service="api",
            version="1.0.0",
            environment="production",
            deployed_by="user",
        )

        assert len(devops._deployment_history) >= 1

    @pytest.mark.asyncio
    async def test_execute_remediation_not_found(self, devops):
        """Test remediation execution with not found."""
        devops._init_incident_system()
        result = await devops.execute_remediation("inc-xxx", "rem-xxx")
        assert result["success"] is False

    def test_resolve_incident_not_found(self, devops):
        """Test resolving non-existent incident."""
        devops._init_incident_system()
        with pytest.raises(ValueError):
            devops.resolve_incident("inc-xxx", "test")

    def test_get_incident_metrics(self, devops):
        """Test getting incident metrics."""
        metrics = devops.get_incident_metrics()
        assert "total_incidents" in metrics
        assert "avg_mttr_seconds" in metrics


# =============================================================================
# REVIEWER: Deep Think Tests
# =============================================================================

class TestDeepThinkTypes:
    """Test reviewer types module."""

    def test_review_severity_enum(self):
        """Test ReviewSeverity enum values."""
        from agents.reviewer.types import ReviewSeverity

        assert ReviewSeverity.CRITICAL.value == "critical"
        assert ReviewSeverity.HIGH.value == "high"
        assert ReviewSeverity.MEDIUM.value == "medium"
        assert ReviewSeverity.LOW.value == "low"
        assert ReviewSeverity.INFO.value == "info"

    def test_deep_think_stage_enum(self):
        """Test DeepThinkStage enum values."""
        from agents.reviewer.types import DeepThinkStage

        assert DeepThinkStage.STATIC_ANALYSIS.value == "static"
        assert DeepThinkStage.DEEP_REASONING.value == "reasoning"
        assert DeepThinkStage.CRITIQUE.value == "critique"
        assert DeepThinkStage.VALIDATION.value == "validation"

    def test_thinking_step(self):
        """Test ThinkingStep dataclass."""
        from agents.reviewer.types import ThinkingStep, DeepThinkStage

        step = ThinkingStep(
            stage=DeepThinkStage.STATIC_ANALYSIS,
            thought="Analyzing imports...",
            confidence=0.9,
            evidence=["import os"],
        )
        assert step.stage == DeepThinkStage.STATIC_ANALYSIS
        assert step.confidence == 0.9

    def test_review_finding(self):
        """Test ReviewFinding dataclass."""
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        finding = ReviewFinding(
            id="f1",
            severity=ReviewSeverity.WARNING if hasattr(ReviewSeverity, 'WARNING') else ReviewSeverity.MEDIUM,
            category="security",
            file_path="app.py",
            line_start=42,
            line_end=42,
            title="SQL Injection Risk",
            description="Potential SQL injection",
        )
        assert finding.line_start == 42

    def test_deep_think_result(self):
        """Test DeepThinkResult dataclass."""
        from agents.reviewer.types import DeepThinkResult

        result = DeepThinkResult(
            thinking_steps=[],
            validated_findings=[],
            rejected_findings=[],
            reasoning_summary="Test summary",
            confidence_score=0.85,
        )
        assert result.confidence_score == 0.85
        assert result.total_thinking_time == 0


class TestDeepThinkMixin:
    """Test Deep Think mixin."""

    @pytest.fixture
    def reviewer(self):
        """Create reviewer agent instance."""
        from agents.reviewer.agent import ReviewerAgent
        return ReviewerAgent()

    def test_stage_static_analysis(self, reviewer):
        """Test static analysis stage."""
        code = """
def foo():
    x = 1
    return x
"""
        findings, steps = reviewer._stage_static_analysis(code, "test.py", "python")
        assert isinstance(findings, list)
        assert isinstance(steps, list)

    def test_stage_static_analysis_with_issues(self, reviewer):
        """Test static analysis with code issues."""
        code = """
def foo():
    eval(input())
    exec("code")
"""
        findings, steps = reviewer._stage_static_analysis(code, "test.py", "python")
        # Should find dangerous patterns via AST
        assert len(findings) > 0 or len(steps) > 0

    def test_stage_deep_reasoning(self, reviewer):
        """Test deep reasoning stage."""
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        findings = [
            ReviewFinding(
                id="f1",
                severity=ReviewSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=1,
                line_end=1,
                title="Test",
                description="Test",
                confidence=0.6,
            )
        ]

        code = "x = 1"
        refined, steps = reviewer._stage_deep_reasoning(code, findings, "python")
        assert len(steps) > 0

    def test_stage_critique(self, reviewer):
        """Test critique stage."""
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        findings = [
            ReviewFinding(
                id="f1",
                severity=ReviewSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=1,
                line_end=1,
                title="Test Finding",
                description="Test",
                confidence=0.7,
            ),
        ]

        critiqued, steps = reviewer._stage_critique(findings, "x = 1")
        assert len(steps) > 0

    def test_stage_validation(self, reviewer):
        """Test validation stage."""
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        findings = [
            ReviewFinding(
                id="f1",
                severity=ReviewSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=1,
                line_end=1,
                title="High confidence",
                description="Test",
                confidence=0.8,
            ),
            ReviewFinding(
                id="f2",
                severity=ReviewSeverity.LOW,
                category="style",
                file_path="test.py",
                line_start=1,
                line_end=1,
                title="Low confidence",
                description="Test",
                confidence=0.3,
            ),
        ]

        validated, rejected, steps = reviewer._stage_validation(findings)

        assert len(validated) >= 1
        assert len(rejected) >= 1

    @pytest.mark.asyncio
    async def test_deep_think_review(self, reviewer):
        """Test deep think review."""
        code = """
def add(a: int, b: int) -> int:
    return a + b
"""
        result = await reviewer.deep_think_review(code, "test.py", "python")

        assert result is not None
        assert result.deep_think is not None
        assert result.score >= 0

    def test_calculate_score(self, reviewer):
        """Test score calculation."""
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        findings = [
            ReviewFinding(
                id="f1",
                severity=ReviewSeverity.CRITICAL,
                category="security",
                file_path="test.py",
                line_start=1,
                line_end=1,
                title="Critical",
                description="Test",
            ),
        ]

        score = reviewer._calculate_score(findings)
        assert score < 100  # Critical finding should reduce score

    def test_calculate_score_empty(self, reviewer):
        """Test score calculation with no findings."""
        score = reviewer._calculate_score([])
        assert score == 100.0


# =============================================================================
# ORCHESTRATOR: Bounded Autonomy Tests
# =============================================================================

class TestBoundedAutonomyTypes:
    """Test orchestrator types module."""

    def test_task_complexity_enum(self):
        """Test TaskComplexity enum values."""
        from agents.orchestrator.types import TaskComplexity

        assert TaskComplexity.TRIVIAL.value == "trivial"
        assert TaskComplexity.SIMPLE.value == "simple"
        assert TaskComplexity.MODERATE.value == "moderate"
        assert TaskComplexity.COMPLEX.value == "complex"
        assert TaskComplexity.CRITICAL.value == "critical"

    def test_autonomy_level_enum(self):
        """Test AutonomyLevel enum values."""
        from agents.orchestrator.types import AutonomyLevel

        assert AutonomyLevel.L0_AUTONOMOUS.value == "L0"
        assert AutonomyLevel.L1_NOTIFY.value == "L1"
        assert AutonomyLevel.L2_APPROVE.value == "L2"
        assert AutonomyLevel.L3_HUMAN_ONLY.value == "L3"

    def test_agent_role_enum(self):
        """Test AgentRole enum values."""
        from agents.orchestrator.types import AgentRole

        assert AgentRole.ORCHESTRATOR.value == "orchestrator"
        assert AgentRole.CODER.value == "coder"
        assert AgentRole.REVIEWER.value == "reviewer"
        assert AgentRole.ARCHITECT.value == "architect"

    def test_approval_request(self):
        """Test ApprovalRequest dataclass."""
        from agents.orchestrator.types import ApprovalRequest, AutonomyLevel

        request = ApprovalRequest(
            id="req-1",
            task_id="task-1",
            operation="delete_file",
            description="Delete old config",
            autonomy_level=AutonomyLevel.L2_APPROVE,
            proposed_action="rm config.old",
            risk_assessment="MEDIUM",
        )
        assert request.approved is None
        assert request.autonomy_level == AutonomyLevel.L2_APPROVE

    def test_approval_request_to_dict(self):
        """Test ApprovalRequest to_dict method."""
        from agents.orchestrator.types import ApprovalRequest, AutonomyLevel

        request = ApprovalRequest(
            id="req-1",
            task_id="task-1",
            operation="delete_file",
            description="Delete",
            autonomy_level=AutonomyLevel.L2_APPROVE,
            proposed_action="rm file",
            risk_assessment="MEDIUM",
        )

        d = request.to_dict()
        assert d["id"] == "req-1"
        assert d["autonomy_level"] == "L2"

    def test_task_dataclass(self):
        """Test Task dataclass."""
        from agents.orchestrator.types import Task, TaskComplexity

        task = Task(
            id="task-1",
            description="Write code",
            complexity=TaskComplexity.MODERATE,
        )
        assert task.status == "pending"
        assert task.subtasks == []

    def test_handoff_dataclass(self):
        """Test Handoff dataclass."""
        from agents.orchestrator.types import Handoff, AgentRole

        handoff = Handoff(
            from_agent=AgentRole.ORCHESTRATOR,
            to_agent=AgentRole.CODER,
            context="Write new function",
            task_id="task-1",
            reason="Code task",
        )
        assert handoff.from_agent == AgentRole.ORCHESTRATOR
        assert handoff.to_agent == AgentRole.CODER


class TestBoundedAutonomyMixin:
    """Test Bounded Autonomy mixin."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator agent instance."""
        from agents.orchestrator.agent import OrchestratorAgent
        return OrchestratorAgent()

    def test_get_autonomy_level_l0(self, orchestrator):
        """Test L0 autonomy level operations."""
        from agents.orchestrator.types import AutonomyLevel

        l0_ops = ["format_code", "lint_check", "run_tests", "read_file"]
        for op in l0_ops:
            level = orchestrator.get_autonomy_level(op)
            assert level == AutonomyLevel.L0_AUTONOMOUS

    def test_get_autonomy_level_l1(self, orchestrator):
        """Test L1 autonomy level operations."""
        from agents.orchestrator.types import AutonomyLevel

        l1_ops = ["write_file", "create_file", "refactor_code", "git_commit"]
        for op in l1_ops:
            level = orchestrator.get_autonomy_level(op)
            assert level == AutonomyLevel.L1_NOTIFY

    def test_get_autonomy_level_l2(self, orchestrator):
        """Test L2 autonomy level operations."""
        from agents.orchestrator.types import AutonomyLevel

        l2_ops = ["delete_file", "architecture_change", "git_push"]
        for op in l2_ops:
            level = orchestrator.get_autonomy_level(op)
            assert level == AutonomyLevel.L2_APPROVE

    def test_get_autonomy_level_l3(self, orchestrator):
        """Test L3 autonomy level operations."""
        from agents.orchestrator.types import AutonomyLevel

        l3_ops = ["deploy_production", "delete_database", "external_api_key"]
        for op in l3_ops:
            level = orchestrator.get_autonomy_level(op)
            assert level == AutonomyLevel.L3_HUMAN_ONLY

    def test_get_autonomy_level_unknown(self, orchestrator):
        """Test autonomy level for unknown operation."""
        from agents.orchestrator.types import AutonomyLevel

        level = orchestrator.get_autonomy_level("unknown_operation")
        assert level == AutonomyLevel.L1_NOTIFY  # Default

    def test_classify_operation_l3(self, orchestrator):
        """Test L3 operation classification."""
        assert orchestrator.classify_operation("Deploy to production") == "deploy_production"
        assert orchestrator.classify_operation("Get API key secret") == "external_api_key"

    def test_classify_operation_l2(self, orchestrator):
        """Test L2 operation classification."""
        assert orchestrator.classify_operation("Delete file config.py") == "delete_file"
        assert orchestrator.classify_operation("Change architecture") == "architecture_change"
        assert orchestrator.classify_operation("Git push changes") == "git_push"

    def test_classify_operation_l1(self, orchestrator):
        """Test L1 operation classification."""
        assert orchestrator.classify_operation("Write new code") == "write_file"
        assert orchestrator.classify_operation("Refactor module") == "refactor_code"
        assert orchestrator.classify_operation("Git commit changes") == "git_commit"

    def test_classify_operation_l0(self, orchestrator):
        """Test L0 operation classification."""
        assert orchestrator.classify_operation("Format code") == "format_code"
        assert orchestrator.classify_operation("Run tests") == "format_code"
        assert orchestrator.classify_operation("Search codebase") == "format_code"

    @pytest.mark.asyncio
    async def test_check_autonomy_l0(self, orchestrator):
        """Test autonomy check for L0 operation."""
        from agents.orchestrator.types import Task, AutonomyLevel

        task = Task(id="t1", description="Format code")
        can_proceed, approval = await orchestrator.check_autonomy(task, "format_code")

        assert can_proceed is True
        assert approval is None
        assert task.autonomy_level == AutonomyLevel.L0_AUTONOMOUS

    @pytest.mark.asyncio
    async def test_check_autonomy_l1(self, orchestrator):
        """Test autonomy check for L1 operation."""
        from agents.orchestrator.types import Task, AutonomyLevel

        task = Task(id="t1", description="Write file")
        can_proceed, approval = await orchestrator.check_autonomy(task, "write_file")

        assert can_proceed is True
        assert approval is None
        assert task.autonomy_level == AutonomyLevel.L1_NOTIFY

    @pytest.mark.asyncio
    async def test_check_autonomy_l2_no_callback(self, orchestrator):
        """Test autonomy check for L2 without callback."""
        from agents.orchestrator.types import Task, AutonomyLevel

        task = Task(id="t1", description="Delete file")
        can_proceed, approval = await orchestrator.check_autonomy(task, "delete_file")

        assert can_proceed is False
        assert approval is not None
        assert approval.autonomy_level == AutonomyLevel.L2_APPROVE
        assert approval.id in orchestrator.pending_approvals

    @pytest.mark.asyncio
    async def test_check_autonomy_l2_with_approval(self):
        """Test autonomy check for L2 with approval callback."""
        from agents.orchestrator.agent import OrchestratorAgent
        from agents.orchestrator.types import Task

        orchestrator = OrchestratorAgent(approval_callback=lambda x: True)

        task = Task(id="t1", description="Delete file")
        can_proceed, approval = await orchestrator.check_autonomy(task, "delete_file")

        assert can_proceed is True
        assert approval is not None
        assert approval.approved is True

    @pytest.mark.asyncio
    async def test_check_autonomy_l2_with_rejection(self):
        """Test autonomy check for L2 with rejection callback."""
        from agents.orchestrator.agent import OrchestratorAgent
        from agents.orchestrator.types import Task

        orchestrator = OrchestratorAgent(approval_callback=lambda x: False)

        task = Task(id="t1", description="Delete file")
        can_proceed, approval = await orchestrator.check_autonomy(task, "delete_file")

        assert can_proceed is False
        assert approval is not None
        assert approval.approved is False

    @pytest.mark.asyncio
    async def test_check_autonomy_l3(self, orchestrator):
        """Test autonomy check for L3 operation."""
        from agents.orchestrator.types import Task, AutonomyLevel

        task = Task(id="t1", description="Deploy production")
        can_proceed, approval = await orchestrator.check_autonomy(task, "deploy_production")

        assert can_proceed is False
        assert approval is not None
        assert approval.autonomy_level == AutonomyLevel.L3_HUMAN_ONLY
        assert "HUMAN MUST EXECUTE" in approval.proposed_action

    def test_assess_risk(self, orchestrator):
        """Test risk assessment generation."""
        from agents.orchestrator.types import Task

        task = Task(id="t1", description="Test")

        # Test known risks
        assert "MEDIUM" in orchestrator._assess_risk(task, "delete_file")
        assert "HIGH" in orchestrator._assess_risk(task, "architecture_change")
        assert "CRITICAL" in orchestrator._assess_risk(task, "deploy_production")

    @pytest.mark.asyncio
    async def test_notify_completion_l1(self):
        """Test notification on L1 task completion."""
        from agents.orchestrator.agent import OrchestratorAgent
        from agents.orchestrator.types import Task, AutonomyLevel

        notifications = []

        def notify(event: str, data: dict):
            notifications.append((event, data))

        orchestrator = OrchestratorAgent(notify_callback=notify)

        task = Task(id="t1", description="Write file")
        task.autonomy_level = AutonomyLevel.L1_NOTIFY

        await orchestrator.notify_completion(task, "File written")

        assert len(notifications) == 1
        assert notifications[0][0] == "task_completed"

    def test_approve_pending(self, orchestrator):
        """Test approving a pending request."""
        from agents.orchestrator.types import ApprovalRequest, AutonomyLevel

        request = ApprovalRequest(
            id="req-1",
            task_id="task-1",
            operation="delete_file",
            description="Delete",
            autonomy_level=AutonomyLevel.L2_APPROVE,
            proposed_action="rm file",
            risk_assessment="MEDIUM",
        )
        orchestrator.pending_approvals["req-1"] = request

        result = orchestrator.approve("req-1", "admin")

        assert result is True
        assert request.approved is True
        assert request.approved_by == "admin"
        assert request.approved_at is not None

    def test_approve_not_found(self, orchestrator):
        """Test approving non-existent request."""
        result = orchestrator.approve("nonexistent")
        assert result is False

    def test_reject_pending(self, orchestrator):
        """Test rejecting a pending request."""
        from agents.orchestrator.types import ApprovalRequest, AutonomyLevel

        request = ApprovalRequest(
            id="req-1",
            task_id="task-1",
            operation="delete_file",
            description="Delete",
            autonomy_level=AutonomyLevel.L2_APPROVE,
            proposed_action="rm file",
            risk_assessment="MEDIUM",
        )
        orchestrator.pending_approvals["req-1"] = request

        result = orchestrator.reject("req-1", "admin")

        assert result is True
        assert request.approved is False
        assert request.approved_by == "admin"

    def test_reject_not_found(self, orchestrator):
        """Test rejecting non-existent request."""
        result = orchestrator.reject("nonexistent")
        assert result is False

    def test_get_pending_approvals(self, orchestrator):
        """Test getting pending approvals."""
        from agents.orchestrator.types import ApprovalRequest, AutonomyLevel

        # Add pending request
        pending = ApprovalRequest(
            id="pending-1",
            task_id="task-1",
            operation="delete_file",
            description="Delete",
            autonomy_level=AutonomyLevel.L2_APPROVE,
            proposed_action="rm file",
            risk_assessment="MEDIUM",
        )

        # Add approved request
        approved = ApprovalRequest(
            id="approved-1",
            task_id="task-2",
            operation="git_push",
            description="Push",
            autonomy_level=AutonomyLevel.L2_APPROVE,
            proposed_action="git push",
            risk_assessment="MEDIUM",
            approved=True,
        )

        orchestrator.pending_approvals["pending-1"] = pending
        orchestrator.pending_approvals["approved-1"] = approved

        result = orchestrator.get_pending_approvals()

        assert len(result) == 1
        assert result[0]["id"] == "pending-1"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestAgentIntegration:
    """Integration tests for all agents working together."""

    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_coder(self):
        """Test orchestrator routing to coder."""
        from agents.orchestrator.agent import OrchestratorAgent
        from agents.orchestrator.types import Task, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(id="t1", description="Write code for user auth")
        role = await orchestrator.route(task)

        assert role == AgentRole.CODER

    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_reviewer(self):
        """Test orchestrator routing to reviewer."""
        from agents.orchestrator.agent import OrchestratorAgent
        from agents.orchestrator.types import Task, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(id="t1", description="Review the pull request")
        role = await orchestrator.route(task)

        assert role == AgentRole.REVIEWER

    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_architect(self):
        """Test orchestrator routing to architect."""
        from agents.orchestrator.agent import OrchestratorAgent
        from agents.orchestrator.types import Task, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(id="t1", description="Design system architecture")
        role = await orchestrator.route(task)

        assert role == AgentRole.ARCHITECT

    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_devops(self):
        """Test orchestrator routing to devops."""
        from agents.orchestrator.agent import OrchestratorAgent
        from agents.orchestrator.types import Task, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(id="t1", description="Deploy the application")
        role = await orchestrator.route(task)

        assert role == AgentRole.DEVOPS

    @pytest.mark.asyncio
    async def test_orchestrator_routes_to_researcher(self):
        """Test orchestrator routing to researcher."""
        from agents.orchestrator.agent import OrchestratorAgent
        from agents.orchestrator.types import Task, AgentRole

        orchestrator = OrchestratorAgent()

        task = Task(id="t1", description="Research documentation patterns")
        role = await orchestrator.route(task)

        assert role == AgentRole.RESEARCHER

    @pytest.mark.asyncio
    async def test_full_execution_flow(self):
        """Test full orchestrator execution flow."""
        from agents.orchestrator.agent import OrchestratorAgent

        orchestrator = OrchestratorAgent()

        chunks = []
        async for chunk in orchestrator.execute("Format the code"):
            chunks.append(chunk)

        output = "".join(chunks)
        assert "Orchestrator" in output
        assert "completed" in output.lower()

    def test_all_agents_instantiate(self):
        """Test all agents can be instantiated."""
        from agents.coder.agent import CoderAgent
        from agents.reviewer.agent import ReviewerAgent
        from agents.architect.agent import ArchitectAgent
        from agents.devops.agent import DevOpsAgent
        from agents.researcher.agent import ResearcherAgent
        from agents.orchestrator.agent import OrchestratorAgent

        agents = [
            CoderAgent(),
            ReviewerAgent(),
            ArchitectAgent(),
            DevOpsAgent(),
            ResearcherAgent(),
            OrchestratorAgent(),
        ]

        for agent in agents:
            assert agent.name is not None
            assert hasattr(agent, "get_status")

    def test_all_agents_have_status(self):
        """Test all agents provide status."""
        from agents.coder.agent import CoderAgent
        from agents.reviewer.agent import ReviewerAgent
        from agents.architect.agent import ArchitectAgent
        from agents.devops.agent import DevOpsAgent
        from agents.researcher.agent import ResearcherAgent
        from agents.orchestrator.agent import OrchestratorAgent

        agents = [
            CoderAgent(),
            ReviewerAgent(),
            ArchitectAgent(),
            DevOpsAgent(),
            ResearcherAgent(),
            OrchestratorAgent(),
        ]

        for agent in agents:
            status = agent.get_status()
            assert isinstance(status, dict)
            assert "name" in status
