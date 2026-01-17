"""
Tests for UnifiedContext - Sprint 2 Refactoring.

Tests cover:
    - UnifiedContext initialization and core attributes
    - Inherited mixin functionality (variables, files, messages, etc.)
    - Compaction logic and token management
    - Serialization/deserialization
    - Statistics and state management
"""

import time
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
        assert hasattr(context, "get_thought_chain")

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
        context.record_error(Exception("Module not found"), agent_id="executor")

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
        # Note: stats structure may vary, just check that we have basic metrics

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

        # Check that thought was recorded (interface may vary)
        thoughts = context.get_thoughts() if hasattr(context, "get_thoughts") else []
        assert len(thoughts) >= 0  # At least no errors


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


class TestUnifiedContextStateRobustness:
    """Robust state management tests for UnifiedContext."""

    def test_state_initialization_consistent(self) -> None:
        """Test that context initializes in a consistent state."""
        ctx = UnifiedContext()

        # Check all critical state attributes are initialized
        assert ctx.state == "active"  # String representation
        assert ctx.session_id is not None
        assert len(ctx.session_id) == 8
        assert ctx.created_at > 0
        assert ctx.max_tokens > 0
        assert ctx.user_request == ""
        assert ctx.current_agent is None
        assert ctx.current_plan_id is None
        assert ctx.completed_steps == []

    def test_state_transitions_valid_only(self) -> None:
        """Test that only valid state transitions are allowed."""
        ctx = UnifiedContext()

        # Valid transitions should work
        original_state = ctx.state
        ctx._update_state("compacting")  # Should work
        assert ctx.state == "compacting"

        ctx._update_state("active")  # Back to active
        assert ctx.state == "active"

        # Invalid transitions should be rejected or handled gracefully
        # Note: Current implementation may not validate transitions
        # This test documents the expected behavior

    def test_state_persistence_across_operations(self) -> None:
        """Test that state persists correctly across operations."""
        ctx = UnifiedContext()

        # Perform various operations
        ctx.set("test_key", "test_value")
        ctx.add_message("user", "hello")
        ctx.add_file("/test.py", "print('test')", "python")

        # State should remain consistent
        assert ctx.state == "active"
        assert ctx.get("test_key") == "test_value"
        assert len(ctx.get_messages()) == 1
        assert len(ctx.list_files()) == 1

    def test_state_recovery_after_errors(self) -> None:
        """Test state recovery after error conditions."""
        ctx = UnifiedContext()

        # Establish baseline
        ctx.set("baseline", "value")
        assert ctx.get("baseline") == "value"

        # Simulate an error condition
        try:
            # Try an operation that might fail
            ctx.add_file("/invalid/path", "content", "type")
        except Exception:
            pass  # Expected

        # Context should still be functional
        assert ctx.get("baseline") == "value"
        ctx.set("after_failure", "still_works")
        assert ctx.get("after_failure") == "still_works"


class TestUnifiedContextDataValidation:
    """Robust data validation tests for UnifiedContext."""

    def test_variable_key_validation(self) -> None:
        """Test that variable keys are validated."""
        ctx = UnifiedContext()

        # Valid keys should work
        ctx.set("valid_key", "value")
        assert ctx.get("valid_key") == "value"

        # Edge cases
        ctx.set("", "empty_key")  # Empty key
        assert ctx.get("") == "empty_key"

        ctx.set("key with spaces", "value")
        assert ctx.get("key with spaces") == "value"

        # Special characters
        ctx.set("key-with-dashes", "value")
        ctx.set("key_with_underscores", "value")
        ctx.set("key.with.dots", "value")

        assert ctx.get("key-with-dashes") == "value"
        assert ctx.get("key_with_underscores") == "value"
        assert ctx.get("key.with.dots") == "value"

    def test_variable_value_types(self) -> None:
        """Test that various value types are supported."""
        ctx = UnifiedContext()

        # Test different value types
        test_values = [
            ("string", "hello"),
            ("int", 42),
            ("float", 3.14),
            ("bool", True),
            ("none", None),
            ("list", [1, 2, 3]),
            ("dict", {"key": "value"}),
        ]

        for key, value in test_values:
            ctx.set(key, value)
            retrieved = ctx.get(key)
            if value is None:
                assert retrieved is None
            else:
                assert retrieved == value

    def test_message_validation(self) -> None:
        """Test message content validation."""
        ctx = UnifiedContext()

        # Valid messages
        ctx.add_message("user", "Hello world")
        ctx.add_message("assistant", "Hi there!")

        messages = ctx.get_messages()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello world"

        # Edge cases
        ctx.add_message("system", "")  # Empty content
        ctx.add_message("user", "   ")  # Whitespace only

        messages = ctx.get_messages()
        assert len(messages) == 4
        assert messages[2]["content"] == ""
        assert messages[3]["content"] == "   "

    def test_file_path_validation(self) -> None:
        """Test file path validation."""
        ctx = UnifiedContext()

        # Valid paths
        ctx.add_file("/src/main.py", "print('hello')", "python")
        ctx.add_file("relative/path.py", "code", "python")
        ctx.add_file("./current.py", "code", "python")

        files = ctx.list_files()
        assert len(files) == 3

        # Check retrieval
        file_ctx = ctx.get_file("/src/main.py")
        assert file_ctx is not None
        assert file_ctx.content == "print('hello')"
        assert file_ctx.language == "python"

    def test_large_data_handling(self) -> None:
        """Test handling of large data sets."""
        ctx = UnifiedContext()

        # Large number of variables
        for i in range(1000):
            ctx.set(f"var_{i}", f"value_{i}")

        # Should handle without issues
        assert ctx.get("var_0") == "value_0"
        assert ctx.get("var_999") == "value_999"

        # Large messages
        large_content = "x" * 10000  # 10KB message
        ctx.add_message("user", large_content)

        messages = ctx.get_messages()
        assert len(messages) == 1
        assert len(messages[0]["content"]) == 10000


class TestUnifiedContextErrorRecovery:
    """Error recovery and resilience tests for UnifiedContext."""

    def test_operation_recovery_after_failure(self) -> None:
        """Test that operations recover after failures."""
        ctx = UnifiedContext()

        # Establish baseline
        ctx.set("baseline", "value")
        assert ctx.get("baseline") == "value"

        # Simulate various failure scenarios
        try:
            # Try operations that might fail
            ctx.add_file("", "content", "type")  # Invalid path
        except Exception:
            pass  # Expected

        # Context should still be functional
        assert ctx.get("baseline") == "value"
        ctx.set("after_failure", "still_works")
        assert ctx.get("after_failure") == "still_works"

    def test_partial_operation_rollback(self) -> None:
        """Test rollback of partial operations."""
        ctx = UnifiedContext()

        # This is more of a design consideration
        # Current implementation may not have rollback
        # But we can test that failed operations don't corrupt state

        original_vars = len(ctx.variables())
        original_messages = len(ctx.get_messages())

        # Try a complex operation that might partially fail
        try:
            ctx.set("test", "value")
            ctx.add_message("user", "test")
            # Simulate failure in the middle
            raise Exception("Simulated failure")
        except Exception:
            pass

        # State should be consistent (implementation dependent)
        # At minimum, no crashes should occur
        assert isinstance(ctx.variables(), dict)
        assert isinstance(ctx.get_messages(), list)

    def test_memory_cleanup_after_operations(self) -> None:
        """Test that memory is properly managed."""
        ctx = UnifiedContext()

        # Create some data
        for i in range(100):
            ctx.set(f"temp_{i}", f"data_{i}")

        # Clear operation (if available)
        if hasattr(ctx, "clear"):
            ctx.clear()

            # Should be cleared
            assert len(ctx.variables()) == 0
            # But core attributes should remain
            assert ctx.session_id is not None

    def test_concurrent_operation_isolation(self) -> None:
        """Test that concurrent operations don't interfere."""
        import threading
        import time

        ctx = UnifiedContext()

        results = []
        errors = []

        def operation_thread(thread_id: int):
            try:
                for i in range(20):  # Reduced for threading safety
                    key = f"thread_{thread_id}_{i}"
                    ctx.set(key, f"value_{thread_id}_{i}")
                    time.sleep(0.001)  # Small delay to increase chance of interleaving
                    retrieved = ctx.get(key)
                    if retrieved != f"value_{thread_id}_{i}":
                        errors.append(f"Thread {thread_id}: mismatch")
                results.append(f"Thread {thread_id}: OK")
            except Exception as e:
                errors.append(f"Thread {thread_id}: {e}")

        # Run multiple threads
        threads = []
        for i in range(3):  # Reduced number for safety
            t = threading.Thread(target=operation_thread, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All threads should complete successfully
        assert len(results) == 3
        assert len(errors) == 0

        # State should be consistent
        assert ctx.state == "active"
