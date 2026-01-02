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

        # SCALE & SUSTAIN Phase 1.3-1.7: Semantic Handlers (Modularization)
        # Initialize AFTER registry is available (required dependency)
        from .handlers.git_handler import GitHandler
        from .handlers.file_ops_handler import FileOpsHandler
        from .handlers.tool_execution_handler import ToolExecutionHandler
        from .handlers.llm_processing_handler import LLMProcessingHandler
        from .handlers.palette_handler import PaletteHandler
        from .handlers.ui_handler import UIHandler
        self._git_handler = GitHandler(self)
        self._file_ops_handler = FileOpsHandler(self)
        self._tool_executor = ToolExecutionHandler(self)
        self._llm_processor = LLMProcessingHandler(self)
        self._palette_handler = PaletteHandler(self)
        self._ui_handler = UIHandler(self)

        # Register palette commands AFTER handlers are initialized
        self._palette_handler.register_palette_commands()

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

    # =========================================================================
    # SCALE & SUSTAIN Phase 1.6: Palette - Delegated to PaletteHandler
    # =========================================================================
    # See: vertice_cli/handlers/palette_handler.py

    def _show_welcome(self):
        """SCALE & SUSTAIN Phase 1.7: Delegated to UIHandler."""
        return self._ui_handler.show_welcome()

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

    # =========================================================================
    # SCALE & SUSTAIN Phase 1.7: UI Operations - Delegated to UIHandler
    # =========================================================================

    def _show_metrics(self) -> None:
        """SCALE & SUSTAIN Phase 1.7: Delegated to UIHandler."""
        return self._ui_handler.show_metrics()

    def _show_cache_stats(self) -> None:
        """SCALE & SUSTAIN Phase 1.7: Delegated to UIHandler."""
        return self._ui_handler.show_cache_stats()

    def _on_file_changed(self, event) -> None:
        """SCALE & SUSTAIN Phase 1.7: Delegated to UIHandler."""
        return self._ui_handler.on_file_changed(event)

    async def _handle_explain(self, command: str) -> None:
        """SCALE & SUSTAIN Phase 1.7: Delegated to UIHandler."""
        return await self._ui_handler.handle_explain(command)

    # =========================================================================
    # SCALE & SUSTAIN Phase 1.6: Palette Interactive - Delegated to PaletteHandler
    # =========================================================================

    async def _show_palette_interactive(self):
        """SCALE & SUSTAIN Phase 1.6: Delegated to PaletteHandler."""
        return await self._palette_handler.show_palette_interactive()

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

    # =========================================================================
    # SCALE & SUSTAIN Phase 1.5: LLM Processing - Delegated to Handler
    # =========================================================================

    async def _process_request_with_llm(self, user_input: str, suggestion_engine):
        """SCALE & SUSTAIN Phase 1.5: Delegated to LLMProcessingHandler."""
        return await self._llm_processor.process_request_with_llm(user_input, suggestion_engine)

    async def _get_command_suggestion(self, user_request: str, context: dict) -> str:
        """SCALE & SUSTAIN Phase 1.5: Delegated to LLMProcessingHandler."""
        return await self._llm_processor.get_command_suggestion(user_request, context)

    def _fallback_suggest(self, user_request: str) -> str:
        """SCALE & SUSTAIN Phase 1.5: Delegated to LLMProcessingHandler."""
        return self._llm_processor.fallback_suggest(user_request)

    def _extract_command(self, llm_response: str) -> str:
        """SCALE & SUSTAIN Phase 1.5: Delegated to LLMProcessingHandler."""
        return self._llm_processor.extract_command(llm_response)

    def _get_safety_level(self, command: str) -> int:
        """SCALE & SUSTAIN Phase 1.5: Delegated to LLMProcessingHandler."""
        return self._llm_processor.get_safety_level(command)

    async def _execute_command(self, command: str) -> dict:
        """SCALE & SUSTAIN Phase 1.5: Delegated to LLMProcessingHandler."""
        return await self._llm_processor.execute_command(command)

    async def _handle_error(self, error: Exception, user_input: str):
        """SCALE & SUSTAIN Phase 1.5: Delegated to LLMProcessingHandler."""
        return await self._llm_processor.handle_error(error, user_input)

    async def _palette_run_squad(self):
        """SCALE & SUSTAIN Phase 1.6: Delegated to PaletteHandler."""
        return await self._palette_handler.palette_run_squad()

    def _palette_list_workflows(self):
        """SCALE & SUSTAIN Phase 1.6: Delegated to PaletteHandler."""
        return self._palette_handler.palette_list_workflows()

    def _show_help(self):
        """SCALE & SUSTAIN Phase 1.7: Delegated to UIHandler."""
        return self._ui_handler.show_help()


async def main():
    """Entry point for shell."""
    shell = InteractiveShell()
    await shell.run()


if __name__ == "__main__":
    asyncio.run(main())
