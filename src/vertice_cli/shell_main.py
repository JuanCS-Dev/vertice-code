"Interactive shell with tool-based architecture."

import asyncio
import os
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING, tuple
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
            def _create_fake_code_block(*a, **k):
                def render(s):
                    return str(a[0]) if a else ""

                return type("FakeCodeBlock", (), {"render": render})()

            def _create_fake_diff_viewer(*a, **k):
                def render(s):
                    return ""

                return type("FakeDiffViewer", (), {"render": render})()

            _CodeBlock = _create_fake_code_block
            _DiffViewer = _create_fake_diff_viewer
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
    # TUI components (used conditionally)
    pass

# Core imports (lightweight, needed early)
from .core.context import ContextBuilder  # noqa: E402
from .core.conversation import ConversationManager  # noqa: E402
from .core.recovery import ErrorRecoveryEngine  # noqa: E402

# P1: Import error parser and danger detector

# P2: Import enhanced help system
from .core.help_system import help_system  # noqa: E402

# Import LLM client (using existing implementation)
from .core.async_executor import AsyncExecutor  # noqa: E402
from .core.file_watcher import FileWatcher, RecentFilesTracker  # noqa: E402

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
    ReadFileTool,
    WriteFileTool,
    EditFileTool,
    ListDirectoryTool,
    DeleteFileTool,
)
from .tools.file_mgmt import (
    MoveFileTool,
    CopyFileTool,
    CreateDirectoryTool,
    ReadMultipleFilesTool,
    InsertLinesTool,
)
from .tools.search import SearchFilesTool, GetDirectoryTreeTool
from .tools.exec_hardened import BashCommandTool
from .tools.git_ops import GitStatusTool, GitDiffTool
from .tools.context import GetContextTool, SaveSessionTool, RestoreBackupTool
from .tools.noesis_mcp import (
    GetNoesisConsciousnessTool,
    ActivateNoesisConsciousnessTool,
    DeactivateNoesisConsciousnessTool,
    QueryNoesisTribunalTool,
    ShareNoesisInsightTool,
)
from .tools.distributed_noesis_mcp import (
    ActivateDistributedConsciousnessTool,
    DeactivateDistributedConsciousnessTool,
    GetDistributedConsciousnessStatusTool,
    ProposeDistributedCaseTool,
    GetDistributedCaseStatusTool,
    ShareDistributedInsightTool,
    GetCollectiveInsightsTool,
    ConnectToDistributedNodeTool,
)
from .tools.terminal import (
    CdTool,
    LsTool,
    PwdTool,
    MkdirTool,
    RmTool,
    CpTool,
    MvTool,
    TouchTool,
    CatTool,
)

# TUI Components - Core only (others lazy loaded in methods)
from .tui.styles import get_rich_theme

# Phase 2: Enhanced Input System (needed for __init__)
from .tui.input_enhanced import EnhancedInputSession, InputContext
from .tui.history import CommandHistory, HistoryEntry, SessionReplay

# Phase 3: Visual Workflow (needed for __init__)
from .tui.components.workflow_visualizer import WorkflowVisualizer
from .tui.components.execution_timeline import ExecutionTimeline

# Phase 4: Command Palette (needed for __init__)
from .tui.components.palette import (
    create_default_palette,
)

# Phase 5: Animations (needed for __init__)
from .tui.animations import Animator, AnimationConfig, StateTransition

# Phase 6: Dashboard (needed for __init__)
from .tui.components.dashboard import Dashboard

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
            max_recovery_attempts=2,  # Constitutional P6
        )

        # Phase 3.1: Error recovery engine
        self.recovery_engine = ErrorRecoveryEngine(
            llm_client=self.llm,
            max_attempts=2,
            enable_learning=True,  # Constitutional P6
        )

        # Setup enhanced input session (DAY 8: Phase 2)
        history_file = Path.home() / ".qwen_shell_history"
        self.input_context = InputContext(
            cwd=str(Path.cwd()),
            env=os.environ.copy(),
            recent_files=[],
            command_history=[],
            session_data={},
        )
        self.enhanced_input = EnhancedInputSession(
            history_file=history_file, context=self.input_context
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
            cost_per_1k=0.002,  # Gemini Pro pricing ($0.002 per 1k tokens)
        )

        from .tui.components.context_awareness import ContextAwarenessEngine

        self.context_engine = ContextAwarenessEngine(
            max_context_tokens=100_000,
            console=self.console,  # 100k token window
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
        self.file_watcher = FileWatcher(
            root_path=".", watch_extensions={".py", ".js", ".ts", ".go", ".rs"}
        )
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
                indexer=self.indexer,  # This will trigger indexer lazy load
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
            ReadFileTool(),
            ReadMultipleFilesTool(),
            ListDirectoryTool(),
            WriteFileTool(),
            EditFileTool(),
            InsertLinesTool(),
            DeleteFileTool(),
            MoveFileTool(),
            CopyFileTool(),
            CreateDirectoryTool(),
            SearchFilesTool(),
            GetDirectoryTreeTool(),
            BashCommandTool(),
            GitStatusTool(),
            GitDiffTool(),
            GetContextTool(),
            SaveSessionTool(),
            RestoreBackupTool(),
            GetNoesisConsciousnessTool(),
            ActivateNoesisConsciousnessTool(),
            DeactivateNoesisConsciousnessTool(),
            QueryNoesisTribunalTool(),
            ShareNoesisInsightTool(),
            ActivateDistributedConsciousnessTool(),
            DeactivateDistributedConsciousnessTool(),
            GetDistributedConsciousnessStatusTool(),
            ProposeDistributedCaseTool(),
            GetDistributedCaseStatusTool(),
            ShareDistributedInsightTool(),
            GetCollectiveInsightsTool(),
            ConnectToDistributedNodeTool(),
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

    async def _handle_palette_trigger(self) -> None:
        """Handle Command Palette trigger."""
        self.console.print("\n[cyan]✨ Command Palette[/cyan]\n")
        selected = await self._show_palette_interactive()
        if selected:
            try:
                self.console.print(f"\n[dim]Executing: {selected.title}[/dim]\n")
                result = selected.action()
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                self.console.print(f"[red]Error executing command: {e}[/red]")

    async def _handle_noesis_trigger(self) -> None:
        """Handle manual Noesis trigger."""
        self.console.print(
            "\n[magenta]🧠 Activating Modo Noesis - Consciência Estratégica[/magenta]\n"
        )
        from .modes.noesis_mode import NoesisMode

        try:
            noesis = NoesisMode()
            if await noesis.activate():
                self.console.print("[green]✅ Modo Noesis ativado com sucesso[/green]")
                status = noesis.get_status()
                self.console.print(
                    f"[dim]📊 Tribunal: {status['tribunal_status']} | Quality: {status['quality_level']}[/dim]\n"
                )
            else:
                self.console.print("[red]❌ Falha na ativação do Modo Noesis[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Erro ao ativar Noesis: {e}[/red]")

    async def _handle_distributed_noesis_trigger(self) -> None:
        """Handle manual Distributed Noesis trigger."""
        self.console.print(
            "\n[cyan]🕸️ Activating Distributed Consciousness - Rede de Consciência Coletiva[/cyan]\n"
        )
        from .modes.distributed_noesis import DistributedNoesisMode

        try:
            distributed_noesis = DistributedNoesisMode()
            if await distributed_noesis.activate_distributed():
                self.console.print("[green]✅ Consciência Distribuída ativada com sucesso[/green]")
                status = distributed_noesis.get_distributed_status()
                self.console.print(
                    f"[dim]📊 Rede: {status['connected_nodes']} nós | Port: {status['network_port']}[/dim]\n"
                )
            else:
                self.console.print("[red]❌ Falha na ativação da Consciência Distribuída[/red]")
        except Exception as e:
            self.console.print(f"[red]❌ Erro ao ativar Consciência Distribuída: {e}[/red]")

    async def _check_auto_activation(self, user_input: str) -> None:
        """Check and handle auto-activation of strategic modes."""
        if user_input and user_input.strip():
            from .modes.noesis_mode import NoesisMode
            from .core.base_mode import ModeContext

            noesis = NoesisMode()
            context = ModeContext(
                cwd=str(Path.cwd()),
                env=dict(os.environ),
                session_id=self.session_state.session_id
                if hasattr(self, "session_state")
                else None,
            )

            action_data = {
                "command": user_input.strip().split()[0] if user_input.strip() else "",
                "prompt": user_input.strip(),
            }

            if noesis.should_auto_activate(action_data, context):
                self.console.print(
                    "\n[blue]🧠 Auto-activating Modo Noesis - Strategic moment detected[/blue]\n"
                )
                if await noesis.activate():
                    self.console.print(
                        "[green]✅ Modo Noesis auto-ativado para qualidade absoluta[/green]\n"
                    )
                else:
                    self.console.print(
                        "[yellow]⚠️ Auto-activation failed, proceeding normally[/yellow]\n"
                    )

    async def _handle_input_commands(self, user_input: str) -> tuple[bool, bool]:
        """Handle shell input commands. Returns (should_exit, was_handled)."""
        if user_input is None:  # Ctrl+D
            self.console.print("[cyan]👋 Goodbye![/cyan]")
            return True, True

        input_clean = user_input.strip()
        if not input_clean:
            return False, True

        if input_clean.lower() in ["quit", "exit", "q"]:
            self.console.print("[cyan]👋 Goodbye![/cyan]")
            return True, True

        if input_clean.lower() == "help":
            help_system.show_main_help()
            return False, True
        if input_clean.lower().startswith("help "):
            topic = input_clean[5:].strip()
            help_system.show_examples(topic if topic != "examples" else None)
            return False, True
        if input_clean.lower() == "/tutorial":
            help_system.show_tutorial()
            return False, True
        if input_clean.lower().startswith("/explain "):
            command = input_clean[9:].strip()
            self.console.print(help_system.explain_command(command))
            return False, True

        if user_input.startswith("/"):
            should_exit, message = await self._handle_system_command(user_input)
            if message:
                self.console.print(message)
            return should_exit, True

        return False, False

    def _display_token_metrics(self) -> None:
        """Display token usage metrics and warnings."""
        if self.context_engine.window.current_output_tokens > 0:
            self.console.print(self.context_engine.render_token_usage_realtime())
            usage_percent = (
                self.context_engine.window.total_tokens
                / self.context_engine.max_context_tokens
                * 100
            )
            if usage_percent >= 90:
                self.console.print("\n[bold red]⚠️  WARNING: Context window >90% full![/bold red]")
                self.console.print("[yellow]Consider using /clear to reset context[/yellow]\n")
            elif usage_percent >= 80:
                self.console.print("\n[yellow]⚠️  Context window >80% full[/yellow]\n")

    async def run(self):
        """Interactive REPL."""
        self._ui_handler.show_welcome()
        from .intelligence.engine import SuggestionEngine

        suggestion_engine = SuggestionEngine()
        from .intelligence.patterns import register_builtin_patterns

        register_builtin_patterns(suggestion_engine)

        async def file_watcher_loop():
            while True:
                self.file_watcher.check_updates()
                await asyncio.sleep(1.0)

        watcher_task = asyncio.create_task(file_watcher_loop())
        self._auto_index_task = asyncio.create_task(self._auto_index_background())

        try:
            while True:
                try:
                    start_time = time.time()
                    user_input = await self.enhanced_input.prompt_async()

                    if user_input == "__PALETTE__":
                        await self._handle_palette_trigger()
                        continue
                    if user_input == "__NOESIS__":
                        await self._handle_noesis_trigger()
                        continue
                    if user_input == "__DISTRIBUTED_NOESIS__":
                        await self._handle_distributed_noesis_trigger()
                        continue

                    await self._check_auto_activation(user_input)
                    should_exit, handled = await self._handle_input_commands(user_input)
                    if handled:
                        if should_exit:
                            break
                        continue

                    success = True
                    try:
                        await self._process_request_with_llm(user_input, suggestion_engine)
                        self._display_token_metrics()
                    except Exception as proc_error:
                        success = False
                        raise proc_error
                    finally:
                        duration_ms = int((time.time() - start_time) * 1000)
                        history_entry = HistoryEntry(
                            timestamp=datetime.now().isoformat(),
                            command=user_input[:200],
                            cwd=str(Path.cwd()),
                            success=success,
                            duration_ms=duration_ms,
                            tokens_used=0,
                            tool_calls=len(self.context.tool_calls),
                            files_modified=list(self.context.modified_files),
                            session_id=self.session_state.session_id,
                        )
                        self.cmd_history.add(history_entry)
                        self.enhanced_input.update_context(
                            cwd=str(Path.cwd()),
                            recent_files=list(self.recent_files.get_recent()),
                            command_history=self.cmd_history.get_recent(limit=10),
                        )
                except KeyboardInterrupt:
                    self.console.print("\n[dim]Use 'quit' to exit[/dim]")
                    continue
                except EOFError:
                    break
                except Exception as e:
                    await self._handle_error(e, user_input)
        finally:
            try:
                self.session_manager.save_session(self.session_state)
            except Exception as e:
                logger.warning(f"Failed to auto-save session: {e}")
            self.file_watcher.stop()
            watcher_task.cancel()
            if hasattr(self, "_auto_index_task") and self._auto_index_task:
                self._auto_index_task.cancel()

    async def _auto_index_background(self) -> None:
        try:
            await asyncio.sleep(2.0)
            if self._indexer_initialized:
                return
            start_time = asyncio.get_event_loop().time()
            count = await asyncio.to_thread(self.indexer.index_codebase, force=False)
            elapsed = asyncio.get_event_loop().time() - start_time
            stats = self.indexer.get_stats()
            self._indexer_initialized = True
            self.console.print(
                f"\n[green]✓ Indexed {count} files in {elapsed:.1f}s[/green] [dim]({stats['total_symbols']} symbols)[/dim]\n"
            )
        except Exception as e:
            logger.error(f"Background indexing failed: {e}")

    async def _execute_with_recovery(self, tool, tool_name: str, args: Dict[str, Any], turn):
        return await self._tool_executor.execute_with_recovery(tool, tool_name, args, turn)

    async def _process_tool_calls(self, user_input: str) -> str:
        return await self._tool_executor.process_tool_calls(user_input)

    async def _execute_tool_calls(self, tool_calls: list[Dict[str, Any]], turn) -> str:
        return await self._tool_executor.execute_tool_calls(tool_calls, turn)

    async def _handle_system_command(self, cmd: str) -> tuple[bool, Optional[str]]:
        result = await self._command_dispatcher.dispatch(cmd)
        return result.should_exit, result.message

    def _show_metrics(self) -> None:
        return self._ui_handler.show_metrics()

    def _show_cache_stats(self) -> None:
        return self._ui_handler.show_cache_stats()

    def _on_file_changed(self, event) -> None:
        return self._ui_handler.on_file_changed(event)

    async def _handle_explain(self, command: str) -> None:
        return await self._ui_handler.handle_explain(command)

    async def _show_palette_interactive(self):
        return await self._palette_handler.show_palette_interactive()

    async def _process_request_with_llm(self, user_input: str, suggestion_engine):
        return await self._llm_processor.process_request_with_llm(user_input, suggestion_engine)

    async def _get_command_suggestion(self, user_request: str, context: dict) -> str:
        return await self._llm_processor.get_command_suggestion(user_request, context)

    def _fallback_suggest(self, user_request: str) -> str:
        return self._llm_processor.fallback_suggest(user_request)

    def _extract_command(self, llm_response: str) -> str:
        return self._llm_processor.extract_command(llm_response)

    def _get_safety_level(self, command: str) -> int:
        return self._llm_processor.get_safety_level(command)

    async def _execute_command(self, command: str) -> dict:
        return await self._llm_processor.execute_command(command)

    async def _handle_error(self, error: Exception, user_input: str):
        return await self._llm_processor.handle_error(error, user_input)

    async def _palette_run_squad(self):
        return await self._palette_handler.palette_run_squad()

    def _palette_list_workflows(self):
        return self._palette_handler.palette_list_workflows()

    def _show_help(self):
        return self._ui_handler.show_help()


async def main():
    """Entry point for shell."""
    shell = InteractiveShell()
    await shell.run()


if __name__ == "__main__":
    asyncio.run(main())
