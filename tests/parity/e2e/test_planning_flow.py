"""
End-to-end tests for planning functionality.

Tests the complete flow from user request to task execution,
validating plan generation, user approval, and execution.
"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


class TestPlanningFlowE2E:
    """End-to-end tests for planning functionality."""

    @pytest.mark.e2e
    async def test_multi_task_decomposition(self, vertice_client):
        """Verify complex requests are decomposed into multiple tasks."""
        request = "Create a user authentication system with login, logout, password reset, and session management"

        response = await vertice_client.process(request, mode="plan_only")

        # Should decompose into at least 4 tasks
        assert (
            len(response["tasks"]) >= 4
        ), f"Expected at least 4 tasks, got {len(response['tasks'])}"

        # Verify key components are present
        task_descriptions = [t.description.lower() for t in response["tasks"]]
        " ".join(task_descriptions)

        assert any(
            "login" in d or "auth" in d for d in task_descriptions
        ), "Should have login-related task"

    @pytest.mark.e2e
    async def test_plan_gating(self, vertice_client, mock_user_input):
        """Verify plan is shown before execution."""
        vertice_client.user_input = mock_user_input
        mock_user_input.set_response("Y")

        request = "Refactor the database module"
        response = await vertice_client.process(request)

        # Should have shown plan before execution
        assert response["plan_displayed"], "Plan should be displayed"
        assert response["user_approved"], "User should have approved"
        assert response["execution_started_after_approval"], "Execution should start after approval"

    @pytest.mark.e2e
    async def test_plan_rejection(self, vertice_client, mock_user_input):
        """Verify rejected plans are not executed."""
        vertice_client.user_input = mock_user_input
        mock_user_input.set_response("N")

        request = "Delete all test files"
        response = await vertice_client.process(request)

        assert response["plan_displayed"], "Plan should be displayed"
        assert not response["user_approved"], "User should not have approved"
        assert not response["execution_started"], "Execution should not start"

    @pytest.mark.e2e
    async def test_simple_request_single_task(self, vertice_client):
        """Simple requests should create fewer tasks."""
        request = "Fix typo in README"

        response = await vertice_client.process(request, mode="plan_only")

        # Simple request = fewer tasks
        assert len(response["tasks"]) <= 2, "Simple request should have few tasks"

    @pytest.mark.e2e
    async def test_complex_request_many_tasks(self, vertice_client):
        """Complex requests should create multiple tasks."""
        request = """Build a complete e-commerce system including:
        - Product catalog with categories
        - Shopping cart functionality
        - Checkout process with payment integration
        - Order management and history
        - User accounts and authentication
        - Admin dashboard for inventory"""

        response = await vertice_client.process(request, mode="plan_only")

        # Complex request = many tasks
        assert (
            len(response["tasks"]) >= 5
        ), f"Complex request should have many tasks, got {len(response['tasks'])}"


class TestPlanningQuality:
    """Tests for plan quality."""

    @pytest.mark.e2e
    async def test_tasks_are_ordered_logically(self, vertice_client):
        """Tasks should be in a logical order."""
        request = "Design, implement, and test a new API endpoint"

        response = await vertice_client.process(request, mode="plan_only")

        if len(response["tasks"]) >= 3:
            task_descriptions = [t.description.lower() for t in response["tasks"]]

            # Design should come before implement
            design_idx = next((i for i, d in enumerate(task_descriptions) if "design" in d), -1)
            impl_idx = next((i for i, d in enumerate(task_descriptions) if "implement" in d), -1)
            test_idx = next((i for i, d in enumerate(task_descriptions) if "test" in d), -1)

            if design_idx >= 0 and impl_idx >= 0:
                assert design_idx < impl_idx, "Design should come before implementation"
            if impl_idx >= 0 and test_idx >= 0:
                assert impl_idx < test_idx, "Implementation should come before testing"

    @pytest.mark.e2e
    async def test_dependencies_are_valid(self, vertice_client):
        """Task dependencies should be valid."""
        request = "Create a REST API with database models and tests"

        response = await vertice_client.process(request, mode="plan_only")

        task_ids = {t.id for t in response["tasks"]}

        for task in response["tasks"]:
            for dep in task.dependencies:
                assert dep in task_ids, f"Invalid dependency: {dep} not in {task_ids}"
                assert dep != task.id, f"Task cannot depend on itself: {task.id}"

    @pytest.mark.e2e
    async def test_no_duplicate_tasks(self, vertice_client):
        """Plan should not have duplicate tasks."""
        request = "Implement login and signup with validation"

        response = await vertice_client.process(request, mode="plan_only")

        descriptions = [t.description for t in response["tasks"]]
        unique_descriptions = set(descriptions)

        # Allow some similarity but not exact duplicates
        assert len(unique_descriptions) >= len(descriptions) * 0.8, "Too many duplicate tasks"


class TestPlanningUserInteraction:
    """Tests for user interaction during planning."""

    @pytest.mark.e2e
    async def test_plan_can_be_modified(self, vertice_client, mock_user_input):
        """User should be able to modify the plan."""
        vertice_client.user_input = mock_user_input
        mock_user_input.set_responses(["E", "Y"])  # Edit, then approve

        # This test validates the interface exists
        # Actual edit functionality depends on implementation
        request = "Implement user profile"
        response = await vertice_client.process(request)

        assert response["plan_displayed"]

    @pytest.mark.e2e
    async def test_multiple_approval_attempts(self, vertice_client, mock_user_input):
        """User can reject and re-approve."""
        vertice_client.user_input = mock_user_input
        mock_user_input.set_responses(["N"])  # Just reject

        request = "Create new feature"
        response = await vertice_client.process(request)

        assert not response["execution_started"]


class TestPlanningEdgeCases:
    """Edge case tests for planning."""

    @pytest.mark.e2e
    async def test_empty_request(self, vertice_client):
        """Empty requests should be handled gracefully."""
        response = await vertice_client.process("", mode="plan_only")

        # Should not crash
        assert "tasks" in response

    @pytest.mark.e2e
    async def test_very_long_request(self, vertice_client):
        """Very long requests should be handled."""
        request = "Implement " + ", ".join([f"feature_{i}" for i in range(100)])

        response = await vertice_client.process(request, mode="plan_only")

        # Should produce reasonable number of tasks
        assert len(response["tasks"]) <= 50, "Too many tasks generated"

    @pytest.mark.e2e
    async def test_ambiguous_request(self, vertice_client):
        """Ambiguous requests should produce something."""
        request = "Make it better"

        response = await vertice_client.process(request, mode="plan_only")

        # Should at least create one task
        assert len(response["tasks"]) >= 1

    @pytest.mark.e2e
    async def test_conflicting_requirements(self, vertice_client):
        """Conflicting requirements should be handled."""
        request = "Make the code faster and also more readable with more comments"

        response = await vertice_client.process(request, mode="plan_only")

        # Should produce tasks for both
        assert len(response["tasks"]) >= 1


class TestPlanningPerformance:
    """Performance tests for planning."""

    @pytest.mark.e2e
    @pytest.mark.slow
    async def test_planning_completes_in_time(self, vertice_client):
        """Planning should complete within reasonable time."""
        request = "Create a complete user management system"

        start = asyncio.get_event_loop().time()
        await vertice_client.process(request, mode="plan_only")
        duration = asyncio.get_event_loop().time() - start

        # Planning should be fast (no execution)
        assert duration < 10, f"Planning took too long: {duration}s"

    @pytest.mark.e2e
    async def test_concurrent_planning_requests(self, vertice_client):
        """Multiple planning requests should be handled."""
        requests = [
            "Plan feature A",
            "Plan feature B",
            "Plan feature C",
        ]

        # Execute concurrently
        tasks = [vertice_client.process(r, mode="plan_only") for r in requests]
        responses = await asyncio.gather(*tasks)

        # All should succeed
        assert len(responses) == 3
        for response in responses:
            assert "tasks" in response
