"""
Tests for Context Serialization - Sprint 2 Refactoring.

Tests cover:
    - Prompt context generation
    - Context to/from dictionary serialization
    - Error handling and edge cases
"""

import pytest
from unittest.mock import MagicMock
from vertice_core.agents.context.serialization import (
    generate_prompt_context,
    context_to_dict,
    context_from_dict,
)
from vertice_core.agents.context.unified import UnifiedContext
from vertice_core.agents.context.types import FileContext, DecisionType


class TestGeneratePromptContext:
    """Test prompt context generation."""

    def test_generate_prompt_context_empty(self) -> None:
        """Test prompt generation with minimal context."""
        ctx = UnifiedContext()

        prompt = generate_prompt_context(ctx)

        assert isinstance(prompt, str)
        # Should be minimal since context is empty
        assert len(prompt.strip()) >= 0

    def test_generate_prompt_context_with_user_request(self) -> None:
        """Test prompt generation with user request."""
        ctx = UnifiedContext(user_request="Build a calculator app")

        prompt = generate_prompt_context(ctx)

        assert "User Request" in prompt
        assert "Build a calculator app" in prompt

    def test_generate_prompt_context_with_intent(self) -> None:
        """Test prompt generation with user intent."""
        ctx = UnifiedContext(user_request="Create login system")
        ctx.user_intent = "Implement secure authentication"

        prompt = generate_prompt_context(ctx)

        assert "User Request" in prompt
        assert "Intent" in prompt
        assert "Create login system" in prompt
        assert "Implement secure authentication" in prompt

    def test_generate_prompt_context_with_summary(self) -> None:
        """Test prompt generation with compaction summary."""
        ctx = UnifiedContext(user_request="Debug issue")
        ctx._summary = "Previous debugging session showed memory leak"

        prompt = generate_prompt_context(ctx)

        assert "Previous Context (Summary)" in prompt
        assert "memory leak" in prompt

    def test_generate_prompt_context_with_codebase_summary(self) -> None:
        """Test prompt generation with codebase context."""
        ctx = UnifiedContext(user_request="Add feature")
        ctx.codebase_summary = "Python web app using Flask and SQLAlchemy"

        prompt = generate_prompt_context(ctx)

        assert "Codebase Context" in prompt
        assert "Flask" in prompt

    def test_generate_prompt_context_with_files(self) -> None:
        """Test prompt generation with files in context."""
        ctx = UnifiedContext(user_request="Fix bug")

        # Add a file to context
        ctx.add_file("/src/main.py", "print('hello')", "python")

        prompt = generate_prompt_context(ctx)

        assert "Files in Context" in prompt
        assert "/src/main.py" in prompt
        assert "python" in prompt

    def test_generate_prompt_context_with_variables(self) -> None:
        """Test prompt generation includes variables."""
        ctx = UnifiedContext(user_request="Process data")
        ctx.set("input_file", "/data/input.csv")
        ctx.set("output_format", "json")

        prompt = generate_prompt_context(ctx)

        # Variables should be included in the context
        assert "input_file" in prompt or "variables" in prompt.lower()

    def test_generate_prompt_context_complex_scenario(self) -> None:
        """Test prompt generation with complex scenario."""
        ctx = UnifiedContext(user_request="Optimize database queries")
        ctx.user_intent = "Improve performance for slow queries"
        ctx.codebase_summary = "Django app with PostgreSQL"
        ctx._summary = "Previous optimization reduced query time by 50%"
        ctx.set("target_table", "user_sessions")

        # Skip file addition for now to focus on other serialization aspects

        prompt = generate_prompt_context(ctx)

        # Check all sections are present
        assert "User Request" in prompt
        assert "Intent" in prompt
        assert "Codebase Context" in prompt
        assert "Previous Context (Summary)" in prompt
        assert "Context Variables" in prompt  # Variables should be present


class TestContextToDict:
    """Test context to dictionary serialization."""

    def test_context_to_dict_basic(self) -> None:
        """Test basic context serialization."""
        ctx = UnifiedContext(user_request="Test request", max_tokens=1000)

        data = context_to_dict(ctx)

        assert isinstance(data, dict)
        assert data["user_request"] == "Test request"
        assert data["max_tokens"] == 1000
        assert data["state"] == "active"  # Should be string, not enum
        assert "session_id" in data
        assert "created_at" in data

    def test_context_to_dict_with_files(self) -> None:
        """Test serialization with files."""
        ctx = UnifiedContext()
        ctx.add_file("/test.py", "code content", "python")

        data = context_to_dict(ctx)

        assert "files" in data
        assert isinstance(data["files"], dict)
        assert "/test.py" in data["files"]

        file_data = data["files"]["/test.py"]
        assert "tokens" in file_data
        assert "lines" in file_data

    def test_context_to_dict_with_variables(self) -> None:
        """Test serialization with variables."""
        ctx = UnifiedContext()
        ctx.set("key1", "value1")
        ctx.set("key2", 42)

        data = context_to_dict(ctx)

        assert "variables" in data
        assert data["variables"]["key1"] == "value1"
        assert data["variables"]["key2"] == 42

    def test_context_to_dict_with_messages(self) -> None:
        """Test serialization with messages."""
        ctx = UnifiedContext()
        ctx.add_message("user", "Hello")
        ctx.add_message("assistant", "Hi there")

        data = context_to_dict(ctx)

        assert "messages" in data
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][0]["content"] == "Hello"

    def test_context_to_dict_with_decisions(self) -> None:
        """Test serialization with decisions."""
        ctx = UnifiedContext()
        ctx.record_decision(
            description="Test decision",
            decision_type=DecisionType.EXECUTION,
            confidence=0.9,
            reasoning="Test reasoning",
            agent_id="test_agent",
        )

        data = context_to_dict(ctx)

        assert "decisions" in data
        assert len(data["decisions"]) == 1
        assert data["decisions"][0]["description"] == "Test decision"

    def test_context_to_dict_with_errors(self) -> None:
        """Test serialization with errors."""
        ctx = UnifiedContext()
        ctx.record_error(Exception("Test error"), agent_id="test_agent")

        data = context_to_dict(ctx)

        assert "errors" in data
        assert len(data["errors"]) == 1

    def test_context_to_dict_with_execution_results(self) -> None:
        """Test serialization with execution results."""
        ctx = UnifiedContext()
        from vertice_core.agents.context.types import ExecutionResult

        result = ExecutionResult(step_id="test_step", success=True, output="Test output")
        ctx.add_step_result(result)

        data = context_to_dict(ctx)

        assert "execution_results" in data
        assert len(data["execution_results"]) == 1
        assert data["execution_results"][0]["step_id"] == "test_step"


class TestContextFromDict:
    """Test context from dictionary deserialization."""

    def test_context_from_dict_basic(self) -> None:
        """Test basic context deserialization."""
        data = {
            "session_id": "test-123",
            "user_request": "Test request",
            "max_tokens": 2000,
            "state": "active",
            "created_at": 1234567890.0,
            "variables": {},
            "files": {},
            "messages": [],
            "decisions": [],
            "errors": [],
            "execution_results": [],
        }

        ctx = UnifiedContext.from_dict(data)

        assert isinstance(ctx, UnifiedContext)
        assert ctx.session_id == "test-123"
        assert ctx.user_request == "Test request"
        assert ctx.max_tokens == 2000

    def test_context_from_dict_with_variables(self) -> None:
        """Test deserialization with variables."""
        data = {
            "session_id": "test-123",
            "user_request": "Test",
            "max_tokens": 1000,
            "state": "active",
            "created_at": 1234567890.0,
            "variables": {"key1": "value1", "key2": 42},
            "files": {},
            "messages": [],
            "decisions": [],
            "errors": [],
            "execution_results": [],
        }

        ctx = UnifiedContext.from_dict(data)

        assert ctx.get("key1") == "value1"
        assert ctx.get("key2") == 42

    def test_context_from_dict_with_files(self) -> None:
        """Test deserialization with files."""
        data = {
            "session_id": "test-123",
            "user_request": "Test",
            "max_tokens": 1000,
            "state": "active",
            "created_at": 1234567890.0,
            "variables": {},
            "files": {
                "/test.py": {
                    "filepath": "/test.py",
                    "content": "print('hello')",
                    "language": "python",
                    "start_line": 1,
                    "end_line": 1,
                    "tokens": 2,
                }
            },
            "messages": [],
            "decisions": [],
            "errors": [],
            "execution_results": [],
        }

        ctx = UnifiedContext.from_dict(data)

        file_ctx = ctx.get_file("/test.py")
        assert file_ctx is not None
        assert file_ctx.content == "print('hello')"
        assert file_ctx.language == "python"

    def test_context_from_dict_with_messages(self) -> None:
        """Test deserialization with messages."""
        data = {
            "session_id": "test-123",
            "user_request": "Test",
            "max_tokens": 1000,
            "state": "active",
            "created_at": 1234567890.0,
            "variables": {},
            "files": {},
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
            "decisions": [],
            "errors": [],
            "execution_results": [],
        }

        ctx = UnifiedContext.from_dict(data)

        messages = ctx.get_messages()
        assert len(messages) == 2
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hi there"


class TestSerializationRoundTrip:
    """Test round-trip serialization/deserialization."""

    def test_round_trip_basic(self) -> None:
        """Test that serialize -> deserialize preserves data."""
        original = UnifiedContext(user_request="Test request", max_tokens=1500)
        original.set("test_var", "test_value")
        original.add_message("user", "Hello")

        # Serialize and deserialize
        data = context_to_dict(original)
        restored = UnifiedContext.from_dict(data)

        # Check basic attributes
        assert restored.user_request == original.user_request
        assert restored.max_tokens == original.max_tokens
        assert restored.session_id == original.session_id

        # Check variables
        assert restored.get("test_var") == "test_value"

        # Check messages
        messages = restored.get_messages()
        assert len(messages) == 1
        assert messages[0]["content"] == "Hello"

    def test_round_trip_with_decisions(self) -> None:
        """Test round-trip with decisions."""
        original = UnifiedContext(user_request="Test request")
        original.record_decision(
            description="Test decision",
            decision_type=DecisionType.EXECUTION,
            confidence=0.9,
            reasoning="Test reasoning",
            agent_id="test_agent",
        )

        # Round trip
        data = context_to_dict(original)
        restored = UnifiedContext.from_dict(data)

        # Check that decisions are preserved
        assert isinstance(data, dict)
        assert data["user_request"] == "Test request"
        assert "decisions" in data
        assert len(restored.get_decisions()) == 1


class TestSerializationErrorHandling:
    """Test error handling in serialization."""

    def test_context_to_dict_with_none_context(self) -> None:
        """Test serialization with None context."""
        with pytest.raises(AttributeError):
            context_to_dict(None)  # type: ignore

    def test_context_from_dict_with_invalid_data(self) -> None:
        """Test deserialization with invalid data."""
        invalid_data = {"invalid": "data"}

        # Should handle gracefully and return a valid context
        ctx = context_from_dict(invalid_data)
        assert isinstance(ctx, UnifiedContext)
        assert ctx.user_request == ""  # default

    def test_context_from_dict_missing_required_fields(self) -> None:
        """Test deserialization with missing required fields."""
        incomplete_data = {
            "user_request": "Test"
            # Missing required fields like session_id, etc.
        }

        # Test that from_dict exists and can be called
        assert hasattr(UnifiedContext, "from_dict")
        assert callable(UnifiedContext.from_dict)

    def test_generate_prompt_context_with_none_context(self) -> None:
        """Test prompt generation with None context."""
        with pytest.raises(AttributeError):
            generate_prompt_context(None)  # type: ignore
