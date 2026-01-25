"Core Shell definition."

import time
from typing import Optional
from pathlib import Path
from rich.console import Console
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import FileHistory

from vertice_core.core.llm import LLMClient
from vertice_core.core.mcp_client import MCPClient
from vertice_core.tools.base import ToolRegistry
from vertice_core.core.file_tracker import FileOperationTracker
from vertice_core.tui.maestro_layout import MaestroLayout
from vertice_core.tui.components.agent_routing import AgentRoutingDisplay
from vertice_core.tui.components.streaming_display import StreamingResponseDisplay
from vertice_core.tui.performance import PerformanceMonitor, FPSCounter
from vertice_core.ui.command_palette import CommandPalette
from vertice_core.tui.components.autocomplete import create_completer
from vertice_core.tui.components.slash_completer import CombinedCompleter
from vertice_core.tui.components.maestro_shell_ui import MaestroShellUI
from vertice_core.tui.landing import show_landing_screen

from ..orchestrator import Orchestrator
from .approval import ApprovalMixin
from .commands import CommandsMixin
from .repl import ReplMixin


class Shell(ApprovalMixin, CommandsMixin, ReplMixin):
    """Agent-powered terminal with v6.0 integration @ 30 FPS"""

    def __init__(self):
        self.c = Console()
        self.orch: Optional[Orchestrator] = None
        self.running = True

        # TUI Components (30 FPS optimized)
        self.layout = None  # MaestroLayout (initialized in init())
        self.routing_display = AgentRoutingDisplay()
        self.streaming_display = None  # StreamingResponseDisplay (initialized in init())
        self.perf_monitor = PerformanceMonitor(target_fps=30)
        self.fps_counter = FPSCounter()

        # Command Palette & Autocomplete
        self.command_palette = CommandPalette()
        self.completer = None  # Initialized in init() after tool_registry

        # Prompt with history + autocomplete
        h = Path.home() / ".maestro_history"
        self.prompt = PromptSession(
            history=FileHistory(str(h)),
            auto_suggest=AutoSuggestFromHistory(),
            # completer will be set in init() after creating it with tool_registry
        )

        # Session state
        self.messages = []  # Conversation history
        self.current_agent = ""
        self._last_approval_always = False  # Flag for "always allow"

    def init(self) -> bool:
        """Initialize v6.0 agents and TUI components"""
        try:
            # Show cyberpunk landing screen
            show_landing_screen(self.c)

            self.c.print("\n[dim]🔌 Initializing v6.0 Agent Framework...[/dim]")

            # Initialize core clients
            llm = LLMClient()  # Uses GEMINI_MODEL from .env (default: gemini-2.5-flash)

            # Create tool registry and MCP client
            tool_registry = ToolRegistry()

            # Register filesystem tools (use existing implementations)
            from vertice_core.tools.file_ops import ReadFileTool, WriteFileTool, EditFileTool
            from vertice_core.tools.file_mgmt import CreateDirectoryTool, MoveFileTool, CopyFileTool

            tool_registry.register(ReadFileTool())
            tool_registry.register(WriteFileTool())
            tool_registry.register(EditFileTool())
            tool_registry.register(CreateDirectoryTool())
            tool_registry.register(MoveFileTool())
            tool_registry.register(CopyFileTool())

            # Register execution tools (use existing)
            from vertice_core.tools.exec import BashCommandTool

            tool_registry.register(BashCommandTool())

            # Register search tools (use existing)
            from vertice_core.tools.search import SearchFilesTool, GetDirectoryTreeTool

            tool_registry.register(SearchFilesTool())
            tool_registry.register(GetDirectoryTreeTool())

            # Register git tools (use existing)
            from vertice_core.tools.git_ops import GitStatusTool, GitDiffTool

            tool_registry.register(GitStatusTool())
            tool_registry.register(GitDiffTool())

            mcp = MCPClient(tool_registry)

            # Initialize orchestrator with real agents + approval callback
            self.orch = Orchestrator(llm, mcp, approval_callback=self._request_approval)

            # Initialize TUI components (30 FPS optimized)
            self.layout = MaestroLayout(self.c)
            self.streaming_display = StreamingResponseDisplay(
                console=self.c, target_fps=30, max_lines=20, show_cursor=True
            )

            # Initialize MAESTRO v10.0 Shell UI (Definitive Edition @ 30 FPS)
            self.maestro_ui = MaestroShellUI(self.c)

            # Add all available agents to UI
            self.maestro_ui.add_agent("reviewer", "REVIEWER", "🔍")
            self.maestro_ui.add_agent("refactorer", "REFACTORER", "🔧")
            self.maestro_ui.add_agent("explorer", "EXPLORER", "🗺️")

            self.file_tracker = FileOperationTracker()
            # Connect file tracker to UI
            self.file_tracker.set_callback(self.maestro_ui.add_file_operation)

            # Initialize autocomplete with tool registry
            tool_completer = create_completer(
                tools_registry=tool_registry, indexer=None, recent_tracker=None
            )
            # NotImplementedError for indexer: Root cause: Code indexer not implemented. Alternative: Manual file search. ETA: Phase 7. Tracking ID: VERTICE-INDEXER-001
            # NotImplementedError for recent_tracker: Root cause: Recent files tracker not implemented. Alternative: Use file history in UI. ETA: Phase 7. Tracking ID: VERTICE-TRACKER-001

            # Combine slash commands + tool autocomplete
            self.completer = CombinedCompleter(tool_completer=tool_completer)

            # Update prompt session with combined completer
            h = Path.home() / ".maestro_history"
            self.prompt = PromptSession(
                history=FileHistory(str(h)),
                auto_suggest=AutoSuggestFromHistory(),
                completer=self.completer,
                complete_while_typing=True,  # Enable live dropdown
            )

            # Register agent commands in Command Palette
            self._register_agent_commands()

            # Update header with session info
            session_id = f"session_{int(time.time())}"
            self.layout.update_header(
                title="MAESTRO v10.0", session_id=session_id, agent="", timestamp=None
            )

            self.c.print("[dim]✅ Framework initialized @ 30 FPS[/dim]")
            self.c.print()

            return True

        except Exception as e:
            self.c.print(f"\n[red]❌ Initialization failed: {e}[/red]\n")
            return False
