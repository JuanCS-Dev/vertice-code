"""
Tests for Context Types - Sprint 2 Refactoring.
"""

from vertice_core.agents.context.types import (
    ContextState,
    DecisionType,
    Decision,
    ErrorContext,
    FileContext,
    ExecutionResult,
    ThoughtSignature,
)


class TestContextEnums:
    """Test context enums."""

    def test_context_states(self) -> None:
        """Test ContextState enum values."""
        assert ContextState.ACTIVE == "active"
        assert ContextState.COMPACTING == "compacting"
        assert ContextState.STALE == "stale"
        assert ContextState.PERSISTED == "persisted"

    def test_decision_types(self) -> None:
        """Test DecisionType enum values."""
        assert DecisionType.ROUTING == "routing"
        assert DecisionType.PLANNING == "planning"
        assert DecisionType.EXECUTION == "execution"
        assert DecisionType.APPROVAL == "approval"


class TestContextDataclasses:
    """Test context dataclasses."""

    def test_decision_creation(self) -> None:
        """Test Decision dataclass."""
        decision = Decision(
            decision_type=DecisionType.EXECUTION,
            description="Execute code analysis",
            confidence=0.85,
            reasoning="Code shows clear patterns",
        )
        assert decision.decision_type == DecisionType.EXECUTION
        assert decision.description == "Execute code analysis"
        assert decision.confidence == 0.85
        assert decision.reasoning == "Code shows clear patterns"

    def test_error_context_creation(self) -> None:
        """Test ErrorContext dataclass."""
        error = ErrorContext(
            error_message="Import error occurred",
            stack_trace="Traceback details...",
            recovery_attempted=True,
        )
        assert error.error_message == "Import error occurred"
        assert error.stack_trace == "Traceback details..."
        assert error.recovery_attempted is True

    def test_file_context_creation(self) -> None:
        """Test FileContext dataclass."""
        file_ctx = FileContext(
            filepath="/src/main.py",
            content="print('hello')",
            language="python",
        )
        assert file_ctx.filepath == "/src/main.py"
        assert file_ctx.content == "print('hello')"
        assert file_ctx.language == "python"

    def test_execution_result_creation(self) -> None:
        """Test ExecutionResult dataclass."""
        result = ExecutionResult(
            step_id="step-001",
            success=True,
            output="Hello World",
            duration_ms=150.5,
        )
        assert result.step_id == "step-001"
        assert result.success is True
        assert result.output == "Hello World"
        assert result.duration_ms == 150.5

    def test_thought_signature_creation(self) -> None:
        """Test ThoughtSignature dataclass."""
        thought = ThoughtSignature(
            agent_id="architect-001",
            key_insights=["Complex task", "Needs planning"],
            next_action="Create detailed plan",
            confidence=0.92,
        )
        assert thought.agent_id == "architect-001"
        assert len(thought.key_insights) == 2
        assert thought.next_action == "Create detailed plan"
        assert thought.confidence == 0.92
