"""Interactive shell with tool-based architecture."""

import asyncio
import os
import time
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path

# =============================================================================
# PHASE 3 OPTIMIZATION: Lazy Imports for Startup Performance
# =============================================================================
# Heavy imports are deferred to reduce startup time from 1000ms to ~200ms.
# Only imports needed for class definition are at module level.

# Essential imports (needed for class definition)
from rich.console import Console

# Lazy import utilities

# Deferred heavy imports (loaded on first use)
_PromptSession = None
_FileHistory = None
_AutoSuggestFromHistory = None
_CodeBlock = None
_DiffViewer = None

def _get_tui_components():
    """Lazy load TUI components."""
    global _CodeBlock, _DiffViewer
    if _CodeBlock is None:
        try:
            from .tui.components.code import CodeBlock as CB
            from .tui.components.diff import DiffViewer as DV
            _CodeBlock, _DiffViewer = CB, DV
        except ImportError:
            # Fallback if TUI components not available
            _CodeBlock = lambda *a, **k: type('FakeCodeBlock', (), {'render': lambda s: str(a[0]) if a else ''})()
            _DiffViewer = lambda *a, **k: type('FakeDiffViewer', (), {'render': lambda s: ''})()
    return _CodeBlock, _DiffViewer

def _get_prompt_toolkit():
    """Lazy load prompt_toolkit components."""
    global _PromptSession, _FileHistory, _AutoSuggestFromHistory
    if _PromptSession is None:
        from prompt_toolkit import PromptSession as PS
        from prompt_toolkit.history import FileHistory as FH
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory as AS
        _PromptSession, _FileHistory, _AutoSuggestFromHistory = PS, FH, AS
    return _PromptSession, _FileHistory, _AutoSuggestFromHistory

# Type hints only (no runtime cost)
if TYPE_CHECKING:
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    # TUI components (used conditionally)
    from .tui.components.code import CodeBlock
    from .tui.components.diff import DiffViewer

# Core imports (lightweight, needed early)
from .core.context import ContextBuilder
from .core.conversation import ConversationManager, ConversationState
from .core.recovery import (
    ErrorRecoveryEngine,
    ErrorCategory,
    create_recovery_context
)

# P1: Import error parser and danger detector
from .core.error_parser import error_parser
from .core.danger_detector import danger_detector

# P2: Import enhanced help system
from .core.help_system import help_system

# Import LLM client (using existing implementation)
from .core.async_executor import AsyncExecutor
from .core.file_watcher import FileWatcher, RecentFilesTracker

# Lazy: SemanticIndexer (heavy, used lazily anyway)
_SemanticIndexer = None
def _get_semantic_indexer():
    global _SemanticIndexer
    if _SemanticIndexer is None:
        from .intelligence.indexer import SemanticIndexer
        _SemanticIndexer = SemanticIndexer
    return _SemanticIndexer

try:
    from .core.llm import llm_client as default_llm_client
except ImportError:
    default_llm_client = None

from .tools.base import ToolRegistry
from .tools.file_ops import (
    ReadFileTool, WriteFileTool, EditFileTool,
    ListDirectoryTool, DeleteFileTool
)
from .tools.file_mgmt import (
    MoveFileTool, CopyFileTool, CreateDirectoryTool,
    ReadMultipleFilesTool, InsertLinesTool
)
from .tools.search import SearchFilesTool, GetDirectoryTreeTool
from .tools.exec_hardened import BashCommandTool
from .tools.git_ops import GitStatusTool, GitDiffTool
from .tools.context import GetContextTool, SaveSessionTool, RestoreBackupTool
from .tools.terminal import (
    CdTool, LsTool, PwdTool, MkdirTool, RmTool,
    CpTool, MvTool, TouchTool, CatTool
)
from .intelligence.context_enhanced import build_rich_context
from .intelligence.risk import assess_risk

# TUI Components - Core only (others lazy loaded in methods)
from .tui.components.status import StatusBadge, StatusLevel
from .tui.theme import COLORS
from .tui.styles import PRESET_STYLES, get_rich_theme

# Phase 2: Enhanced Input System (needed for __init__)
from .tui.input_enhanced import EnhancedInputSession, InputContext
from .tui.history import CommandHistory, HistoryEntry, SessionReplay

# Phase 3: Visual Workflow (needed for __init__)
from .tui.components.workflow_visualizer import WorkflowVisualizer, StepStatus
from .tui.components.execution_timeline import ExecutionTimeline

# Phase 4: Command Palette (needed for __init__)
from .tui.components.palette import (
    create_default_palette, Command, CommandCategory,
    CATEGORY_CONFIG
)

# Phase 5: Animations (needed for __init__)
from .tui.animations import Animator, AnimationConfig, StateTransition

# Phase 6: Dashboard (needed for __init__)
from .tui.components.dashboard import Dashboard, Operation, OperationStatus

# Phase 7: Token Tracking
from .core.token_tracker import TokenTracker

# Phase 8: LSP - Lazy loaded in property
_LSPClient = None
def _get_lsp_client():
    global _LSPClient
    if _LSPClient is None:
        from .intelligence.lsp_client import LSPClient
        _LSPClient = LSPClient
    return _LSPClient

from .core.mcp_client import MCPClient
from .orchestration.squad import DevSquad

# SCALE & SUSTAIN Phase 1.2: Command Dispatcher (CC Reduction)
from .handlers import CommandDispatcher

# Logger
logger = logging.getLogger(__name__)

# Phase 2.2: Import from modular shell package
from .shell.context import SessionContext
from .shell.safety import get_safety_level as _get_safety_level_fn

# SCALE & SUSTAIN Phase 2: Modular output rendering
from .shell.output import ResultRenderer


class InteractiveShell:
    """Tool-based interactive shell (Claude Code-level) with multi-turn conversation."""

    def __init__(self, llm_client=None, session_id: Optional[str] = None, session_state=None):
        # TUI-enhanced console with custom theme
        self.console = Console(theme=get_rich_theme())
        self.llm = llm_client or default_llm_client
        self.context = SessionContext()
        self.context_builder = ContextBuilder()

        # P2: Rich context builder
        from .core.context_rich import RichContextBuilder
        self.rich_context = RichContextBuilder()

        # Session state management (AIR GAP #2)
        from .session import SessionManager
        self.session_manager = SessionManager()

        if session_state:
            # Resume existing session
            self.session_state = session_state
            session_id = session_state.session_id
        else:
            # Create new session
            if session_id is None:
                session_id = f"shell_{int(time.time() * 1000)}"
            self.session_state = self.session_manager.create_session(cwd=Path.cwd())
            self.session_state.session_id = session_id

        # Phase 2.3: Multi-turn conversation manager
        self.conversation = ConversationManager(
            session_id=session_id,
            max_context_tokens=4000,
            enable_auto_recovery=True,
            max_recovery_attempts=2  # Constitutional P6
        )

        # Phase 3.1: Error recovery engine
        self.recovery_engine = ErrorRecoveryEngine(
            llm_client=self.llm,
            max_attempts=2,  # Constitutional P6
            enable_learning=True
        )

        # Setup enhanced input session (DAY 8: Phase 2)
        history_file = Path.home() / ".qwen_shell_history"
        self.input_context = InputContext(
            cwd=str(Path.cwd()),
            env=os.environ.copy(),
            recent_files=[],
            command_history=[],
            session_data={}
        )
        self.enhanced_input = EnhancedInputSession(
            history_file=history_file,
            context=self.input_context
        )

        # Command history with analytics (DAY 8: Phase 2)
        self.cmd_history = CommandHistory()
        self.session_replay = SessionReplay(self.cmd_history)

        # Workflow visualization (DAY 8: Phase 3)
        self.workflow_viz = WorkflowVisualizer(console=self.console)
        self.execution_timeline = ExecutionTimeline(console=self.console)

        # Command Palette - container initialized here, commands registered after registry
        self.palette = create_default_palette()

        # Token Tracking (Integration Sprint Week 1: Day 1 - Task 1.2 - ACTIVATED)
        self.token_tracker = TokenTracker(
            budget=1000000,  # 1M tokens budget
            cost_per_1k=0.002  # Gemini Pro pricing ($0.002 per 1k tokens)
        )

        from .tui.components.context_awareness import ContextAwarenessEngine
        self.context_engine = ContextAwarenessEngine(
            max_context_tokens=100_000,  # 100k token window
            console=self.console
        )

        # Animations (Integration Sprint Week 1: Day 3 - Task 1.5)
        self.animator = Animator(AnimationConfig(duration=0.3, easing="ease-out"))
        self.state_transition = StateTransition("idle")

        # Dashboard (Integration Sprint Week 1: Day 3 - Task 1.6)
        self.dashboard = Dashboard(console=self.console, max_history=5)

        # LSP Client (Week 3 Day 3 - Code Intelligence) - LAZY LOADED
        self._lsp_client = None
        self._lsp_initialized = False

        # Semantic Indexer - LAZY LOADED (background initialization)
        self._indexer = None
        self._indexer_initialized = False
        self._auto_index_task = None  # Week 3 Day 1: Background indexing task

        # Context Suggestions (Week 4 Day 1 - Smart Recommendations) - LAZY LOADED
        self._suggestion_engine = None

        # Week 4 Day 1: Consolidated context manager (wraps ContextAwarenessEngine)
        from .core.context_manager_consolidated import ConsolidatedContextManager
        self.context_manager = ConsolidatedContextManager(max_tokens=100_000)

        # Week 4 Day 2: Refactoring engine - LAZY LOADED
        self._refactoring_engine = None

        # Legacy session (fallback) - lazy loaded prompt_toolkit
        PromptSession, FileHistory, AutoSuggestFromHistory = _get_prompt_toolkit()
        self.session = PromptSession(
            history=FileHistory(str(history_file)),
            auto_suggest=AutoSuggestFromHistory(),
        )

        # Initialize tool registry
        self.registry = ToolRegistry()
        self._register_tools()

        # Day 5: DevSquad Orchestration - LAZY LOADED
        self.mcp_client = MCPClient(self.registry)
        self._squad = None

        # Phase 4.3: Async executor for parallel tool execution
        self.async_executor = AsyncExecutor(max_parallel=5)

        # Phase 4.4: File watcher for context tracking
        self.file_watcher = FileWatcher(root_path=".", watch_extensions={'.py', '.js', '.ts', '.go', '.rs'})
        self.recent_files = RecentFilesTracker(maxsize=50)

        # Setup file watcher callback
        self.file_watcher.add_callback(self._on_file_changed)
        self.file_watcher.start()

        # SCALE & SUSTAIN Phase 1.2: Command Dispatcher (CC Reduction)
        # Replaces massive if/elif chain (CC=112) with O(1) dictionary dispatch
        self._command_dispatcher = CommandDispatcher(self)

        # SCALE & SUSTAIN Phase 2: Modular Result Renderer
        # Replaces 120-line if/elif chain with Strategy pattern
        self._result_renderer = ResultRenderer(self.console)

        # SCALE & SUSTAIN Phase 1.3-1.4: Semantic Handlers (Modularization)
        # Initialize AFTER registry is available (required dependency)
        from .handlers.git_handler import GitHandler
        from .handlers.file_ops_handler import FileOpsHandler
        from .handlers.tool_execution_handler import ToolExecutionHandler
        self._git_handler = GitHandler(self)
        self._file_ops_handler = FileOpsHandler(self)
        self._tool_executor = ToolExecutionHandler(self)

        # Register palette commands AFTER handlers are initialized
        self._register_palette_commands()

        # Note: Semantic indexer moved earlier (before ContextSuggestionEngine)

    # ========== LAZY-LOADED PROPERTIES (Phase 1: Startup Optimization) ==========

    @property
    def lsp_client(self):
        """Lazy-loaded LSP client for code intelligence."""
        if self._lsp_client is None:
            LSPClient = _get_lsp_client()
            self._lsp_client = LSPClient(root_path=Path.cwd())
            self.console.print("[dim]🔧 Initialized LSP client[/dim]")
        return self._lsp_client

    @property
    def indexer(self):
        """Lazy-loaded semantic indexer."""
        if self._indexer is None:
            SemanticIndexer = _get_semantic_indexer()
            self._indexer = SemanticIndexer(root_path=os.getcwd())
            self._indexer.load_cache()
            self.console.print("[dim]📚 Loaded semantic index[/dim]")
        return self._indexer

    @property
    def suggestion_engine(self):
        """Lazy-loaded context suggestion engine."""
        if self._suggestion_engine is None:
            from .intelligence.context_suggestions import ContextSuggestionEngine
            self._suggestion_engine = ContextSuggestionEngine(
                project_root=Path.cwd(),
                indexer=self.indexer  # This will trigger indexer lazy load
            )
            self.console.print("[dim]💡 Initialized suggestion engine[/dim]")
        return self._suggestion_engine

    @property
    def refactoring_engine(self):
        """Lazy-loaded refactoring engine."""
        if self._refactoring_engine is None:
            from .refactoring.engine import RefactoringEngine
            self._refactoring_engine = RefactoringEngine(project_root=Path.cwd())
            self.console.print("[dim]🔨 Initialized refactoring engine[/dim]")
        return self._refactoring_engine

    @property
    def squad(self):
        """Lazy-loaded DevSquad orchestrator."""
        if self._squad is None:
            self._squad = DevSquad(self.llm, self.mcp_client)
            self.console.print("[dim]👥 Assembled DevSquad[/dim]")
        return self._squad

    # ========== END LAZY-LOADED PROPERTIES ==========


    def _register_tools(self):
        """Register all available tools."""
        tools = [
            # File reading (4 tools)
            ReadFileTool(),
            ReadMultipleFilesTool(),
            ListDirectoryTool(),

            # File writing (4 tools)
            WriteFileTool(),
            EditFileTool(),
            InsertLinesTool(),
            DeleteFileTool(),

            # File management (3 tools)
            MoveFileTool(),
            CopyFileTool(),
            CreateDirectoryTool(),

            # Search (2 tools)
            SearchFilesTool(),
            GetDirectoryTreeTool(),

            # Execution (1 tool)
            BashCommandTool(),

            # Git (2 tools)
            GitStatusTool(),
            GitDiffTool(),

            # Context (3 tools)
            GetContextTool(),
            SaveSessionTool(),
            RestoreBackupTool(),

            # Terminal commands (9 tools)
            CdTool(),
            LsTool(),
            PwdTool(),
            MkdirTool(),
            RmTool(),
            CpTool(),
            MvTool(),
            TouchTool(),
            CatTool(),
        ]

        for tool in tools:
            self.registry.register(tool)

        self.console.print(f"[dim]Loaded {len(tools)} tools[/dim]")

    def _register_palette_commands(self):
        """
        Register commands in command palette (Ctrl+K).

        SCALE & SUSTAIN Phase 1.3: Delegates to modular handlers for
        maintainability and semantic clarity.
        """
        # File operations - delegated to FileOpsHandler
        self.palette.add_command(Command(
            id="file.read",
            title="Read File",
            description="Read and display file contents",
            category=CommandCategory.FILE,
            keywords=["open", "cat", "view", "show"],
            keybinding=None,
            action=lambda: self._file_ops_handler.palette_read_file()
        ))

        self.palette.add_command(Command(
            id="file.write",
            title="Write File",
            description="Create or overwrite a file",
            category=CommandCategory.FILE,
            keywords=["create", "save", "new"],
            action=lambda: self._file_ops_handler.palette_write_file()
        ))

        self.palette.add_command(Command(
            id="file.edit",
            title="Edit File",
            description="Edit file with AI assistance",
            category=CommandCategory.EDIT,
            keywords=["modify", "change", "update", "fix"],
            action=lambda: self._file_ops_handler.palette_edit_file()
        ))

        # Git operations - delegated to GitHandler
        self.palette.add_command(Command(
            id="git.status",
            title="Git Status",
            description="Show git repository status",
            category=CommandCategory.GIT,
            keywords=["git", "status", "changes", "diff"],
            action=lambda: self._git_handler.palette_status()
        ))

        self.palette.add_command(Command(
            id="git.diff",
            title="Git Diff",
            description="Show git diff",
            category=CommandCategory.GIT,
            keywords=["git", "diff", "changes"],
            action=lambda: self._git_handler.palette_diff()
        ))

        # Search operations - delegated to FileOpsHandler
        self.palette.add_command(Command(
            id="search.files",
            title="Search Files",
            description="Search for text in files",
            category=CommandCategory.SEARCH,
            keywords=["find", "grep", "search", "locate"],
            action=lambda: self._file_ops_handler.palette_search_files()
        ))

        # Help & System
        self.palette.add_command(Command(
            id="help.main",
            title="Help",
            description="Show main help",
            category=CommandCategory.HELP,
            keywords=["help", "docs", "guide"],
            keybinding="?",
            action=lambda: help_system.show_main_help()
        ))

        self.palette.add_command(Command(
            id="system.clear",
            title="Clear Screen",
            description="Clear the terminal screen",
            category=CommandCategory.SYSTEM,
            keywords=["clear", "cls", "clean"],
            action=lambda: os.system('clear')
        ))

        self.palette.add_command(Command(
            id="tools.list",
            title="List Available Tools",
            description="Show all registered tools",
            category=CommandCategory.TOOLS,
            keywords=["tools", "list", "available"],
            action=lambda: self._file_ops_handler.palette_list_tools()
        ))

        # DevSquad commands
        self.palette.add_command(Command(
            id="squad.run",
            title="Run DevSquad Mission",
            description="Execute a complex task with agent squad",
            category=CommandCategory.TOOLS,
            keywords=["squad", "mission", "agent", "devsquad"],
            action=lambda: self._palette_run_squad()
        ))

        self.palette.add_command(Command(
            id="workflow.list",
            title="List Workflows",
            description="Show available workflows",
            category=CommandCategory.TOOLS,
            keywords=["workflow", "list", "template"],
            action=lambda: self._palette_list_workflows()
        ))

    def _show_welcome(self):
        """Show welcome message with TUI styling."""
        from rich.text import Text

        # Build styled welcome content
        content = Text()
        content.append("QWEN-DEV-CLI Interactive Shell ", style=PRESET_STYLES.EMPHASIS)
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
            title="[bold]🚀 AI-Powered Code Shell[/bold]",
            border_style=COLORS['accent_blue'],
            padding=(1, 2)
        )
        self.console.print(welcome)

    # =========================================================================
    # TOOL EXECUTION - DELEGATED TO ToolExecutionHandler (Phase 1.4)
    # =========================================================================
    # The following methods delegate to self._tool_executor for maintainability.
    # See: vertice_cli/handlers/tool_execution_handler.py

    async def _execute_with_recovery(
        self, tool, tool_name: str, args: Dict[str, Any], turn
    ):
        """Execute tool with error recovery. Delegated to ToolExecutionHandler."""
        return await self._tool_executor.execute_with_recovery(
            tool, tool_name, args, turn
        )

    async def _process_tool_calls(self, user_input: str) -> str:
        """
        Process user input and execute tools via LLM.

        SCALE & SUSTAIN Phase 1.4: Delegated to ToolExecutionHandler.
        See: vertice_cli/handlers/tool_execution_handler.py
        """
        return await self._tool_executor.process_tool_calls(user_input)

    async def _execute_tool_calls(self, tool_calls: list[Dict[str, Any]], turn) -> str:
        """
        Execute a sequence of tool calls with conversation tracking.

        SCALE & SUSTAIN Phase 1.4: Delegated to ToolExecutionHandler.
        See: vertice_cli/handlers/tool_execution_handler.py
        """
        return await self._tool_executor.execute_tool_calls(tool_calls, turn)

    async def _handle_system_command(self, cmd: str) -> tuple[bool, Optional[str]]:
        """
        Handle system commands (/help, /exit, etc.).

        SCALE & SUSTAIN Phase 1.2: Refactored to use CommandDispatcher
        - Before: CC=112 (F rating - untestable)
        - After: CC=1 (A rating - trivial delegation)
        - Handlers: 6 specialized handlers with avg CC=2.9
        """
        result = await self._command_dispatcher.dispatch(cmd)
        return result.should_exit, result.message

    # ========== HELPER METHODS ==========
    # NOTE: The old _handle_system_command implementation (CC=112, 677 lines) has been
    # replaced with CommandDispatcher (CC=1). See vertice_cli/handlers/ for handlers.

    def _show_metrics(self) -> None:
        """Show constitutional metrics."""
        self.console.print("\n[bold cyan]📊 Constitutional Metrics[/bold cyan]\n")

        metrics = generate_constitutional_report(
            codebase_path="vertice_cli",
            completeness=0.95,
            precision=0.98,
            recall=0.92
        )

        self.console.print(metrics.format_report())

    def _show_cache_stats(self) -> None:
        """Show cache statistics."""
        cache = get_cache()
        stats = cache.stats

        self.console.print("\n[bold cyan]💾 Cache Statistics[/bold cyan]\n")
        self.console.print(f"Hits: {stats.hits}")
        self.console.print(f"Misses: {stats.misses}")
        self.console.print(f"Hit Rate: {stats.hit_rate:.1%}")
        self.console.print(f"Memory Hits: {stats.memory_hits}")
        self.console.print(f"Disk Hits: {stats.disk_hits}")

        # File watcher stats
        self.console.print("\n[bold cyan]📁 File Watcher[/bold cyan]\n")
        self.console.print(f"Tracked Files: {self.file_watcher.tracked_files}")
        self.console.print(f"Recent Events: {len(self.file_watcher.recent_events)}")
        recent = self.recent_files.get_recent(5)
        if recent:
            self.console.print("\nRecent Files:")
            for f in recent:
                self.console.print(f"  • {f}")

    def _on_file_changed(self, event) -> None:
        """Handle file change events."""
        # Add to recent files tracker
        self.recent_files.add(event.path)

        # Invalidate cache if needed (files used in context)
        if event.event_type in ['modified', 'deleted']:
            # Cache invalidation deferred - would require cache key tracking
            logger.debug(f"File {event.path} {event.event_type} - cache invalidation not yet implemented")

    async def _handle_explain(self, command: str) -> None:
        """Explain a command."""
        if not command.strip():
            self.console.print("[yellow]Usage: /explain <command>[/yellow]")
            return

        # Build rich context
        context = build_rich_context(
            current_command=command,
            command_history=self.context.history[-10:],
            working_dir="."
        )

        # Get explanation
        explanation = explain_command(command, context)

        self.console.print(f"\n{explanation.format()}\n")

    # Command Palette Helper Methods - EXTRACTED to handlers/
    # Phase 1.3: Git operations -> GitHandler
    # Phase 1.3: File operations -> FileOpsHandler
    # See: vertice_cli/handlers/git_handler.py
    # See: vertice_cli/handlers/file_ops_handler.py

    async def _show_palette_interactive(self) -> Optional[Command]:
        """Show interactive palette and return selected command."""
        # Show search prompt
        query = await self.enhanced_input.prompt_async("[cyan]Command Palette >[/cyan] ")

        if not query or not query.strip():
            return None

        # Fuzzy search
        results = self.palette.search(query, limit=10)

        if not results:
            self.console.print("[yellow]No commands found[/yellow]")
            return None

        # Display results
        self.console.print("\n[cyan]Results:[/cyan]")
        for i, cmd in enumerate(results, 1):
            category_icon = CATEGORY_CONFIG.get(cmd.category, {}).get('icon', '📄')
            self.console.print(f"  {i}. {category_icon} {cmd.title} - [dim]{cmd.description}[/dim]")

        # Get selection
        try:
            selection = await self.enhanced_input.prompt_async("\nSelect (1-10) or Enter to cancel: ")
            if selection and selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(results):
                    return results[idx]
        except (ValueError, IndexError):
            pass

        return None

    async def _auto_index_background(self) -> None:
        """
        Week 3 Day 1: Background indexing task.
        
        Automatically indexes codebase on startup without blocking.
        Shows progress indicator and updates cache incrementally.
        """
        try:
            # Wait a bit for shell to start
            await asyncio.sleep(2.0)

            # Check if we need to index (cache stale or missing)
            if self._indexer_initialized:
                return  # Already indexed

            start_time = asyncio.get_event_loop().time()

            # Index codebase (non-blocking for cached files)
            count = await asyncio.to_thread(self.indexer.index_codebase, force=False)

            elapsed = asyncio.get_event_loop().time() - start_time

            # Get stats
            stats = self.indexer.get_stats()

            self._indexer_initialized = True

            # Show completion message
            self.console.print(
                f"\n[green]✓ Indexed {count} files in {elapsed:.1f}s[/green] "
                f"[dim]({stats['total_symbols']} symbols)[/dim]\n"
            )

        except Exception as e:
            # Don't crash on indexing errors
            import logging
            logging.error(f"Background indexing failed: {e}")

    async def run(self):
        """Interactive REPL with Cursor+Claude+Gemini best practices."""
        self._show_welcome()

        # Initialize suggestion engine
        from .intelligence.engine import SuggestionEngine
        suggestion_engine = SuggestionEngine()
        from .intelligence.patterns import register_builtin_patterns
        register_builtin_patterns(suggestion_engine)


        # Start background file watcher task
        async def file_watcher_loop():
            while True:
                self.file_watcher.check_updates()
                await asyncio.sleep(1.0)

        watcher_task = asyncio.create_task(file_watcher_loop())

        # Week 3 Day 1: Start background indexing task
        self._auto_index_task = asyncio.create_task(self._auto_index_background())

        try:
            while True:
                try:
                    # [IDLE] Get user input (DAY 8: Enhanced input)
                    start_time = time.time()
                    user_input = await self.enhanced_input.prompt_async()

                    # Handle Command Palette (Ctrl+K) - Integration Sprint Week 1
                    if user_input == "__PALETTE__":
                        self.console.print("\n[cyan]✨ Command Palette[/cyan]\n")

                        # Show palette interactively
                        selected = await self._show_palette_interactive()

                        if selected:
                            try:
                                self.console.print(f"\n[dim]Executing: {selected.title}[/dim]\n")
                                # Execute command action
                                result = selected.action()
                                if asyncio.iscoroutine(result):
                                    await result
                            except Exception as e:
                                self.console.print(f"[red]Error executing command: {e}[/red]")

                        continue

                    # Handle empty input or Ctrl+D
                    if user_input is None or not user_input.strip():
                        if user_input is None:  # Ctrl+D
                            self.console.print("[cyan]👋 Goodbye![/cyan]")
                            break
                        continue

                    # Handle system commands (quit, help, etc)
                    if user_input.strip().lower() in ['quit', 'exit', 'q']:
                        self.console.print("[cyan]👋 Goodbye![/cyan]")
                        break
                    elif user_input.strip().lower() == 'help':
                        # P2: Enhanced help system
                        help_system.show_main_help()
                        continue
                    elif user_input.strip().lower().startswith('help '):
                        # P2: Topic-specific help
                        topic = user_input.strip()[5:].strip()
                        if topic == 'examples':
                            help_system.show_examples()
                        else:
                            help_system.show_examples(topic)
                        continue
                    elif user_input.strip().lower() == '/tutorial':
                        # P2: Interactive tutorial
                        help_system.show_tutorial()
                        continue
                    elif user_input.strip().lower().startswith('/explain '):
                        # P2: Command explanation
                        command = user_input.strip()[9:].strip()
                        explanation = help_system.explain_command(command)
                        self.console.print(explanation)
                        continue
                    elif user_input.startswith("/"):
                        should_exit, message = await self._handle_system_command(user_input)
                        if message:
                            self.console.print(message)
                        if should_exit:
                            break
                        continue

                    # [THINKING] Process request with LLM
                    success = True
                    try:
                        # Process with LLM (workflow viz disabled - fixing bugs)
                        await self._process_request_with_llm(user_input, suggestion_engine)

                        # Show token usage after LLM response (Integration Sprint Week 1: Task 1.2)
                        if self.context_engine.window.current_output_tokens > 0:
                            token_panel = self.context_engine.render_token_usage_realtime()
                            self.console.print(token_panel)

                            # Warning if approaching limit
                            usage_percent = (self.context_engine.window.total_tokens /
                                           self.context_engine.max_context_tokens * 100)

                            if usage_percent >= 90:
                                self.console.print(
                                    "\n[bold red]⚠️  WARNING: Context window >90% full![/bold red]"
                                )
                                self.console.print(
                                    "[yellow]Consider using /clear to reset context[/yellow]\n"
                                )
                            elif usage_percent >= 80:
                                self.console.print(
                                    "\n[yellow]⚠️  Context window >80% full[/yellow]\n"
                                )

                    except Exception as proc_error:
                        success = False
                        raise proc_error
                    finally:
                        # Track command in history (DAY 8: Phase 2)
                        duration_ms = int((time.time() - start_time) * 1000)
                        history_entry = HistoryEntry(
                            timestamp=datetime.now().isoformat(),
                            command=user_input[:200],  # Limit to 200 chars
                            cwd=str(Path.cwd()),
                            success=success,
                            duration_ms=duration_ms,
                            tokens_used=0,  # Will be updated later
                            tool_calls=len(self.context.tool_calls),
                            files_modified=list(self.context.modified_files),
                            session_id=self.session_state.session_id
                        )
                        self.cmd_history.add(history_entry)

                        # Update input context
                        self.enhanced_input.update_context(
                            cwd=str(Path.cwd()),
                            recent_files=list(self.recent_files.get_recent()),
                            command_history=self.cmd_history.get_recent(limit=10)
                        )

                except KeyboardInterrupt:
                    self.console.print("\n[dim]Use 'quit' to exit[/dim]")
                    continue
                except EOFError:
                    break
                except Exception as e:
                    # Claude pattern: Never crash, specific error handling
                    await self._handle_error(e, user_input)

        finally:
            # Auto-save session on exit (AIR GAP #2)
            try:
                self.session_manager.save_session(self.session_state)
                self.console.print(f"[dim]💾 Session auto-saved: {self.session_state.session_id}[/dim]")
            except Exception as e:
                logger.warning(f"Failed to auto-save session: {e}")

            # Cleanup
            self.file_watcher.stop()
            watcher_task.cancel()

            # Cancel auto-index background task
            if hasattr(self, '_auto_index_task') and self._auto_index_task:
                self._auto_index_task.cancel()
                try:
                    await self._auto_index_task
                except asyncio.CancelledError:
                    logger.debug("Auto-index task cancelled successfully")

            # Stop LSP server if running
            if self._lsp_initialized:
                try:
                    await self.lsp_client.stop()
                    logger.info("LSP server stopped")
                except Exception as e:
                    logger.warning(f"Failed to stop LSP server: {e}")
            try:
                await watcher_task
            except asyncio.CancelledError:
                logger.debug("File watcher task cancelled successfully")

    async def _process_request_with_llm(self, user_input: str, suggestion_engine):
        """
        Process user request with LLM using Cursor+Claude+Gemini patterns.
        
        Cursor: Multi-step breakdown with visual feedback
        Claude: Explicit state machine + tiered safety
        Gemini: Visual hierarchy + typography
        """
        import time

        # Generate operation ID for dashboard tracking
        op_id = f"llm_request_{int(time.time() * 1000)}"

        # Track user message in session (AIR GAP #2)
        self.session_state.add_message("user", user_input)

        # P2: Build rich context (enhanced)
        context_dict = self.rich_context.build_rich_context(
            include_git=True,
            include_env=True,
            include_recent=True
        )

        # Old format for compatibility
        rich_ctx = build_rich_context(
            current_command=user_input,
            command_history=self.context.history[-10:],
            recent_errors=[],
            working_dir=os.getcwd()
        )

        # Show analyzing status
        from rich.text import Text
        text = Text("💭 Analyzing request...", style="cyan")
        self.console.print(text)
        start_time = time.time()

        # PHASE 2: Stream LLM response with visual feedback (simplified - no workflow viz for now)
        try:
            from .shell.streaming_integration import stream_llm_response

            # Build system prompt (fix - convert list items to strings)
            recent_files_str = ', '.join([
                str(f) if isinstance(f, dict) else f
                for f in context_dict.get('recent_files', [])[:5]
            ])

            system_prompt = f"""You are an AI code assistant with access to the following context:

Project: {os.getcwd()}
Recent files: {recent_files_str}
Git status: {context_dict.get('git_status', 'N/A')}

Provide clear, actionable suggestions."""

            # Stream the response with visual feedback
            suggestion = await stream_llm_response(
                llm_client=self.llm,
                prompt=user_input,
                console=self.console,
                workflow_viz=None,  # Disabled for now
                context_engine=self.context_engine,
                system_prompt=system_prompt
            )

        except Exception as e:
            self.console.print(f"[red]❌ LLM failed: {e}[/red]")
            self.console.print("[yellow]💡 Tip: Check your API key (GEMINI_API_KEY or HF_TOKEN)[/yellow]")
            return

        elapsed = time.time() - start_time
        self.console.print(f"[dim]✓ Response generated in {elapsed:.1f}s[/dim]")


        # Step 3/3: Show suggestion (Gemini: visual hierarchy)
        self.console.print()
        self.console.print(f"[dim]You:[/dim] {user_input}")
        self.console.print()
        self.console.print("[bold]💡 Suggested action:[/bold]")
        self.console.print(f"   [cyan]{suggestion}[/cyan]")
        self.console.print()

        # P1: Danger detection with visual warnings
        self.workflow_viz.add_step("safety", "Safety check", StepStatus.RUNNING)
        danger_warning = danger_detector.analyze(suggestion)

        if danger_warning:
            self.workflow_viz.update_step_status("safety", StepStatus.WARNING)
            # Show rich visual warning
            warning_panel = danger_detector.get_visual_warning(danger_warning)
            self.console.print(warning_panel)
            self.console.print()

            # Get appropriate confirmation prompt
            prompt_text = danger_detector.format_confirmation_prompt(danger_warning, suggestion)
            self.console.print(prompt_text, end="")

            user_confirmation = input()

            # Validate confirmation
            if not danger_detector.validate_confirmation(danger_warning, user_confirmation, suggestion):
                self.console.print("[yellow]❌ Cancelled - confirmation failed[/yellow]")
                return

            self.console.print("[green]✓ Confirmation accepted[/green]")
        else:
            # Old safety system as fallback
            risk = assess_risk(suggestion)
            safety_level = self._get_safety_level(suggestion)

            if safety_level == 2:  # Dangerous (fallback for old system)
                self.console.print("[red]⚠️  DANGEROUS COMMAND[/red]")
                self.console.print(f"[yellow]This will: {risk.description}[/yellow]")
                confirm = input("Type command name to confirm: ").strip()
                if confirm != suggestion.split()[0]:
                    self.console.print("[yellow]Cancelled[/yellow]")
                    return
            elif safety_level == 1:  # Needs confirmation
                self.console.print("[yellow]⚠️  Requires confirmation[/yellow]")
                confirm = input("Execute? [y/N] ").strip().lower()
                if confirm not in ['y', 'yes']:
                    self.console.print("[dim]Cancelled[/dim]")
                    return
            else:  # Safe
                self.console.print("[green]✓ Safe command[/green]")
                confirm = input("Execute? [Y/n] ").strip().lower()
                if not confirm:  # Default yes for safe commands
                    confirm = 'y'
                if confirm not in ['y', 'yes']:
                    self.console.print("[dim]Cancelled[/dim]")
                    return

        # [EXECUTING] Run command
        self.state_transition.transition_to("executing")
        self.workflow_viz.update_step_status("safety", StepStatus.COMPLETED)
        self.workflow_viz.add_step("execute", "Executing command", StepStatus.RUNNING)

        # Animated status message (Task 1.5)
        text = Text("[EXECUTING] Running command...", style="cyan")
        self.console.print(text)
        self.console.print()

        try:
            result = await self._execute_command(suggestion)

            # Show result
            if result.get('success'):
                self.state_transition.transition_to("success")
                self.workflow_viz.update_step_status("execute", StepStatus.COMPLETED)

                # Complete dashboard operation (Task 1.6)
                self.dashboard.complete_operation(op_id, OperationStatus.SUCCESS, tokens_used=0, cost=0.0)

                # Animated success message (Task 1.5)
                text = Text("✓ Success", style="green bold")
                self.console.print(text)
                if result.get('output'):
                    self.console.print(result['output'])

                # Track assistant response in session (AIR GAP #2)
                response = f"Executed: {suggestion}\nOutput: {result.get('output', '')[:200]}"
                self.session_state.add_message("assistant", response)
                self.session_state.increment_tool_calls()
            else:
                self.state_transition.transition_to("error")
                self.workflow_viz.update_step_status("execute", StepStatus.FAILED)

                # Complete dashboard operation as error (Task 1.6)
                self.dashboard.complete_operation(op_id, OperationStatus.ERROR)

                # Animated error message (Task 1.5)
                text = Text("❌ Failed", style="red bold")
                self.console.print(text)

                # P1: Intelligent error parsing
                if result.get('error'):
                    error_text = result['error']
                    self.console.print(f"[red]{error_text}[/red]")
                    self.console.print()

                    # Parse error and show suggestions
                    analysis = error_parser.parse(error_text, suggestion)

                    # Show user-friendly message
                    self.console.print(f"[yellow]💡 {analysis.user_friendly}[/yellow]")
                    self.console.print()

                    # Show suggestions
                    if analysis.suggestions:
                        self.console.print("[bold]Suggestions:[/bold]")
                        for i, sug in enumerate(analysis.suggestions[:3], 1):
                            self.console.print(f"  {i}. [cyan]{sug}[/cyan]")
                        self.console.print()

                    # Show auto-fix if available
                    if analysis.can_auto_fix and analysis.auto_fix_command:
                        self.console.print(f"[green]Auto-fix: {analysis.auto_fix_command}[/green]")
                        fix = input("Run auto-fix? [y/N] ").strip().lower()
                        if fix == 'y':
                            fix_result = await self._execute_command(analysis.auto_fix_command)
                            if fix_result['success']:
                                self.console.print("[green]✓ Auto-fix completed[/green]")
                                if fix_result['output']:
                                    self.console.print(fix_result['output'])

        except Exception as e:
            self.console.print(f"[red]❌ Execution failed: {e}[/red]")

        # Add to history
        self.context.history.append(user_input)

    async def _get_command_suggestion(self, user_request: str, context: dict) -> str:
        """Get command suggestion from LLM."""
        if not self.llm:
            # Fallback: basic regex parsing (Claude: graceful degradation)
            return self._fallback_suggest(user_request)

        # P2: Build prompt with RICH context (Cursor: context injection)
        rich_context = self.rich_context.build_rich_context()
        context_str = self.rich_context.format_context_for_llm(rich_context)

        prompt = f"""User request: {user_request}

{context_str}

Suggest ONE shell command to accomplish this task.
Output ONLY the command, no explanation, no markdown."""

        # Call LLM with error handling
        try:
            response = await self.llm.generate(prompt)

            # Handle None or empty response
            if not response:
                return self._fallback_suggest(user_request)

            # Parse command from response
            command = self._extract_command(response)
            return command

        except Exception:
            # Any LLM error: fallback gracefully
            self.console.print("[yellow]⚠️  LLM unavailable, using fallback[/yellow]")
            return self._fallback_suggest(user_request)

    def _fallback_suggest(self, user_request: str) -> str:
        """Fallback suggestion using regex (when LLM unavailable)."""
        req_lower = user_request.lower()

        # Simple pattern matching
        if 'large file' in req_lower or 'big file' in req_lower:
            return "find . -type f -size +100M"
        elif 'process' in req_lower and 'memory' in req_lower:
            return "ps aux --sort=-%mem | head -10"
        elif 'disk' in req_lower and ('space' in req_lower or 'usage' in req_lower):
            return "df -h"
        elif 'list' in req_lower and 'file' in req_lower:
            return "ls -lah"
        else:
            # Truncate huge inputs to prevent memory issues
            max_display = 100
            truncated = user_request[:max_display] + "..." if len(user_request) > max_display else user_request
            return f"# Could not parse: {truncated}"

    def _extract_command(self, llm_response: str) -> str:
        """Extract command from LLM response."""
        # Handle None or non-string
        if not llm_response or not isinstance(llm_response, str):
            return "# Could not extract command"

        # Remove markdown code blocks
        import re
        code_block = re.search(r'```(?:bash|sh)?\s*\n?(.*?)\n?```', llm_response, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()

        # Remove common prefixes
        lines = llm_response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Remove shell prompt prefix if present
                if line.startswith('$'):
                    line = line[1:].strip()
                if line:  # Only return if there's content after stripping
                    return line

        return llm_response.strip() if llm_response else "# Empty response"

    def _get_safety_level(self, command: str) -> int:
        """
        Get safety level (Claude pattern: tiered confirmations).

        Delegated to shell.safety module.
        """
        return _get_safety_level_fn(command)

    async def _execute_command(self, command: str) -> dict:
        """Execute shell command and return result."""
        from .tools.exec_hardened import BashCommandTool
        import os
        import shlex

        # Handle state changes manually via Context (Thread Safety Fix)
        cmd_parts = command.strip().split()
        if cmd_parts:
            # Handle 'cd'
            if cmd_parts[0] == 'cd':
                target_dir = cmd_parts[1] if len(cmd_parts) > 1 else os.path.expanduser('~')
                try:
                    # Expand user/vars using CONTEXT env
                    # We need to manually expand vars since we aren't using os.environ
                    # Simple expansion for $HOME and $VAR
                    for key, val in self.enhanced_input.context.env.items():
                        target_dir = target_dir.replace(f"${key}", val)

                    target_dir = os.path.expanduser(target_dir)

                    # Resolve relative paths against CONTEXT cwd
                    if not os.path.isabs(target_dir):
                        target_dir = os.path.abspath(os.path.join(self.enhanced_input.context.cwd, target_dir))

                    if os.path.isdir(target_dir):
                        # Update Context CWD (No os.chdir!)
                        self.enhanced_input.context.cwd = target_dir
                        self.console.print(f"[dim]📁 Changed directory to: {target_dir}[/dim]")
                        return {'success': True, 'output': '', 'error': None}
                    else:
                        return {'success': False, 'error': f"cd: no such file or directory: {target_dir}"}
                except Exception as e:
                    return {'success': False, 'error': str(e)}

            # Handle 'export'
            if cmd_parts[0] == 'export':
                try:
                    # Re-parse with shlex to handle quotes
                    parts = shlex.split(command)
                    if len(parts) > 1:
                        arg = parts[1]
                        if '=' in arg:
                            key, val = arg.split('=', 1)

                            # Expand variables using CONTEXT env
                            for env_key, env_val in self.enhanced_input.context.env.items():
                                val = val.replace(f"${env_key}", env_val)

                            # Update Context Env (No os.environ!)
                            self.enhanced_input.context.env[key] = val
                            self.console.print(f"[dim]✓ Exported: {key}={val}[/dim]")
                            return {'success': True, 'output': '', 'error': None}
                except Exception as e:
                    return {'success': False, 'error': str(e)}

            # Handle 'unset'
            if cmd_parts[0] == 'unset':
                try:
                    for key in cmd_parts[1:]:
                        self.enhanced_input.context.env.pop(key, None)
                    return {'success': True, 'output': '', 'error': None}
                except Exception as e:
                    return {'success': False, 'error': str(e)}

        # PHASE 2: Execute with visual feedback
        bash = BashCommandTool()

        # Show execution status (streaming indicator)
        with self.console.status(
            f"[cyan]⚡ Executing:[/cyan] {command[:60]}...",
            spinner="dots"
        ):
            result = await bash.execute(
                command=command,
                interactive=True,
                cwd=self.enhanced_input.context.cwd,
                env=self.enhanced_input.context.env
            )


        if result.success:
            return {
                'success': True,
                'output': result.data['stdout'],
                'error': result.data.get('stderr')
            }
        else:
            return {
                'success': False,
                'error': result.error or 'Command failed'
            }

    async def _handle_error(self, error: Exception, user_input: str):
        """
        Handle errors gracefully (Claude pattern: specific error handlers).
        Never crash, always suggest fix.
        """
        error_type = type(error).__name__

        # Specific handlers
        if isinstance(error, PermissionError):
            self.console.print("[red]❌ Permission denied[/red]")
            self.console.print("[yellow]💡 Try: sudo {user_input}[/yellow]")
        elif isinstance(error, FileNotFoundError):
            self.console.print("[red]❌ File or command not found[/red]")
            self.console.print("[yellow]💡 Check if the file exists or install the command[/yellow]")
        elif isinstance(error, TimeoutError):
            self.console.print("[red]❌ Operation timed out[/red]")
            self.console.print("[yellow]💡 Check network connection or increase timeout[/yellow]")
        else:
            # Generic fallback
            self.console.print(f"[red]❌ Error: {error_type}[/red]")
            self.console.print(f"[dim]{str(error)}[/dim]")
            self.console.print("[yellow]💡 Try rephrasing your request[/yellow]")

    async def _palette_run_squad(self):
        """Handle squad run from palette."""
        self.console.print("[bold blue]🤖 DevSquad Mission[/bold blue]")
        # Use input_session if available, or simple prompt
        try:
            request = await self.input_session.prompt_async("Mission Request: ")
        except (AttributeError, EOFError, KeyboardInterrupt):
            # Fallback if input_session not fully set up in tests or some modes
            request = self.console.input("Mission Request: ")

        if not request: return

        try:
            with self.console.status("[bold green]DevSquad Active...[/bold green]"):
                result = await self.squad.execute_workflow(request)
            self.console.print(self.squad.get_phase_summary(result))
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {e}")

    def _palette_list_workflows(self):
        """Handle workflow list from palette."""
        from .orchestration.workflows import WorkflowLibrary
        from rich.table import Table

        lib = WorkflowLibrary()
        workflows = lib.list_workflows()

        table = Table(title="Available Workflows")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="blue")
        table.add_column("Description", style="white")

        for w in workflows:
            table.add_row(w.id, w.name, w.description)

        self.console.print(table)

    def _show_help(self):
        """Show help message (Gemini: visual hierarchy)."""
        help_text = """
[bold cyan]Qwen CLI - AI-Powered Shell Assistant[/bold cyan]

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
  ⚠️  Regular commands ask confirmation (cp, mv)
  🚨 Dangerous commands double-confirm (rm, dd)

[dim]Powered by Qwen + Constitutional AI[/dim]
"""
        self.console.print(help_text)


async def main():
    """Entry point for shell."""
    shell = InteractiveShell()
    await shell.run()


if __name__ == "__main__":
    asyncio.run(main())
