"""Approval handling for Maestro Shell."""
import asyncio
from rich.panel import Panel
from rich.text import Text


class ApprovalMixin:
    """Handles user approval for dangerous commands."""

    async def _request_approval(self, command: str) -> bool:
        """Request user approval for command execution (async).

        PATCHED: Now properly pauses Live display to prevent
        screen flickering during input.

        Args:
            command: The command requiring approval

        Returns:
            True if approved, False otherwise
        """
        # ══════════════════════════════════════════════════════════════
        # CRITICAL: Pause UI before requesting input
        # ══════════════════════════════════════════════════════════════

        # 1. PAUSE the streaming display
        if hasattr(self, "maestro_ui") and self.maestro_ui:
            self.maestro_ui.pause()

        # 2. Also stop the streaming_display if present
        if hasattr(self, "streaming_display") and self.streaming_display:
            if hasattr(self.streaming_display, "stop"):
                try:
                    self.streaming_display.stop()
                except (RuntimeError, AttributeError):
                    pass

        # 3. Clear terminal for clean display
        self.c.clear()

        try:
            # Show approval panel
            self.c.print()
            panel = Panel(
                Text(command, style="bright_yellow"),
                title="[bold bright_red]⚠️  APPROVAL REQUIRED[/bold bright_red]",
                border_style="bright_red",
                padding=(1, 2),
            )
            self.c.print(panel)
            self.c.print()
            self.c.print("[dim]This command requires your approval to execute.[/dim]")
            self.c.print(
                "[dim]Options: [bright_green][y]es[/bright_green] | [bright_red][n]o[/bright_red] | [bright_cyan][a]lways allow this command[/bright_cyan][/dim]"
            )
            self.c.print()

            loop = asyncio.get_event_loop()

            while True:
                # SYNC input is now safe because Live is stopped
                response = await loop.run_in_executor(
                    None,
                    lambda: self.c.input(
                        "[bold bright_yellow]Allow this command? [y/n/a]:[/bold bright_yellow] "
                    ),
                )
                response = response.strip().lower()

                if response in ["y", "yes"]:
                    self._last_approval_always = False
                    self.c.print("[green]✅ Approved (this time only)[/green]\n")
                    return True
                elif response in ["n", "no"]:
                    self._last_approval_always = False
                    self.c.print("[red]❌ Denied[/red]\n")
                    return False
                elif response in ["a", "always"]:
                    self._last_approval_always = True
                    self.c.print("[cyan]✅ Always allowed[/cyan]\n")
                    return True
                else:
                    self.c.print("[dim]Invalid option. Please enter y, n, or a.[/dim]\n")

        finally:
            # ══════════════════════════════════════════════════════════
            # CRITICAL: Resume UI after input is complete
            # ══════════════════════════════════════════════════════════

            # 4. Resume streaming display
            if hasattr(self, "streaming_display") and self.streaming_display:
                if hasattr(self.streaming_display, "start"):
                    try:
                        self.streaming_display.start()
                    except (RuntimeError, AttributeError):
                        pass

            # 5. Resume maestro UI
            if hasattr(self, "maestro_ui") and self.maestro_ui:
                self.maestro_ui.resume()
