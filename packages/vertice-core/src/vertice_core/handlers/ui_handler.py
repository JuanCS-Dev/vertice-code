"""
UIHandler - User Interface Display Operations.

SCALE & SUSTAIN Phase 1.7 - Semantic Modularization.

Handles:
- Welcome message display
- Help system display
- Metrics and cache statistics
- Command explanation
- File change notifications

Principles:
- Single Responsibility: UI/Display operations
- Semantic Clarity: All visual output in one place
- Scalability: Easy to add new UI components

Author: Vertice Team
Date: 2026-01-02
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_core.shell_main import InteractiveShell

logger = logging.getLogger(__name__)


class UIHandler:
    """
    Handler for user interface display operations.

    Manages:
    1. Welcome and help displays
    2. Metrics and statistics
    3. Command explanations
    4. File change notifications
    """

    def __init__(self, shell: "InteractiveShell"):
        """
        Initialize with shell reference.

        Args:
            shell: The InteractiveShell instance providing access to
                   console, registry, context, file_watcher, etc.
        """
        self.shell = shell
        self.console = shell.console
        self.registry = shell.registry
        self.context = shell.context
        self.file_watcher = shell.file_watcher
        self.recent_files = shell.recent_files

    # =========================================================================
    # Welcome and Help
    # =========================================================================

    def show_welcome(self) -> None:
        """Show welcome message with TUI styling."""
        from rich.text import Text
        from rich.panel import Panel
        from vertice_core.tui.styles import COLORS, PRESET_STYLES

        # Build styled welcome content
        content = Text()
        content.append("VÉRTICE Interactive Shell ", style=PRESET_STYLES.EMPHASIS)
        content.append("v1.0", style=PRESET_STYLES.SUCCESS)
        content.append("\n\n")
        content.append("🔧 Tools available: ", style=PRESET_STYLES.SECONDARY)
        content.append(f"{len(self.registry.get_all())}\n", style=PRESET_STYLES.INFO)
        content.append("📁 Working directory: ", style=PRESET_STYLES.SECONDARY)
        content.append(f"{self.context.cwd}\n\n", style=PRESET_STYLES.PATH)
        content.append("Type natural language commands or ", style=PRESET_STYLES.TERTIARY)
        content.append("/help", style=PRESET_STYLES.COMMAND)
        content.append(" for system commands", style=PRESET_STYLES.TERTIARY)

        welcome = Panel(
            content,
            title="[bold]🚀 Vertice AI-Powered Code Shell[/bold]",
            border_style=COLORS["accent_blue"],
            padding=(1, 2),
        )
        self.console.print(welcome)

    def show_help(self) -> None:
        """Show help message (Gemini: visual hierarchy)."""
        help_text = """
[bold cyan]Vértice - Sovereign Intelligence & Tactical Execution[/bold cyan]

[bold]Commands:[/bold]
  Just type what you want in natural language!

[bold]Examples:[/bold]
  • "list large files"
  • "find files modified today"
  • "show processes using most memory"

[bold]System commands:[/bold]
  • [cyan]help[/cyan]  - Show this help
  • [cyan]quit[/cyan]  - Exit shell
  • [cyan]/metrics[/cyan] - Show metrics
  • [cyan]/explain <cmd>[/cyan] - Explain a command

[bold]Safety:[/bold]
  ✓ Safe commands auto-execute (ls, pwd)
  ⚠️  AI-Safe commands ask confirmation (cp, mv)
  🚨 Dangerous commands double-confirm (rm, dd)

[dim]Operando sob a CONSTITUIÇÃO VÉRTICE v3.0[/dim]
"""
        self.console.print(help_text)

    # =========================================================================
    # Metrics and Statistics
    # =========================================================================

    def show_metrics(self) -> None:
        """Show constitutional metrics."""
        from vertice_core.core.metrics import generate_constitutional_report

        from vertice_core.core import get_temporal_context

        temporal = get_temporal_context()
        self.console.print(
            f"\n[bold cyan]🛡️ AI Constitutional Metrics ({temporal['date']})[/bold cyan]\n"
        )

        metrics = generate_constitutional_report(
            codebase_path="vertice_core", completeness=0.95, precision=0.98, recall=0.92
        )

        self.console.print(metrics.format_report())

    def show_cache_stats(self) -> None:
        """Show cache statistics."""
        from vertice_core.core.cache import get_cache

        cache = get_cache()
        stats = cache.stats

        self.console.print("\n[bold cyan]💾 Cache Statistics[/bold cyan]\n")
        self.console.print(f"Hits: {stats.hits}")
        self.console.print(f"Misses: {stats.misses}")
        self.console.print(f"Hit Rate: {stats.hit_rate:.1%}")
        self.console.print(f"Memory Hits: {stats.memory_hits}")
        self.console.print(f"Disk Hits: {stats.disk_hits}")

        # File watcher stats
        from vertice_core.core import get_temporal_context

        temporal = get_temporal_context()
        self.console.print(
            f"\n[bold cyan]👁️ AI File Watcher ({temporal['time'][:8]} UTC)[/bold cyan]\n"
        )
        self.console.print(f"Tracked Files: {self.file_watcher.tracked_files}")
        self.console.print(f"Recent Events: {len(self.file_watcher.recent_events)}")
        recent = self.recent_files.get_recent(5)
        if recent:
            self.console.print("\nRecent Files:")
            for f in recent:
                self.console.print(f"  • {f}")

    # =========================================================================
    # Command Explanation
    # =========================================================================

    async def handle_explain(self, command: str) -> None:
        """
        Explain a command.

        Args:
            command: The command to explain.
        """
        from vertice_core.core.ai_patterns import build_rich_context
        from vertice_core.shell.explain import explain_command

        if not command.strip():
            self.console.print("[yellow]Usage: /explain <command>[/yellow]")
            return

        # Build rich context
        context = build_rich_context(
            current_command=command, command_history=self.context.history[-10:], working_dir="."
        )

        # Get explanation
        explanation = explain_command(command, context)

        self.console.print(f"\n{explanation.format()}\n")

    # =========================================================================
    # File Change Handling
    # =========================================================================

    def on_file_changed(self, event) -> None:
        """
        Handle file change events.

        Args:
            event: File change event with path and event_type.
        """
        # Add to recent files tracker
        self.recent_files.add(event.path)

        # Invalidate cache if needed (files used in context)
        if event.event_type in ["modified", "deleted"]:
            # Cache invalidation deferred - would require cache key tracking
            logger.debug(
                f"File {event.path} {event.event_type} - cache invalidation not yet implemented"
            )
