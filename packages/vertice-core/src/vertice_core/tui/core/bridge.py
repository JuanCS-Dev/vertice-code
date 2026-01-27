"""
Bridge Module - Facade Pattern Integration
==========================================

Main integration bridge between TUI and agent system.

Dec 2025 REFACTORING: Reduced from 1065 lines to <500 by extracting:
- help_builder.py: Tool listing and command help
- plan_executor.py: Plan execution detection

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

# Core systems
from vertice_core.tui.core.resilience import AsyncLock
from vertice_core.tui.core.prometheus_client import PrometheusClient
from vertice_core.tui.core.maximus_client import MaximusClient

# Extracted modules
from .governance import RiskLevel, GovernanceConfig, GovernanceObserver, ELP
from .llm_client import GeminiClient, ToolCallParser
from .agents import AgentInfo, AGENT_REGISTRY, AgentRouter, AgentManager
from .tools_bridge import ToolBridge, MinimalRegistry
from .ui_bridge import CommandPaletteBridge, MinimalCommandPalette, AutocompleteBridge
from .history_manager import HistoryManager
from .help_builder import build_tool_list, build_command_help, get_agent_commands
from .plan_executor import prepare_plan_execution
from .parallel_executor import ParallelExecutionResult, ParallelToolExecutor
from .chat import ChatController, ChatConfig
from .protocol_bridge import ProtocolBridgeMixin

# Managers
from .managers import (
    TodoManager,
    StatusManager,
    PullRequestManager,
    MemoryManager,
    ContextManager,
    AuthenticationManager,
    ProviderManager,
    MCPManager,
    A2AManager,
)

# Optional managers (graceful degradation)
try:
    from .custom_commands import CustomCommandsManager
except ImportError:
    CustomCommandsManager = None  # type: ignore

try:
    from .hooks_manager import HooksManager
except ImportError:
    HooksManager = None  # type: ignore

try:
    from .plan_mode_manager import PlanModeManager
except ImportError:
    PlanModeManager = None  # type: ignore

# Load .env file if exists
try:
    from dotenv import load_dotenv

    load_dotenv()
    script_dir = Path(__file__).parent.parent.parent
    env_file = script_dir / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # python-dotenv not installed - env vars must be set externally
    pass

logger = logging.getLogger(__name__)


class Bridge(ProtocolBridgeMixin):
    """Main integration bridge between TUI and agent system."""

    MAX_TOOL_ITERATIONS = 5
    MAX_PARALLEL_TOOLS = 5
    _router_lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize Bridge with all subsystems using phased approach with graceful degradation."""
        initialization_errors: list[tuple[str, str]] = []
        partial_initialization = False

        def _init_optional(component_key: str, component_factory) -> Any:
            """Initialize component with error handling and graceful degradation."""
            nonlocal partial_initialization

            try:
                component = (
                    component_factory() if callable(component_factory) else component_factory
                )
                logger.debug(f"✓ {component_key} initialized")
                return component
            except Exception as e:
                partial_initialization = True
                error_msg = f"{component_key} initialization failed: {e}"
                logger.warning(error_msg)
                initialization_errors.append((component_key, error_msg))
                return None

        # System prompt cache init
        self._system_prompt_cache: Optional[str] = None
        self._system_prompt_time: float = 0.0
        self._system_prompt_lock = AsyncLock("system_prompt")
        self._system_prompt_refresh_task = None
        try:
            self._system_prompt_ttl_s = float(os.getenv("VERTICE_SYSTEM_PROMPT_TTL_S", "60"))
        except ValueError:
            self._system_prompt_ttl_s = 60.0

        # Import structured logging and error tracking
        from .logging import get_bridge_logger, create_operation_context
        from .error_tracking import track_error

        # Ensure providers are registered (dependency injection)
        try:
            from vertice_core.providers.register import ensure_providers_registered

            ensure_providers_registered()
        except ImportError:
            # Fallback if vertice_core not available (rare)
            pass

        bridge_logger = get_bridge_logger()

        bridge_logger.info("Bridge initialization: Starting phased initialization")

        # Phase 1: Critical components (fail fast)
        with create_operation_context("critical_init", "bridge", {"phase": 1}):
            try:
                bridge_logger.info("Bridge initialization: Phase 1 - Critical components")
                self._auth_manager = AuthenticationManager()
                self._auth_manager.load_credentials()
                bridge_logger.debug("✓ Authentication manager initialized")

                self.llm = GeminiClient()
                if not self.llm.is_available:
                    bridge_logger.warning(
                        "LLM client initialized but not connected - limited functionality"
                    )
                bridge_logger.debug("✓ LLM client initialized")

            except Exception as e:
                error_event = track_error(
                    "bridge", "critical_init", e, {"phase": 1, "component": "critical"}
                )
                error_msg = f"Critical component initialization failed: {e}"
                bridge_logger.critical(error_msg, extra={"error_event": error_event.correlation_id})
                initialization_errors.append(("critical", error_msg))
                raise RuntimeError("Cannot continue without critical components") from e

        # Phase 2: Important components (graceful degradation)
        logger.info("Bridge initialization: Phase 2 - Important components")

        self.governance = _init_optional("Governance observer", GovernanceObserver)
        self.agents = _init_optional("Agent manager", lambda: AgentManager(self.llm))
        self.tools = _init_optional("Tool bridge", ToolBridge)
        if self.tools:
            logger.debug(f"✓ Tool bridge initialized with {self.tools.get_tool_count()} tools")

        # Phase 3: UI components (less critical)
        logger.info("Bridge initialization: Phase 3 - UI components")

        self.palette = _init_optional("Command palette bridge", CommandPaletteBridge)
        if self.tools:
            self.autocomplete = _init_optional(
                "Autocomplete bridge", lambda: AutocompleteBridge(self.tools)
            )
        else:
            self.autocomplete = None
        self.history = _init_optional("History manager", HistoryManager)

        # Phase 4: Managers with graceful degradation
        logger.info("Bridge initialization: Phase 4 - Managers")

        self._todo_manager = _init_optional("Todo manager", TodoManager)
        self._status_manager = _init_optional(
            "Status manager",
            lambda: StatusManager(
                llm_checker=lambda: self.llm.is_available,
                tool_counter=lambda: self.tools.get_tool_count() if self.tools else 0,
                agent_counter=lambda: len(self.agents.available_agents) if self.agents else 0,
            ),
        )
        self._pr_manager = _init_optional("PR manager", PullRequestManager)
        self._memory_manager = _init_optional("Memory manager", MemoryManager)
        self._context_manager = _init_optional(
            "Context manager",
            lambda: ContextManager(
                context_getter=lambda: self.history.context if self.history else {},
                context_setter=lambda ctx: (
                    setattr(self.history, "context", ctx) if self.history else None
                ),
            ),
        )
        self._initialization_errors = initialization_errors
        self._partial_initialization = partial_initialization

        # State
        self._tools_configured = False
        self._auto_route_enabled = True
        self._state_lock = AsyncLock("bridge_state")

        # Optional managers
        self._custom_commands_manager = CustomCommandsManager() if CustomCommandsManager else None
        self._hooks_manager = HooksManager() if HooksManager else None
        self._plan_mode_manager = PlanModeManager() if PlanModeManager else None

        # Provider manager
        self._provider_manager = ProviderManager(
            gemini_client=self.llm,
            prometheus_factory=lambda: PrometheusClient(),
            maximus_factory=lambda: MaximusClient(),
        )

        # MCP manager (Phase 6.2)
        self._mcp_manager = MCPManager()

        # A2A manager (Phase 6.3)
        self._a2a_manager = A2AManager()

        # PROMETHEUS state (Phase 7: Meta-Agent Integration)
        self._provider_mode: str = "auto"  # Synced with _provider_manager.mode

        # Chat controller
        self._chat_controller = ChatController(
            tools=self.tools,
            history=self.history,
            governance=self.governance,
            agents=self.agents,
            agent_registry=AGENT_REGISTRY,
            config=ChatConfig(
                max_parallel_tools=self.MAX_PARALLEL_TOOLS,
            ),
        )

    async def warmup(self) -> None:
        """
        Background warm-up of heavy components.

        Called by VerticeApp.on_mount to perform lazy loading of
        providers and tools without blocking the UI.
        """
        import asyncio

        loop = asyncio.get_running_loop()
        logger.debug("Starting Bridge warm-up (threaded)...")

        # 1. Configure LLM tools (generates schemas) - CPU bound
        if self.tools:
            try:
                await loop.run_in_executor(None, self._configure_llm_tools)
                logger.debug("✓ Tools configured")
            except Exception as e:
                logger.warning(f"Warm-up: Tool config failed: {e}")

        # 2. Initialize default provider (triggers heavy imports) - IO/CPU bound
        try:
            await loop.run_in_executor(None, self._warmup_provider)
            logger.debug("✓ Default provider loaded")
        except Exception as e:
            logger.warning(f"Warm-up: Provider init failed: {e}")

        # 3. Pre-build system prompt (git context, memory, tools list) - may involve I/O
        try:
            await self._build_system_prompt_and_cache()
            logger.debug("✓ System prompt cached")
        except Exception as e:
            logger.warning(f"Warm-up: System prompt build failed: {e}")

        # 4. Warm file cache for @ autocomplete (filesystem scan) - I/O bound
        if self.autocomplete:
            try:
                await loop.run_in_executor(None, self.autocomplete.warmup_file_cache)
                logger.debug("✓ Autocomplete file cache warmed")
            except Exception as e:
                logger.warning(f"Warm-up: Autocomplete file cache failed: {e}")

        logger.debug("Bridge warm-up complete")

    def _warmup_provider(self) -> None:
        """Helper for threaded provider warmup."""
        if hasattr(self._provider_manager, "get_client"):
            self._provider_manager.get_client()

    # =========================================================================
    # CORE PROPERTIES
    # =========================================================================

    @property
    def is_connected(self) -> bool:
        """Check if LLM is available."""
        return self.llm.is_available

    def _verify_initialization(self) -> bool:
        """Verify that all critical components were initialized successfully."""
        critical_components = [
            ("llm", self.llm),
            ("governance", self.governance),
            ("agents", self.agents),
            ("tools", self.tools),
            ("auth_manager", self._auth_manager),
        ]

        for name, component in critical_components:
            if component is None:
                logger.error(f"Critical component {name} is None")
                return False

        # Verify LLM connectivity
        if not self.is_connected:
            logger.warning("LLM is not connected - system may have limited functionality")

        return True

    @property
    def status_line(self) -> str:
        """Get status line for TUI."""
        llm_status = f"{ELP['approved']} Gemini" if self.is_connected else f"{ELP['error']} No LLM"

        tool_count = self.tools.get_tool_count() if self.tools else 0
        agent_count = len(self.agents.available_agents) if self.agents else 0

        return (
            f"{llm_status} | {self.governance.get_status_emoji() if self.governance else '??'} | "
            f"{ELP['agent']} {agent_count} agents | "
            f"{ELP['tool']} {tool_count} tools"
        )

    @property
    def _prometheus_client(self):
        """Get Prometheus client from provider manager (for backward compatibility)."""
        return self._provider_manager._prometheus

    @property
    def prometheus_mode(self) -> bool:
        """Check if PROMETHEUS mode is enabled."""
        return self._provider_manager.mode == "prometheus"

    @prometheus_mode.setter
    def prometheus_mode(self, enabled: bool) -> None:
        """Enable or disable PROMETHEUS mode."""
        self._provider_manager.mode = "prometheus" if enabled else "auto"
        self._provider_mode = self._provider_manager.mode

    # =========================================================================
    # CHAT
    # =========================================================================

    def _get_client(self, message: str = "") -> Tuple[Any, str]:
        """Get appropriate LLM client."""
        return self._provider_manager.get_client(message)

    def _configure_llm_tools(self) -> None:
        """Configure LLM with tool schemas."""
        if self._tools_configured:
            return

        if not self.tools:
            logger.warning("Cannot configure LLM tools: Tool bridge not initialized")
            return

        schemas = self.tools.get_schemas_for_llm()
        if schemas:
            self.llm.set_tools(schemas)
            self._tools_configured = True

    def _build_fallback_system_prompt(self) -> str:
        """Build a minimal, non-agentic system prompt (always safe)."""
        tool_names = self.tools.list_tools()[:25] if self.tools else []
        tool_list = ", ".join(tool_names) if tool_names else "none loaded"
        return f"""You are PROMETHEUS, an AI coding assistant.
Available tools: {tool_list}
Working directory: {os.getcwd()}"""

    def _build_system_prompt_sync(self) -> str:
        """
        Build the agentic system prompt (SYNC).

        NOTE: This function may perform blocking work (file I/O, git subprocess).
        Prefer calling via `await asyncio.to_thread(...)` from async code.
        """
        from vertice_core.tui.core.agentic_prompt import (
            build_agentic_system_prompt,
            load_project_memory,
            get_dynamic_context,
        )

        try:
            tool_schemas = self.tools.get_schemas_for_llm() if self.tools else []
        except Exception as e:
            tool_schemas = []

        try:
            context = get_dynamic_context()
        except Exception as e:
            context = {"cwd": os.getcwd()}

        try:
            project_memory = load_project_memory()
        except Exception as e:
            project_memory = None

        user_memory = None
        try:
            memory_result = self.read_memory(scope="project")
            if memory_result.get("success"):
                user_memory = memory_result.get("content")
        except Exception as e:
            user_memory = None

        return build_agentic_system_prompt(
            tools=tool_schemas,
            context=context,
            project_memory=project_memory,
            user_memory=user_memory,
        )

    def _maybe_schedule_system_prompt_refresh(self) -> None:
        """Schedule a background system prompt refresh (non-blocking)."""
        import asyncio

        task = getattr(self, "_system_prompt_refresh_task", None)
        if task is not None and not task.done():
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        refresh_task = loop.create_task(self._build_system_prompt_and_cache())

        def _log_task_result(t: "asyncio.Task[str]") -> None:
            try:
                t.result()
            except Exception as e:
                logger.debug(f"System prompt refresh failed: {e}")

        refresh_task.add_done_callback(_log_task_result)
        self._system_prompt_refresh_task = refresh_task

    async def _build_system_prompt_and_cache(self) -> str:
        """Build and cache the system prompt without blocking the event loop."""
        import asyncio
        import time

        ttl_s = self._system_prompt_ttl_s
        async with self._system_prompt_lock:
            now = time.time()
            if (
                self._system_prompt_cache
                and self._system_prompt_time > 0.0
                and (now - self._system_prompt_time) < ttl_s
            ):
                return self._system_prompt_cache

            try:
                prompt = await asyncio.to_thread(self._build_system_prompt_sync)
            except Exception as e:
                logger.debug(f"System prompt build failed, using fallback: {e}")
                prompt = self._build_fallback_system_prompt()
            self._system_prompt_cache = prompt
            self._system_prompt_time = time.time()
            return prompt

    async def _get_system_prompt_async(self) -> str:
        """Get system prompt for agentic interaction (non-blocking, stale-while-revalidate)."""
        import time

        now = time.time()
        ttl_s = self._system_prompt_ttl_s

        if (
            self._system_prompt_cache
            and self._system_prompt_time > 0.0
            and (now - self._system_prompt_time) < ttl_s
        ):
            return self._system_prompt_cache

        if self._system_prompt_cache:
            # Serve stale and refresh in background to avoid UI stalls.
            self._maybe_schedule_system_prompt_refresh()
            return self._system_prompt_cache

        # First build (no cache yet): build once in a background thread.
        return await self._build_system_prompt_and_cache()

    def _get_system_prompt(self) -> str:
        """Get system prompt for agentic interaction (SYNC fallback)."""
        import time

        now = time.time()
        if (
            hasattr(self, "_system_prompt_cache")
            and self._system_prompt_cache
            and (now - self._system_prompt_time) < self._system_prompt_ttl_s
        ):
            return self._system_prompt_cache
        try:
            prompt = self._build_system_prompt_sync()
            self._system_prompt_cache = prompt
            self._system_prompt_time = time.time()
            return prompt
        except Exception as e:
            logger.warning(f"Agentic system prompt failed, using fallback: {e}")
            return self._build_fallback_system_prompt()

    async def chat(self, message: str, auto_route: bool = True) -> AsyncIterator[str]:
        """Handle chat message with streaming response and circuit breaker protection."""
        import asyncio

        # Circuit breaker check
        if not self._check_circuit_breaker():
            yield "❌ Service temporarily unavailable. Please try again later."
            return

        # Input validation
        if not message or not isinstance(message, str) or len(message.strip()) == 0:
            yield "❌ Invalid message"
            return

        if len(message) > 10000:  # Reasonable limit
            yield "❌ Message too long (max 10000 characters)"
            return

        try:
            # Check for plan execution
            last_plan = getattr(self.agents, "_last_plan", None)
            message, skip_routing, preamble = prepare_plan_execution(message, last_plan)
            if preamble:
                yield preamble
                self.agents._last_plan = None

            # Record success for circuit breaker
            self._record_circuit_breaker_success()

        except Exception as e:
            self._record_circuit_breaker_failure()
            yield f"❌ Error preparing chat: {str(e)[:100]}"
            return

        # Yield to the UI loop early (prevents Enter→render stalls).
        await asyncio.sleep(0)

        # Ensuring tools are configured (may be expensive on first run)
        if not self._tools_configured:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._configure_llm_tools)
        else:
            self._configure_llm_tools()

        # Get client (may block on first run if warmup didn't finish, but safe)
        client, provider_name = self._get_client(message)

        self._chat_controller.config.auto_route_enabled = (
            auto_route and self.is_auto_routing_enabled() and not skip_routing
        )

        system_prompt = await self._get_system_prompt_async()
        async for chunk in self._chat_controller.chat(
            client=client,
            message=message,
            system_prompt=system_prompt,
            provider_name=provider_name if self._provider_manager.mode == "auto" else "",
            skip_routing=skip_routing,
        ):
            yield chunk

    async def invoke_agent(
        self, agent_name: str, task: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Invoke a specific agent with streaming response."""
        self.history.add_command(f"/{agent_name} {task}")
        plan_buffer = [] if agent_name == "planner" else None

        gov_report = self.governance.observe(f"agent:{agent_name}", task, agent_name)
        yield f"*{gov_report}*\n"
        yield f"🤖 Routing to **{agent_name.title()}Agent**...\n\n"

        async for chunk in self.agents.invoke_agent(agent_name, task, context):
            if plan_buffer is not None and chunk:
                plan_buffer.append(chunk)
            yield chunk

        if plan_buffer:
            self.agents._last_plan = "".join(plan_buffer)
            yield "\n\n💾 **Plan saved!** Say `create the files` or `make it real` to execute.\n"

    async def invoke_planner_multi(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Invoke planner with Multi-Plan Generation."""
        self.history.add_command(f"/plan multi {task}")
        yield f"*{self.governance.observe('agent:planner:multi', task, 'planner')}*\n"
        yield "📋 **Multi-Plan Generation Mode** (v6.1)...\n\n"
        async for chunk in self.agents.invoke_planner_multi(task, context):
            yield chunk

    async def invoke_planner_clarify(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Invoke planner with Clarification Mode."""
        self.history.add_command(f"/plan clarify {task}")
        yield f"*{self.governance.observe('agent:planner:clarify', task, 'planner')}*\n"
        yield "❓ **Clarification Mode** (v6.1)...\n\n"
        async for chunk in self.agents.invoke_planner_clarify(task, context):
            yield chunk

    async def invoke_planner_explore(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Invoke planner with Exploration Mode (read-only)."""
        self.history.add_command(f"/plan explore {task}")
        yield f"*{self.governance.observe('agent:planner:explore', task, 'planner')}*\n"
        yield "🔍 **Exploration Mode** (v6.1 - read-only)...\n\n"
        async for chunk in self.agents.invoke_planner_explore(task, context):
            yield chunk

    async def execute_tool(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a tool by name."""
        if not self.tools:
            raise RuntimeError("Tool bridge not initialized")

        if self.governance:
            gov_report = self.governance.observe(f"tool:{tool_name}", str(kwargs))
        else:
            gov_report = "Governance not active"

        result = await self.tools.execute_tool(tool_name, **kwargs)
        result["governance"] = gov_report
        return result

    async def _execute_tools_parallel(
        self, tool_calls: List[Tuple[str, Dict[str, Any]]]
    ) -> ParallelExecutionResult:
        """Execute tool calls with intelligent parallelization."""
        executor = ParallelToolExecutor(
            self.tools.execute_tool, max_parallel=self.MAX_PARALLEL_TOOLS
        )
        return await executor.execute(tool_calls)

    # =========================================================================
    # COMMAND HELP (delegates to help_builder)
    # =========================================================================

    def get_agent_commands(self) -> Dict[str, str]:
        """Get mapping of slash commands to agents."""
        return get_agent_commands()

    def get_command_help(self) -> str:
        """Get help text for agent commands."""
        return build_command_help(AGENT_REGISTRY)

    def get_tool_list(self) -> str:
        """Get formatted list of tools."""
        if not self.tools:
            return "No tools loaded (Bridge not fully initialized)"
        return build_tool_list(self.tools.list_tools())

    # =========================================================================
    # DELEGATED METHODS (keeping API compatibility)
    # =========================================================================

    # Context management
    def compact_context(self, focus: Optional[str] = None) -> Dict[str, Any]:
        return self._context_manager.compact_context(focus)

    def get_token_stats(self) -> Dict[str, Any]:
        return self._context_manager.get_token_stats()

    # Todo management
    def get_todos(self) -> List[Dict[str, Any]]:
        return self._todo_manager.get_todos()

    def add_todo(self, text: str) -> None:
        self._todo_manager.add_todo(text)

    def update_todo(self, index: int, done: bool) -> bool:
        return self._todo_manager.update_todo(index, done)

    def clear_todos(self) -> None:
        self._todo_manager.clear_todos()

    # Model management
    def set_model(self, model_name: str) -> None:
        self.llm.model_name = model_name

    def get_model_name(self) -> str:
        """Get current model name."""
        return getattr(self.llm, "model_name", "gemini-3-flash")

    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        # Hardcoded for now, should come from provider
        return [
            "gemini-3-flash-preview",
            "gemini-3-flash",
            "gemini-3-pro-preview",
            "gemini-3-pro",
        ]

    def get_current_model(self) -> str:
        """Alias for get_model_name (Claude parity)."""
        return self.get_model_name()

    # Session management
    def resume_session(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        return self.history.load_session(session_id)

    def save_session(self, session_id: Optional[str] = None) -> str:
        return self.history.save_session(session_id)

    def list_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.history.list_sessions(limit)

    def create_checkpoint(self, label: Optional[str] = None) -> Dict[str, Any]:
        return self.history.create_checkpoint(label)

    def get_checkpoints(self) -> List[Dict[str, Any]]:
        return self.history.get_checkpoints()

    def rewind_to(self, index: int) -> Dict[str, Any]:
        return self.history.rewind_to_checkpoint(index)

    # Circuit breaker for resilience
    def _check_circuit_breaker(self) -> bool:
        """Check circuit breaker state for chat operations."""
        # Simple in-memory circuit breaker
        if not hasattr(self, "_circuit_state"):
            self._circuit_state = {
                "failures": 0,
                "last_failure": 0,
                "state": "closed",  # closed, open, half-open
            }

        state = self._circuit_state
        now = time.time()

        if state["state"] == "open":
            if now - state["last_failure"] > 60:  # 60 second timeout
                state["state"] = "half-open"
                return True
            return False

        return True

    def _record_circuit_breaker_success(self) -> None:
        """Record successful operation."""
        if hasattr(self, "_circuit_state"):
            state = self._circuit_state
            if state["state"] == "half-open":
                state["state"] = "closed"
                state["failures"] = 0

    def _record_circuit_breaker_failure(self) -> None:
        """Record failed operation."""
        if not hasattr(self, "_circuit_state"):
            self._circuit_state = {"failures": 0, "last_failure": 0, "state": "closed"}

        state = self._circuit_state
        state["failures"] += 1
        state["last_failure"] = time.time()

        if state["failures"] >= 3:  # Lower threshold for TUI
            state["state"] = "open"

    # Status management
    def check_health(self) -> Dict[str, Dict[str, Any]]:
        return self._status_manager.check_health()

    def get_permissions(self) -> Dict[str, bool]:
        return self._status_manager.get_permissions()

    def set_sandbox(self, enabled: bool) -> None:
        self._status_manager.set_sandbox(enabled)

    # Router control
    def toggle_auto_routing(self) -> bool:
        with self._router_lock:
            self._auto_route_enabled = not self._auto_route_enabled
            return self._auto_route_enabled

    def is_auto_routing_enabled(self) -> bool:
        with self._router_lock:
            return self._auto_route_enabled

    def get_router_status(self) -> Dict[str, Any]:
        router = self.agents.router
        return {
            "enabled": self.is_auto_routing_enabled(),
            "min_confidence": router.MIN_CONFIDENCE,
            "agents_configured": len(router.INTENT_PATTERNS),
        }

    # Hooks (optional)
    def get_hooks(self) -> Dict[str, Dict[str, Any]]:
        return self._hooks_manager.get_hooks() if self._hooks_manager else {}

    def set_hook(self, hook_name: str, commands: List[str]) -> bool:
        return self._hooks_manager.set_hook(hook_name, commands) if self._hooks_manager else False

    # Custom commands (optional)
    def load_custom_commands(self) -> Dict[str, Dict[str, Any]]:
        return (
            self._custom_commands_manager.load_commands() if self._custom_commands_manager else {}
        )

    def get_custom_commands(self) -> Dict[str, Dict[str, Any]]:
        return self._custom_commands_manager.get_commands() if self._custom_commands_manager else {}

    def execute_custom_command(self, name: str, args: str = "") -> Optional[str]:
        return (
            self._custom_commands_manager.execute_command(name, args)
            if self._custom_commands_manager
            else None
        )

    # Plan mode (optional)
    def enter_plan_mode(self, task: Optional[str] = None) -> Dict[str, Any]:
        return (
            self._plan_mode_manager.enter_plan_mode(task)
            if self._plan_mode_manager
            else {"success": False}
        )

    def exit_plan_mode(self, approved: bool = False) -> Dict[str, Any]:
        return (
            self._plan_mode_manager.exit_plan_mode(approved)
            if self._plan_mode_manager
            else {"success": False}
        )

    def is_plan_mode(self) -> bool:
        return self._plan_mode_manager.is_plan_mode() if self._plan_mode_manager else False

    # PR management
    async def create_pull_request(
        self, title: str, body: Optional[str] = None, base: str = "main", draft: bool = False
    ) -> Dict[str, Any]:
        return await self._pr_manager.create_pull_request(title, body, base, draft)

    # Auth management
    def login(
        self, provider: str = "gemini", api_key: Optional[str] = None, scope: str = "global"
    ) -> Dict[str, Any]:
        return self._auth_manager.login(provider, api_key, scope)

    def logout(self, provider: Optional[str] = None, scope: str = "all") -> Dict[str, Any]:
        return self._auth_manager.logout(provider, scope)

    def get_auth_status(self) -> Dict[str, Any]:
        return self._auth_manager.get_auth_status()

    # Memory management
    def read_memory(self, scope: str = "project") -> Dict[str, Any]:
        return self._memory_manager.read_memory(scope)

    def write_memory(
        self, content: str, scope: str = "project", append: bool = False
    ) -> Dict[str, Any]:
        return self._memory_manager.write_memory(content, scope, append)

    def remember(self, note: str, scope: str = "project") -> Dict[str, Any]:
        return self._memory_manager.remember(note, scope)

    # Project init
    def init_project(self) -> Dict[str, Any]:
        vertice_content = """# VERTICE.md - Project Context

This file helps Vértice understand your project context.
Define your project rules, core technologies, and coding standards here.
"""
        vertice_path = Path.cwd() / "VERTICE.md"
        if not vertice_path.exists():
            vertice_path.write_text(vertice_content)
            return {"summary": "Created VERTICE.md - edit to add project context"}
        return {"summary": "VERTICE.md already exists"}


# =============================================================================
# SINGLETON
# =============================================================================

_bridge_instance: Optional[Bridge] = None
_bridge_lock = threading.Lock()


def get_bridge() -> Bridge:
    """Get or create bridge singleton (thread-safe)."""
    global _bridge_instance
    if _bridge_instance is None:
        with _bridge_lock:
            if _bridge_instance is None:
                _bridge_instance = Bridge()

    # Verify bridge health after creation
    if _bridge_instance:
        try:
            # Quick health check
            health = _bridge_instance.check_health()
            critical_failures = [k for k, v in health.items() if not v.get("ok", False)]
            if critical_failures:
                logger.warning(f"Bridge health check failed for: {critical_failures}")
        except Exception as e:
            logger.error(f"Bridge health check failed: {e}")

    return _bridge_instance


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "Bridge",
    "get_bridge",
    "RiskLevel",
    "GovernanceConfig",
    "GovernanceObserver",
    "ELP",
    "GeminiClient",
    "ToolCallParser",
    "AgentInfo",
    "AGENT_REGISTRY",
    "AgentRouter",
    "AgentManager",
    "ToolBridge",
    "MinimalRegistry",
    "CommandPaletteBridge",
    "MinimalCommandPalette",
    "AutocompleteBridge",
    "HistoryManager",
]
