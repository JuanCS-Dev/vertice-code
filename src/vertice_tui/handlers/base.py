"""
BaseHandler - Common functionality for all command handlers.

Phase 5.2 TUI Lightweight - Handler Optimization.

Provides:
- Common initialization pattern
- Bridge access property
- Command routing logic
- Utility methods for displaying messages

References:
- Google Style: https://google.github.io/styleguide/pyguide.html
- DRY Principle: Don't Repeat Yourself

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Coroutine, Dict, Optional

if TYPE_CHECKING:
    from vertice_tui.app import QwenApp
    from vertice_tui.widgets.response_view import ResponseView

# Type alias for handler methods
HandlerMethod = Callable[[str, "ResponseView"], Coroutine[Any, Any, None]]


class BaseHandler(ABC):
    """
    Abstract base class for command handlers.

    Provides common functionality:
    - App and bridge access
    - Command routing
    - Message display utilities
    - Error handling

    Usage:
        class MyHandler(BaseHandler):
            def _get_handlers(self) -> Dict[str, HandlerMethod]:
                return {
                    "/mycommand": self._handle_mycommand,
                }

            async def _handle_mycommand(self, args: str, view: "ResponseView") -> None:
                self.show_success(view, "Done!", "Command executed")
    """

    def __init__(self, app: "QwenApp") -> None:
        """Initialize handler with app reference.

        Args:
            app: The main TUI application
        """
        self.app = app

    @property
    def bridge(self) -> Any:
        """Get the bridge instance for API access."""
        return self.app.bridge

    @abstractmethod
    def _get_handlers(self) -> Dict[str, HandlerMethod]:
        """Get mapping of commands to handler methods.

        Returns:
            Dict mapping command strings to async handler methods
        """
        pass

    async def handle(
        self,
        command: str,
        args: str,
        view: "ResponseView",
    ) -> bool:
        """Route command to appropriate handler method.

        Args:
            command: The command string (e.g., "/help")
            args: Arguments after the command
            view: ResponseView for output

        Returns:
            True if command was handled, False otherwise
        """
        handlers = self._get_handlers()
        handler = handlers.get(command)

        if handler:
            await handler(args, view)
            return True

        return False

    def can_handle(self, command: str) -> bool:
        """Check if this handler can process the given command.

        Args:
            command: The command to check

        Returns:
            True if this handler handles the command
        """
        return command in self._get_handlers()

    # =========================================================================
    # UTILITY METHODS FOR DISPLAYING MESSAGES
    # =========================================================================

    def show_success(
        self,
        view: "ResponseView",
        title: str,
        message: str,
        icon: str = "✅",
    ) -> None:
        """Display a success message.

        Args:
            view: ResponseView for output
            title: Message title
            message: Message body
            icon: Icon to display (default: ✅)
        """
        view.add_system_message(f"## {icon} {title}\n\n{message}")

    def show_error(
        self,
        view: "ResponseView",
        title: str,
        error: str,
        suggestion: Optional[str] = None,
        icon: str = "❌",
    ) -> None:
        """Display an error message.

        Args:
            view: ResponseView for output
            title: Error title
            error: Error description
            suggestion: Optional suggestion for fixing
            icon: Icon to display (default: ❌)
        """
        msg = f"## {icon} {title}\n\n{error}"
        if suggestion:
            msg += f"\n\n💡 {suggestion}"
        view.add_system_message(msg)

    def show_info(
        self,
        view: "ResponseView",
        title: str,
        message: str,
        icon: str = "ℹ️",
    ) -> None:
        """Display an info message.

        Args:
            view: ResponseView for output
            title: Message title
            message: Message body
            icon: Icon to display (default: ℹ️)
        """
        view.add_system_message(f"## {icon} {title}\n\n{message}")

    def show_warning(
        self,
        view: "ResponseView",
        title: str,
        message: str,
        icon: str = "⚠️",
    ) -> None:
        """Display a warning message.

        Args:
            view: ResponseView for output
            title: Warning title
            message: Warning body
            icon: Icon to display (default: ⚠️)
        """
        view.add_system_message(f"## {icon} {title}\n\n{message}")

    def show_list(
        self,
        view: "ResponseView",
        title: str,
        items: list,
        icon: str = "📋",
        numbered: bool = False,
    ) -> None:
        """Display a list of items.

        Args:
            view: ResponseView for output
            title: List title
            items: List of items to display
            icon: Icon to display (default: 📋)
            numbered: Use numbered list (default: bullet points)
        """
        if numbered:
            formatted = "\n".join(f"{i+1}. {item}" for i, item in enumerate(items))
        else:
            formatted = "\n".join(f"- {item}" for item in items)

        view.add_system_message(f"## {icon} {title}\n\n{formatted}")

    def show_table(
        self,
        view: "ResponseView",
        title: str,
        headers: list,
        rows: list,
        icon: str = "📊",
    ) -> None:
        """Display a simple table.

        Args:
            view: ResponseView for output
            title: Table title
            headers: Column headers
            rows: List of row tuples/lists
            icon: Icon to display (default: 📊)
        """
        # Header row
        header_row = " | ".join(str(h) for h in headers)
        separator = " | ".join("-" * len(str(h)) for h in headers)

        # Data rows
        data_rows = "\n".join(" | ".join(str(cell) for cell in row) for row in rows)

        table = f"{header_row}\n{separator}\n{data_rows}"
        view.add_system_message(f"## {icon} {title}\n\n{table}")

    # =========================================================================
    # ARGUMENT PARSING UTILITIES
    # =========================================================================

    def parse_args(self, args: str) -> list:
        """Parse space-separated arguments.

        Args:
            args: Raw argument string

        Returns:
            List of argument strings
        """
        return args.split() if args else []

    def parse_key_value(self, args: str) -> Dict[str, str]:
        """Parse key=value arguments.

        Args:
            args: Raw argument string (e.g., "key1=val1 key2=val2")

        Returns:
            Dict of key-value pairs
        """
        result: Dict[str, str] = {}
        for part in self.parse_args(args):
            if "=" in part:
                key, value = part.split("=", 1)
                result[key.strip()] = value.strip()
        return result

    def get_first_arg(self, args: str, default: Optional[str] = None) -> Optional[str]:
        """Get the first argument.

        Args:
            args: Raw argument string
            default: Default value if no args

        Returns:
            First argument or default
        """
        parts = self.parse_args(args)
        return parts[0] if parts else default

    def get_int_arg(
        self,
        args: str,
        default: int = 0,
        index: int = 0,
    ) -> int:
        """Get an integer argument.

        Args:
            args: Raw argument string
            default: Default value if not valid
            index: Index of argument to get

        Returns:
            Integer value or default
        """
        parts = self.parse_args(args)
        if len(parts) > index:
            try:
                return int(parts[index])
            except ValueError:
                pass
        return default
