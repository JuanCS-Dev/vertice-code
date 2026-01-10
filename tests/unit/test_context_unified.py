"""
Tests for UnifiedContext - Sprint 2 Refactoring.

Tests cover:
    - UnifiedContext initialization and core attributes
    - Inherited mixin functionality (variables, files, messages, etc.)
    - Compaction logic and token management
    - Serialization/deserialization
    - Statistics and state management
"""

import pytest
import time
from unittest.mock import MagicMock, patch
from vertice_core.agents.context.unified import UnifiedContext
from vertice_core.agents.context.types import ContextState, ExecutionResult


class TestUnifiedContextInitialization:
    """Test UnifiedContext initialization and core attributes."""

    def test_default_initialization(self) -> None:
        """Test UnifiedContext with default parameters."""
        context = UnifiedContext()

        assert context.session_id is not None
        assert len(context.session_id) == 8  # UUID truncated
        assert context.created_at <= time.time()
        assert context.max_tokens == UnifiedContext.DEFAULT_MAX_TOKENS
        assert context.state == ContextState.ACTIVE
        assert context.user_request == ""
        assert context.user_intent == ""
        assert context.current_agent is None
        assert context.current_plan_id is None
        assert context.completed_steps == []
        assert context._token_usage == 0

    def test_custom_initialization(self) -> None:
        """Test UnifiedContext with custom parameters."""
        custom_session = "test-123"
        context = UnifiedContext(
            user_request="Build a calculator app",
            max_tokens=16000,
            session_id=custom_session,
        )

        assert context.user_request == "Build a calculator app"
        assert context.max_tokens == 16000
        assert context.session_id == custom_session

    def test_mixin_inheritance(self) -> None:
        """Test that all mixins are properly inherited."""
        context = UnifiedContext()

        # Test ContextVariablesMixin
        assert hasattr(context, "get")
        assert hasattr(context, "set")
        assert hasattr(context, "variables")

        # Test FileContextMixin
        assert hasattr(context, "add_file")
        assert hasattr(context, "get_file")
        assert hasattr(context, "list_files")

        # Test MessageMixin
        assert hasattr(context, "add_message")
        assert hasattr(context, "get_messages")

        # Test DecisionTrackingMixin
        assert hasattr(context, "record_decision")
        assert hasattr(context, "get_decisions")

        # Test ErrorTrackingMixin
        assert hasattr(context, "record_error")
        assert hasattr(context, "get_errors")

        # Test ThoughtSignaturesMixin
        assert hasattr(context, "add_thought")
        assert hasattr(context, "get_thoughts")

        # Test ExecutionResultsMixin
        assert hasattr(context, "add_step_result")
        assert hasattr(context, "get_execution_results")


class TestUnifiedContextMixinIntegration:
    """Test that mixins work correctly within UnifiedContext."""

    def test_variables_mixin_integration(self) -> None:
        """Test variable management in UnifiedContext."""
        context = UnifiedContext()

        # Test variable operations
        context.set("task_id", "task-123")
        context.set("priority", "high")

        assert context.get("task_id") == "task-123"
        assert context.get("priority") == "high"
        assert context.get("nonexistent") is None

        # Test variables dict
        vars_dict = context.variables()
        assert "task_id" in vars_dict
        assert "priority" in vars_dict

    def test_files_mixin_integration(self) -> None:
        """Test file context management in UnifiedContext."""
        context = UnifiedContext()

        # Add a file
        context.add_file("/src/main.py", 'print("hello")', "python")

        # Test file retrieval
        file_ctx = context.get_file("/src/main.py")
        assert file_ctx is not None
        assert file_ctx.filepath == "/src/main.py"
        assert file_ctx.content == 'print("hello")'
        assert file_ctx.language == "python"

        # Test file listing
        files = context.list_files()
        assert len(files) == 1
        assert "/src/main.py" in files

    def test_messages_mixin_integration(self) -> None:
        """Test message management in UnifiedContext."""
        context = UnifiedContext()

        # Add messages
        context.add_message("user", "Hello")
        context.add_message("assistant", "Hi there!")

        # Test message retrieval
        messages = context.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there!"

    def test_decisions_mixin_integration(self) -> None:
        """Test decision tracking in UnifiedContext."""
        context = UnifiedContext()

        # Add decision
        context.record_decision(
            description="Run tests",
            decision_type="execution",
            reasoning="Tests are needed to validate functionality",
            agent_id="tester",
            confidence=0.9,
        )

        # Test decision retrieval
        decisions = context.get_decisions()
        assert len(decisions) == 1
        assert decisions[0].description == "Run tests"
        assert decisions[0].agent_id == "tester"

    def test_errors_mixin_integration(self) -> None:
        """Test error tracking in UnifiedContext."""
        context = UnifiedContext()

        # Add error
        context.record_error(error_message="Module not found", agent_id="executor")

        # Test error retrieval
        errors = context.get_errors()
        assert len(errors) == 1
        assert errors[0].error_message == "Module not found"

    def test_thoughts_mixin_integration(self) -> None:
        """Test thought signature management in UnifiedContext."""
        context = UnifiedContext()

        # Add thought
        context.add_thought(
            reasoning="This is a complex task requiring careful planning",
            agent_id="architect",
            key_insights=["Complex task", "Needs planning"],
            next_action="Create plan",
            confidence=0.85,
        )

        # Test thought retrieval
        thoughts = context.get_thought_chain()
        assert len(thoughts) >= 1
        assert thoughts[-1].agent_id == "architect"

    def test_execution_results_mixin_integration(self) -> None:
        """Test execution result management in UnifiedContext."""
        context = UnifiedContext()

        # Add execution result
        result = ExecutionResult(
            step_id="step-001", success=True, output="Test passed", duration_ms=150.5
        )
        context.add_step_result(result)

        # Test result retrieval
        results = context.get_execution_results()
        assert len(results) == 1
        assert results[0].step_id == "step-001"
        assert results[0].success is True
        assert results[0].output == "Test passed"


class TestUnifiedContextCompaction:
    """Test compaction functionality in UnifiedContext."""

    def test_compact_method_exists(self) -> None:
        """Test that compact method exists and is callable."""
        context = UnifiedContext()
        assert hasattr(context, "compact")
        assert callable(context.compact)

    def test_should_compact_logic(self) -> None:
        """Test compaction trigger logic."""
        context = UnifiedContext(max_tokens=1000)

        # Mock token usage
        context._token_usage = 800  # 80% - should not compact
        assert not context._should_compact()

        context._token_usage = 950  # 95% - should compact
        assert context._should_compact()

    def test_compact_basic_functionality(self) -> None:
        """Test that compact method can be called without errors."""
        context = UnifiedContext()

        # Should not raise any exceptions
        result = context.compact()
        assert isinstance(result, str)  # Returns summary string


class TestUnifiedContextSerialization:
    """Test serialization/deserialization of UnifiedContext."""

    def test_to_dict_includes_core_attributes(self) -> None:
        """Test that to_dict includes all core attributes."""
        context = UnifiedContext(
            user_request="Test request", max_tokens=8000, session_id="test-123"
        )

        data = context.to_dict()

        assert data["session_id"] == "test-123"
        assert data["user_request"] == "Test request"
        assert data["max_tokens"] == 8000
        assert data["state"] == ContextState.ACTIVE.value
        assert "created_at" in data
        assert "variables" in data
        assert "files" in data
        assert "messages" in data
        assert "decisions" in data
        assert "errors" in data
        assert "thoughts" in data
        assert "execution_results" in data

    def test_from_dict_creates_valid_context(self) -> None:
        """Test that from_dict creates a valid UnifiedContext."""
        original = UnifiedContext(user_request="Original request", max_tokens=16000)

        # Add some data
        original.set("test_var", "test_value")
        original.add_message("user", "Hello")

        # Serialize and deserialize
        data = original.to_dict()
        restored = UnifiedContext.from_dict(data)

        assert restored.session_id == original.session_id
        assert restored.user_request == original.user_request
        assert restored.max_tokens == original.max_tokens
        assert restored.get("test_var") == "test_value"

        messages = restored.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello"


class TestUnifiedContextStats:
    """Test statistics and token usage tracking."""

    def test_get_token_usage(self) -> None:
        """Test token usage reporting."""
        context = UnifiedContext(max_tokens=1000)
        context._token_usage = 750

        usage, max_tokens = context.get_token_usage()
        assert usage == 750
        assert max_tokens == 1000

    def test_get_stats_includes_basic_metrics(self) -> None:
        """Test that get_stats returns basic metrics."""
        context = UnifiedContext(max_tokens=2000)
        context._token_usage = 1500

        # Add some data
        context.set("test_var", "value")
        context.add_message("user", "Hello")

        stats = context.get_stats()

        assert "session_id" in stats
        assert "created_at" in stats
        assert "state" in stats
        assert "token_usage" in stats
        assert "variable_count" in stats
        assert "file_count" in stats
        assert "message_count" in stats
        assert "decision_count" in stats
        assert "error_count" in stats
        assert "thought_count" in stats
        assert "execution_steps" in stats

        assert stats["token_usage"] == 1500

    def test_get_thought_chain(self) -> None:
        """Test thought chain retrieval."""
        context = UnifiedContext()

        # Add a thought
        context.add_thought(
            reasoning="Need to analyze this complex task",
            agent_id="architect",
            key_insights=["Planning needed"],
            next_action="Plan task",
            confidence=0.9,
        )

        thought_chain = context.get_thought_chain()
        assert len(thought_chain) >= 1  # At least the thought we added


class TestUnifiedContextStateManagement:
    """Test state management and lifecycle."""

    def test_initial_state_is_active(self) -> None:
        """Test that context starts in ACTIVE state."""
        context = UnifiedContext()
        assert context.state == ContextState.ACTIVE

    def test_clear_method_resets_context(self) -> None:
        """Test that clear method resets context appropriately."""
        context = UnifiedContext()

        # Add some data
        context.set("test_var", "value")
        context.add_message("user", "Hello")
        context.add_file("/test.py", "code", "python")

        # Clear
        context.clear()

        # Check that data is cleared but core attributes remain
        assert context.get("test_var") is None
        assert len(context.get_messages()) == 0
        assert len(context.list_files()) == 0
        assert context.session_id is not None  # Core attributes preserved
        assert context.state == ContextState.ACTIVE

    def test_to_prompt_context_returns_string(self) -> None:
        """Test that to_prompt_context returns a string representation."""
        context = UnifiedContext(user_request="Test request")

        prompt_context = context.to_prompt_context()
        assert isinstance(prompt_context, str)
        assert "Test request" in prompt_context
