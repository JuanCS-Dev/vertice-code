"""
shell: Interactive Shell Package.

This package provides the interactive shell interface for qwen-dev-cli.

Modules:
- context: Session context management (SessionContext)
- safety: Command safety evaluation
- tool_executor: Tool execution with recovery
- executor: ShellExecutor for LLM-driven tool execution
- streaming_integration: Streaming response handling
- repl: REPL entry point

Usage:
    from qwen_dev_cli.shell import InteractiveShell, SessionContext
    from qwen_dev_cli.shell.safety import get_safety_level, is_dangerous
    from qwen_dev_cli.shell.tool_executor import ToolExecutor
"""

from .repl import main
from .context import SessionContext

# Export safety utilities
from .safety import (
    get_safety_level,
    is_safe,
    is_dangerous,
    needs_confirmation,
    SAFE_COMMANDS,
    DANGEROUS_COMMANDS,
)

# Export tool executor
from .tool_executor import ToolExecutor, ExecutionAttempt


def __getattr__(name: str):
    """
    Lazy import for InteractiveShell to avoid circular import.

    shell/__init__.py imports shell_main.InteractiveShell
    shell_main.py imports shell.context.SessionContext

    Using __getattr__ breaks the cycle.
    """
    if name == "InteractiveShell":
        from qwen_dev_cli.shell_main import InteractiveShell
        return InteractiveShell
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Main classes
    "main",
    "InteractiveShell",
    "SessionContext",
    # Tool execution
    "ToolExecutor",
    "ExecutionAttempt",
    # Safety
    "get_safety_level",
    "is_safe",
    "is_dangerous",
    "needs_confirmation",
    "SAFE_COMMANDS",
    "DANGEROUS_COMMANDS",
]
