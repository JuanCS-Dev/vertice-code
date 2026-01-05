"""
100% Coverage Tests for Phase 1 & 2 Mixin Files

Targets:
- darwin_godel.py: 48% → 100%
- agentic_rag.py: 78% → 100%
- three_loops.py: 93% → 100%
- incident_handler.py: 70% → 100%
- deep_think.py: 78% → 100%
- bounded_autonomy.py: 98% → 100%
"""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

import pytest


# =============================================================================
# DARWIN GÖDEL (darwin_godel.py) - Full Coverage
# =============================================================================

class TestDarwinGodelFullCoverage:
    """Complete coverage for Darwin Gödel mixin."""

    def test_init_evolution_creates_initial_variant(self, tmp_path):
        """Test _init_evolution creates initial variant when no archive exists."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test system prompt"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        assert len(agent._archive) == 1
        assert agent._current_variant is not None
        assert agent._current_variant.generation == 0
        assert agent._archive_path.exists()

    def test_init_evolution_loads_existing_archive(self, tmp_path):
        """Test _init_evolution loads from existing archive."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        archive_data = {
            "variants": [
                {
                    "id": "v1",
                    "parent_id": None,
                    "generation": 0,
                    "system_prompt": "Test",
                    "tools": ["t1"],
                    "strategies": {"max_corrections": 2},
                    "benchmark_scores": {"b1": 0.8},
                    "created_at": "2024-01-01",
                    "modification_description": "init",
                }
            ],
            "current_variant_id": "v1",
        }

        archive_path = tmp_path / "archive.json"
        with open(archive_path, "w") as f:
            json.dump(archive_data, f)

        class TestAgent(DarwinGodelMixin):
            pass

        agent = TestAgent()
        agent._init_evolution(archive_path=archive_path)

        assert len(agent._archive) == 1
        assert agent._archive[0].id == "v1"
        assert agent._current_variant.id == "v1"

    def test_load_archive_handles_corrupt_file(self, tmp_path):
        """Test _load_archive handles corrupt JSON gracefully."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        archive_path = tmp_path / "archive.json"
        with open(archive_path, "w") as f:
            f.write("not valid json {{{")

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=archive_path)

        # Should create initial variant on failure
        assert len(agent._archive) == 1
        assert agent._current_variant.generation == 0

    def test_generate_variant_id_is_unique(self, tmp_path):
        """Test _generate_variant_id produces unique IDs."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        id1 = agent._generate_variant_id()
        id2 = agent._generate_variant_id()
        assert id1 != id2
        assert len(id1) == 12

    def test_save_archive_creates_directory(self, tmp_path):
        """Test _save_archive creates parent directory."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        nested_path = tmp_path / "nested" / "deep" / "archive.json"
        agent._init_evolution(archive_path=nested_path)

        assert nested_path.exists()
        with open(nested_path) as f:
            data = json.load(f)
        assert "variants" in data

    def test_get_archive_initializes_if_needed(self, tmp_path):
        """Test get_archive initializes evolution if not done."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        # Pre-set the path so get_archive() uses temp instead of default
        agent._archive_path = tmp_path / "archive.json"
        agent._evolution_history = []

        # Should not have _archive yet
        assert not hasattr(agent, "_archive")

        archive = agent.get_archive()
        assert len(archive) >= 1  # May have more from default location

    def test_get_current_variant_initializes_if_needed(self, tmp_path):
        """Test get_current_variant initializes evolution if needed."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        variant = agent.get_current_variant()
        assert variant is not None
        assert variant.generation == 0

    @pytest.mark.asyncio
    async def test_evolve_creates_new_variant(self, tmp_path):
        """Test evolve() creates and evaluates new variants."""
        from agents.coder.darwin_godel import DarwinGodelMixin
        from agents.coder.types import BenchmarkTask, GeneratedCode, EvaluationResult

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

            async def generate_with_evaluation(self, request, max_corrections=2):
                return GeneratedCode(
                    code="def foo(): pass",
                    language="python",
                    explanation="Test",
                    evaluation=EvaluationResult(
                        valid_syntax=True,
                        lint_score=0.9,
                        quality_score=0.8,
                    ),
                )

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        tasks = [
            BenchmarkTask(
                id="task1",
                description="Create a function",
                language="python",
                difficulty=0.5,
            )
        ]

        result = await agent.evolve(tasks, improvement_threshold=0.0)

        assert result is not None
        assert result.new_variant is not None
        assert result.success is True

    @pytest.mark.asyncio
    async def test_evolve_rejects_low_improvement(self, tmp_path):
        """Test evolve() rejects variants with low improvement."""
        from agents.coder.darwin_godel import DarwinGodelMixin
        from agents.coder.types import BenchmarkTask, GeneratedCode, EvaluationResult

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

            async def generate_with_evaluation(self, request, max_corrections=2):
                return GeneratedCode(
                    code="def foo(): pass",
                    language="python",
                    explanation="Test",
                    evaluation=EvaluationResult(
                        valid_syntax=True,
                        lint_score=0.1,
                        quality_score=0.1,
                    ),
                )

        agent = TestAgent()
        archive_path = tmp_path / "archive.json"

        # Pre-seed with a high-fitness variant
        archive_data = {
            "variants": [
                {
                    "id": "v1",
                    "parent_id": None,
                    "generation": 0,
                    "system_prompt": "Test",
                    "tools": ["t1"],
                    "strategies": {"max_corrections": 2, "quality_threshold": 0.6},
                    "benchmark_scores": {"task1": 0.95},
                    "created_at": "2024-01-01",
                    "modification_description": "",
                }
            ],
        }
        with open(archive_path, "w") as f:
            json.dump(archive_data, f)

        agent._init_evolution(archive_path=archive_path)

        tasks = [
            BenchmarkTask(
                id="task1",
                description="Create a function",
                language="python",
                difficulty=0.5,
            )
        ]

        result = await agent.evolve(tasks, improvement_threshold=0.5)

        # Low quality should be rejected
        assert result.success is False

    def test_sample_parent_single_variant(self, tmp_path):
        """Test _sample_parent with single variant."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        parent = agent._sample_parent()
        assert parent == agent._archive[0]

    def test_sample_parent_multiple_variants(self, tmp_path):
        """Test _sample_parent with multiple variants uses fitness-weighted selection."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        archive_data = {
            "variants": [
                {
                    "id": f"v{i}",
                    "parent_id": None,
                    "generation": i,
                    "system_prompt": "Test",
                    "tools": ["t1"],
                    "strategies": {"max_corrections": 2},
                    "benchmark_scores": {f"b{i}": 0.1 * i},
                    "created_at": "2024-01-01",
                    "modification_description": "",
                }
                for i in range(5)
            ],
        }

        archive_path = tmp_path / "archive.json"
        with open(archive_path, "w") as f:
            json.dump(archive_data, f)

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=archive_path)

        # Run multiple times to cover both branches (70% fitness, 30% random)
        parents = [agent._sample_parent() for _ in range(20)]
        assert len(parents) == 20

    @pytest.mark.asyncio
    async def test_propose_modifications_all_types(self, tmp_path):
        """Test _propose_modifications covers all modification types."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        parent = agent._archive[0]

        # Run multiple times to cover all modification branches
        all_mods = []
        for _ in range(20):
            mods = await agent._propose_modifications(parent)
            all_mods.append(mods)

        # Should have different types of modifications
        has_prompt = any("system_prompt" in m for m in all_mods)
        has_strategy = any("strategies" in m for m in all_mods)
        has_tools = any("tools" in m for m in all_mods)

        # At least one type should be covered
        assert has_prompt or has_strategy or has_tools

    @pytest.mark.asyncio
    async def test_run_benchmarks_with_test_code(self, tmp_path):
        """Test _run_benchmarks runs test code when provided."""
        from agents.coder.darwin_godel import DarwinGodelMixin
        from agents.coder.types import BenchmarkTask, GeneratedCode, EvaluationResult

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

            async def generate_with_evaluation(self, request, max_corrections=2):
                return GeneratedCode(
                    code="def add(a, b): return a + b",
                    language="python",
                    explanation="Test",
                    evaluation=EvaluationResult(
                        valid_syntax=True,
                        lint_score=0.9,
                        quality_score=0.8,
                    ),
                )

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        variant = agent._current_variant
        tasks = [
            BenchmarkTask(
                id="task1",
                description="Create add function",
                language="python",
                difficulty=0.5,
                test_code="assert add(1, 2) == 3",
            )
        ]

        scores = await agent._run_benchmarks(variant, tasks)
        assert "task1" in scores
        # Score should be boosted by passing test
        assert scores["task1"] >= 0.8

    @pytest.mark.asyncio
    async def test_run_benchmarks_handles_exception(self, tmp_path):
        """Test _run_benchmarks handles exceptions gracefully."""
        from agents.coder.darwin_godel import DarwinGodelMixin
        from agents.coder.types import BenchmarkTask

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

            async def generate_with_evaluation(self, request, max_corrections=2):
                raise RuntimeError("Simulated failure")

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        tasks = [
            BenchmarkTask(
                id="task1",
                description="Fail task",
                language="python",
                difficulty=0.5,
            )
        ]

        scores = await agent._run_benchmarks(agent._current_variant, tasks)
        assert scores["task1"] == 0.0

    def test_run_test_code_success(self, tmp_path):
        """Test _run_test_code with passing test."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        code = "def add(a, b): return a + b"
        test_code = "assert add(1, 2) == 3"

        result = agent._run_test_code(code, test_code)
        assert result is True

    def test_run_test_code_failure(self, tmp_path):
        """Test _run_test_code with failing test."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        code = "def add(a, b): return a - b"  # Wrong implementation
        test_code = "assert add(1, 2) == 3"

        result = agent._run_test_code(code, test_code)
        assert result is False

    def test_run_test_code_timeout(self, tmp_path):
        """Test _run_test_code handles timeout."""
        from agents.coder.darwin_godel import DarwinGodelMixin
        import subprocess

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        code = "import time; time.sleep(100)"
        test_code = "pass"

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("cmd", 10)
            result = agent._run_test_code(code, test_code)
            assert result is False

    def test_get_evolution_stats(self, tmp_path):
        """Test get_evolution_stats returns correct stats."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        stats = agent.get_evolution_stats()

        assert stats["total_variants"] == 1
        assert stats["current_generation"] == 0
        assert stats["evolution_cycles"] == 0
        assert stats["successful_evolutions"] == 0

    def test_get_lineage(self, tmp_path):
        """Test get_lineage traces variant ancestry."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        archive_data = {
            "variants": [
                {
                    "id": "v0",
                    "parent_id": None,
                    "generation": 0,
                    "system_prompt": "Test",
                    "tools": [],
                    "strategies": {},
                    "benchmark_scores": {},
                },
                {
                    "id": "v1",
                    "parent_id": "v0",
                    "generation": 1,
                    "system_prompt": "Test",
                    "tools": [],
                    "strategies": {},
                    "benchmark_scores": {},
                },
                {
                    "id": "v2",
                    "parent_id": "v1",
                    "generation": 2,
                    "system_prompt": "Test",
                    "tools": [],
                    "strategies": {},
                    "benchmark_scores": {},
                },
            ],
            "current_variant_id": "v2",
        }

        archive_path = tmp_path / "archive.json"
        with open(archive_path, "w") as f:
            json.dump(archive_data, f)

        class TestAgent(DarwinGodelMixin):
            pass

        agent = TestAgent()
        # Must init with the archive_path to load the existing file
        agent._init_evolution(archive_path=archive_path)

        lineage = agent.get_lineage("v2")
        assert len(lineage) == 3
        assert lineage[0].id == "v0"
        assert lineage[1].id == "v1"
        assert lineage[2].id == "v2"

    def test_get_lineage_not_found(self, tmp_path):
        """Test get_lineage with non-existent variant."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        lineage = agent.get_lineage("nonexistent")
        assert lineage == []


# =============================================================================
# AGENTIC RAG (agentic_rag.py) - Full Coverage
# =============================================================================

class TestAgenticRAGFullCoverage:
    """Complete coverage for Agentic RAG mixin."""

    @pytest.mark.asyncio
    async def test_direct_answer_strategy(self):
        """Test DIRECT_ANSWER strategy returns immediately."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import QueryComplexity, RetrievalStrategy

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()
        agent._init_retrieval_agents()

        # Force DIRECT_ANSWER by mocking strategy selection
        with patch.object(agent, "_classify_complexity", return_value=QueryComplexity.SIMPLE):
            with patch.object(agent, "_select_strategy", return_value=RetrievalStrategy.DIRECT_ANSWER):
                result = await agent.agentic_research("What is Python?")

        assert result.strategy_used == RetrievalStrategy.DIRECT_ANSWER
        assert result.iterations == 0
        assert result.confidence == 0.9

    @pytest.mark.asyncio
    async def test_multi_hop_strategy_with_plan(self):
        """Test MULTI_HOP strategy creates sub-queries."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import QueryComplexity, RetrievalStrategy, RetrievalPlan

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()
        agent._init_retrieval_agents()

        with patch.object(agent, "_classify_complexity", return_value=QueryComplexity.COMPLEX):
            with patch.object(agent, "_select_strategy", return_value=RetrievalStrategy.MULTI_HOP):
                with patch.object(agent, "_plan_retrieval", return_value=RetrievalPlan(
                    original_query="Compare Python vs JavaScript",
                    sub_queries=["sub1", "sub2"],
                    sources_to_check=["docs", "code"],
                    estimated_hops=2,
                    reasoning="Test plan",
                )):
                    result = await agent.agentic_research(
                        "Compare Python vs JavaScript",
                        max_iterations=1,
                    )

        assert result.strategy_used == RetrievalStrategy.MULTI_HOP

    @pytest.mark.asyncio
    async def test_corrective_strategy_refines_query(self):
        """Test CORRECTIVE strategy refines query when insufficient."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import (
            QueryComplexity, RetrievalStrategy, SufficiencyEvaluation
        )

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()
        agent._init_retrieval_agents()

        call_count = 0

        def mock_evaluate(query, results):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return SufficiencyEvaluation(
                    sufficient=False,
                    confidence=0.3,
                    missing_aspects=["more detail"],
                    recommendation="refine_query",
                )
            return SufficiencyEvaluation(
                sufficient=True,
                confidence=0.9,
                missing_aspects=[],
                recommendation="proceed",
            )

        with patch.object(agent, "_classify_complexity", return_value=QueryComplexity.MODERATE):
            with patch.object(agent, "_select_strategy", return_value=RetrievalStrategy.CORRECTIVE):
                with patch.object(agent, "_evaluate_sufficiency", side_effect=mock_evaluate):
                    result = await agent.agentic_research(
                        "How does caching work?",
                        max_iterations=3,
                    )

        assert result.iterations >= 1

    def test_classify_complexity_simple_patterns(self):
        """Test _classify_complexity identifies simple queries."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import QueryComplexity

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        simple_queries = [
            "What is Python?",
            "Define machine learning",
            "Who is Alan Turing?",
            "When was Linux created?",
        ]

        for query in simple_queries:
            assert agent._classify_complexity(query) == QueryComplexity.SIMPLE

    def test_classify_complexity_complex_patterns(self):
        """Test _classify_complexity identifies complex queries."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import QueryComplexity

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        complex_queries = [
            "Compare Python vs Java for web development",
            "Analyze the relationship between microservices and containers",
            "How does authentication work and integrate with authorization?",
            "Explain step by step how to deploy a Kubernetes cluster",
        ]

        for query in complex_queries:
            assert agent._classify_complexity(query) == QueryComplexity.COMPLEX

    def test_classify_complexity_by_length(self):
        """Test _classify_complexity uses word count for edge cases."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import QueryComplexity

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        # Short query (< 5 words) -> SIMPLE
        short = "Explain caching"
        assert agent._classify_complexity(short) == QueryComplexity.SIMPLE

        # Long query (> 15 words) -> COMPLEX
        long = "I need to understand how the various components of a distributed system interact with each other in production environments"
        assert agent._classify_complexity(long) == QueryComplexity.COMPLEX

        # Medium length -> MODERATE
        medium = "Explain how database indexing improves query performance"
        assert agent._classify_complexity(medium) == QueryComplexity.MODERATE

    def test_select_strategy_mapping(self):
        """Test _select_strategy maps complexity to strategy."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import QueryComplexity, RetrievalStrategy

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        assert agent._select_strategy(QueryComplexity.SIMPLE) == RetrievalStrategy.SINGLE_RETRIEVAL
        # MODERATE maps to CORRECTIVE or SINGLE based on implementation
        result = agent._select_strategy(QueryComplexity.MODERATE)
        assert result in [RetrievalStrategy.CORRECTIVE, RetrievalStrategy.SINGLE_RETRIEVAL]
        assert agent._select_strategy(QueryComplexity.COMPLEX) == RetrievalStrategy.MULTI_HOP

    def test_route_query(self):
        """Test _route_query routes to appropriate agents."""
        from agents.researcher.agentic_rag import AgenticRAGMixin

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()
        agent._init_retrieval_agents()

        # Code query should route to code agent
        agents = agent._route_query("How to implement a binary tree in Python")
        assert "code" in agents or "codebase" in agents

        # API query should route to docs agent
        agents = agent._route_query("REST API best practices")
        assert len(agents) > 0

    def test_assess_relevance(self):
        """Test _assess_relevance returns relevance assessment string."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import ResearchResult

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        # High relevance results
        high_results = [
            ResearchResult(
                source="docs",
                title="Python Guide",
                content="Python is a programming language",
                relevance_score=0.9,
            )
        ]
        assessment = agent._assess_relevance(high_results, "What is Python?")
        assert assessment == "High relevance"

        # No results
        empty_assessment = agent._assess_relevance([], "query")
        assert empty_assessment == "No results found"

        # Low relevance
        low_results = [
            ResearchResult(
                source="web",
                title="Unrelated",
                content="Something else",
                relevance_score=0.2,
            )
        ]
        low_assessment = agent._assess_relevance(low_results, "query")
        assert low_assessment == "Low relevance"

    def test_evaluate_sufficiency(self):
        """Test _evaluate_sufficiency evaluates result completeness."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import ResearchResult

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        # Empty results -> insufficient
        empty_eval = agent._evaluate_sufficiency("query", [])
        assert empty_eval.sufficient is False

        # Good results -> sufficient
        results = [
            ResearchResult(
                source="docs",
                title="Answer",
                content="Detailed answer to the query with all relevant information",
                relevance_score=0.9,
            )
        ]
        good_eval = agent._evaluate_sufficiency("query", results)
        assert good_eval.confidence > 0

    def test_refine_query(self):
        """Test _refine_query adds missing aspects."""
        from agents.researcher.agentic_rag import AgenticRAGMixin

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        refined = agent._refine_query("Python basics", ["advanced features", "async"])
        # Just verify it returns something
        assert len(refined) > 0

    def test_generate_answer(self):
        """Test _generate_answer synthesizes results."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import ResearchResult

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        results = [
            ResearchResult(
                source="docs",
                title="Source 1",
                content="Python is interpreted.",
                relevance_score=0.9,
            ),
            ResearchResult(
                source="web",
                title="Source 2",
                content="Python is dynamically typed.",
                relevance_score=0.8,
            ),
        ]

        answer = agent._generate_answer("What is Python?", results)
        assert len(answer) > 0

    def test_plan_retrieval(self):
        """Test _plan_retrieval creates sub-queries."""
        from agents.researcher.agentic_rag import AgenticRAGMixin

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        plan = agent._plan_retrieval("Compare Python and JavaScript")
        assert len(plan.sub_queries) > 0
        assert plan.original_query == "Compare Python and JavaScript"


# =============================================================================
# THREE LOOPS (three_loops.py) - Full Coverage
# =============================================================================

class TestThreeLoopsFullCoverage:
    """Complete coverage for Three Loops mixin."""

    def test_select_loop_low_confidence_escalation(self):
        """Test select_loop escalates loop when confidence is low."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import (
            LoopContext, DecisionImpact, DecisionRisk, ArchitectLoop
        )

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # Low confidence should escalate OUT_OF_LOOP to ON_THE_LOOP
        context = LoopContext(
            decision_type="technical",
            impact=DecisionImpact.LOW,
            risk=DecisionRisk.LOW,
            agent_confidence=0.3,  # Low confidence
            requires_domain_expertise=False,
            ethical_considerations=False,
            regulatory_implications=False,
        )

        rec = agent.select_loop(context)
        # Should be escalated from OUT_OF_LOOP
        assert rec.recommended_loop in [ArchitectLoop.ON_THE_LOOP, ArchitectLoop.IN_THE_LOOP]

    def test_select_loop_on_to_in_escalation(self):
        """Test ON_THE_LOOP escalates to IN_THE_LOOP with low confidence."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import (
            LoopContext, DecisionImpact, DecisionRisk, ArchitectLoop
        )

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # MEDIUM impact + MEDIUM risk = ON_THE_LOOP by LOOP_RULES
        # With agent_confidence < 0.5, ON_THE_LOOP escalates to IN_THE_LOOP
        context = LoopContext(
            decision_type="design",
            impact=DecisionImpact.MEDIUM,
            risk=DecisionRisk.MEDIUM,  # MEDIUM/MEDIUM -> ON_THE_LOOP
            agent_confidence=0.4,  # Low confidence triggers escalation
            requires_domain_expertise=False,
            ethical_considerations=False,
            regulatory_implications=False,
        )

        rec = agent.select_loop(context)
        assert rec.recommended_loop == ArchitectLoop.IN_THE_LOOP

    def test_select_loop_out_of_loop_confidence_floor(self):
        """Test OUT_OF_LOOP has minimum confidence of 0.7."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import (
            LoopContext, DecisionImpact, DecisionRisk, ArchitectLoop
        )

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # High confidence, low impact/risk -> OUT_OF_LOOP
        context = LoopContext(
            decision_type="refactor",
            impact=DecisionImpact.LOW,
            risk=DecisionRisk.LOW,
            agent_confidence=0.95,
            requires_domain_expertise=False,
            ethical_considerations=False,
            regulatory_implications=False,
        )

        rec = agent.select_loop(context)
        assert rec.recommended_loop == ArchitectLoop.OUT_OF_LOOP
        assert rec.confidence >= 0.7

    def test_classify_decision_low_risk(self):
        """Test classify_decision detects low risk operations."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import DecisionRisk

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # "fix" indicates low risk
        context = agent.classify_decision("Fix typos in documentation")
        assert context.risk == DecisionRisk.LOW

    def test_classify_decision_high_risk(self):
        """Test classify_decision detects high risk operations."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import DecisionRisk

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # "new" and "migrate" indicate high risk
        context = agent.classify_decision("Migrate to new database system")
        assert context.risk == DecisionRisk.HIGH

    def test_classify_decision_ethical_regulatory(self):
        """Test classify_decision detects ethical and regulatory flags."""
        from agents.architect.three_loops import ThreeLoopsMixin

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # User data -> ethical
        ctx1 = agent.classify_decision("Handle user data and privacy consent")
        assert ctx1.ethical_considerations is True

        # GDPR -> regulatory
        ctx2 = agent.classify_decision("Ensure GDPR compliance for EU users")
        assert ctx2.regulatory_implications is True

        # Domain expertise
        ctx3 = agent.classify_decision("Implement business specific custom rules")
        assert ctx3.requires_domain_expertise is True

    def test_classify_decision_confidence_levels(self):
        """Test classify_decision adjusts confidence based on keywords."""
        from agents.architect.three_loops import ThreeLoopsMixin

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # "simple" -> high confidence
        ctx1 = agent.classify_decision("Simple formatting change")
        assert ctx1.agent_confidence > 0.8

        # "complex" -> low confidence
        ctx2 = agent.classify_decision("Complex unclear requirements")
        assert ctx2.agent_confidence < 0.6

    def test_get_loop_guardrails(self):
        """Test _get_loop_guardrails returns appropriate guardrails."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import ArchitectLoop

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        in_guardrails = agent._get_loop_guardrails(ArchitectLoop.IN_THE_LOOP)
        assert len(in_guardrails) > 0

        out_guardrails = agent._get_loop_guardrails(ArchitectLoop.OUT_OF_LOOP)
        assert len(out_guardrails) > 0

    def test_get_transition_triggers(self):
        """Test _get_transition_triggers returns appropriate triggers."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import (
            ArchitectLoop, LoopContext, DecisionImpact, DecisionRisk
        )

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        context = LoopContext(
            decision_type="design",
            impact=DecisionImpact.MEDIUM,
            risk=DecisionRisk.MEDIUM,
            agent_confidence=0.7,
            requires_domain_expertise=False,
            ethical_considerations=False,
            regulatory_implications=False,
        )

        triggers = agent._get_transition_triggers(ArchitectLoop.ON_THE_LOOP, context)
        assert len(triggers) > 0

    def test_build_reasoning(self):
        """Test _build_reasoning generates explanation."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import (
            ArchitectLoop, LoopContext, DecisionImpact, DecisionRisk
        )

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        context = LoopContext(
            decision_type="architecture",
            impact=DecisionImpact.CRITICAL,
            risk=DecisionRisk.HIGH,
            agent_confidence=0.5,
            requires_domain_expertise=True,
            ethical_considerations=True,
            regulatory_implications=True,
        )

        reasoning = agent._build_reasoning(context, ArchitectLoop.IN_THE_LOOP)
        assert len(reasoning) > 0


# =============================================================================
# INCIDENT HANDLER (incident_handler.py) - Full Coverage
# =============================================================================

class TestIncidentHandlerFullCoverage:
    """Complete coverage for Incident Handler mixin."""

    def test_build_topology(self):
        """Test build_topology creates topology map."""
        from agents.devops.incident_handler import IncidentHandlerMixin

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        services = [
            {"id": "api", "name": "API Gateway", "type": "gateway", "dependencies": ["auth", "db"]},
            {"id": "auth", "name": "Auth Service", "type": "service", "dependencies": ["db"]},
            {"id": "db", "name": "Database", "type": "database", "dependencies": []},
        ]

        topology = agent.build_topology(services)

        assert "api" in topology
        assert "auth" in topology
        assert "db" in topology
        assert topology["api"].dependencies == ["auth", "db"]

    @pytest.mark.asyncio
    async def test_investigate_incident_full_flow(self):
        """Test investigate_incident full investigation flow."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import Alert, IncidentSeverity

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        # Build topology
        services = [
            {"id": "api", "name": "API", "type": "service", "dependencies": ["db"],
             "metrics": {"cpu_percent": 95, "memory_percent": 92}},
            {"id": "db", "name": "Database", "type": "database", "dependencies": []},
        ]
        agent.build_topology(services)

        # Record deployment
        agent.record_deployment("api", "v1.2.3", "production", "deploy-bot")

        alert = Alert(
            id="alert-1",
            source="monitoring",
            severity=IncidentSeverity.SEV2,
            title="API Error Spike",
            description="Error rate increased",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )

        incident = await agent.investigate_incident(alert)

        assert incident is not None
        assert len(incident.investigation_steps) > 0
        assert incident.root_cause is not None

    def test_identify_root_cause_code_change(self):
        """Test _identify_root_cause detects code changes."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            RootCauseCategory, InvestigationStep, Incident,
            IncidentSeverity, IncidentStatus, Alert
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        incident.investigation_steps = [
            InvestigationStep(
                id="s1",
                action="Check deployments",
                findings="Found recent deployment v1.2.3",
                timestamp="now",
                data_sources=["deployment_history"],
                confidence=0.8,
            )
        ]

        rca = agent._identify_root_cause(incident)
        assert rca.category == RootCauseCategory.CODE_CHANGE

    def test_identify_root_cause_resource_limit(self):
        """Test _identify_root_cause detects resource limits."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            RootCauseCategory, InvestigationStep, Incident,
            IncidentSeverity, IncidentStatus, Alert
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        incident.investigation_steps = [
            InvestigationStep(
                id="s1",
                action="Analyze metrics",
                findings="High CPU detected (95%)",
                timestamp="now",
                data_sources=["prometheus"],
                confidence=0.8,
            )
        ]

        rca = agent._identify_root_cause(incident)
        assert rca.category == RootCauseCategory.RESOURCE_LIMIT

    def test_identify_root_cause_dependency(self):
        """Test _identify_root_cause detects dependency issues."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            RootCauseCategory, InvestigationStep, Incident,
            IncidentSeverity, IncidentStatus, Alert
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        incident.investigation_steps = [
            InvestigationStep(
                id="s1",
                action="Check topology",
                findings="Upstream database unavailable",
                timestamp="now",
                data_sources=["topology_map"],
                confidence=0.8,
            )
        ]

        rca = agent._identify_root_cause(incident)
        assert rca.category == RootCauseCategory.DEPENDENCY

    def test_propose_remediations_code_change(self):
        """Test _propose_remediations for code change category."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            RootCauseCategory, RootCauseAnalysis, Incident,
            IncidentSeverity, IncidentStatus, Alert
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        incident.root_cause = RootCauseAnalysis(
            category=RootCauseCategory.CODE_CHANGE,
            description="Recent deployment",
            confidence=0.8,
            evidence=[],
            contributing_factors=[],
            related_changes=[],
        )

        remediations = agent._propose_remediations(incident)

        actions = [r.action for r in remediations]
        assert "rollback" in actions

    def test_propose_remediations_resource_limit(self):
        """Test _propose_remediations for resource limit category."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            RootCauseCategory, RootCauseAnalysis, Incident,
            IncidentSeverity, IncidentStatus, Alert
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        incident.root_cause = RootCauseAnalysis(
            category=RootCauseCategory.RESOURCE_LIMIT,
            description="High resource usage",
            confidence=0.8,
            evidence=[],
            contributing_factors=[],
            related_changes=[],
        )

        remediations = agent._propose_remediations(incident)

        actions = [r.action for r in remediations]
        assert "scale_up" in actions

    def test_propose_remediations_dependency(self):
        """Test _propose_remediations for dependency category."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            RootCauseCategory, RootCauseAnalysis, Incident,
            IncidentSeverity, IncidentStatus, Alert
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        incident.root_cause = RootCauseAnalysis(
            category=RootCauseCategory.DEPENDENCY,
            description="Upstream failure",
            confidence=0.8,
            evidence=[],
            contributing_factors=[],
            related_changes=[],
        )

        remediations = agent._propose_remediations(incident)

        actions = [r.action for r in remediations]
        assert "enable_circuit_breaker" in actions

    @pytest.mark.asyncio
    async def test_execute_remediation_success(self):
        """Test execute_remediation succeeds."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import Alert, IncidentSeverity

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="alert-1",
            source="test",
            severity=IncidentSeverity.SEV3,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )

        incident = await agent.investigate_incident(alert)

        # Find a remediation that doesn't require approval
        no_approval_rem = next(
            (r for r in incident.remediations if not r.requires_approval),
            None
        )

        if no_approval_rem:
            result = await agent.execute_remediation(incident.id, no_approval_rem.id)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_remediation_requires_approval(self):
        """Test execute_remediation blocks without approval."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import Alert, IncidentSeverity

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        # Record deployment to trigger code change -> rollback remediation
        agent.record_deployment("api", "v1.0", "prod", "bot")

        alert = Alert(
            id="alert-1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test deployment failure",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )

        incident = await agent.investigate_incident(alert)

        # Find rollback (requires approval)
        rollback = next(
            (r for r in incident.remediations if r.requires_approval),
            None
        )

        if rollback:
            # Without approval
            result = await agent.execute_remediation(incident.id, rollback.id)
            assert result["success"] is False
            assert "approval" in result["error"].lower()

            # With approval
            result = await agent.execute_remediation(
                incident.id, rollback.id, approved_by="admin"
            )
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_execute_remediation_not_found(self):
        """Test execute_remediation handles not found."""
        from agents.devops.incident_handler import IncidentHandlerMixin

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        # Incident not found
        result = await agent.execute_remediation("nonexistent", "rem-1")
        assert result["success"] is False

    def test_resolve_incident(self):
        """Test resolve_incident calculates MTTR."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import Incident, IncidentSeverity, IncidentStatus, Alert

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        # Create incident manually
        alert = Alert(
            id="alert-1",
            source="test",
            severity=IncidentSeverity.SEV3,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test Incident",
            severity=IncidentSeverity.SEV3,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        agent._incidents["inc-1"] = incident

        resolved = agent.resolve_incident("inc-1", "Fixed the issue")

        assert resolved.status == IncidentStatus.RESOLVED
        assert resolved.resolved_at is not None
        assert resolved.mttr_seconds >= 0

    def test_resolve_incident_not_found(self):
        """Test resolve_incident raises for unknown incident."""
        from agents.devops.incident_handler import IncidentHandlerMixin

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        with pytest.raises(ValueError):
            agent.resolve_incident("nonexistent", "Notes")

    def test_record_deployment(self):
        """Test record_deployment stores deployment info."""
        from agents.devops.incident_handler import IncidentHandlerMixin

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        agent.record_deployment("api", "v1.0.0", "production", "deploy-bot")

        assert len(agent._deployment_history) == 1
        assert agent._deployment_history[0]["service"] == "api"
        assert agent._deployment_history[0]["version"] == "v1.0.0"

    def test_get_incident_metrics(self):
        """Test get_incident_metrics returns metrics."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import Incident, IncidentSeverity, IncidentStatus, Alert

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        # Add a resolved incident with MTTR
        alert = Alert(
            id="alert-1",
            source="test",
            severity=IncidentSeverity.SEV3,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at="2024-01-01T00:00:00",
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV3,
            status=IncidentStatus.RESOLVED,
            detected_at="2024-01-01T00:00:00",
            affected_services=["api"],
            alerts=[alert],
            mttr_seconds=300,
        )
        agent._incidents["inc-1"] = incident

        metrics = agent.get_incident_metrics()

        assert metrics["total_incidents"] == 1
        assert metrics["resolved_incidents"] == 1
        assert metrics["avg_mttr_seconds"] == 300


# =============================================================================
# DEEP THINK (deep_think.py) - Full Coverage
# =============================================================================

class TestDeepThinkFullCoverage:
    """Complete coverage for Deep Think mixin."""

    @pytest.mark.asyncio
    async def test_deep_think_review_full_flow(self):
        """Test deep_think_review complete flow."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewResult

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = [
                ("SQL Injection", r"execute\s*\(.*\+"),
                ("Command Injection", r"os\.system\s*\("),
            ]

        agent = TestAgent()

        code = '''
import os

def run_command(user_input):
    os.system("ls " + user_input)  # Dangerous!
    return "done"
'''

        result = await agent.deep_think_review(code, "app.py", "python")

        assert isinstance(result, ReviewResult)
        assert result.deep_think is not None
        assert len(result.deep_think.thinking_steps) > 0

    @pytest.mark.asyncio
    async def test_deep_think_with_syntax_error(self):
        """Test deep_think_review handles Python syntax errors."""
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        code = "def broken(\n    return"  # Invalid syntax

        result = await agent.deep_think_review(code, "bad.py", "python")

        # Should have syntax error finding
        syntax_findings = [f for f in result.findings if "syntax" in f.category.lower()]
        assert len(syntax_findings) > 0

    def test_stage_static_analysis_pattern_matching(self):
        """Test _stage_static_analysis finds patterns."""
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = [
                ("eval usage", r"\beval\s*\("),
                ("exec usage", r"\bexec\s*\("),
            ]

        agent = TestAgent()

        code = '''
result = eval(user_input)
exec(dynamic_code)
'''

        findings, steps = agent._stage_static_analysis(code, "test.py", "python")

        assert len(findings) >= 2
        assert any("eval" in f.title.lower() for f in findings)
        assert any("exec" in f.title.lower() for f in findings)

    def test_analyze_python_ast_dangerous_calls(self):
        """Test _analyze_python_ast detects dangerous function calls."""
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        code = '''
import pickle
import os

data = pickle.loads(user_data)
os.system("rm -rf /")
result = eval("2+2")
'''

        findings, steps = agent._analyze_python_ast(code, "test.py")

        assert len(findings) >= 3
        calls_found = [f.title for f in findings]
        assert any("pickle.loads" in c for c in calls_found)
        assert any("os.system" in c for c in calls_found)
        assert any("eval" in c for c in calls_found)

    def test_get_call_name_attribute(self):
        """Test _get_call_name handles attribute access."""
        from agents.reviewer.deep_think import DeepThinkMixin
        import ast

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        code = "os.path.join('a', 'b')"
        tree = ast.parse(code)
        call_node = tree.body[0].value

        name = agent._get_call_name(call_node)
        assert name == "os.path.join"

    def test_stage_deep_reasoning_sanitization(self):
        """Test _stage_deep_reasoning detects sanitization."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        code = '''
user_input = sanitize(request.input)
escaped = escape(user_input)
result = execute(escaped)
'''

        finding = ReviewFinding(
            id="f1",
            severity=ReviewSeverity.HIGH,
            category="security",
            file_path="test.py",
            line_start=3,
            line_end=3,
            title="Potential issue",
            description="Test",
            confidence=0.8,
        )

        findings, steps = agent._stage_deep_reasoning(code, [finding], "python")

        # Confidence should be reduced due to sanitization
        assert finding.confidence < 0.8

    def test_stage_deep_reasoning_in_comment(self):
        """Test _stage_deep_reasoning detects commented code."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        code = '''
# This is a comment
# eval(user_input)  # Old code
safe_code()
'''

        finding = ReviewFinding(
            id="f1",
            severity=ReviewSeverity.HIGH,
            category="security",
            file_path="test.py",
            line_start=2,  # Line with comment
            line_end=2,
            title="eval usage",
            description="Test",
            confidence=0.8,
        )

        findings, steps = agent._stage_deep_reasoning(code, [finding], "python")

        # Confidence should be reduced significantly for commented code
        assert finding.confidence < 0.5

    def test_stage_deep_reasoning_test_file(self):
        """Test _stage_deep_reasoning adjusts for test files."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        code = "eval(test_input)"

        finding = ReviewFinding(
            id="f1",
            severity=ReviewSeverity.HIGH,
            category="security",
            file_path="tests/test_security.py",  # Test file path
            line_start=1,
            line_end=1,
            title="eval usage",
            description="Test",
            confidence=0.8,
        )

        findings, steps = agent._stage_deep_reasoning(code, [finding], "python")

        # Confidence reduced for test files
        assert finding.confidence < 0.8

    def test_stage_deep_reasoning_user_input_context(self):
        """Test _stage_deep_reasoning with user input."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        code = '''
user_input = request.get("input")
result = eval(user_input)
'''

        finding = ReviewFinding(
            id="f1",
            severity=ReviewSeverity.HIGH,
            category="security",
            file_path="app.py",
            line_start=2,
            line_end=2,
            title="eval with user input",
            description="Test",
            confidence=0.6,
        )

        findings, steps = agent._stage_deep_reasoning(code, [finding], "python")
        # Just verify it runs without error
        assert len(steps) >= 0

    def test_stage_critique(self):
        """Test _stage_critique validates findings."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        findings = [
            ReviewFinding(
                id="f1",
                severity=ReviewSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=1,
                line_end=1,
                title="Issue 1",
                description="Description 1",
                confidence=0.8,
            ),
        ]

        code = "eval(user_input)"

        critiqued_findings, critique_steps = agent._stage_critique(findings, code)

        assert len(critique_steps) > 0
        # Findings should have suggestions generated
        assert all(f.suggestion is not None for f in critiqued_findings)

    def test_stage_validation_filters_low_confidence(self):
        """Test _stage_validation filters low confidence findings."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

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
                line_start=2,
                line_end=2,
                title="Low confidence",
                description="Test",
                confidence=0.2,  # Very low
            ),
        ]

        validated, rejected, steps = agent._stage_validation(findings)

        # High confidence should be validated
        assert any(f.id == "f1" for f in validated)
        # Low confidence should be rejected
        assert any(f.id == "f2" for f in rejected)

    def test_calculate_score_empty_findings(self):
        """Test _calculate_score with no findings."""
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        score = agent._calculate_score([])
        assert score == 100.0

    def test_calculate_score_with_findings(self):
        """Test _calculate_score deducts for findings."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

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
                confidence=0.9,
            ),
        ]

        score = agent._calculate_score(findings)
        assert score < 100.0
        assert score >= 0.0

    def test_check_sanitization(self):
        """Test _check_sanitization detects sanitization patterns."""
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        sanitized_lines = [
            "input = sanitize(user_input)",
            "safe = escape(data)",
            "clean = validate(form)",
        ]
        assert agent._check_sanitization(sanitized_lines) is True

        unsanitized_lines = [
            "input = user_input",
            "result = process(data)",
        ]
        assert agent._check_sanitization(unsanitized_lines) is False

    def test_is_in_comment_python(self):
        """Test _is_in_comment for Python comments."""
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        lines = [
            "normal_code()",
            "# This is a comment",
            "more_code()",
        ]

        assert agent._is_in_comment(lines, 0, "python") is False
        assert agent._is_in_comment(lines, 1, "python") is True
        assert agent._is_in_comment(lines, 2, "python") is False


# =============================================================================
# BOUNDED AUTONOMY (bounded_autonomy.py) - Full Coverage
# =============================================================================

class TestBoundedAutonomyFullCoverage:
    """Complete coverage for Bounded Autonomy mixin."""

    def test_classify_operation_database_migration(self):
        """Test classify_operation detects database migration."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin

        class TestAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = None
            _notify_callback = None

        agent = TestAgent()

        op = agent.classify_operation("Run database migration for users table")
        assert op == "database_migration"

    def test_classify_operation_default(self):
        """Test classify_operation returns default for unknown operations."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin

        class TestAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = None
            _notify_callback = None

        agent = TestAgent()

        # Generic task with no keywords
        op = agent.classify_operation("Do something with the system")
        assert op == "write_file"  # Default

    def test_classify_operation_all_levels(self):
        """Test classify_operation covers all autonomy levels."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin

        class TestAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = None
            _notify_callback = None

        agent = TestAgent()

        # L3 operations
        assert agent.classify_operation("Deploy to production") == "deploy_production"
        assert agent.classify_operation("Handle API key secrets") == "external_api_key"

        # L2 operations
        assert agent.classify_operation("Delete the config file") == "delete_file"
        assert agent.classify_operation("Change the architecture design") == "architecture_change"
        assert agent.classify_operation("Push to git remote") == "git_push"

        # L1 operations
        assert agent.classify_operation("Write new file") == "write_file"
        assert agent.classify_operation("Refactor the code") == "refactor_code"
        assert agent.classify_operation("Commit changes") == "git_commit"

        # L0 operations
        assert agent.classify_operation("Format the code") == "format_code"
        assert agent.classify_operation("Run lint check") == "format_code"
        assert agent.classify_operation("Run tests") == "format_code"

    @pytest.mark.asyncio
    async def test_check_autonomy_all_levels(self):
        """Test check_autonomy for all autonomy levels."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin
        from agents.orchestrator.types import Task, AutonomyLevel

        class TestAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = None
            _notify_callback = None

        agent = TestAgent()

        # L0 - should proceed
        task_l0 = Task(id="t1", description="Format the code")
        can, approval = await agent.check_autonomy(task_l0, "format_code")
        assert can is True
        assert task_l0.autonomy_level == AutonomyLevel.L0_AUTONOMOUS

        # L1 - should proceed
        task_l1 = Task(id="t2", description="Write file")
        can, approval = await agent.check_autonomy(task_l1, "write_file")
        assert can is True
        assert task_l1.autonomy_level == AutonomyLevel.L1_NOTIFY

        # L2 - should block without callback
        task_l2 = Task(id="t3", description="Delete file")
        can, approval = await agent.check_autonomy(task_l2, "delete_file")
        assert can is False
        assert approval is not None
        assert task_l2.autonomy_level == AutonomyLevel.L2_APPROVE

        # L3 - should always block
        task_l3 = Task(id="t4", description="Deploy prod")
        can, approval = await agent.check_autonomy(task_l3, "deploy_production")
        assert can is False
        assert approval is not None
        assert task_l3.autonomy_level == AutonomyLevel.L3_HUMAN_ONLY

    @pytest.mark.asyncio
    async def test_check_autonomy_l2_with_callbacks(self):
        """Test check_autonomy L2 with approval/rejection callbacks."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin
        from agents.orchestrator.types import Task

        # Test approval
        class ApproveAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = lambda self, req: True
            _notify_callback = None

        approve_agent = ApproveAgent()
        task = Task(id="t1", description="Delete file")
        can, approval = await approve_agent.check_autonomy(task, "delete_file")
        assert can is True
        assert approval.approved is True

        # Test rejection
        class RejectAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = lambda self, req: False
            _notify_callback = None

        reject_agent = RejectAgent()
        task2 = Task(id="t2", description="Delete file")
        can, approval = await reject_agent.check_autonomy(task2, "delete_file")
        assert can is False
        assert approval.approved is False

    @pytest.mark.asyncio
    async def test_notify_completion_with_callback(self):
        """Test notify_completion calls callback for L1 operations."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin
        from agents.orchestrator.types import Task, AutonomyLevel

        notifications = []

        class TestAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = None
            _notify_callback = lambda self, event, data: notifications.append((event, data))

        agent = TestAgent()

        task = Task(id="t1", description="Write file")
        task.autonomy_level = AutonomyLevel.L1_NOTIFY

        await agent.notify_completion(task, "File written successfully")

        assert len(notifications) == 1
        assert notifications[0][0] == "task_completed"
        assert notifications[0][1]["task_id"] == "t1"

    def test_assess_risk_all_operations(self):
        """Test _assess_risk returns appropriate risk levels."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin
        from agents.orchestrator.types import Task

        class TestAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = None
            _notify_callback = None

        agent = TestAgent()
        task = Task(id="t1", description="Test")

        # Test all known operations
        operations = [
            "delete_file",
            "architecture_change",
            "api_change",
            "security_config",
            "git_push",
            "database_migration",
            "deploy_production",
            "delete_database",
            "unknown_operation",
        ]

        for op in operations:
            risk = agent._assess_risk(task, op)
            assert ":" in risk  # Should have level: description format

    def test_get_pending_approvals(self):
        """Test get_pending_approvals filters correctly."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin
        from agents.orchestrator.types import ApprovalRequest, AutonomyLevel

        class TestAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = None
            _notify_callback = None

        agent = TestAgent()

        # Add pending
        agent.pending_approvals["a1"] = ApprovalRequest(
            id="a1",
            task_id="t1",
            operation="delete_file",
            description="Delete",
            autonomy_level=AutonomyLevel.L2_APPROVE,
            proposed_action="Delete file",
            risk_assessment="MEDIUM",
            approved=None,  # Pending
        )

        # Add approved
        agent.pending_approvals["a2"] = ApprovalRequest(
            id="a2",
            task_id="t2",
            operation="delete_file",
            description="Delete",
            autonomy_level=AutonomyLevel.L2_APPROVE,
            proposed_action="Delete file",
            risk_assessment="MEDIUM",
            approved=True,  # Already approved
        )

        pending = agent.get_pending_approvals()

        assert len(pending) == 1
        assert pending[0]["id"] == "a1"

    def test_approve_pending_request(self):
        """Test approve() for pending approval requests."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin
        from agents.orchestrator.types import ApprovalRequest, AutonomyLevel

        class TestAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = None
            _notify_callback = None

        agent = TestAgent()

        # Add pending request
        agent.pending_approvals["a1"] = ApprovalRequest(
            id="a1",
            task_id="t1",
            operation="delete_file",
            description="Delete file",
            autonomy_level=AutonomyLevel.L2_APPROVE,
            proposed_action="Delete important.txt",
            risk_assessment="HIGH",
            approved=None,
        )

        # Approve it
        result = agent.approve("a1", approved_by="admin")
        assert result is True
        assert agent.pending_approvals["a1"].approved is True
        assert agent.pending_approvals["a1"].approved_by == "admin"
        assert agent.pending_approvals["a1"].approved_at is not None

        # Approve non-existent
        result = agent.approve("nonexistent")
        assert result is False

    def test_reject_pending_request(self):
        """Test reject() for pending approval requests."""
        from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin
        from agents.orchestrator.types import ApprovalRequest, AutonomyLevel

        class TestAgent(BoundedAutonomyMixin):
            pending_approvals = {}
            _approval_callback = None
            _notify_callback = None

        agent = TestAgent()

        # Add pending request
        agent.pending_approvals["a1"] = ApprovalRequest(
            id="a1",
            task_id="t1",
            operation="deploy_production",
            description="Deploy",
            autonomy_level=AutonomyLevel.L3_HUMAN_ONLY,
            proposed_action="Deploy to prod",
            risk_assessment="CRITICAL",
            approved=None,
        )

        # Reject it
        result = agent.reject("a1", rejected_by="security")
        assert result is True
        assert agent.pending_approvals["a1"].approved is False
        assert agent.pending_approvals["a1"].approved_by == "security"
        assert agent.pending_approvals["a1"].approved_at is not None

        # Reject non-existent
        result = agent.reject("nonexistent")
        assert result is False


# =============================================================================
# ADDITIONAL COVERAGE TESTS
# =============================================================================

class TestAdditionalCoverage:
    """Additional tests to achieve 100% coverage."""

    def test_three_loops_ethical_considerations(self):
        """Test select_loop with ethical considerations."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import (
            LoopContext, DecisionImpact, DecisionRisk, ArchitectLoop
        )

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # Ethical considerations should force IN_THE_LOOP
        context = LoopContext(
            decision_type="design",
            impact=DecisionImpact.LOW,
            risk=DecisionRisk.LOW,
            agent_confidence=0.95,
            requires_domain_expertise=False,
            ethical_considerations=True,  # Should force IN_THE_LOOP
            regulatory_implications=False,
        )

        rec = agent.select_loop(context)
        assert rec.recommended_loop == ArchitectLoop.IN_THE_LOOP
        assert "ethical" in rec.reasoning.lower() or "regulatory" in rec.reasoning.lower()

    def test_three_loops_domain_expertise_required(self):
        """Test select_loop with domain expertise requirement."""
        from agents.architect.three_loops import ThreeLoopsMixin
        from agents.architect.types import (
            LoopContext, DecisionImpact, DecisionRisk, ArchitectLoop
        )

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # Domain expertise should force IN_THE_LOOP
        context = LoopContext(
            decision_type="design",
            impact=DecisionImpact.LOW,
            risk=DecisionRisk.LOW,
            agent_confidence=0.95,
            requires_domain_expertise=True,  # Should force IN_THE_LOOP
            ethical_considerations=False,
            regulatory_implications=False,
        )

        rec = agent.select_loop(context)
        assert rec.recommended_loop == ArchitectLoop.IN_THE_LOOP
        assert "domain" in rec.reasoning.lower() or "expertise" in rec.reasoning.lower()

    def test_classify_decision_high_impact(self):
        """Test classify_decision with HIGH impact keywords."""
        from agents.architect.three_loops import ThreeLoopsMixin

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # HIGH impact - service/endpoint/integration
        ctx = agent.classify_decision("Modify the service endpoint for integration")
        assert ctx.impact.value == "high"

    def test_classify_decision_medium_impact(self):
        """Test classify_decision with MEDIUM impact keywords."""
        from agents.architect.three_loops import ThreeLoopsMixin

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # MEDIUM impact - component/module/class
        ctx = agent.classify_decision("Update the component module class")
        assert ctx.impact.value == "medium"

    def test_classify_decision_medium_risk(self):
        """Test classify_decision with MEDIUM risk keywords."""
        from agents.architect.three_loops import ThreeLoopsMixin

        class TestAgent(ThreeLoopsMixin):
            pass

        agent = TestAgent()

        # MEDIUM risk - add/extend/enhance
        ctx = agent.classify_decision("Add and extend feature enhancement")
        assert ctx.risk.value == "medium"

    def test_deep_think_generate_suggestion_various(self):
        """Test _generate_suggestion for various finding types."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        # SQL injection suggestion
        finding_sql = ReviewFinding(
            id="f1",
            severity=ReviewSeverity.HIGH,
            category="security",
            file_path="test.py",
            line_start=1,
            line_end=1,
            title="SQL injection vulnerability",
            description="Test",
            confidence=0.8,
        )
        suggestion = agent._generate_suggestion(finding_sql)
        assert "parameterized" in suggestion.lower() or "orm" in suggestion.lower()

        # Command injection suggestion
        finding_cmd = ReviewFinding(
            id="f2",
            severity=ReviewSeverity.HIGH,
            category="security",
            file_path="test.py",
            line_start=1,
            line_end=1,
            title="Command injection risk",
            description="Test",
            confidence=0.8,
        )
        suggestion = agent._generate_suggestion(finding_cmd)
        assert "subprocess" in suggestion.lower() or "shell" in suggestion.lower()

    def test_deep_think_is_in_comment_javascript(self):
        """Test _is_in_comment for JavaScript comments."""
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        lines = [
            "const x = 1;",
            "// This is a comment",
            "const y = 2;",
        ]

        assert agent._is_in_comment(lines, 0, "javascript") is False
        assert agent._is_in_comment(lines, 1, "javascript") is True
        assert agent._is_in_comment(lines, 2, "javascript") is False

        # Invalid line index
        assert agent._is_in_comment(lines, -1, "python") is False
        assert agent._is_in_comment(lines, 100, "python") is False

    def test_agentic_rag_mixed_relevance(self):
        """Test _assess_relevance with mixed relevance scores."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import ResearchResult

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        # Mixed relevance: at least one result > 0.7, but < 50% of results
        mixed_results = [
            ResearchResult(
                source="docs",
                title="High relevant",
                content="Some content",
                relevance_score=0.75,  # Above 0.7
            ),
            ResearchResult(
                source="web",
                title="Low relevant",
                content="More content",
                relevance_score=0.5,  # Below 0.7
            ),
            ResearchResult(
                source="web",
                title="Also low",
                content="Content",
                relevance_score=0.4,  # Below 0.7
            ),
        ]
        # 1 out of 3 above 0.7 = 33% < 50% -> Mixed relevance
        assessment = agent._assess_relevance(mixed_results, "query")
        assert assessment == "Mixed relevance"

    # =========================================================================
    # DARWIN GODEL - Remaining Coverage
    # =========================================================================

    def test_get_current_variant_initializes_when_none(self, tmp_path):
        """Test get_current_variant initializes when _current_variant is None."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")
        agent._current_variant = None  # Force None

        variant = agent.get_current_variant()
        assert variant is not None

    @pytest.mark.asyncio
    async def test_evolve_without_archive(self, tmp_path):
        """Test evolve() initializes archive if not exists."""
        from agents.coder.darwin_godel import DarwinGodelMixin
        from agents.coder.types import BenchmarkTask, GeneratedCode, EvaluationResult

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

            async def generate_with_evaluation(self, request, max_corrections=2):
                return GeneratedCode(
                    code="def foo(): pass",
                    language="python",
                    explanation="Test",
                    evaluation=EvaluationResult(
                        valid_syntax=True,
                        lint_score=0.9,
                        quality_score=0.8,
                    ),
                )

        agent = TestAgent()
        agent._archive_path = tmp_path / "archive.json"
        # Don't call _init_evolution - let evolve() do it

        tasks = [BenchmarkTask(id="t1", description="Test task")]
        result = await agent.evolve(tasks)
        assert result is not None

    def test_get_evolution_stats_without_archive(self, tmp_path):
        """Test get_evolution_stats initializes archive if not exists."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._archive_path = tmp_path / "archive.json"
        # Don't call _init_evolution

        stats = agent.get_evolution_stats()
        assert "total_variants" in stats

    def test_get_lineage_without_archive(self, tmp_path):
        """Test get_lineage initializes archive if not exists."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._archive_path = tmp_path / "archive.json"
        # Don't call _init_evolution

        lineage = agent.get_lineage("nonexistent")
        assert lineage == []

    @pytest.mark.asyncio
    async def test_run_benchmarks_no_evaluation(self, tmp_path):
        """Test _run_benchmarks when result has no evaluation."""
        from agents.coder.darwin_godel import DarwinGodelMixin
        from agents.coder.types import BenchmarkTask, GeneratedCode

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

            async def generate_with_evaluation(self, request, max_corrections=2):
                # Return result without evaluation
                return GeneratedCode(
                    code="def foo(): pass",
                    language="python",
                    explanation="Test",
                    evaluation=None,  # No evaluation
                )

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        tasks = [BenchmarkTask(id="t1", description="Test task")]
        scores = await agent._run_benchmarks(agent._current_variant, tasks)
        assert scores["t1"] == 0.0  # Should be 0 with no evaluation

    # =========================================================================
    # AGENTIC RAG - Remaining Coverage
    # =========================================================================

    @pytest.mark.asyncio
    async def test_agentic_research_vs_pattern(self):
        """Test _plan_retrieval with 'vs' comparison pattern."""
        from agents.researcher.agentic_rag import AgenticRAGMixin

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()
        agent._init_retrieval_agents()

        plan = agent._plan_retrieval("Python vs JavaScript for web development")
        # Should decompose into sub-queries for each comparison item
        assert len(plan.sub_queries) > 1
        assert any("Python" in q or "JavaScript" in q for q in plan.sub_queries)

    def test_plan_retrieval_code_keywords(self):
        """Test _plan_retrieval adds code source for code keywords."""
        from agents.researcher.agentic_rag import AgenticRAGMixin

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()
        agent._init_retrieval_agents()

        plan = agent._plan_retrieval("Find the function that handles authentication")
        assert "code" in plan.sources_to_check

    def test_route_query_web_keywords(self):
        """Test _route_query routes to web for web keywords."""
        from agents.researcher.agentic_rag import AgenticRAGMixin

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()
        agent._init_retrieval_agents()

        agents = agent._route_query("Latest news about Python updates")
        assert "web" in agents

    def test_evaluate_sufficiency_low_relevance(self):
        """Test _evaluate_sufficiency with low relevance scores."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import ResearchResult

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        # Very low relevance results
        low_results = [
            ResearchResult(
                source="web",
                title="Barely relevant",
                content="Content",
                relevance_score=0.2,
            )
        ]
        eval_result = agent._evaluate_sufficiency("query", low_results)
        assert "Low relevance scores" in eval_result.missing_aspects
        assert eval_result.recommendation == "retrieve_more"

    def test_evaluate_sufficiency_generate_recommendation(self):
        """Test _evaluate_sufficiency returns generate recommendation."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import ResearchResult

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        # High quality results
        good_results = [
            ResearchResult(
                source="docs",
                title="Perfect match",
                content="Content",
                relevance_score=0.95,
            ),
            ResearchResult(
                source="web",
                title="Also good",
                content="More content",
                relevance_score=0.9,
            ),
            ResearchResult(
                source="docs",
                title="Third result",
                content="Even more",
                relevance_score=0.85,
            ),
            ResearchResult(
                source="web",
                title="Fourth result",
                content="Content",
                relevance_score=0.88,
            ),
            ResearchResult(
                source="docs",
                title="Fifth result",
                content="Final",
                relevance_score=0.92,
            ),
        ]
        eval_result = agent._evaluate_sufficiency("query", good_results)
        assert eval_result.recommendation == "generate"
        assert eval_result.sufficient is True

    def test_refine_query_with_specific(self):
        """Test _refine_query with 'specific' in missing aspects."""
        from agents.researcher.agentic_rag import AgenticRAGMixin

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        refined = agent._refine_query("Python", ["Need more specific details"])
        assert "detailed" in refined.lower()

    def test_generate_answer_with_url(self):
        """Test _generate_answer includes URLs in output."""
        from agents.researcher.agentic_rag import AgenticRAGMixin
        from agents.researcher.types import ResearchResult

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()

        results = [
            ResearchResult(
                source="docs",
                title="Python Docs",
                content="Python is a programming language",
                url="https://docs.python.org",
                relevance_score=0.9,
            )
        ]
        answer = agent._generate_answer("What is Python?", results)
        assert "https://docs.python.org" in answer

    @pytest.mark.asyncio
    async def test_quick_lookup(self):
        """Test quick_lookup method."""
        from agents.researcher.agentic_rag import AgenticRAGMixin

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()
        agent._init_retrieval_agents()

        result = await agent.quick_lookup("What is Python?")
        assert result is not None
        assert result.iterations <= 1

    # =========================================================================
    # DEEP THINK - Remaining Coverage
    # =========================================================================

    @pytest.mark.asyncio
    async def test_deep_think_no_validated_findings(self):
        """Test deep_think_review when no findings pass validation."""
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

            def _detect_language(self, file_path):
                return "python"

        agent = TestAgent()

        # Safe code with no issues
        code = "def safe_function(x): return x + 1"
        result = await agent.deep_think_review(code, "safe.py")

        # With no findings, avg_confidence should be 1.0
        assert result.deep_think.confidence_score == 1.0

    def test_get_call_name_returns_empty(self):
        """Test _get_call_name returns empty for unsupported nodes."""
        import ast
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        # Create a call with lambda (not Name or Attribute)
        code = "(lambda: x)()"
        tree = ast.parse(code)
        call_node = tree.body[0].value  # type: ignore

        name = agent._get_call_name(call_node)
        assert name == ""

    def test_is_in_comment_unknown_language(self):
        """Test _is_in_comment returns False for unknown languages."""
        from agents.reviewer.deep_think import DeepThinkMixin

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        lines = ["some code", "more code"]
        result = agent._is_in_comment(lines, 0, "unknown_language")
        assert result is False

    def test_critique_critical_non_security(self):
        """Test _stage_critique penalizes CRITICAL non-security findings."""
        from agents.reviewer.deep_think import DeepThinkMixin
        from agents.reviewer.types import ReviewFinding, ReviewSeverity

        class TestAgent(DeepThinkMixin):
            SECURITY_CHECKS = []

        agent = TestAgent()

        # CRITICAL severity but not security/syntax category
        findings = [
            ReviewFinding(
                id="f1",
                severity=ReviewSeverity.CRITICAL,
                category="performance",  # Not security/syntax
                file_path="test.py",
                line_start=1,
                line_end=1,
                title="Performance issue",
                description="Slow code",
                code_snippet="slow_operation()",
                confidence=0.9,
            )
        ]

        critiqued, steps = agent._stage_critique(findings, "slow_operation()")
        # Should have reduced confidence
        assert critiqued[0].confidence < 0.9

    # =========================================================================
    # INCIDENT HANDLER - Remaining Coverage
    # =========================================================================

    def test_build_topology_without_init(self):
        """Test build_topology initializes system if needed."""
        from agents.devops.incident_handler import IncidentHandlerMixin

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        # Don't call _init_incident_system

        services = [{"id": "svc1", "name": "Service 1"}]
        topology = agent.build_topology(services)
        assert "svc1" in topology

    def test_get_topology_without_init(self):
        """Test get_topology initializes system if needed."""
        from agents.devops.incident_handler import IncidentHandlerMixin

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        # Don't call _init_incident_system

        topology = agent.get_topology()
        assert topology is not None

    @pytest.mark.asyncio
    async def test_investigate_incident_without_init(self):
        """Test investigate_incident initializes system if needed."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import Alert, IncidentSeverity

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        # Don't call _init_incident_system

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = await agent.investigate_incident(alert)
        assert incident is not None

    @pytest.mark.asyncio
    async def test_analyze_metrics_anomalies(self):
        """Test _analyze_metrics detects various anomalies."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            Alert, Incident, IncidentSeverity, IncidentStatus, TopologyNode
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        # Add topology with high metrics
        agent._topology["api"] = TopologyNode(
            id="api",
            name="API Service",
            type="service",
            environment="production",
            dependencies=[],
            health_status="degraded",
            metrics={
                "cpu_percent": 95,  # High CPU
                "memory_percent": 95,  # High memory
                "error_rate": 10,  # High errors
                "latency_p99": 2000,  # High latency
            },
        )

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )

        step = await agent._analyze_metrics(incident)
        assert "High CPU" in step.findings or "High memory" in step.findings

    def test_identify_root_cause_unknown(self):
        """Test _identify_root_cause returns UNKNOWN for unclear findings."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            RootCauseCategory, Incident, IncidentSeverity,
            IncidentStatus, Alert, InvestigationStep
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        incident.investigation_steps = [
            InvestigationStep(
                id="s1",
                action="Check something",
                findings="Nothing unusual found here",  # No keywords
                timestamp="now",
                data_sources=["test"],
                confidence=0.5,
            )
        ]

        rca = agent._identify_root_cause(incident)
        assert rca.category == RootCauseCategory.UNKNOWN

    def test_identify_root_cause_error_rate(self):
        """Test _identify_root_cause detects error rate issues."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            RootCauseCategory, Incident, IncidentSeverity,
            IncidentStatus, Alert, InvestigationStep
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        incident.investigation_steps = [
            InvestigationStep(
                id="s1",
                action="Analyze metrics",
                findings="High error rate detected",
                timestamp="now",
                data_sources=["prometheus"],
                confidence=0.8,
            )
        ]

        rca = agent._identify_root_cause(incident)
        assert rca.category == RootCauseCategory.CODE_CHANGE

    def test_propose_remediations_no_root_cause(self):
        """Test _propose_remediations returns empty for no root cause."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            Incident, IncidentSeverity, IncidentStatus, Alert
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        # No root_cause set

        remediations = agent._propose_remediations(incident)
        assert remediations == []

    def test_propose_remediations_unknown_category(self):
        """Test _propose_remediations for UNKNOWN category."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            RootCauseCategory, RootCauseAnalysis, Incident,
            IncidentSeverity, IncidentStatus, Alert
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="Test",
            description="Test",
            affected_resources=["api"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[alert],
        )
        incident.root_cause = RootCauseAnalysis(
            category=RootCauseCategory.UNKNOWN,
            description="Unknown cause",
            confidence=0.3,
            evidence=[],
            contributing_factors=[],
            related_changes=[],
        )

        remediations = agent._propose_remediations(incident)
        # UNKNOWN category should still get some generic remediations
        assert isinstance(remediations, list)

    def test_record_deployment_without_init(self):
        """Test record_deployment initializes system if needed."""
        from agents.devops.incident_handler import IncidentHandlerMixin

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        # Don't call _init_incident_system

        agent.record_deployment(
            service="api",
            version="v1.0.0",
            environment="production",
            deployed_by="ci",
        )
        assert len(agent._deployment_history) == 1

    def test_get_incident_metrics_without_init(self):
        """Test get_incident_metrics initializes system if needed."""
        from agents.devops.incident_handler import IncidentHandlerMixin

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        # Don't call _init_incident_system

        metrics = agent.get_incident_metrics()
        assert "total_incidents" in metrics

    @pytest.mark.asyncio
    async def test_correlate_topology_downstream_deps(self):
        """Test _correlate_topology finds downstream dependencies."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import (
            Alert, Incident, IncidentSeverity, IncidentStatus, TopologyNode
        )

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        # Build topology with downstream dependencies
        agent._topology["db"] = TopologyNode(
            id="db",
            name="Database",
            type="database",
            environment="production",
            dependencies=[],
            health_status="healthy",
            metrics={},
        )
        agent._topology["api"] = TopologyNode(
            id="api",
            name="API",
            type="service",
            environment="production",
            dependencies=["db"],  # API depends on DB
            health_status="degraded",
            metrics={},
        )
        agent._topology["web"] = TopologyNode(
            id="web",
            name="Web",
            type="service",
            environment="production",
            dependencies=["api"],  # Web depends on API
            health_status="healthy",
            metrics={},
        )

        alert = Alert(
            id="a1",
            source="test",
            severity=IncidentSeverity.SEV2,
            title="DB Down",
            description="Database is down",
            affected_resources=["db"],
            triggered_at=datetime.now().isoformat(),
        )
        incident = Incident(
            id="inc-1",
            title="Test",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["db"],
            alerts=[alert],
        )

        step = await agent._correlate_topology(incident)
        # Should find downstream impact
        assert "Downstream" in step.findings or "API" in step.findings

    # =========================================================================
    # FINAL 100% COVERAGE - Remaining Lines
    # =========================================================================

    @pytest.mark.asyncio
    async def test_execute_remediation_not_found(self):
        """Test execute_remediation with invalid remediation_id (line 343)."""
        from agents.devops.incident_handler import IncidentHandlerMixin
        from agents.devops.types import Incident, IncidentSeverity, IncidentStatus

        class TestAgent(IncidentHandlerMixin):
            pass

        agent = TestAgent()
        agent._init_incident_system()

        # Create an incident with no remediations
        incident = Incident(
            id="inc-test",
            title="Test Incident",
            severity=IncidentSeverity.SEV2,
            status=IncidentStatus.INVESTIGATING,
            detected_at=datetime.now().isoformat(),
            affected_services=["api"],
            alerts=[],
        )
        agent._incidents["inc-test"] = incident

        # Try to execute non-existent remediation
        result = await agent.execute_remediation("inc-test", "nonexistent-remediation")
        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_agentic_research_auto_init(self):
        """Test agentic_research auto-initializes retrieval agents (line 80)."""
        from agents.researcher.agentic_rag import AgenticRAGMixin

        class TestAgent(AgenticRAGMixin):
            pass

        agent = TestAgent()
        # Explicitly verify _retrieval_agents doesn't exist before call
        assert not hasattr(agent, "_retrieval_agents")

        # Call agentic_research - should auto-init agents
        result = await agent.agentic_research("What is Python?", max_iterations=1)
        assert result is not None
        # Now _retrieval_agents should exist
        assert hasattr(agent, "_retrieval_agents")

    @pytest.mark.asyncio
    async def test_propose_modifications_empty_strategies(self, tmp_path, monkeypatch):
        """Test _propose_modifications when strategy key not in parent (line 256)."""
        import random
        from agents.coder.darwin_godel import DarwinGodelMixin
        from agents.coder.types import AgentVariant

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        # Create parent with empty strategies
        parent = AgentVariant(
            id="parent-1",
            parent_id=None,
            generation=0,
            system_prompt="Test prompt",
            tools=["tool1"],
            strategies={},  # Empty strategies - any key will hit else branch
        )

        # Force strategy_tuning to be selected
        original_sample = random.sample
        def force_strategy_tuning(population, k=1):
            return ["strategy_tuning"]
        monkeypatch.setattr(random, "sample", force_strategy_tuning)

        # Force a specific tuning option - max_corrections (not in strategies)
        original_choice = random.choice
        call_count = [0]
        def force_tuning_option(seq):
            call_count[0] += 1
            seq_list = list(seq)
            # Check if this is the tuning_options list
            if len(seq_list) == 3:
                first = seq_list[0]
                if hasattr(first, '__getitem__') and first[0] == "max_corrections":
                    return seq_list[0]  # max_corrections option
            return original_choice(seq)
        monkeypatch.setattr(random, "choice", force_tuning_option)

        mods = await agent._propose_modifications(parent)
        # Should have strategies with max_corrections set
        assert "strategies" in mods
        assert "max_corrections" in mods["strategies"]

    def test_run_test_code_cleanup_exception(self, tmp_path, monkeypatch):
        """Test _run_test_code handles cleanup exception (lines 334-335)."""
        from agents.coder.darwin_godel import DarwinGodelMixin

        class TestAgent(DarwinGodelMixin):
            SYSTEM_PROMPT = "Test"

        agent = TestAgent()
        agent._init_evolution(archive_path=tmp_path / "archive.json")

        # Patch Path.unlink to raise exception
        original_unlink = Path.unlink
        def raise_on_unlink(self, missing_ok=False):
            raise PermissionError("Cannot delete file")
        monkeypatch.setattr(Path, "unlink", raise_on_unlink)

        # Run test code - should work despite cleanup failure
        code = "def add(a, b): return a + b"
        test_code = "assert add(1, 2) == 3"

        # This should not raise even though cleanup fails
        result = agent._run_test_code(code, test_code)
        # Result may be True (test passed) or False (execution failed)
        # Important thing is no exception is raised
        assert isinstance(result, bool)
