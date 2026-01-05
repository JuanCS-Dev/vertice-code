"""
Tests for Agency Coordinator.

Validates the facade that coordinates between the three
VERTICE orchestrators without modifying them.

Author: JuanCS Dev
Date: 2025-12-31
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from vertice_agents import (
    AgencyCoordinator,
    get_coordinator,
    OrchestratorType,
    TaskCategory,
    CoordinationDecision,
    CoordinationResult,
)


# =============================================================================
# ENUM TESTS
# =============================================================================


class TestOrchestratorType:
    """Tests for OrchestratorType enum."""

    def test_all_types_exist(self) -> None:
        """All orchestrator types are defined."""
        assert OrchestratorType.CORE
        assert OrchestratorType.STATE
        assert OrchestratorType.SQUAD
        assert OrchestratorType.AUTO

    def test_type_values_unique(self) -> None:
        """Each type has a unique value."""
        values = [t.value for t in OrchestratorType]
        assert len(values) == len(set(values))


class TestTaskCategory:
    """Tests for TaskCategory enum."""

    def test_all_categories_exist(self) -> None:
        """All task categories are defined."""
        assert TaskCategory.SIMPLE_QUERY
        assert TaskCategory.CODE_CHANGE
        assert TaskCategory.ARCHITECTURE
        assert TaskCategory.PRODUCTION
        assert TaskCategory.FULL_FEATURE
        assert TaskCategory.COMPLEX_WORKFLOW

    def test_categories_have_values(self) -> None:
        """Categories have string values."""
        assert TaskCategory.SIMPLE_QUERY.value == "simple_query"
        assert TaskCategory.CODE_CHANGE.value == "code_change"
        assert TaskCategory.FULL_FEATURE.value == "full_feature"


# =============================================================================
# DATACLASS TESTS
# =============================================================================


class TestCoordinationDecision:
    """Tests for CoordinationDecision dataclass."""

    def test_create_decision(self) -> None:
        """Can create a coordination decision."""
        decision = CoordinationDecision(
            orchestrator=OrchestratorType.CORE,
            category=TaskCategory.CODE_CHANGE,
            confidence=0.9,
            reasoning="Test reasoning",
        )

        assert decision.orchestrator == OrchestratorType.CORE
        assert decision.category == TaskCategory.CODE_CHANGE
        assert decision.confidence == 0.9
        assert decision.reasoning == "Test reasoning"
        assert decision.metadata == {}

    def test_decision_with_metadata(self) -> None:
        """Decision can have metadata."""
        decision = CoordinationDecision(
            orchestrator=OrchestratorType.SQUAD,
            category=TaskCategory.FULL_FEATURE,
            confidence=0.85,
            reasoning="Complex task",
            metadata={"files": 5, "estimated_phases": 3},
        )

        assert decision.metadata["files"] == 5
        assert decision.metadata["estimated_phases"] == 3


class TestCoordinationResult:
    """Tests for CoordinationResult dataclass."""

    def test_create_result(self) -> None:
        """Can create a coordination result."""
        result = CoordinationResult(
            success=True,
            orchestrator_used=OrchestratorType.CORE,
            output="Task completed",
        )

        assert result.success is True
        assert result.orchestrator_used == OrchestratorType.CORE
        assert result.output == "Task completed"
        assert result.decisions == []
        assert result.errors == []

    def test_result_with_decisions(self) -> None:
        """Result can include decisions history."""
        decision = CoordinationDecision(
            orchestrator=OrchestratorType.STATE,
            category=TaskCategory.COMPLEX_WORKFLOW,
            confidence=0.8,
            reasoning="Workflow task",
        )

        result = CoordinationResult(
            success=True,
            orchestrator_used=OrchestratorType.STATE,
            output="Done",
            decisions=[decision],
        )

        assert len(result.decisions) == 1
        assert result.decisions[0].orchestrator == OrchestratorType.STATE


# =============================================================================
# COORDINATOR INITIALIZATION TESTS
# =============================================================================


class TestCoordinatorInit:
    """Tests for AgencyCoordinator initialization."""

    def test_create_without_args(self) -> None:
        """Can create coordinator without arguments."""
        coordinator = AgencyCoordinator()

        assert coordinator is not None
        assert coordinator._vertice_client is None
        assert coordinator._mcp_client is None
        assert coordinator._approval_callback is None
        assert coordinator._notify_callback is None

    def test_create_with_clients(self) -> None:
        """Can create coordinator with clients."""
        mock_vertice = MagicMock()
        mock_mcp = MagicMock()

        coordinator = AgencyCoordinator(
            vertice_client=mock_vertice,
            mcp_client=mock_mcp,
        )

        assert coordinator._vertice_client is mock_vertice
        assert coordinator._mcp_client is mock_mcp

    def test_create_with_callbacks(self) -> None:
        """Can create coordinator with callbacks."""
        async def approval_cb(x):
            return True

        async def notify_cb(x):
            pass

        coordinator = AgencyCoordinator(
            approval_callback=approval_cb,
            notify_callback=notify_cb,
        )

        assert coordinator._approval_callback is approval_cb
        assert coordinator._notify_callback is notify_cb

    def test_orchestrators_not_loaded_initially(self) -> None:
        """Orchestrators are lazy-loaded."""
        coordinator = AgencyCoordinator()

        assert coordinator._core_orchestrator is None
        assert coordinator._state_orchestrator is None
        assert coordinator._squad_orchestrator is None


# =============================================================================
# TASK CATEGORIZATION TESTS
# =============================================================================


class TestTaskCategorization:
    """Tests for task categorization logic."""

    def test_simple_query_categorization(self) -> None:
        """Simple queries are categorized correctly."""
        coordinator = AgencyCoordinator()

        queries = [
            "What is the purpose of this function?",
            "Explain how the auth system works",
            "How does the caching mechanism work?",
            "Show me the API endpoints",
            "List all the models",
        ]

        for query in queries:
            category = coordinator.categorize_task(query)
            assert category == TaskCategory.SIMPLE_QUERY, f"Failed for: {query}"

    def test_code_change_categorization(self) -> None:
        """Code change requests are categorized correctly."""
        coordinator = AgencyCoordinator()

        requests = [
            "Fix the bug in the login function",
            "Update the user model",
            "Change the database connection",
            "Refactor the payment module",
            "Add a new method to the class",
        ]

        for request in requests:
            category = coordinator.categorize_task(request)
            assert category == TaskCategory.CODE_CHANGE, f"Failed for: {request}"

    def test_architecture_categorization(self) -> None:
        """Architecture tasks are categorized correctly."""
        coordinator = AgencyCoordinator()

        requests = [
            "Design a new microservices architecture",
            "Architect the notification system",
            "Create a new API structure",
            "Migration from monolith to microservices",
        ]

        for request in requests:
            category = coordinator.categorize_task(request)
            assert category == TaskCategory.ARCHITECTURE, f"Failed for: {request}"

    def test_production_categorization(self) -> None:
        """Production tasks are categorized correctly."""
        coordinator = AgencyCoordinator()

        requests = [
            "Deploy to production",
            "Release version 2.0",
            "Publish the package",
            "Update security credentials",
        ]

        for request in requests:
            category = coordinator.categorize_task(request)
            assert category == TaskCategory.PRODUCTION, f"Failed for: {request}"

    def test_full_feature_categorization(self) -> None:
        """Full feature requests are categorized correctly."""
        coordinator = AgencyCoordinator()

        requests = [
            "Implement user authentication",
            "Create feature for file upload",
            "Build the dashboard module",
            "Develop the reporting system",
        ]

        for request in requests:
            category = coordinator.categorize_task(request)
            assert category == TaskCategory.FULL_FEATURE, f"Failed for: {request}"

    def test_complex_workflow_categorization(self) -> None:
        """Complex workflow tasks are categorized correctly."""
        coordinator = AgencyCoordinator()

        requests = [
            "Orchestrate the CI/CD pipeline",
            "Coordinate the deployment workflow",
            "Multi-step data processing pipeline",
        ]

        for request in requests:
            category = coordinator.categorize_task(request)
            assert category == TaskCategory.COMPLEX_WORKFLOW, f"Failed for: {request}"

    def test_default_categorization(self) -> None:
        """Unknown requests default to CODE_CHANGE."""
        coordinator = AgencyCoordinator()

        # Random text with no keywords
        category = coordinator.categorize_task("asdfgh qwerty")
        assert category == TaskCategory.CODE_CHANGE


# =============================================================================
# ORCHESTRATOR SELECTION TESTS
# =============================================================================


class TestOrchestratorSelection:
    """Tests for orchestrator selection logic."""

    def test_select_for_simple_query(self) -> None:
        """Simple queries use CORE orchestrator."""
        coordinator = AgencyCoordinator()

        decision = coordinator.select_orchestrator("What is this?")

        assert decision.orchestrator == OrchestratorType.CORE
        assert decision.category == TaskCategory.SIMPLE_QUERY

    def test_select_for_code_change(self) -> None:
        """Code changes use CORE orchestrator."""
        coordinator = AgencyCoordinator()

        decision = coordinator.select_orchestrator("Fix the bug")

        assert decision.orchestrator == OrchestratorType.CORE
        assert decision.category == TaskCategory.CODE_CHANGE

    def test_select_for_full_feature(self) -> None:
        """Full features select SQUAD but fallback to CORE."""
        coordinator = AgencyCoordinator()

        # Without llm/mcp clients, SQUAD is unavailable
        decision = coordinator.select_orchestrator("Implement new feature")

        # Falls back to CORE because SQUAD requires clients
        assert decision.orchestrator == OrchestratorType.CORE
        assert decision.category == TaskCategory.FULL_FEATURE

    def test_select_with_force(self) -> None:
        """Force parameter overrides selection."""
        coordinator = AgencyCoordinator()

        decision = coordinator.select_orchestrator(
            "Simple query",
            force=OrchestratorType.STATE,
        )

        assert decision.orchestrator == OrchestratorType.STATE
        assert decision.confidence == 1.0
        assert decision.reasoning == "Forced by caller"

    def test_select_with_auto_force(self) -> None:
        """AUTO force still uses normal selection."""
        coordinator = AgencyCoordinator()

        decision = coordinator.select_orchestrator(
            "What is this?",
            force=OrchestratorType.AUTO,
        )

        # AUTO doesn't force, uses normal selection
        assert decision.orchestrator == OrchestratorType.CORE

    def test_decision_recorded(self) -> None:
        """Decisions are recorded in history."""
        coordinator = AgencyCoordinator()

        coordinator.select_orchestrator("Query 1")
        coordinator.select_orchestrator("Query 2")

        decisions = coordinator.get_decisions()
        assert len(decisions) == 2


# =============================================================================
# STATUS AND HISTORY TESTS
# =============================================================================


class TestStatusAndHistory:
    """Tests for status and history methods."""

    def test_get_status(self) -> None:
        """get_status returns correct structure."""
        coordinator = AgencyCoordinator()

        status = coordinator.get_status()

        assert "execution_count" in status
        assert "decisions_made" in status
        assert "orchestrators" in status
        assert "has_callbacks" in status

        assert status["execution_count"] == 0
        assert status["decisions_made"] == 0
        assert status["orchestrators"]["core"] is False
        assert status["has_callbacks"]["approval"] is False

    def test_get_decisions_returns_copy(self) -> None:
        """get_decisions returns a copy."""
        coordinator = AgencyCoordinator()

        coordinator.select_orchestrator("Test")

        decisions1 = coordinator.get_decisions()
        decisions2 = coordinator.get_decisions()

        # Should be equal but not same object
        assert decisions1 == decisions2
        assert decisions1 is not decisions2

    def test_clear_history(self) -> None:
        """clear_history removes all decisions."""
        coordinator = AgencyCoordinator()

        coordinator.select_orchestrator("Test 1")
        coordinator.select_orchestrator("Test 2")
        assert len(coordinator.get_decisions()) == 2

        coordinator.clear_history()
        assert len(coordinator.get_decisions()) == 0


# =============================================================================
# CALLBACK AND CLIENT MANAGEMENT TESTS
# =============================================================================


class TestCallbackManagement:
    """Tests for callback management."""

    def test_set_callbacks(self) -> None:
        """set_callbacks updates callbacks."""
        coordinator = AgencyCoordinator()

        async def approval_cb(x):
            return True

        async def notify_cb(x):
            pass

        coordinator.set_callbacks(
            approval_callback=approval_cb,
            notify_callback=notify_cb,
        )

        assert coordinator._approval_callback is approval_cb
        assert coordinator._notify_callback is notify_cb

    def test_set_partial_callbacks(self) -> None:
        """Can set only one callback."""
        async def existing(x):
            return True

        coordinator = AgencyCoordinator(approval_callback=existing)

        async def new_notify(x):
            pass

        coordinator.set_callbacks(notify_callback=new_notify)

        # Approval unchanged, notify updated
        assert coordinator._approval_callback is existing
        assert coordinator._notify_callback is new_notify


class TestClientManagement:
    """Tests for client management."""

    def test_set_clients(self) -> None:
        """set_clients updates clients."""
        coordinator = AgencyCoordinator()

        mock_vertice = MagicMock()
        mock_mcp = MagicMock()

        coordinator.set_clients(vertice_client=mock_vertice, mcp_client=mock_mcp)

        assert coordinator._vertice_client is mock_vertice
        assert coordinator._mcp_client is mock_mcp

    def test_set_clients_resets_squad(self) -> None:
        """Setting clients resets squad orchestrator cache."""
        coordinator = AgencyCoordinator()
        coordinator._squad_orchestrator = MagicMock()  # Fake cached

        coordinator.set_clients(vertice_client=MagicMock())

        # Should be reset to pick up new client
        assert coordinator._squad_orchestrator is None


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestConvenienceFunctions:
    """Tests for get_coordinator function."""

    def test_get_coordinator(self) -> None:
        """get_coordinator returns coordinator instance."""
        coordinator = get_coordinator()

        assert isinstance(coordinator, AgencyCoordinator)

    def test_get_coordinator_with_args(self) -> None:
        """get_coordinator passes kwargs."""
        mock_vertice = MagicMock()

        coordinator = get_coordinator(vertice_client=mock_vertice)

        assert coordinator._vertice_client is mock_vertice


# =============================================================================
# CATEGORY ORCHESTRATOR MAPPING TESTS
# =============================================================================


class TestCategoryMapping:
    """Tests for category to orchestrator mapping."""

    def test_all_categories_mapped(self) -> None:
        """All categories have a mapping."""
        coordinator = AgencyCoordinator()

        for category in TaskCategory:
            mapped = coordinator.CATEGORY_ORCHESTRATOR.get(category)
            assert mapped is not None, f"No mapping for {category}"

    def test_mapping_correctness(self) -> None:
        """Mappings are correct."""
        coordinator = AgencyCoordinator()
        mapping = coordinator.CATEGORY_ORCHESTRATOR

        assert mapping[TaskCategory.SIMPLE_QUERY] == OrchestratorType.CORE
        assert mapping[TaskCategory.CODE_CHANGE] == OrchestratorType.CORE
        assert mapping[TaskCategory.ARCHITECTURE] == OrchestratorType.CORE
        assert mapping[TaskCategory.PRODUCTION] == OrchestratorType.CORE
        assert mapping[TaskCategory.FULL_FEATURE] == OrchestratorType.SQUAD
        assert mapping[TaskCategory.COMPLEX_WORKFLOW] == OrchestratorType.STATE


# =============================================================================
# EXECUTION TESTS (Async)
# =============================================================================


class TestExecution:
    """Tests for execute method."""

    @pytest.mark.asyncio
    async def test_execute_yields_header(self) -> None:
        """Execute yields coordinator header."""
        coordinator = AgencyCoordinator()

        chunks = []
        async for chunk in coordinator.execute("What is this?"):
            chunks.append(chunk)

        output = "".join(chunks)
        assert "[Coordinator]" in output
        assert "simple_query" in output
        assert "CORE" in output

    @pytest.mark.asyncio
    async def test_execute_increments_count(self) -> None:
        """Execute increments execution count."""
        coordinator = AgencyCoordinator()

        assert coordinator._execution_count == 0

        async for _ in coordinator.execute("Test"):
            pass

        assert coordinator._execution_count == 1

    @pytest.mark.asyncio
    async def test_execute_with_force_orchestrator(self) -> None:
        """Execute respects forced orchestrator."""
        coordinator = AgencyCoordinator()

        chunks = []
        async for chunk in coordinator.execute(
            "Test",
            orchestrator=OrchestratorType.STATE,
        ):
            chunks.append(chunk)

        output = "".join(chunks)
        assert "STATE" in output

    @pytest.mark.asyncio
    async def test_execute_handles_unavailable_orchestrator(self) -> None:
        """Execute handles unavailable orchestrators gracefully."""
        coordinator = AgencyCoordinator()

        # Force STATE which may not be available
        chunks = []
        async for chunk in coordinator.execute(
            "Complex workflow pipeline",
            orchestrator=OrchestratorType.STATE,
        ):
            chunks.append(chunk)

        # Should not raise, should yield something
        assert len(chunks) > 0
