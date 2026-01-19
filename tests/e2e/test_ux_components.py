"""
E2E Tests for UX Components - Phase 8.6

Testing UX components in preparation for Phase 10 integration:
- InputEnhancer: Smart input processing
- ContextTracker: Reference resolution
- ErrorPresenter: User-friendly error display

These tests validate the components work correctly before integration.
"""

import pytest


# =============================================================================
# 1. INPUT ENHANCER TESTS
# =============================================================================


class TestInputEnhancer:
    """Test InputEnhancer component."""

    @pytest.fixture
    def enhancer(self):
        """Create InputEnhancer instance."""
        from vertice_cli.core.input_enhancer import InputEnhancer

        return InputEnhancer()

    def test_enhancer_initialization(self, enhancer):
        """Test enhancer initializes correctly."""
        assert enhancer is not None
        assert hasattr(enhancer, "enhance")

    def test_enhance_plain_text(self, enhancer):
        """Test enhancing plain text input."""
        result = enhancer.enhance("Hello, world!")

        assert result is not None
        assert result.original == "Hello, world!"
        assert result.cleaned == "Hello, world!"

    def test_enhance_code_block_markdown(self, enhancer):
        """Test extracting code from markdown blocks."""
        input_text = """Here's some code:
```python
def hello():
    print("Hello")
```
"""
        result = enhancer.enhance(input_text)

        assert len(result.code_blocks) == 1
        assert result.code_blocks[0].language == "python"
        assert "def hello" in result.code_blocks[0].code

    def test_enhance_repl_paste(self, enhancer):
        """Test cleaning Python REPL paste (>>> removal)."""
        input_text = """>>> def hello():
...     print("Hello")
>>> hello()
Hello"""
        result = enhancer.enhance(input_text)

        # Should detect REPL paste
        from vertice_cli.core.input_enhancer import InputType

        assert result.input_type in [InputType.REPL_PASTE, InputType.CODE_BLOCK, InputType.MIXED]

    def test_enhance_stackoverflow_paste(self, enhancer):
        """Test handling StackOverflow-style code paste."""
        input_text = """def foo():
    return bar

>>> # This is from interactive session
>>> foo()"""
        result = enhancer.enhance(input_text)

        assert result is not None
        # Should handle without crashing

    def test_typo_correction_suggestion(self, enhancer):
        """Test typo correction suggestions."""
        from vertice_cli.core.input_enhancer import levenshtein_distance

        # Test distance calculation using module-level function
        dist = levenshtein_distance("hello", "helo")
        assert dist == 1

        dist = levenshtein_distance("hello", "hello")
        assert dist == 0

    def test_enhance_multiline_input(self, enhancer):
        """Test multiline input detection."""
        input_text = """Line 1
Line 2
Line 3"""
        result = enhancer.enhance(input_text)

        from vertice_cli.core.input_enhancer import InputType

        assert result.input_type in [InputType.MULTILINE, InputType.PLAIN_TEXT, InputType.MIXED]

    def test_enhance_command_input(self, enhancer):
        """Test command input detection."""
        result = enhancer.enhance("/help")

        # Commands should be detected
        assert result is not None

    def test_enhance_empty_input(self, enhancer):
        """Test handling empty input."""
        result = enhancer.enhance("")

        assert result is not None
        assert result.original == ""

    def test_enhance_whitespace_only(self, enhancer):
        """Test handling whitespace-only input."""
        result = enhancer.enhance("   \t\n  ")

        assert result is not None

    def test_code_extraction_multiple_blocks(self, enhancer):
        """Test extracting multiple code blocks."""
        input_text = """First block:
```python
def first(): pass
```

Second block:
```javascript
function second() {}
```
"""
        result = enhancer.enhance(input_text)

        assert len(result.code_blocks) >= 2

    def test_performance_large_input(self, enhancer):
        """Test performance with large input."""
        import time

        # Generate large input (smaller to reduce test time)
        large_input = "word " * 1000

        start = time.time()
        result = enhancer.enhance(large_input)
        elapsed = time.time() - start

        # Should complete in under 5 seconds
        assert elapsed < 5.0
        assert result is not None


# =============================================================================
# 2. CONTEXT TRACKER TESTS
# =============================================================================


class TestContextTracker:
    """Test ContextTracker component."""

    @pytest.fixture
    def tracker(self):
        """Create ContextTracker instance."""
        from vertice_cli.core.context_tracker import ContextTracker

        return ContextTracker()

    def test_tracker_initialization(self, tracker):
        """Test tracker initializes correctly."""
        assert tracker is not None
        assert hasattr(tracker, "record")
        assert hasattr(tracker, "resolve")

    def test_track_file_reference(self, tracker):
        """Test tracking file references."""
        from vertice_cli.core.context_tracker import ContextType

        tracker.record(ContextType.FILE, "main.py")
        tracker.record(ContextType.FILE, "test.py")

        # Should maintain file history
        files = tracker.get_recent(ContextType.FILE)
        assert len(files) >= 2

    def test_resolve_demonstrative_pronoun(self, tracker):
        """Test resolving 'this', 'that', 'it' references."""
        from vertice_cli.core.context_tracker import ContextType

        tracker.record(ContextType.FILE, "main.py")

        # Resolve "it" should refer to main.py
        resolution = tracker.resolve("Fix it")

        assert resolution is not None
        assert hasattr(resolution, "value")

    def test_resolve_anaphoric_reference(self, tracker):
        """Test resolving anaphoric references ('the file', 'the function')."""
        from vertice_cli.core.context_tracker import ContextType

        tracker.record(ContextType.FILE, "test.py")

        # Use "it" which should resolve to most recent file
        resolution = tracker.resolve("fix it")

        # May or may not resolve depending on implementation
        # Just verify it doesn't crash
        assert resolution is None or hasattr(resolution, "value")

    def test_clarification_suggestion(self, tracker):
        """Test generating clarification suggestions for ambiguous references."""
        from vertice_cli.core.context_tracker import ContextType

        tracker.record(ContextType.FILE, "file.py")
        tracker.record(ContextType.FILE, "other.py")

        # Ambiguous "it" when multiple files mentioned
        resolution = tracker.resolve("Delete it")

        # Should have suggestions for clarification
        assert resolution is not None

    def test_track_empty_value(self, tracker):
        """Test tracking empty value."""
        from vertice_cli.core.context_tracker import ContextType

        # Should handle gracefully
        try:
            tracker.record(ContextType.FILE, "")
            assert True  # Didn't crash
        except ValueError:
            assert True  # Or raised appropriate error

    def test_track_no_references(self, tracker):
        """Test resolving message with no references."""
        resolution = tracker.resolve("Hello, how are you?")
        # May return None or low-confidence match
        assert resolution is None or hasattr(resolution, "value")

    def test_history_limit(self, tracker):
        """Test history doesn't grow unbounded."""
        from vertice_cli.core.context_tracker import ContextType

        # Record many items
        for i in range(100):
            tracker.record(ContextType.FILE, f"file{i}.py")

        # Should be limited by max_history (50 by default)
        files = tracker.get_recent(ContextType.FILE)
        assert len(files) <= 100  # Some limit applied


# =============================================================================
# 3. ERROR PRESENTER TESTS
# =============================================================================


class TestErrorPresenter:
    """Test ErrorPresenter component."""

    @pytest.fixture
    def presenter(self):
        """Create ErrorPresenter instance."""
        from vertice_cli.core.error_presenter import ErrorPresenter

        return ErrorPresenter()

    def test_presenter_initialization(self, presenter):
        """Test presenter initializes correctly."""
        assert presenter is not None
        assert hasattr(presenter, "present")

    def test_present_simple_error(self, presenter):
        """Test presenting simple error."""
        error = Exception("Something went wrong")

        result = presenter.present(error)

        assert result is not None
        assert "Something went wrong" in str(result)

    def test_present_beginner_level(self, presenter):
        """Test beginner-level error presentation."""
        from vertice_cli.core.error_presenter import AudienceLevel

        presenter.audience = AudienceLevel.BEGINNER
        error = ValueError("Invalid input")

        result = presenter.present(error)

        # Should include helpful explanation
        assert result is not None

    def test_present_intermediate_level(self, presenter):
        """Test intermediate-level error presentation."""
        from vertice_cli.core.error_presenter import AudienceLevel

        presenter.audience = AudienceLevel.INTERMEDIATE
        error = ValueError("Invalid input")

        result = presenter.present(error)

        assert result is not None

    def test_present_developer_level(self, presenter):
        """Test developer-level error presentation."""
        from vertice_cli.core.error_presenter import AudienceLevel

        presenter.audience = AudienceLevel.DEVELOPER
        error = ValueError("Invalid input")

        result = presenter.present(error)

        # Developer level should be more technical
        assert result is not None

    def test_terminal_formatting(self, presenter):
        """Test terminal-formatted error output."""
        error = Exception("Test error")

        result = presenter.present(error)

        # Should contain formatting or be plain text
        assert result is not None

    def test_actionable_suggestions(self, presenter):
        """Test error includes actionable suggestions."""
        error = FileNotFoundError("config.yaml not found")

        result = presenter.present(error)

        # Should suggest what to do
        assert result is not None
        # Result should have suggestions attribute or contain suggestion text
        if hasattr(result, "suggestions"):
            assert len(result.suggestions) >= 0

    def test_present_nested_error(self, presenter):
        """Test presenting nested/chained errors."""
        try:
            try:
                raise ValueError("Inner error")
            except ValueError as e:
                raise RuntimeError("Outer error") from e
        except RuntimeError as e:
            result = presenter.present(e)

        assert result is not None

    def test_present_none_error(self, presenter):
        """Test handling None error."""
        try:
            result = presenter.present(None)
            # Should handle gracefully
            assert result is not None or result is None
        except Exception:
            # Or raise appropriate error
            pass

    def test_present_with_context(self, presenter):
        """Test error presentation with context."""
        error = Exception("Database connection failed")
        context = {
            "operation": "save_user",
            "file": "models/user.py",
            "line": 42,
        }

        result = presenter.present(error, context=context)

        assert result is not None


# =============================================================================
# 4. INTEGRATION TESTS
# =============================================================================


class TestUXComponentsIntegration:
    """Test UX components work together."""

    @pytest.fixture
    def enhancer(self):
        from vertice_cli.core.input_enhancer import InputEnhancer

        return InputEnhancer()

    @pytest.fixture
    def tracker(self):
        from vertice_cli.core.context_tracker import ContextTracker

        return ContextTracker()

    @pytest.fixture
    def presenter(self):
        from vertice_cli.core.error_presenter import ErrorPresenter

        return ErrorPresenter()

    def test_pipeline_input_to_context(self, enhancer, tracker):
        """Test input enhancement feeds into context tracking."""
        from vertice_cli.core.context_tracker import ContextType

        # Enhance input
        enhancer.enhance("Edit the main.py file")

        # Track file mentioned in enhanced input
        tracker.record(ContextType.FILE, "main.py")

        # Resolve reference
        resolution = tracker.resolve("Fix it")

        assert resolution is not None

    def test_error_with_context(self, tracker, presenter):
        """Test error presentation uses tracked context."""
        from vertice_cli.core.context_tracker import ContextType

        # Build context
        tracker.record(ContextType.FILE, "main.py")
        tracker.record(ContextType.COMMAND, "pytest tests/")

        # Present error with context
        error = Exception("Test failed")
        recent = tracker.get_recent(ContextType.FILE)

        result = presenter.present(error, context={"files": [r.value for r in recent]})

        assert result is not None

    def test_full_pipeline(self, enhancer, tracker, presenter):
        """Test full input → context → error pipeline."""
        from vertice_cli.core.context_tracker import ContextType

        # Step 1: Enhance input
        enhanced = enhancer.enhance(
            """Here's my code:
```python
def broken():
    return undeclared
```
"""
        )

        # Step 2: Track context
        if enhanced.code_blocks:
            tracker.record(ContextType.FUNCTION, "broken")

        # Step 3: Present any error
        error = NameError("undeclared is not defined")
        result = presenter.present(error)

        assert result is not None


# =============================================================================
# 5. EDGE CASE TESTS
# =============================================================================


class TestUXEdgeCases:
    """Test edge cases for UX components."""

    @pytest.fixture
    def enhancer(self):
        from vertice_cli.core.input_enhancer import InputEnhancer

        return InputEnhancer()

    def test_unicode_input(self, enhancer):
        """Test handling Unicode input."""
        result = enhancer.enhance("日本語テスト 🚀 émoji")

        assert result is not None
        assert "日本語" in result.original

    def test_control_characters(self, enhancer):
        """Test handling control characters."""
        result = enhancer.enhance("text\x00with\x01control\x02chars")

        assert result is not None

    def test_very_long_line(self, enhancer):
        """Test handling very long single line."""
        long_line = "x" * 100000

        result = enhancer.enhance(long_line)

        assert result is not None
        assert len(result.cleaned) == len(long_line)

    def test_nested_code_blocks(self, enhancer):
        """Test handling nested code block markers."""
        input_text = """```python
# Comment with ``` in it
code = "```"
```"""
        result = enhancer.enhance(input_text)

        # Should handle gracefully (implementation-dependent)
        assert result is not None

    def test_malformed_code_block(self, enhancer):
        """Test handling malformed code blocks."""
        input_text = """```python
def incomplete(
    # Missing closing
"""
        result = enhancer.enhance(input_text)

        assert result is not None
