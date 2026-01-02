"""
Agent Manager - Lazy-loading agent lifecycle management.

Extracted from agents_bridge.py for semantic modularity.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import inspect
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, TYPE_CHECKING

from .types import AgentInfo
from .registry import AGENT_REGISTRY
from .router import AgentRouter
from .streaming import normalize_streaming_chunk
from .formatters import format_agent_result

if TYPE_CHECKING:
    from ..llm_client import GeminiClient


class AgentManager:
    """
    Lazy-loading agent manager.

    Only imports agents when first used to keep startup fast.

    Usage:
        manager = AgentManager(llm_client)
        async for chunk in manager.invoke("planner", "Plan this feature"):
            print(chunk, end='')
    """

    def __init__(self, llm_client: Optional['GeminiClient'] = None) -> None:
        """Initialize agent manager.

        Args:
            llm_client: LLM client for fallback and agent creation
        """
        # CRITICAL: Register providers before any agent is created
        # This was missing and caused "Provider not available" errors
        try:
            from vertice_cli.core.providers.register import ensure_providers_registered
            ensure_providers_registered()
        except ImportError:
            pass  # CLI providers not available (minimal install)

        # Lazy import to avoid circular dependency
        if llm_client is None:
            from ..llm_client import GeminiClient
            llm_client = GeminiClient()

        self.llm_client = llm_client
        self._agents: Dict[str, Any] = {}
        self._load_errors: Dict[str, Tuple[str, float]] = {}  # (error, timestamp) - TTL cache
        self._lock = asyncio.Lock()  # FIX 1.1: Protect _agents dict
        self._error_ttl_seconds = 60.0  # FIX 1.8: Retry failed agents after 60 seconds
        self.router = AgentRouter()
        self._last_plan: Optional[str] = None  # Store last plan for execution

        # CRITICAL: Create MCP client for tools - was missing (passed None)
        self._mcp_client: Optional[Any] = None
        try:
            from vertice_cli.core.mcp import create_mcp_client
            # Attempt to create MCP client with error handling
            self._mcp_client = create_mcp_client()
            if self._mcp_client is None:
                # FIX 3.3: Use logger instead of print
                import logging
                logging.warning("MCP Client creation returned None - capabilities will be limited.")
        except ImportError:
            # FIX 3.3: Use logger instead of print
            import logging
            logging.warning("MCP module not found - running in standalone mode.")
        except Exception as e:
            # FIX 3.3: Use logger instead of print
            import logging
            logging.error(f"Failed to initialize MCP client: {e} - capabilities will be limited.")


    @property
    def available_agents(self) -> List[str]:
        """List of available agent names."""
        return list(AGENT_REGISTRY.keys())

    async def cleanup_agents(self) -> None:
        """
        Clean up all agent instances to prevent memory leaks (FIX 1.7).

        Should be called when the agent manager is no longer needed
        or when resetting the agent pool.
        """
        async with self._lock:
            for name, agent in list(self._agents.items()):
                # Call agent cleanup if available
                if hasattr(agent, 'cleanup'):
                    try:
                        if asyncio.iscoroutinefunction(agent.cleanup):
                            await agent.cleanup()
                        else:
                            agent.cleanup()
                    except Exception:
                        pass  # Ignore cleanup errors
                # Clear references
                if hasattr(agent, 'llm_client'):
                    agent.llm_client = None
                if hasattr(agent, 'mcp_client'):
                    agent.mcp_client = None
            self._agents.clear()
            self._load_errors.clear()

    def get_agent_info(self, name: str) -> Optional[AgentInfo]:
        """Get agent metadata."""
        return AGENT_REGISTRY.get(name)

    async def get_agent(self, name: str) -> Optional[Any]:
        """
        Get or create agent instance.

        Lazy loads the agent module on first use.
        Uses inspect.signature() to detect constructor parameters.
        Thread-safe with asyncio.Lock (FIX 1.1).
        Supports TTL on error cache (FIX 1.8).

        Args:
            name: Agent name from registry

        Returns:
            Agent instance or None if unavailable
        """
        # FIX 1.1: Use lock for thread-safe access
        async with self._lock:
            if name in self._agents:
                return self._agents[name]

            # FIX 1.8: Check if error is expired (TTL)
            if name in self._load_errors:
                error_msg, error_time = self._load_errors[name]
                if time.time() - error_time < self._error_ttl_seconds:
                    return None
                # TTL expired - remove from cache and retry
                del self._load_errors[name]

            info = AGENT_REGISTRY.get(name)
            if not info:
                self._load_errors[name] = (f"Unknown agent: {name}", time.time())
                return None

            try:
                # Dynamic import
                import importlib
                module = importlib.import_module(info.module_path)
                agent_class = getattr(module, info.class_name)

                # Detect __init__ signature and pass appropriate args
                sig = inspect.signature(agent_class.__init__)
                params = sig.parameters

                init_kwargs: Dict[str, Any] = {}
                if 'llm_client' in params:
                    init_kwargs['llm_client'] = self.llm_client
                if 'mcp_client' in params:
                    # FIXED: Pass actual MCP client instead of None
                    init_kwargs['mcp_client'] = self._mcp_client
                if 'model' in params:
                    init_kwargs['model'] = self.llm_client

                agent = agent_class(**init_kwargs)

                # Wrap core agents with CoreAgentAdapter for mixin activation
                if info.is_core:
                    from .core_adapter import CoreAgentAdapter
                    adapter = CoreAgentAdapter(agent, info.name)
                    self._agents[name] = adapter
                    return adapter

                self._agents[name] = agent
                return agent

            except ImportError as e:
                self._load_errors[name] = (f"Import error: {e}", time.time())
                return None
            except Exception as e:
                self._load_errors[name] = (f"Init error: {e}", time.time())
                return None

    async def invoke(
        self,
        name: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Invoke an agent and stream response.

        Falls back to LLM if agent unavailable.

        Args:
            name: Agent name
            task: Task to execute
            context: Optional context dict

        Yields:
            Response chunks as strings
        """
        agent = await self.get_agent(name)

        if agent is None:
            # Fallback: use LLM directly with agent-specific prompt
            info = AGENT_REGISTRY.get(name)
            if info:
                system_prompt = (
                    f"You are a {info.role}. {info.description}. "
                    f"Capabilities: {', '.join(info.capabilities)}."
                )
                async for chunk in self.llm_client.stream(task, system_prompt):
                    yield chunk
            else:
                yield f"❌ Agent '{name}' not available"
            return

        # Create AgentTask
        from vertice_core import AgentTask
        agent_task = AgentTask(request=task, context=context or {})

        # Track plan output for later execution
        plan_chunks: Optional[List[str]] = [] if name == "planner" else None

        # Try streaming interface first
        if hasattr(agent, 'execute_streaming'):
            try:
                sig = inspect.signature(agent.execute_streaming)
                # FIX 3.5: Exclude 'self' and handle *args/**kwargs properly
                param_count = len([p for p in sig.parameters.values()
                                   if p.name != 'self'
                                   and p.default == inspect.Parameter.empty
                                   and p.kind not in (inspect.Parameter.VAR_POSITIONAL,
                                                      inspect.Parameter.VAR_KEYWORD)])

                if param_count == 1:  # AgentTask only
                    async for chunk in agent.execute_streaming(agent_task):
                        normalized = normalize_streaming_chunk(chunk)
                        if plan_chunks is not None:
                            plan_chunks.append(normalized)
                        yield normalized
                else:  # task + context
                    async for chunk in agent.execute_streaming(task, context or {}):
                        normalized = normalize_streaming_chunk(chunk)
                        if plan_chunks is not None:
                            plan_chunks.append(normalized)
                        yield normalized

                # Save plan for later execution
                if plan_chunks:
                    plan_text = "".join(plan_chunks)
                    self._last_plan = plan_text
                    yield "\n💾 *Plan saved. Say 'create the files' or 'make it real' to execute.*\n"
                return
            except Exception as e:
                yield f"⚠️ Streaming failed: {e}\n"

        # Fallback to sync execute
        if hasattr(agent, 'execute'):
            try:
                result = await agent.execute(agent_task)
                async for chunk in self._format_agent_result(result):
                    yield chunk
                return
            except Exception as e:
                yield f"❌ Agent error: {e}"
                return

        yield f"❌ Agent '{name}' has no execute method"

    async def _format_agent_result(self, result: Any) -> AsyncIterator[str]:
        """Format agent result for display.

        Delegates to formatters module (Strategy pattern).
        See: vertice_tui/core/agents/formatters.py

        Args:
            result: AgentResponse or similar result object

        Yields:
            Formatted chunks
        """
        async for chunk in format_agent_result(result):
            yield chunk

    # SCALE & SUSTAIN Phase 3.2: Removed 250+ lines of deeply nested formatting code.
    # All formatting logic now in formatters.py with max 3 levels of nesting.

    # =========================================================================
    # LEGACY PLACEHOLDER - DO NOT USE DIRECTLY
    # =========================================================================
    # The old _format_agent_result implementation was 261 lines with 16 levels
    # of nesting. It has been extracted to formatters.py using Strategy pattern.
    # This method now delegates to format_agent_result() from formatters module.

    # =========================================================================
    # PLANNER v6.1 SPECIFIC METHODS
    # =========================================================================

    async def invoke_planner_multi(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Invoke planner with Multi-Plan Generation (v6.1).

        Generates 3 alternative plans with different strategies:
        - STANDARD: Conservative, low-risk approach
        - ACCELERATOR: Fast execution, higher risk
        - LATERAL: Creative, unconventional approach
        """
        agent = await self.get_agent("planner")

        if agent is None:
            yield "❌ Planner agent not available"
            return

        if not hasattr(agent, 'generate_multi_plan'):
            yield "⚠️ Planner doesn't support multi-plan (requires v6.1+)\n"
            async for chunk in self.invoke("planner", task, context):
                yield chunk
            return

        try:
            from vertice_core import AgentTask
            agent_task = AgentTask(request=task, context=context or {})

            yield "🎯 **Generating 3 Alternative Plans...**\n\n"

            result = await agent.generate_multi_plan(agent_task)
            yield result.to_markdown()

        except Exception as e:
            yield f"❌ Multi-plan generation failed: {e}"

    async def invoke_planner_clarify(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Invoke planner with Clarification Mode (v6.1).

        Before planning, the agent asks 2-3 clarifying questions.
        """
        agent = await self.get_agent("planner")

        if agent is None:
            yield "❌ Planner agent not available"
            return

        if not hasattr(agent, 'generate_clarifying_questions'):
            yield "⚠️ Planner doesn't support clarification (requires v6.1+)\n"
            async for chunk in self.invoke("planner", task, context):
                yield chunk
            return

        try:
            from vertice_core import AgentTask
            agent_task = AgentTask(request=task, context=context or {})

            yield "🤔 **Analyzing your request...**\n\n"

            questions = await agent.generate_clarifying_questions(agent_task)

            if questions:
                yield "Before I create a plan, I have some questions:\n\n"
                for i, q in enumerate(questions, 1):
                    yield f"**{i}.** {q.question}\n"
                    if q.options:
                        for opt in q.options:
                            yield f"   - {opt}\n"
                    yield "\n"
                yield "\n💡 *Answer these questions, then run `/plan` again with the context.*\n"
            else:
                yield "✅ No clarification needed. Proceeding with planning...\n\n"
                async for chunk in self.invoke("planner", task, context):
                    yield chunk

        except Exception as e:
            yield f"❌ Clarification failed: {e}"

    async def invoke_planner_explore(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """
        Invoke planner in Exploration Mode (v6.1).

        Read-only analysis mode - gathers context without modifications.
        """
        agent = await self.get_agent("planner")

        if agent is None:
            yield "❌ Planner agent not available"
            return

        if not hasattr(agent, 'explore'):
            yield "⚠️ Planner doesn't support exploration (requires v6.1+)\n"
            async for chunk in self.invoke("planner", task, context):
                yield chunk
            return

        try:
            from vertice_core import AgentTask
            agent_task = AgentTask(request=task, context=context or {})

            yield "🔍 **Exploration Mode (Read-Only)**\n\n"
            yield "_No modifications will be made - analysis only._\n\n"

            result = await agent.explore(agent_task)

            if result.success:
                exploration = result.data.get('exploration', {})

                if 'files_analyzed' in exploration:
                    yield f"**📁 Files Analyzed:** {exploration['files_analyzed']}\n\n"

                if 'key_findings' in exploration:
                    yield "**🔑 Key Findings:**\n"
                    for finding in exploration['key_findings']:
                        yield f"- {finding}\n"
                    yield "\n"

                if 'dependencies' in exploration:
                    yield "**🔗 Dependencies:**\n"
                    for dep in exploration['dependencies'][:10]:
                        yield f"- {dep}\n"
                    yield "\n"

                if 'recommendations' in exploration:
                    yield "**💡 Recommendations:**\n"
                    for rec in exploration['recommendations']:
                        yield f"- {rec}\n"
                    yield "\n"

                yield "\n✅ *Exploration complete. Use `/plan` to create an execution plan.*\n"
            else:
                yield f"❌ Exploration failed: {result.error}\n"

        except Exception as e:
            yield f"❌ Exploration failed: {e}"

    def detect_planner_mode(self, message: str) -> Optional[str]:
        """
        Detect which planner mode should be used based on message content.

        Returns:
            "multi" | "clarify" | "explore" | None (regular planning)
        """
        # Check for sub-mode patterns
        for mode in ["planner:multi", "planner:clarify", "planner:explore"]:
            patterns = self.router._compiled_patterns.get(mode, [])
            for compiled_pattern, weight in patterns:
                if compiled_pattern.search(message) and weight >= 0.85:
                    return mode.split(":")[1]

        return None
