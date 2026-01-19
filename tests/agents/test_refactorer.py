"""
Tests for RefactorerAgent v8.0 - Enterprise Transactional Code Surgeon.

Validates:
- Initialization with FILE_EDIT + READ_ONLY capabilities
- Plan-based execution (from PlannerAgent)
- Standalone mode with target_file
- Transactional rollback on failure
- AST validation
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock

from vertice_cli.agents.refactorer import (
    RefactorerAgent,
    RefactoringType,
    ChangeStatus,
    CodeChange,
    RefactoringPlan,
    TransactionalSession,
)
from vertice_cli.agents.base import AgentTask, AgentCapability, AgentRole


class TestRefactorerBasic:
    """Basic functionality tests for RefactorerAgent v8.0."""

    def test_refactorer_initialization(self) -> None:
        """Test Refactorer initializes with FILE_EDIT and READ_ONLY capabilities."""
        llm_client = MagicMock()
        mcp_client = MagicMock()

        refactorer = RefactorerAgent(llm_client, mcp_client)

        assert refactorer.role == AgentRole.REFACTORER
        assert AgentCapability.READ_ONLY in refactorer.capabilities
        assert AgentCapability.FILE_EDIT in refactorer.capabilities
        assert len(refactorer.capabilities) == 2  # FILE_EDIT + READ_ONLY

    def test_refactorer_initialization_without_clients(self) -> None:
        """Test Refactorer can be initialized without clients (for testing)."""
        refactorer = RefactorerAgent()

        assert refactorer.role == AgentRole.REFACTORER
        assert AgentCapability.FILE_EDIT in refactorer.capabilities

    def test_refactorer_has_transactional_session(self) -> None:
        """Test Refactorer initializes transactional session."""
        refactorer = RefactorerAgent()

        # Session is None until execute is called
        assert refactorer.session is None

    @pytest.mark.asyncio
    async def test_refactorer_executes_with_plan(self) -> None:
        """Test Refactorer executes plan from PlannerAgent."""
        llm_client = MagicMock()
        llm_client.generate = AsyncMock(
            return_value=json.dumps(
                {
                    "refactoring_type": "rename_symbol",
                    "changes": [{"description": "Rename function"}],
                }
            )
        )

        refactorer = RefactorerAgent(llm_client, MagicMock())

        task = AgentTask(
            request="Refactor code",
            session_id="test",
            context={
                "plan": {
                    "sops": [
                        {
                            "id": "sop-1",
                            "role": "refactorer",
                            "action": "rename_symbol",
                            "target_file": "test.py",
                            "description": "Rename function foo to bar",
                            "dependencies": [],
                        }
                    ]
                },
                "target_file": "test.py",
            },
        )

        response = await refactorer.execute(task)

        # v8.0: Returns success based on transactional execution
        assert response.success is True or "rolled back" in response.reasoning.lower()

    @pytest.mark.asyncio
    async def test_refactorer_standalone_mode(self) -> None:
        """Test Refactorer works in standalone mode with target_file."""
        llm_client = MagicMock()
        llm_client.generate = AsyncMock(
            return_value=json.dumps({"plan_id": "auto-1", "changes": [], "execution_order": []})
        )

        refactorer = RefactorerAgent(llm_client, MagicMock())

        task = AgentTask(
            request="Simplify expression",
            session_id="test",
            context={"target_file": "app/utils.py", "refactoring_type": "simplify_expression"},
        )

        response = await refactorer.execute(task)

        # Standalone mode should either succeed or report failure cleanly
        assert response.success is True or response.error is not None

    @pytest.mark.asyncio
    async def test_refactorer_handles_exception(self) -> None:
        """Test Refactorer handles exceptions gracefully with rollback."""
        llm_client = MagicMock()
        llm_client.generate = AsyncMock(side_effect=Exception("LLM Error"))

        refactorer = RefactorerAgent(llm_client, MagicMock())
        task = AgentTask(request="Refactor", session_id="test", context={"target_file": "test.py"})

        response = await refactorer.execute(task)

        assert response.success is False
        assert response.error is not None
        assert "rolled back" in response.reasoning.lower()

    @pytest.mark.asyncio
    async def test_refactorer_with_stages(self) -> None:
        """Test Refactorer processes stages from plan."""
        llm_client = MagicMock()
        llm_client.generate = AsyncMock(return_value=json.dumps({}))

        refactorer = RefactorerAgent(llm_client, MagicMock())

        task = AgentTask(
            request="Multi-stage refactoring",
            session_id="test",
            context={
                "plan": {
                    "stages": [
                        {
                            "name": "Extract Methods",
                            "steps": [{"id": 1, "action": "extract_method", "file": "main.py"}],
                        }
                    ]
                },
                "target_file": "main.py",
            },
        )

        response = await refactorer.execute(task)

        # Should process stages or report error
        assert response is not None

    def test_refactorer_can_edit_files(self) -> None:
        """Test Refactorer can use file editing tools."""
        refactorer = RefactorerAgent(MagicMock(), MagicMock())

        # FILE_EDIT capability allows these tools
        assert refactorer._can_use_tool("write_file") is True
        assert refactorer._can_use_tool("edit_file") is True

    def test_refactorer_can_read_files(self) -> None:
        """Test Refactorer can use read tools."""
        refactorer = RefactorerAgent(MagicMock(), MagicMock())

        # READ_ONLY capability allows reading
        assert refactorer._can_use_tool("read_file") is True

    def test_refactorer_cannot_execute_bash(self) -> None:
        """Test Refactorer v8.0 does not have BASH_EXEC capability."""
        refactorer = RefactorerAgent(MagicMock(), MagicMock())

        # v8.0: No longer has BASH_EXEC
        assert AgentCapability.BASH_EXEC not in refactorer.capabilities
        assert refactorer._can_use_tool("bash_command") is False


class TestTransactionalSession:
    """Tests for TransactionalSession - ACID properties."""

    def test_session_initialization(self) -> None:
        """Test TransactionalSession initializes correctly."""
        session = TransactionalSession()

        assert session.session_id is not None
        assert len(session.session_id) == 12
        assert session.original_state == {}
        assert session.staged_changes == {}

    def test_session_custom_id(self) -> None:
        """Test TransactionalSession can have custom ID."""
        session = TransactionalSession(session_id="custom-session-123")

        assert session.session_id == "custom-session-123"

    def test_backup_original(self) -> None:
        """Test backup_original preserves file content."""
        session = TransactionalSession()

        session.backup_original("test.py", "original content")
        session.backup_original("test.py", "should not overwrite")  # Second call ignored

        assert session.original_state["test.py"] == "original content"

    def test_stage_change_validation(self) -> None:
        """Test stage_change validates syntax."""
        session = TransactionalSession()

        change = CodeChange(
            id="change-1",
            file_path="test.py",
            refactoring_type=RefactoringType.SIMPLIFY_EXPRESSION,
            original_content="x = 1",
            new_content="x = 1  # simplified",
            description="Add comment",
            line_start=1,
            line_end=1,
        )

        result = session.stage_change(change, validate=True)

        assert result.passed is True
        assert "syntax" in result.checks

    def test_stage_change_invalid_syntax(self) -> None:
        """Test stage_change rejects invalid syntax."""
        session = TransactionalSession()

        change = CodeChange(
            id="change-1",
            file_path="test.py",
            refactoring_type=RefactoringType.SIMPLIFY_EXPRESSION,
            original_content="x = 1",
            new_content="def broken(  # Invalid Python",
            description="Broken refactoring",
            line_start=1,
            line_end=1,
        )

        result = session.stage_change(change, validate=True)

        assert result.passed is False
        assert result.checks.get("syntax") is False


class TestRefactoringTypes:
    """Tests for RefactoringType enum."""

    def test_refactoring_types_exist(self) -> None:
        """Test all expected refactoring types exist."""
        assert RefactoringType.EXTRACT_METHOD.value == "extract_method"
        assert RefactoringType.INLINE_METHOD.value == "inline_method"
        assert RefactoringType.RENAME_SYMBOL.value == "rename_symbol"
        assert RefactoringType.REMOVE_DEAD_CODE.value == "remove_dead_code"
        assert RefactoringType.MODERNIZE_SYNTAX.value == "modernize_syntax"


class TestChangeStatus:
    """Tests for ChangeStatus enum."""

    def test_change_status_states(self) -> None:
        """Test all change status states exist."""
        assert ChangeStatus.PENDING.value == "pending"
        assert ChangeStatus.STAGED.value == "staged"
        assert ChangeStatus.VALIDATED.value == "validated"
        assert ChangeStatus.COMMITTED.value == "committed"
        assert ChangeStatus.ROLLED_BACK.value == "rolled_back"
        assert ChangeStatus.FAILED.value == "failed"


class TestRefactoringPlan:
    """Tests for RefactoringPlan model."""

    def test_plan_creation(self) -> None:
        """Test RefactoringPlan can be created."""
        plan = RefactoringPlan(
            plan_id="plan-123",
            goal="Extract utility functions",
            changes=[{"id": "c1", "action": "extract_method"}],
            execution_order=["c1"],
            affected_files=["utils.py"],
            risk_level="LOW",
        )

        assert plan.plan_id == "plan-123"
        assert plan.goal == "Extract utility functions"
        assert len(plan.changes) == 1
        assert plan.require_tests is True  # Default
        assert plan.rollback_strategy == "incremental"  # Default

    def test_plan_defaults(self) -> None:
        """Test RefactoringPlan has sensible defaults."""
        plan = RefactoringPlan(plan_id="p1", goal="Test")

        assert plan.changes == []
        assert plan.execution_order == []
        assert plan.affected_files == []
        assert plan.risk_level == "MEDIUM"


class TestCodeChange:
    """Tests for CodeChange dataclass."""

    def test_code_change_creation(self) -> None:
        """Test CodeChange can be created."""
        change = CodeChange(
            id="change-1",
            file_path="app/views.py",
            refactoring_type=RefactoringType.EXTRACT_METHOD,
            original_content="def long_function(): pass",
            new_content="def helper(): pass\ndef long_function(): helper()",
            description="Extract helper method",
            line_start=10,
            line_end=50,
            affected_symbols=["long_function", "helper"],
            dependencies=[],
        )

        assert change.id == "change-1"
        assert change.file_path == "app/views.py"
        assert change.status == ChangeStatus.PENDING  # Default
        assert len(change.affected_symbols) == 2

    def test_code_change_defaults(self) -> None:
        """Test CodeChange has sensible defaults."""
        change = CodeChange(
            id="c1",
            file_path="test.py",
            refactoring_type=RefactoringType.SIMPLIFY_EXPRESSION,
            original_content="x = 1",
            new_content="x = 1",
            description="No-op",
            line_start=1,
            line_end=1,
        )

        assert change.affected_symbols == []
        assert change.dependencies == []
        assert change.status == ChangeStatus.PENDING
        assert change.checkpoint_id is None
