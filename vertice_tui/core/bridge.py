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

logger = logging.getLogger(__name__)
import os
import logging

logger = logging.getLogger(__name__)
import threading
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

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
    import logging

    logging.debug("python-dotenv not installed, skipping .env load")

# Core systems
from vertice_tui.core.resilience import AsyncLock
from vertice_tui.core.prometheus_client import PrometheusClient
from vertice_tui.core.maximus_client import MaximusClient

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


class Bridge(ProtocolBridgeMixin):
    """Main integration bridge between TUI and agent system."""

    MAX_TOOL_ITERATIONS = 5
    MAX_PARALLEL_TOOLS = 5
    _router_lock = threading.Lock()

    def _safe_init(
        self, component_factory, component_name: str, partial_initialization: bool
    ) -> Any:
        """Safely initialize a component with error handling."""
        try:
            if callable(component_factory):
                component = component_factory()
            else:
                component = component_factory
            logger.debug(f"✓ {component_name} initialized")
            return component
        except Exception as e:
            logger.warning(f"{component_name} initialization failed: {e}")
            partial_initialization = True
            return None

    def __init__(self) -> None:
        """Initialize Bridge with all subsystems using phased approach with graceful degradation."""
        initialization_errors = []
        partial_initialization = False

        logger.info("Bridge initialization: Starting phased initialization")

        # Phase 1: Critical components (fail fast)
        try:
            logger.info("Bridge initialization: Phase 1 - Critical components")
            self._auth_manager = AuthenticationManager()
            self._auth_manager.load_credentials()
            logger.debug("✓ Authentication manager initialized")

            self.llm = GeminiClient()
            if not self.llm.is_available:
                logger.warning("LLM client initialized but not connected - limited functionality")
            logger.debug("✓ LLM client initialized")

        except Exception as e:
            error_msg = f"Critical component initialization failed: {e}"
            logger.critical(error_msg)
            initialization_errors.append(("critical", error_msg))
            raise RuntimeError("Cannot continue without critical components") from e

        # Phase 2: Important components (graceful degradation)
        logger.info("Bridge initialization: Phase 2 - Important components")

        try:
            self.governance = GovernanceObserver()
            logger.debug("✓ Governance observer initialized")
        except Exception as e:
            logger.warning(f"Governance initialization failed: {e}")
            self.governance = None

        try:
            self.agents = AgentManager(self.llm)
            logger.debug("✓ Agent manager initialized")
        except Exception as e:
            logger.warning(f"Agent manager initialization failed: {e}")
            self.agents = None

        try:
            self.tools = ToolBridge()
            logger.debug("✓ Tool bridge initialized")
        except Exception as e:
            logger.warning(f"Tool bridge initialization failed: {e}")
            self.tools = None

        try:
            self.palette = CommandPaletteBridge()
            logger.debug("✓ Command palette bridge initialized")
        except Exception as e:
            logger.warning(f"Command palette initialization failed: {e}")
            self.palette = None

        try:
            self.autocomplete = AutocompleteBridge(self.tools) if self.tools else None
            logger.debug("✓ Autocomplete bridge initialized")
        except Exception as e:
            logger.warning(f"Autocomplete initialization failed: {e}")
            self.autocomplete = None

        try:
            self.history = HistoryManager()
            logger.debug("✓ History manager initialized")
        except Exception as e:
            logger.warning(f"History manager initialization failed: {e}")
            self.history = None

        # Phase 3: Managers (graceful degradation)
        logger.info("Bridge initialization: Phase 3 - Managers")

        try:
            self._todo_manager = TodoManager()
            logger.debug("✓ Todo manager initialized")
        except Exception as e:
            logger.warning(f"Todo manager initialization failed: {e}")
            self._todo_manager = None

        try:
            self._status_manager = StatusManager(
                llm_checker=lambda: self.llm.is_available,
                tool_counter=lambda: self.tools.get_tool_count() if self.tools else 0,
                agent_counter=lambda: len(self.agents.available_agents) if self.agents else 0,
            )
            logger.debug("✓ Status manager initialized")
        except Exception as e:
            logger.warning(f"Status manager initialization failed: {e}")
            self._status_manager = None

        try:
            self._pr_manager = PullRequestManager()
            logger.debug("✓ PR manager initialized")
        except Exception as e:
            logger.warning(f"PR manager initialization failed: {e}")
            self._pr_manager = None

        try:
            self._memory_manager = MemoryManager()
            logger.debug("✓ Memory manager initialized")
        except Exception as e:
            logger.warning(f"Memory manager initialization failed: {e}")
            self._memory_manager = None

        try:
            self._context_manager = ContextManager(
                context_getter=lambda: self.history.context if self.history else {},
                context_setter=lambda ctx: setattr(self.history, "context", ctx)
                if self.history
                else None,
            )
            logger.debug("✓ Context manager initialized")
        except Exception as e:
            logger.warning(f"Context manager initialization failed: {e}")
            self._context_manager = None
        except Exception as e:
            error_msg = f"Agent manager initialization failed: {e}"
            logger.error(error_msg)
            initialization_errors.append(("agents", error_msg))
            self.agents = None
            partial_initialization = True

        try:
            self.tools = ToolBridge()
            logger.debug(f"✓ Tool bridge initialized with {self.tools.get_tool_count()} tools")
        except Exception as e:
            error_msg = f"Tool bridge initialization failed: {e}"
            logger.error(error_msg)
            initialization_errors.append(("tools", error_msg))
            self.tools = None
            partial_initialization = True

        # Phase 3: UI components (less critical)
        logger.info("Bridge initialization: Phase 3 - UI components")

        try:
            self.palette = CommandPaletteBridge()
            logger.debug("✓ Command palette bridge initialized")
        except Exception as e:
            error_msg = f"Command palette initialization failed: {e}"
            logger.warning(error_msg)
            initialization_errors.append(("palette", error_msg))
            self.palette = None
            partial_initialization = True

        try:
            self.autocomplete = AutocompleteBridge(self.tools) if self.tools else None
            logger.debug("✓ Autocomplete bridge initialized")
        except Exception as e:
            error_msg = f"Autocomplete initialization failed: {e}"
            logger.warning(error_msg)
            initialization_errors.append(("autocomplete", error_msg))
            self.autocomplete = None
            partial_initialization = True

        try:
            self.history = HistoryManager()
            logger.debug("✓ History manager initialized")
        except Exception as e:
            error_msg = f"History manager initialization failed: {e}"
            logger.warning(error_msg)
            initialization_errors.append(("history", error_msg))
            self.history = None
            partial_initialization = True

        # Phase 4: Managers with graceful degradation
        logger.info("Bridge initialization: Phase 4 - Managers")

        # Initialize managers with error handling
        self._todo_manager = self._safe_init(TodoManager(), "Todo manager", partial_initialization)
        self._status_manager = self._safe_init(
            lambda: StatusManager(
                llm_checker=lambda: self.llm.is_available,
                tool_counter=lambda: self.tools.get_tool_count() if self.tools else 0,
                agent_counter=lambda: len(self.agents.available_agents) if self.agents else 0,
            ),
            "Status manager",
            partial_initialization,
        )
        self._pr_manager = self._safe_init(
            PullRequestManager(), "PR manager", partial_initialization
        )
        self._memory_manager = self._safe_init(
            MemoryManager(), "Memory manager", partial_initialization
        )
        self._context_manager = self._safe_init(
            lambda: ContextManager(
                context_getter=lambda: self.history.context if self.history else {},
                context_setter=lambda ctx: setattr(self.history, "context", ctx)
                if self.history
                else None,
            ),
            "Context manager",
            partial_initialization,
        )

        try:
            self._status_manager = StatusManager(
                llm_checker=lambda: self.llm.is_available,
                tool_counter=lambda: self.tools.get_tool_count() if self.tools else 0,
                agent_counter=lambda: len(self.agents.available_agents) if self.agents else 0,
            )
            logger.debug("✓ Status manager initialized")
        except Exception as e:
            logger.warning(f"Status manager initialization failed: {e}")
            self._status_manager = None
            partial_initialization = True

        try:
            self._pr_manager = PullRequestManager()
            logger.debug("✓ PR manager initialized")
        except Exception as e:
            logger.warning(f"PR manager initialization failed: {e}")
            self._pr_manager = None
            partial_initialization = True

        try:
            self._memory_manager = MemoryManager()
            logger.debug("✓ Memory manager initialized")
        except Exception as e:
            logger.warning(f"Memory manager initialization failed: {e}")
            self._memory_manager = None
            partial_initialization = True

        try:
            self._context_manager = ContextManager(
                context_getter=lambda: self.history.context if self.history else {},
                context_setter=lambda ctx: setattr(self.history, "context", ctx)
                if self.history
                else None,
            )
            logger.debug("✓ Context manager initialized")
        except Exception as e:
            logger.warning(f"Context manager initialization failed: {e}")
            self._context_manager = None
            partial_initialization = True

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
                max_tool_iterations=self.MAX_TOOL_ITERATIONS,
                max_parallel_tools=self.MAX_PARALLEL_TOOLS,
            ),
        )

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
        return (
            f"{llm_status} | {self.governance.get_status_emoji()} | "
            f"{ELP['agent']} {len(self.agents.available_agents)} agents | "
            f"{ELP['tool']} {self.tools.get_tool_count()} tools"
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
        schemas = self.tools.get_schemas_for_llm()
        if schemas:
            self.llm.set_tools(schemas)
            self._tools_configured = True

    def _get_system_prompt(self) -> str:
        """Get system prompt for agentic interaction."""
        try:
            from vertice_tui.core.agentic_prompt import (
                build_agentic_system_prompt,
                load_project_memory,
                get_dynamic_context,
            )

            tool_schemas = self.tools.get_schemas_for_llm()
            context = get_dynamic_context()
            project_memory = load_project_memory()
            user_memory = None
            memory_result = self.read_memory(scope="project")
            if memory_result.get("success"):
                user_memory = memory_result.get("content")
            return build_agentic_system_prompt(
                tools=tool_schemas,
                context=context,
                project_memory=project_memory,
                user_memory=user_memory,
            )
        except Exception as e:
            logger.warning(f"Agentic system prompt failed, using fallback: {e}")

        # Fallback prompt
        tool_names = self.tools.list_tools()[:25]
        tool_list = ", ".join(tool_names) if tool_names else "none loaded"
        return f"""You are PROMETHEUS, an AI coding assistant.
Available tools: {tool_list}
Working directory: {os.getcwd()}"""

    async def chat(self, message: str, auto_route: bool = True) -> AsyncIterator[str]:
        """Handle chat message with streaming response."""
        # Check for plan execution
        last_plan = getattr(self.agents, "_last_plan", None)
        message, skip_routing, preamble = prepare_plan_execution(message, last_plan)
        if preamble:
            yield preamble
            self.agents._last_plan = None

        self._configure_llm_tools()
        client, provider_name = self._get_client(message)

        self._chat_controller.config.auto_route_enabled = (
            auto_route and self.is_auto_routing_enabled() and not skip_routing
        )

        system_prompt = self._get_system_prompt()
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
        gov_report = self.governance.observe(f"tool:{tool_name}", str(kwargs))
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

    def get_current_model(self) -> str:
        return getattr(self.llm, "model_name", "gemini-2.0-flash")

    def get_available_models(self) -> List[str]:
        return ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-pro"]

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
