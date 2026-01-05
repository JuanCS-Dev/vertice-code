"""
Unit tests for error handling in Vertice-Code handlers.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

# Assuming the handlers are in these locations
from vertice_cli.handlers.llm_processing_handler import LLMProcessingHandler
from vertice_cli.handlers.tool_execution_handler import ToolExecutionHandler
import vertice_cli.handlers.tool_execution_handler

import sys
from unittest.mock import patch

@pytest.mark.usefixtures("mock_shell")
class TestLLMProcessingHandlerErrors:
    """Tests for error handling in LLMProcessingHandler."""

    @pytest.mark.asyncio
    async def test_process_request_with_llm_connection_failure(self, mock_shell):
        """Test that LLM connection failure is handled gracefully."""
        # Arrange
        # NOTE: Using sys.modules to patch the late import in the handler.
        # This is a workaround for a pre-existing protobuf error in the test environment.
        streaming_mock = MagicMock()
        streaming_mock.stream_llm_response = AsyncMock(side_effect=RuntimeError("Connection failed"))
        sys.modules['vertice_cli.shell.streaming_integration'] = streaming_mock

        ai_patterns_mock = MagicMock()
        ai_patterns_mock.build_rich_context = MagicMock()
        sys.modules['vertice_cli.core.ai_patterns'] = ai_patterns_mock


        handler = LLMProcessingHandler(mock_shell)

        # Act
        await handler.process_request_with_llm("test input", None)

        # Assert
        mock_shell.console.print.assert_any_call("[red]❌ LLM failed: Connection failed[/red]")

        # Cleanup
        del sys.modules['vertice_cli.shell.streaming_integration']
        del sys.modules['vertice_cli.core.ai_patterns']

    @pytest.mark.asyncio
    async def test_get_command_suggestion_invalid_response(self, mock_shell):
        """Test that an invalid LLM response falls back to regex."""
        # Arrange
        handler = LLMProcessingHandler(mock_shell)
        mock_shell.llm.generate.side_effect = ConnectionError("LLM unavailable")

        # Act
        suggestion = await handler.get_command_suggestion("list large files", {})

        # Assert
        assert "find" in suggestion # Check for fallback
        mock_shell.console.print.assert_any_call("[yellow]⚠️  LLM unavailable, using fallback[/yellow]")


@pytest.mark.usefixtures("mock_shell")
class TestToolExecutionHandlerErrors:
    """Tests for error handling in ToolExecutionHandler."""

    @pytest.mark.asyncio
    async def test_execute_with_recovery_timeout(self, mock_shell):
        """Test that tool execution timeout is handled."""
        # Arrange
        handler = ToolExecutionHandler(mock_shell)
        tool = AsyncMock()
        tool.execute.side_effect = TimeoutError("Execution timed out")
        mock_shell.recovery_engine.max_attempts = 2
        mock_shell.recovery_engine.diagnose_error.return_value = "Timeout detected"
        mock_shell.recovery_engine.attempt_recovery.return_value = None  # Fail recovery

        # Act
        with patch.object(vertice_cli.handlers.tool_execution_handler, 'create_recovery_context', MagicMock()) as mock_create_context:
            result = await handler.execute_with_recovery(tool, "test_tool", {}, "turn")

        # Assert
        assert result is None
        mock_create_context.assert_called()
        assert tool.execute.call_count == 2
        mock_shell.console.print.assert_any_call("[red]x test_tool failed after 2 attempts[/red]")

    @pytest.mark.asyncio
    async def test_attempt_tool_execution_permission_denied(self, mock_shell):
        """Test that permission denied error is handled."""
        # Arrange
        handler = ToolExecutionHandler(mock_shell)
        tool = AsyncMock()
        tool.execute.side_effect = PermissionError("Permission denied")

        # Act
        result, success = await handler._attempt_tool_execution(tool, "test_tool", {}, "turn", 1)

        # Assert
        assert not success
        assert "Permission denied" in result.data
        mock_shell.conversation.add_tool_result.assert_called_with(
            "turn", "test_tool", {}, None, success=False, error="Permission denied"
        )
