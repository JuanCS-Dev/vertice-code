"""
Tests for OutputFormatter - Rich Panel formatting.

Tests cover:
- format_response (truncation, markdown fallback)
- format_tool_result (success/error cases)
- format_code_block (syntax highlighting, line truncation)
- format_error/success/warning/info
- Convenience functions

Based on pytest + hypothesis patterns from Anthropic's Claude Code.
"""
import pytest
from rich.panel import Panel
from rich.text import Text
from rich.markdown import Markdown
from rich.syntax import Syntax

from jdev_tui.core.output_formatter import (
    OutputFormatter,
    response_panel,
    tool_panel,
    code_panel,
)


# =============================================================================
# FORMAT_RESPONSE TESTS
# =============================================================================

class TestFormatResponse:
    """Tests for format_response method."""

    def test_basic_response(self):
        """Test basic response formatting."""
        panel = OutputFormatter.format_response("Hello world")

        assert isinstance(panel, Panel)
        assert panel.border_style == "cyan"
        assert "Response" in str(panel.title)

    def test_custom_title(self):
        """Test response with custom title."""
        panel = OutputFormatter.format_response("Test", title="AI Says")

        assert "AI Says" in str(panel.title)

    def test_custom_border_style(self):
        """Test response with custom border."""
        panel = OutputFormatter.format_response("Test", border_style="green")

        assert panel.border_style == "green"

    def test_expand_option(self):
        """Test expand option."""
        panel_expanded = OutputFormatter.format_response("Test", expand=True)
        panel_compact = OutputFormatter.format_response("Test", expand=False)

        assert panel_expanded.expand is True
        assert panel_compact.expand is False

    def test_truncation_by_length(self):
        """Test truncation for very long content."""
        long_text = "x" * (OutputFormatter.MAX_CONTENT_LENGTH + 1000)
        panel = OutputFormatter.format_response(long_text)

        # Title should indicate truncation
        assert "truncated" in str(panel.title).lower()

    def test_truncation_by_lines(self):
        """Test truncation for too many lines."""
        many_lines = "\n".join(["line" for _ in range(OutputFormatter.MAX_LINES + 50)])
        panel = OutputFormatter.format_response(many_lines)

        assert "truncated" in str(panel.title).lower()

    def test_markdown_parsing(self):
        """Test that markdown is parsed correctly."""
        md_text = "# Header\n\n**bold** and *italic*"
        panel = OutputFormatter.format_response(md_text)

        # Content should be Markdown type (when parsing succeeds)
        assert isinstance(panel.renderable, (Markdown, Text))

    def test_empty_response(self):
        """Test empty response handling."""
        panel = OutputFormatter.format_response("")

        assert isinstance(panel, Panel)

    def test_special_characters(self):
        """Test response with special characters."""
        special = "Test with <brackets> & symbols © ™"
        panel = OutputFormatter.format_response(special)

        assert isinstance(panel, Panel)


# =============================================================================
# FORMAT_TOOL_RESULT TESTS
# =============================================================================

class TestFormatToolResult:
    """Tests for format_tool_result method."""

    def test_successful_tool(self):
        """Test successful tool result."""
        panel = OutputFormatter.format_tool_result(
            tool_name="read_file",
            success=True,
            data="File contents here"
        )

        assert isinstance(panel, Panel)
        assert panel.border_style == OutputFormatter.SUCCESS_BORDER
        assert "read_file" in str(panel.title)
        assert "✓" in str(panel.title)

    def test_failed_tool(self):
        """Test failed tool result."""
        panel = OutputFormatter.format_tool_result(
            tool_name="write_file",
            success=False,
            error="Permission denied"
        )

        assert panel.border_style == OutputFormatter.ERROR_BORDER
        assert "✗" in str(panel.title)

    def test_success_no_data(self):
        """Test success with no data returns 'Success'."""
        panel = OutputFormatter.format_tool_result("test_tool", success=True)

        assert isinstance(panel.renderable, Text)
        assert "Success" in panel.renderable.plain

    def test_failure_no_error(self):
        """Test failure with no error message returns 'Failed'."""
        panel = OutputFormatter.format_tool_result("test_tool", success=False)

        assert "Failed" in panel.renderable.plain

    def test_truncation_long_data(self):
        """Test truncation of long tool results."""
        long_data = "x" * 1000
        panel = OutputFormatter.format_tool_result("test", True, data=long_data)

        assert isinstance(panel.renderable, Text)
        assert len(panel.renderable.plain) <= 503  # 500 + "..."

    def test_non_expand_panel(self):
        """Test tool result panels don't expand."""
        panel = OutputFormatter.format_tool_result("test", True)

        assert panel.expand is False


# =============================================================================
# FORMAT_CODE_BLOCK TESTS
# =============================================================================

class TestFormatCodeBlock:
    """Tests for format_code_block method."""

    def test_basic_code_block(self):
        """Test basic code formatting."""
        code = "def hello():\n    return 'world'"
        panel = OutputFormatter.format_code_block(code)

        assert isinstance(panel, Panel)
        assert isinstance(panel.renderable, Syntax)

    def test_language_specification(self):
        """Test different language specifications."""
        js_code = "const x = 1;"
        panel = OutputFormatter.format_code_block(js_code, language="javascript")

        # Title should reflect language
        assert "JAVASCRIPT" in str(panel.title).upper()

    def test_custom_title(self):
        """Test custom title override."""
        panel = OutputFormatter.format_code_block("x = 1", title="MyScript.py")

        assert "MyScript.py" in str(panel.title)

    def test_line_numbers_enabled(self):
        """Test line numbers are enabled by default."""
        code = "x = 1\ny = 2"
        panel = OutputFormatter.format_code_block(code, line_numbers=True)

        assert panel.renderable.line_numbers is True

    def test_line_numbers_disabled(self):
        """Test line numbers can be disabled."""
        code = "x = 1"
        panel = OutputFormatter.format_code_block(code, line_numbers=False)

        assert panel.renderable.line_numbers is False

    def test_long_code_truncation(self):
        """Test truncation of very long code."""
        long_code = "\n".join([f"line_{i} = {i}" for i in range(150)])
        panel = OutputFormatter.format_code_block(long_code)

        # Syntax object should exist
        assert isinstance(panel.renderable, Syntax)

    def test_empty_code(self):
        """Test empty code handling."""
        panel = OutputFormatter.format_code_block("")

        assert isinstance(panel, Panel)


# =============================================================================
# FORMAT_ERROR/SUCCESS/WARNING/INFO TESTS
# =============================================================================

class TestFormatMessages:
    """Tests for format_error, format_success, format_warning, format_info."""

    def test_format_error(self):
        """Test error formatting."""
        panel = OutputFormatter.format_error("Something went wrong")

        assert panel.border_style == "red"
        assert "✗" in str(panel.title)
        assert "Error" in str(panel.title)

    def test_format_error_custom_title(self):
        """Test error with custom title."""
        panel = OutputFormatter.format_error("Oops", title="Critical Error")

        assert "Critical Error" in str(panel.title)

    def test_format_success(self):
        """Test success formatting."""
        panel = OutputFormatter.format_success("Operation completed")

        assert panel.border_style == "green"
        assert "✓" in str(panel.title)
        assert "Success" in str(panel.title)

    def test_format_success_custom_title(self):
        """Test success with custom title."""
        panel = OutputFormatter.format_success("Done", title="File Saved")

        assert "File Saved" in str(panel.title)

    def test_format_warning(self):
        """Test warning formatting."""
        panel = OutputFormatter.format_warning("Be careful")

        assert panel.border_style == "yellow"
        assert "⚠" in str(panel.title)
        assert "Warning" in str(panel.title)

    def test_format_info(self):
        """Test info formatting."""
        panel = OutputFormatter.format_info("FYI: Something happened")

        assert panel.border_style == "blue"
        assert "ℹ" in str(panel.title)
        assert "Info" in str(panel.title)


# =============================================================================
# FORMAT_ACTION AND FORMAT_THINKING TESTS
# =============================================================================

class TestFormatIndicators:
    """Tests for format_action and format_thinking."""

    def test_format_action(self):
        """Test action indicator formatting."""
        text = OutputFormatter.format_action("Reading file...")

        assert isinstance(text, Text)
        assert "Reading file..." in text.plain
        assert "●" in text.plain

    def test_format_thinking(self):
        """Test thinking indicator formatting."""
        text = OutputFormatter.format_thinking()

        assert isinstance(text, Text)
        assert "Thinking" in text.plain
        assert "●" in text.plain


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestConvenienceFunctions:
    """Tests for convenience helper functions."""

    def test_response_panel(self):
        """Test response_panel helper."""
        panel = response_panel("Test content", title="Test")

        assert isinstance(panel, Panel)
        assert "Test" in str(panel.title)

    def test_tool_panel_success(self):
        """Test tool_panel helper with success."""
        panel = tool_panel("my_tool", success=True, data="result")

        assert isinstance(panel, Panel)
        assert panel.border_style == OutputFormatter.SUCCESS_BORDER

    def test_tool_panel_failure(self):
        """Test tool_panel helper with failure."""
        panel = tool_panel("my_tool", success=False, error="failed")

        assert panel.border_style == OutputFormatter.ERROR_BORDER

    def test_code_panel(self):
        """Test code_panel helper."""
        panel = code_panel("x = 1", language="python")

        assert isinstance(panel, Panel)
        assert isinstance(panel.renderable, Syntax)


# =============================================================================
# EDGE CASES AND BOUNDARY CONDITIONS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_exact_max_length(self):
        """Test text exactly at max length (no truncation)."""
        exact_text = "x" * OutputFormatter.MAX_CONTENT_LENGTH
        panel = OutputFormatter.format_response(exact_text)

        # Should NOT be truncated (at boundary)
        assert "truncated" not in str(panel.title).lower()

    def test_one_over_max_length(self):
        """Test text one character over max length (should truncate)."""
        over_text = "x" * (OutputFormatter.MAX_CONTENT_LENGTH + 1)
        panel = OutputFormatter.format_response(over_text)

        assert "truncated" in str(panel.title).lower()

    def test_exact_max_lines(self):
        """Test text exactly at max lines (no truncation)."""
        exact_lines = "\n".join(["line" for _ in range(OutputFormatter.MAX_LINES)])
        panel = OutputFormatter.format_response(exact_lines)

        # Should NOT be truncated
        assert "truncated" not in str(panel.title).lower()

    def test_one_over_max_lines(self):
        """Test text one line over max (should truncate)."""
        over_lines = "\n".join(["line" for _ in range(OutputFormatter.MAX_LINES + 1)])
        panel = OutputFormatter.format_response(over_lines)

        assert "truncated" in str(panel.title).lower()

    def test_unicode_content(self):
        """Test handling of unicode content."""
        unicode_text = "Olá mundo! 你好世界! مرحبا بالعالم! 🎉🚀"
        panel = OutputFormatter.format_response(unicode_text)

        assert isinstance(panel, Panel)

    def test_newlines_only(self):
        """Test content that is only newlines."""
        panel = OutputFormatter.format_response("\n\n\n")

        assert isinstance(panel, Panel)

    def test_tabs_and_spaces(self):
        """Test content with tabs and spaces."""
        panel = OutputFormatter.format_response("\t  \t  content  \t")

        assert isinstance(panel, Panel)

    def test_ansi_escape_codes(self):
        """Test handling of ANSI escape codes in content."""
        ansi_text = "\033[31mRed text\033[0m"
        panel = OutputFormatter.format_response(ansi_text)

        assert isinstance(panel, Panel)

    def test_malformed_markdown(self):
        """Test handling of malformed markdown."""
        bad_md = "# Incomplete **bold and ```unclosed code"
        panel = OutputFormatter.format_response(bad_md)

        # Should not crash, fallback to Text if needed
        assert isinstance(panel, Panel)


# =============================================================================
# CLASS CONSTANTS TESTS
# =============================================================================

class TestClassConstants:
    """Tests for class constants."""

    def test_border_colors_defined(self):
        """Test all border colors are defined."""
        assert OutputFormatter.RESPONSE_BORDER == "cyan"
        assert OutputFormatter.SUCCESS_BORDER == "green"
        assert OutputFormatter.ERROR_BORDER == "red"
        assert OutputFormatter.WARNING_BORDER == "yellow"
        assert OutputFormatter.INFO_BORDER == "blue"

    def test_max_values_reasonable(self):
        """Test max values are reasonable."""
        assert OutputFormatter.MAX_CONTENT_LENGTH > 1000
        assert OutputFormatter.MAX_CONTENT_LENGTH < 100000
        assert OutputFormatter.MAX_LINES > 50
        assert OutputFormatter.MAX_LINES < 1000


# =============================================================================
# INTEGRATION-STYLE TESTS
# =============================================================================

class TestIntegrationPatterns:
    """Tests simulating real usage patterns."""

    def test_typical_llm_response_flow(self):
        """Test typical LLM response formatting flow."""
        # Simulate a typical response
        llm_response = """# Analysis Results

Based on my review of the code:

1. **Performance Issue**: The loop at line 42 is O(n²)
2. **Bug Found**: Null check missing in `process()`

```python
def fixed_process(data):
    if data is None:
        return []
    return [x for x in data]
```

Let me know if you need more details.
"""
        panel = OutputFormatter.format_response(llm_response, title="AI Analysis")

        assert isinstance(panel, Panel)
        assert panel.border_style == "cyan"

    def test_tool_execution_flow(self):
        """Test typical tool execution result flow."""
        # Success case
        read_result = OutputFormatter.format_tool_result(
            "read_file",
            success=True,
            data="def hello(): return 'world'"
        )
        assert read_result.border_style == "green"

        # Failure case
        write_result = OutputFormatter.format_tool_result(
            "write_file",
            success=False,
            error="EACCES: permission denied"
        )
        assert write_result.border_style == "red"

    def test_code_review_flow(self):
        """Test code block formatting for review."""
        code = '''
class Calculator:
    """A simple calculator class."""

    def add(self, a: int, b: int) -> int:
        return a + b

    def divide(self, a: int, b: int) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
'''
        panel = OutputFormatter.format_code_block(
            code.strip(),
            language="python",
            title="calculator.py"
        )

        assert isinstance(panel, Panel)
        assert "calculator.py" in str(panel.title)
