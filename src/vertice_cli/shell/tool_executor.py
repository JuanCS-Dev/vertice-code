"""
shell/tool_executor.py: Tool Execution with Recovery.

Extracted from shell_main.py for modularity.
Handles tool execution, error recovery, and result formatting.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from rich.console import Console
    from ..tools.base import ToolRegistry
    from ..core.conversation import ConversationManager
    from ..core.recovery import ErrorRecoveryEngine

logger = logging.getLogger(__name__)


@dataclass
class ExecutionAttempt:
    """Result of a single tool execution attempt."""

    success: bool
    result: Any
    attempt_number: int
    recovered: bool = False


class ToolExecutor:
    """
    Handles tool execution with error recovery.

    Features:
    - Multi-attempt execution with recovery
    - Conversation tracking integration
    - Result formatting for various tool types
    """

    def __init__(
        self,
        registry: "ToolRegistry",
        recovery_engine: "ErrorRecoveryEngine",
        conversation: "ConversationManager",
        console: "Console",
        max_attempts: int = 2,
    ):
        self.registry = registry
        self.recovery_engine = recovery_engine
        self.conversation = conversation
        self.console = console
        self.max_attempts = max_attempts

    async def execute_with_recovery(
        self,
        tool,
        tool_name: str,
        args: Dict[str, Any],
        turn: Any,
    ) -> Optional[Any]:
        """
        Execute tool with error recovery.

        Args:
            tool: The tool instance to execute
            tool_name: Name of the tool
            args: Arguments to pass to the tool
            turn: Conversation turn for tracking

        Returns:
            Tool result or None if all attempts failed
        """
        for attempt in range(1, self.max_attempts + 1):
            result, success = await self._attempt_execution(tool, tool_name, args, turn, attempt)

            if success:
                if attempt > 1:
                    self.console.print(f"[green]✓ Recovered on attempt {attempt}[/green]")
                return result

            # Try recovery if not last attempt
            if attempt < self.max_attempts:
                corrected_args = await self._handle_failure(tool_name, args, result, turn, attempt)
                if corrected_args:
                    args = corrected_args
            else:
                self.console.print(
                    f"[red]✗ {tool_name} failed after {self.max_attempts} attempts[/red]"
                )
                return None

        return None

    async def _attempt_execution(
        self,
        tool,
        tool_name: str,
        args: Dict[str, Any],
        turn: Any,
        attempt: int,
    ) -> tuple[Any, bool]:
        """Execute single tool attempt and track result."""
        try:
            result = await tool.execute(**args)

            # Track in conversation
            self.conversation.add_tool_result(
                turn,
                tool_name,
                args,
                result,
                success=result.success,
                error=None if result.success else str(result.data),
            )

            return result, result.success

        except Exception as e:
            logger.error(f"Tool {tool_name} raised exception: {e}")

            # Track exception
            self.conversation.add_tool_result(
                turn,
                tool_name,
                args,
                None,
                success=False,
                error=str(e),
            )

            # Create error result
            @dataclass
            class ErrorResult:
                success: bool = False
                data: str = str(e)

            return ErrorResult(), False

    async def _handle_failure(
        self,
        tool_name: str,
        args: Dict[str, Any],
        result: Any,
        turn: Any,
        attempt: int,
    ) -> Optional[Dict[str, Any]]:
        """Handle tool execution failure and attempt recovery."""
        from ..core.recovery import create_recovery_context, ErrorCategory

        error_msg = str(result.data) if result else "Unknown error"

        self.console.print(
            f"[yellow]Attempting recovery for {tool_name} "
            f"(attempt {attempt}/{self.max_attempts})[/yellow]"
        )

        try:
            # Build recovery context
            recovery_ctx = create_recovery_context(
                error=error_msg,
                tool_name=tool_name,
                args=args,
                category=ErrorCategory.PARAMETER_ERROR,
            )

            # Get diagnosis from LLM
            diagnosis = await self.recovery_engine.diagnose_error(
                recovery_ctx,
                self.conversation.get_recent_context(max_turns=3),
            )

            if diagnosis:
                self.console.print(f"[dim]Diagnosis: {diagnosis}[/dim]")

            # Attempt parameter correction
            corrected = await self.recovery_engine.attempt_recovery(recovery_ctx, self.registry)

            if corrected and "args" in corrected:
                self.console.print("[green]✓ Generated corrected parameters[/green]")
                return corrected["args"]
            else:
                self.console.print("[yellow]No correction found[/yellow]")
                return None

        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            self.console.print(f"[red]Recovery error: {e}[/red]")
            return None

    async def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        turn: Any,
        context: Any,
    ) -> List[str]:
        """
        Execute a sequence of tool calls.

        Args:
            tool_calls: List of tool call dicts with 'tool' and 'args'
            turn: Conversation turn for tracking
            context: SessionContext for tracking

        Returns:
            List of result strings
        """
        results: List[str] = []

        for i, call in enumerate(tool_calls):
            tool_name = call.get("tool", "")
            args = call.get("args", {})

            tool = self.registry.get(tool_name)
            if not tool:
                error_msg = f"Unknown tool: {tool_name}"
                results.append(f"❌ {error_msg}")

                # Track tool failure
                self.conversation.add_tool_result(
                    turn,
                    tool_name,
                    args,
                    None,
                    success=False,
                    error=error_msg,
                )
                continue

            # Execute tool with recovery
            result = await self.execute_with_recovery(tool, tool_name, args, turn)

            if not result:
                results.append(f"❌ {tool_name} failed after recovery attempts")
                continue

            # Track in context
            context.track_tool_call(tool_name, args, result)

            # Format result
            if result.success:
                formatted = self._format_result(tool_name, result, args)
                results.append(formatted)
            else:
                results.append(f"❌ {result.error}")

        return results

    def _format_result(
        self,
        tool_name: str,
        result: Any,
        args: Dict[str, Any],
    ) -> str:
        """Format tool result for display."""

        formatters = {
            "read_file": lambda r: f"✓ Read {r.metadata.get('path', 'file')} ({r.metadata.get('lines', '?')} lines)",
            "search_files": lambda r: f"✓ Found {r.metadata.get('count', 0)} matches",
            "bash_command": lambda r: f"✓ Exit code: {r.data.get('exit_code', 0)}",
            "git_status": lambda _: "✓ Git status retrieved",
            "git_diff": lambda r: "✓ Diff shown" if r.data else "No changes",
            "ls": lambda r: f"✓ {r.metadata.get('count', 0)} items",
            "pwd": lambda _: "✓ Current directory shown",
            "cd": lambda r: f"✓ {r.data}",
            "cat": lambda r: f"✓ Displayed {r.metadata.get('lines', '?')} lines",
        }

        if tool_name in ("write_file", "edit_file"):
            msg = f"✓ {result.data}"
            if result.metadata.get("backup"):
                msg += f"\n  Backup: {result.metadata['backup']}"
            return msg

        if tool_name == "list_directory":
            f_count = result.metadata.get("file_count", 0)
            d_count = result.metadata.get("dir_count", 0)
            return f"✓ Listed {f_count} files, {d_count} directories"

        formatter = formatters.get(tool_name)
        if formatter:
            return formatter(result)

        return f"✓ {result.data}"
