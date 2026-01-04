"""
REPL Masterpiece Core - Main REPL Class.

This module provides the core MasterpieceREPL class that
orchestrates the interactive shell experience.

Features:
- Prompt session management
- Keybindings
- Agent invocation
- Main loop

Philosophy:
    "The REPL is the user's window into the system."
"""

from __future__ import annotations

import asyncio
import io
import logging
import os
import re
import sys
import time
import warnings
from pathlib import Path
from typing import Optional

# Silence warnings during imports
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "3"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
warnings.filterwarnings("ignore")

# Redirect stderr temporarily during imports
_original_stderr = sys.stderr
sys.stderr = io.StringIO()

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Restore stderr
sys.stderr = _original_stderr

# Core imports
from ..shell_context import ShellContext
from ..intent_detector import IntentDetector
from vertice_cli.core.llm import LLMClient
from vertice_cli.core.integration_coordinator import Coordinator
from vertice_cli.core.logging_setup import setup_logging

# Tools
from vertice_cli.tools.exec import BashCommandTool
from vertice_cli.tools.file_ops import ReadFileTool, WriteFileTool, EditFileTool
from vertice_cli.tools.git_ops import GitStatusTool, GitDiffTool

# Agents
from vertice_cli.agents.architect import ArchitectAgent
from vertice_cli.agents.documentation import DocumentationAgent
from vertice_cli.agents.explorer import ExplorerAgent
from vertice_cli.agents.planner import PlannerAgent
from vertice_cli.agents.refactorer import RefactorerAgent
from vertice_cli.agents.reviewer import ReviewerAgent
from vertice_cli.agents.testing import TestingAgent
from vertice_cli.agents.performance import PerformanceAgent
from vertice_cli.agents.security import SecurityAgent

# TUI Components
from vertice_cli.tui.animations import LoadingAnimation, Animator
from vertice_cli.tui.components.enhanced_progress import TokenMetrics
from vertice_cli.tui.minimal_output import MinimalOutput

# Local modules
from .completer import SmartCompleter
from .commands import create_commands, AGENT_ICONS
from .agent_adapter import format_agent_output, register_agents

logger = logging.getLogger(__name__)
setup_logging()


class MasterpieceREPL:
    """
    REPL MASTERPIECE - Divine coding experience.

    Provides an interactive shell with:
    - Fuzzy command completion
    - Agent integration
    - Streaming responses
    - Beautiful output
    """

    # Agent class mapping
    AGENT_MAP = {
        "architect": ArchitectAgent,
        "refactor": RefactorerAgent,
        "refactorer": RefactorerAgent,
        "test": TestingAgent,
        "testing": TestingAgent,
        "review": ReviewerAgent,
        "reviewer": ReviewerAgent,
        "docs": DocumentationAgent,
        "documentation": DocumentationAgent,
        "explore": ExplorerAgent,
        "explorer": ExplorerAgent,
        "plan": PlannerAgent,
        "planner": PlannerAgent,
        "performance": PerformanceAgent,
        "perf": PerformanceAgent,
        "security": SecurityAgent,
        "sec": SecurityAgent,
    }

    def __init__(self):
        """Initialize MasterpieceREPL."""
        self.console = Console()
        self.running = True
        self.dream_mode = False
        self.current_agent: Optional[str] = None

        # State
        self.command_count = 0
        self.session_start = time.time()

        # Core
        self.llm_client = LLMClient()
        self.context = ShellContext()
        self.intent_detector = IntentDetector()

        # Coordinator
        self.coordinator = Coordinator(cwd=os.getcwd())

        # Register agents
        register_agents(self.coordinator, self.llm_client, self.console, format_agent_output)
        self.console.print("[dim]✨ Integration coordinator initialized[/dim]")

        # TUI enhancements
        try:
            self.loading_animation = LoadingAnimation(style="dots", speed=0.08)
            self.animator = Animator()
            self.token_metrics = TokenMetrics()
            self.minimal_output = MinimalOutput()
        except (ImportError, TypeError, AttributeError):
            self.loading_animation = None
            self.animator = None
            self.token_metrics = None
            self.minimal_output = None

        # Output settings
        self.output_mode = "auto"
        self.last_response = ""

        # Tools
        self.bash_tool = BashCommandTool()
        self.file_read = ReadFileTool()
        self.file_write = WriteFileTool()
        self.file_edit = EditFileTool()
        self.git_status = GitStatusTool()
        self.git_diff = GitDiffTool()

        # Agents (lazy load)
        self._agents = {}

        # Commands and session
        self.commands = create_commands(self)
        self.session = self._create_session()

    def _create_session(self) -> PromptSession:
        """Create session with clean, modern prompt."""
        history_file = Path.home() / ".qwen-dev-history"

        clean_style = Style.from_dict(
            {
                "": "#00d4aa",
                "placeholder": "#666666 italic",
            }
        )

        return PromptSession(
            message=[("class:prompt", "⚡ › ")],
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
            completer=SmartCompleter(self.commands),
            key_bindings=self._create_keybindings(),
            enable_history_search=True,
            complete_while_typing=True,
            complete_in_thread=True,
            mouse_support=False,
            placeholder="Ask anything or type / for commands...",
            style=clean_style,
            multiline=False,
        )

    def _create_keybindings(self) -> KeyBindings:
        """Create intuitive keybindings."""
        bindings = KeyBindings()

        @bindings.add("c-p")
        def show_palette(event):
            self._show_palette()

        @bindings.add("c-d")
        def toggle_dream(event):
            self.dream_mode = not self.dream_mode
            status = "🟢 ON" if self.dream_mode else "⚫ OFF"
            self.console.print(f"\n💭 DREAM mode: [bold]{status}[/bold]\n")

        @bindings.add("c-s")
        def show_status(event):
            from .handlers import cmd_status

            cmd_status(self, "")

        @bindings.add("c-l")
        def clear_screen(event):
            self.console.clear()

        @bindings.add("c-o")
        def expand_response(event):
            from .handlers import cmd_expand

            cmd_expand(self, "")

        return bindings

    def _show_palette(self) -> None:
        """Show command palette."""
        self.console.print("\n[bold cyan]📋 Commands[/bold cyan]\n")

        for cmd, meta in sorted(self.commands.items()):
            self.console.print(
                f"  {meta['icon']} [cyan]{cmd:14}[/cyan] " f"[dim]{meta['description']}[/dim]"
            )

        self.console.print("\n[dim]Tab autocomplete • /help details[/dim]\n")

    async def invoke_agent(self, agent_name: str, message: str) -> None:
        """Invoke agent with beautiful feedback."""
        from .streaming import stream_response

        if not message.strip():
            self.console.print(
                f"[yellow]⚠️  Please provide a message for the " f"{agent_name} agent[/yellow]\n"
            )
            return

        # Inject project context if path mentioned
        message = self._inject_project_context(message)

        # Load agent if needed
        if agent_name not in self._agents:
            self._agents[agent_name] = await self._load_agent(agent_name)

        self.current_agent = agent_name
        icon = AGENT_ICONS.get(agent_name, "🤖")

        self.console.print(f"\n{icon} [bold cyan]{agent_name.capitalize()} Agent[/bold cyan]\n")

        # Stream response
        await stream_response(self, message, system=f"You are the {agent_name} agent.")

        self.current_agent = None

    def _inject_project_context(self, message: str) -> str:
        """Inject project context if path is mentioned."""
        path_match = re.search(r'["\']?(/[\w\-/.]+)["\']?', message)

        if not path_match:
            return message

        project_path = path_match.group(1)
        if not os.path.exists(project_path):
            return message

        self.console.print(f"[dim]📁 Analyzing project at {project_path}...[/dim]")

        context_parts = [f"Project Path: {project_path}"]

        # README
        for readme_name in ["README.md", "readme.md", "README"]:
            readme_path = os.path.join(project_path, readme_name)
            if os.path.exists(readme_path):
                try:
                    with open(readme_path, "r") as f:
                        context_parts.append(f"\n=== README ===\n{f.read()[:2000]}")
                        break
                except (IOError, OSError):
                    pass

        # Config files
        for config_file in ["pyproject.toml", "package.json", "setup.py"]:
            config_path = os.path.join(project_path, config_file)
            if os.path.exists(config_path):
                try:
                    with open(config_path, "r") as f:
                        context_parts.append(f"\n=== {config_file} ===\n{f.read()[:1000]}")
                        break
                except (IOError, OSError):
                    pass

        # Structure
        try:
            import subprocess

            result = subprocess.run(
                ["ls", "-la", project_path], capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                context_parts.append(f"\n=== Structure ===\n{result.stdout[:1000]}")
        except (subprocess.TimeoutExpired, OSError):
            pass

        project_context = "\n".join(context_parts)
        return f"{project_context}\n\n{message}"

    async def _load_agent(self, agent_name: str):
        """Load agent with progress indicator."""
        with Progress(
            SpinnerColumn(spinner_name="dots", style="cyan"),
            TextColumn(f"[bold cyan]✨ Loading {agent_name} agent..."),
            console=self.console,
            transient=True,
        ) as progress:
            progress.add_task("load", total=None)

            agent_class = self.AGENT_MAP.get(agent_name)
            if not agent_class:
                raise ValueError(f"Unknown agent: {agent_name}")

            try:
                return agent_class()
            except TypeError:
                return agent_class(llm_client=self.llm_client, mcp_client=None)

    def _process_command(self, user_input: str) -> None:
        """Process with smart routing."""
        from .tools import process_tool
        from .natural import process_natural

        user_input = user_input.strip()
        if not user_input:
            return

        self.command_count += 1

        # Slash command
        if user_input.startswith("/"):
            parts = user_input.split(maxsplit=1)
            cmd = parts[0]
            args = parts[1] if len(parts) > 1 else ""

            if cmd == "/":
                self._show_palette()
                return

            if cmd in self.commands:
                try:
                    self.commands[cmd]["handler"](args)
                except Exception as e:
                    self.console.print(f"\n[red]❌ Error: {e}[/red]")
                    self.console.print("[yellow]💡 Tip: Type /help for usage[/yellow]\n")

            elif cmd in ["/read", "/write", "/edit", "/run", "/git"]:
                asyncio.run(process_tool(self, cmd, args))

            else:
                self.console.print(f"\n[red]❌ Unknown command: {cmd}[/red]")
                self.console.print("[yellow]💡 Type /help to see available commands[/yellow]\n")

        else:
            # Natural language
            asyncio.run(process_natural(self, user_input))

    def cleanup(self) -> None:
        """Cleanup resources."""
        warnings.filterwarnings("ignore", message=".*Unclosed.*")
        warnings.filterwarnings("ignore", message=".*unclosed.*")

    def __del__(self):
        """Destructor."""
        self.cleanup()

    def run(self) -> None:
        """Run the masterpiece."""
        self.console.print("\n[bold cyan]JuanCS Dev CLI[/bold cyan] [dim]v0.2.0[/dim]")
        self.console.print(
            "[dim]Type [bold cyan]/help[/bold cyan] or just start chatting ✨[/dim]\n"
        )

        while self.running:
            try:
                with patch_stdout():
                    user_input = self.session.prompt()

                if user_input is None:
                    continue

                self._process_command(user_input)

            except KeyboardInterrupt:
                self.console.print("\n[dim]💡 Press Ctrl+C again or type /exit to quit[/dim]\n")
                continue

            except EOFError:
                from .handlers import cmd_exit

                cmd_exit(self, "")
                break

            except Exception as e:
                self.console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
                self.console.print("[yellow]💡 Please report this if it persists[/yellow]\n")


__all__ = ["MasterpieceREPL"]
