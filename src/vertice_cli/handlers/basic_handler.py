"""
BasicHandler - Basic System Commands.

SCALE & SUSTAIN Phase 1.2 - CC Reduction.

Handles: /help, /exit, /tools, /clear, /context, /metrics, /cache,
         /tokens, /preview, /nopreview, /dash, /explain

Author: JuanCS Dev
Date: 2025-11-26
"""

from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.table import Table

from .dispatcher import CommandResult

if TYPE_CHECKING:
    from vertice_cli.shell_main import InteractiveShell


class BasicHandler:
    """Handler for basic system commands."""

    def __init__(self, shell: "InteractiveShell"):
        """Initialize with shell reference."""
        self.shell = shell
        self.console = shell.console

    async def handle_exit(self, cmd: str) -> CommandResult:
        """Handle /exit and /quit commands."""
        self.console.print("[yellow]Goodbye! 👋[/yellow]")
        return CommandResult.exit()

    async def handle_help(self, cmd: str) -> CommandResult:
        """Handle /help command."""
        help_text = """
[bold]System Commands:[/bold]
  /help       - Show this help
  /exit       - Exit shell
  /tools      - List available tools
  /context           - Show session context
  /context optimize  - Manually optimize context 🆕
  /clear      - Clear screen
  /metrics    - Show constitutional metrics
  /cache      - Show cache statistics
  /tokens     - Show token usage & budget 💰
  /workflow   - Show AI workflow visualization 🔄
  /dash       - Show AI operations dashboard 📊
  /preview    - Enable AI file preview (default) 👁️
  /nopreview  - Disable AI file preview ⚡
  /noesis-on  - Activate Noesis mode (consciousness) 🧠
  /noesis-off - Deactivate Noesis mode 🔄
  /noesis-status - Check Noesis mode status ⚖️

  [bold]Keyboard Shortcuts:[/bold] ⌨️
  Ctrl+N      - Toggle Noesis mode on/off 🧠

[bold]History & Analytics:[/bold] 🆕
  /history    - Show command history
  /stats      - Show usage statistics
  /sessions   - List previous sessions

[bold]Cursor-style Intelligence:[/bold]
  /index      - Index codebase (Cursor magic!)
  /find NAME  - Search symbols by name
  /explain X  - Explain command/concept

[bold]LSP Code Intelligence:[/bold] 🆕
  /lsp                          - Start LSP server (Python/TypeScript/Go)
  /lsp hover FILE:LINE:CHAR     - Get documentation
  /lsp goto FILE:LINE:CHAR      - Go to definition
  /lsp refs FILE:LINE:CHAR      - Find references
  /lsp diag FILE                - Show diagnostics
  /lsp complete FILE:LINE:CHAR  - Code completion suggestions 🆕
  /lsp signature FILE:LINE:CHAR - Function signature help 🆕

[bold]Smart Suggestions:[/bold] 🆕
  /suggest FILE             - Get related files & code suggestions

[bold]Refactoring:[/bold] 🆕
  /refactor rename FILE OLD NEW - Rename symbol
  /refactor imports FILE        - Organize imports

[bold]Natural Language Commands:[/bold]
  Just type what you want to do, e.g.:
  - "read api.py"
  - "search for UserModel in python files"
  - "show git status"
  - "list files in current directory"
"""
        self.console.print(Panel(help_text, title="Help", border_style="yellow"))
        return CommandResult.ok()

    async def handle_tools(self, cmd: str) -> CommandResult:
        """Handle /tools command."""
        tools = self.shell.registry.get_all()
        table = Table(title="Available Tools")
        table.add_column("Tool", style="cyan")
        table.add_column("Category", style="yellow")
        table.add_column("Description", style="white")

        for tool_name, tool in tools.items():
            table.add_row(tool_name, tool.category.value, tool.description)

        self.console.print(table)
        return CommandResult.ok()

    async def handle_clear(self, cmd: str) -> CommandResult:
        """Handle /clear command."""
        self.console.clear()
        return CommandResult.ok()

    async def handle_context(self, cmd: str) -> CommandResult:
        """Handle /context command."""
        stats = self.shell.context_manager.get_optimization_stats()
        context_text = f"""
CWD: {self.shell.context.cwd}
Modified files: {len(self.shell.context.modified_files)}
Read files: {len(self.shell.context.read_files)}
Tool calls: {len(self.shell.context.tool_calls)}

Context Optimizer:
  Items: {stats["total_items"]}
  Tokens: {stats["total_tokens"]:,} / {stats["max_tokens"]:,}
  Usage: {stats["usage_percent"]:.1f}%
  Optimizations: {stats["optimizations_performed"]}
"""
        self.console.print(Panel(context_text, title="Session Context", border_style="blue"))

        # Show recommendations
        recs = self.shell.context_manager.get_optimization_recommendations()
        if recs:
            self.console.print("\n[yellow]Recommendations:[/yellow]")
            for rec in recs:
                self.console.print(f"  ⚠️  {rec}")

        return CommandResult.ok()

    async def handle_context_optimize(self, cmd: str) -> CommandResult:
        """Handle /context optimize command."""
        self.console.print("[cyan]🧠 AI Optimizing context...[/cyan]")
        metrics = self.shell.context_manager.auto_optimize(target_usage=0.7)

        self.console.print(f"[green]✓ Optimization complete in {metrics.duration_ms:.1f}ms[/green]")
        self.console.print(
            f"  Items: {metrics.items_before} → {metrics.items_after} ({metrics.items_removed} removed)"
        )
        self.console.print(
            f"  Tokens: {metrics.tokens_before:,} → {metrics.tokens_after:,} ({metrics.tokens_freed:,} freed)"
        )

        return CommandResult.ok()

    async def handle_metrics(self, cmd: str) -> CommandResult:
        """Handle /metrics command."""
        from ..core.constitution import generate_constitutional_report

        report = generate_constitutional_report(self.shell.context.history)
        self.console.print(report)
        return CommandResult.ok()

    async def handle_cache(self, cmd: str) -> CommandResult:
        """Handle /cache command."""
        from ..core.cache import get_cache

        cache = get_cache()
        stats = cache.get_stats()
        self.console.print(
            f"\n📊 AI Cache Stats:\n  Hits: {stats['hits']}\n  Misses: {stats['misses']}\n  Size: {stats['size']}"
        )

        if self.shell.file_watcher:
            wstats = self.shell.file_watcher.get_stats()
            self.console.print(
                f"\n👁️ AI File Watcher:\n  Tracked: {wstats['tracked_count']}\n  Events: {wstats['event_count']}"
            )

        return CommandResult.ok()

    async def handle_tokens(self, cmd: str) -> CommandResult:
        """Handle /tokens command."""
        token_panel = self.shell.context_engine.render_token_usage_realtime()
        self.console.print(token_panel)

        # Show token usage history
        if self.shell.context_engine.window.usage_history:
            history_table = Table(title="Token Usage History (Last 10 Interactions)")
            history_table.add_column("Time", style="cyan", width=10)
            history_table.add_column("Input", justify="right", width=10)
            history_table.add_column("Output", justify="right", width=10)
            history_table.add_column("Total", justify="right", width=10)
            history_table.add_column("Cost", justify="right", width=10)

            for snapshot in list(self.shell.context_engine.window.usage_history)[-10:]:
                history_table.add_row(
                    snapshot.timestamp.strftime("%H:%M:%S"),
                    f"{snapshot.input_tokens:,}",
                    f"{snapshot.output_tokens:,}",
                    f"{snapshot.total_tokens:,}",
                    f"${snapshot.cost_estimate_usd:.4f}",
                )

            self.console.print(history_table)
        else:
            self.console.print(
                "\n[dim]No token usage history yet. Start a conversation to track tokens.[/dim]"
            )

        return CommandResult.ok()

    async def handle_preview_on(self, cmd: str) -> CommandResult:
        """Handle /preview command."""
        self.shell.context.preview_enabled = True
        return CommandResult.ok("[green]✓ Preview enabled for file operations[/green]")

    async def handle_preview_off(self, cmd: str) -> CommandResult:
        """Handle /nopreview command."""
        self.shell.context.preview_enabled = False
        return CommandResult.ok(
            "[yellow]⚠ Preview disabled. Files will be written directly.[/yellow]"
        )

    async def handle_dashboard(self, cmd: str) -> CommandResult:
        """Handle /dash and /dashboard commands."""
        dashboard_view = self.shell.dashboard.render()
        self.console.print(dashboard_view)
        return CommandResult.ok()

    async def handle_explain(self, cmd: str) -> CommandResult:
        """Handle /explain command."""
        from ..explainer.command_explainer import explain_command

        command = cmd[9:].strip() if cmd.startswith("/explain ") else ""
        if not command:
            return CommandResult.error("[red]Usage: /explain <command>[/red]")

        explanation = explain_command(command)
        self.console.print(f"\n🤖 AI: {explanation}")

    async def handle_noesis_on(self, args: str) -> None:
        """Ativa Modo Noesis."""
        from vertice_cli.tools.plan_mode import EnterNoesisModeTool

        tool = EnterNoesisModeTool()
        result = await tool.execute()

        if result.success:
            self.console.print(f"\n{result.message}")
        else:
            self.console.print(f"\n❌ Erro: {result.error}")

    async def handle_noesis_off(self, args: str) -> None:
        """Desativa Modo Noesis."""
        from vertice_cli.tools.plan_mode import ExitNoesisModeTool

        tool = ExitNoesisModeTool()
        result = await tool.execute()

        if result.success:
            self.console.print(f"\n{result.message}")
        else:
            self.console.print(f"\n❌ Erro: {result.error}")

    async def handle_noesis_status(self, args: str) -> None:
        """Verifica status do Modo Noesis."""
        from vertice_cli.tools.plan_mode import GetNoesisStatusTool

        tool = GetNoesisStatusTool()
        result = await tool.execute()

        if result.success:
            self.console.print(f"\n{result.message}")
        else:
            self.console.print(f"\n❌ Erro: {result.error}")
        return CommandResult.ok()
