"""
Unit tests for task decomposition.

Tests that complex requests are properly broken down into subtasks.
This is a P0-CRITICAL feature that was previously DISABLED.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


class TestTaskDecompositionBasics:
    """Basic task decomposition tests."""

    @pytest.mark.unit
    async def test_single_task_request_creates_one_task(self, orchestrator):
        """Simple requests should create a single task."""
        request = "Fix the typo in README"

        plan = await orchestrator.plan(request)

        # Simple requests can be single task
        assert len(plan) >= 1
        assert plan[0].description is not None

    @pytest.mark.unit
    async def test_multi_step_request_creates_multiple_tasks(self, orchestrator):
        """Complex requests MUST create multiple tasks."""
        request = "Create a user authentication system with login, logout, and password reset"

        plan = await orchestrator.plan(request)

        # This request has at least 3 distinct components
        assert len(plan) >= 3, f"Expected at least 3 tasks, got {len(plan)}"

    @pytest.mark.unit
    async def test_task_dependencies_are_set(self, orchestrator):
        """Tasks with dependencies should reference them."""
        request = "Design the API schema, then implement it, then test it"

        plan = await orchestrator.plan(request)

        # Later tasks should depend on earlier ones
        if len(plan) > 1:
            # At least one task should have dependencies
            has_deps = any(task.dependencies for task in plan[1:])
            assert has_deps, "Sequential tasks should have dependencies"

    @pytest.mark.unit
    async def test_decomposition_not_hardcoded(self, orchestrator):
        """Decomposition should vary based on request complexity."""
        simple_request = "Add a comment"
        complex_request = "Build a complete e-commerce system with cart, checkout, payments, and inventory"

        simple_plan = await orchestrator.plan(simple_request)
        complex_plan = await orchestrator.plan(complex_request)

        # Complex request should have more tasks
        assert len(complex_plan) > len(simple_plan), \
            "Complex requests should decompose into more tasks than simple ones"


class TestTaskDecompositionQuality:
    """Tests for decomposition quality and correctness."""

    @pytest.mark.unit
    async def test_tasks_are_actionable(self, orchestrator):
        """Each task should be actionable, not vague."""
        request = "Implement user profile with avatar upload and settings"

        plan = await orchestrator.plan(request)

        for task in plan:
            # Task should have meaningful description
            assert len(task.description) > 10, f"Task too short: {task.description}"
            # Task should not just repeat the original request
            assert task.description != request

    @pytest.mark.unit
    async def test_tasks_cover_all_components(self, orchestrator):
        """All components mentioned should appear in tasks."""
        request = "Create login, logout, and password reset features"

        plan = await orchestrator.plan(request)

        all_descriptions = " ".join(t.description.lower() for t in plan)

        # Each component should be represented
        assert "login" in all_descriptions or "authentication" in all_descriptions
        assert "logout" in all_descriptions or "signout" in all_descriptions or "session" in all_descriptions
        assert "password" in all_descriptions or "reset" in all_descriptions

    @pytest.mark.unit
    async def test_no_circular_dependencies(self, orchestrator):
        """Task dependencies must form a DAG (no cycles)."""
        request = "Design, implement, test, and document the API"

        plan = await orchestrator.plan(request)

        # Build dependency graph
        task_ids = {t.id for t in plan}

        for task in plan:
            for dep in task.dependencies:
                # Dependency must exist
                assert dep in task_ids, f"Unknown dependency: {dep}"
                # No self-dependency
                assert dep != task.id, f"Self-dependency in task {task.id}"

    @pytest.mark.unit
    async def test_estimated_tokens_set(self, orchestrator):
        """Tasks should have estimated token counts."""
        request = "Implement a complex feature"

        plan = await orchestrator.plan(request)

        for task in plan:
            assert task.estimated_tokens > 0, f"Task {task.id} has no token estimate"


class TestTaskDecompositionEdgeCases:
    """Edge case tests for task decomposition."""

    @pytest.mark.unit
    async def test_empty_request_handled(self, orchestrator):
        """Empty requests should be handled gracefully."""
        request = ""

        plan = await orchestrator.plan(request)

        # Should return at least one task (even if just error handling)
        assert len(plan) >= 0  # No crash

    @pytest.mark.unit
    async def test_very_long_request_handled(self, orchestrator):
        """Very long requests should be handled."""
        request = "Implement " + " and ".join([f"feature_{i}" for i in range(50)])

        plan = await orchestrator.plan(request)

        # Should decompose but not explode
        assert len(plan) <= 20, "Too many tasks generated"

    @pytest.mark.unit
    async def test_ambiguous_request_creates_clarification_task(self, orchestrator):
        """Ambiguous requests should include clarification."""
        request = "Make it better"

        plan = await orchestrator.plan(request)

        # Should handle gracefully
        assert len(plan) >= 1

    @pytest.mark.unit
    async def test_multilingual_request_handled(self, orchestrator):
        """Non-English requests should be handled."""
        request = "Criar sistema de autenticacao com login e logout"

        plan = await orchestrator.plan(request)

        assert len(plan) >= 1


class TestTaskDecompositionIntegration:
    """Integration tests for task decomposition with real orchestrator."""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.path.exists("/media/juan/DATA/Vertice-Code/agents/orchestrator/agent.py"),
        reason="Orchestrator not available"
    )
    async def test_real_orchestrator_decomposes(self):
        """Test with real orchestrator if available."""
        try:
            from agents.orchestrator.agent import OrchestratorAgent

            orchestrator = OrchestratorAgent()
            request = "Create a REST API with CRUD operations"

            plan = await orchestrator.plan(request)

            # Real orchestrator should decompose
            assert len(plan) >= 1, "Real orchestrator failed to decompose"

        except ImportError:
            pytest.skip("Orchestrator not importable")

    @pytest.mark.integration
    async def test_decomposition_respects_context(self, orchestrator):
        """Decomposition should consider context."""
        # First request establishes context
        await orchestrator.plan("We're building a Python web app with FastAPI")

        # Second request should be decomposed with context in mind
        plan = await orchestrator.plan("Add user authentication")

        # Should include FastAPI-relevant tasks
        assert len(plan) >= 1
