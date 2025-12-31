"""
ChatController - Core chat orchestration.

Extracted from Bridge.chat() for semantic modularity.

Responsibilities:
- Orchestrate streaming chat with LLM
- Handle agent routing decisions
- Execute agentic tool loop
- Manage conversation context

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

from ..llm_client import ToolCallParser
from ..parsing.stream_filter import StreamFilter
from ..output_formatter import (
    tool_success_markup,
    tool_error_markup,
    agent_routing_markup,
)
from ..parallel_executor import ParallelExecutionResult, ParallelToolExecutor

from .types import (
    ChatConfig,
    ChatResult,
    LLMClientProtocol,
    ToolBridgeProtocol,
    HistoryProtocol,
    GovernanceProtocol,
    AgentManagerProtocol,
    ToolExecutionResult,
)

logger = logging.getLogger(__name__)


class ChatController:
    """
    Controls the chat interaction flow.

    Implements the "single-threaded master loop" pattern:
    1. Receive message
    2. Route to agent if applicable
    3. Stream LLM response
    4. Detect and execute tool calls
    5. Repeat until no more tool calls

    Usage:
        controller = ChatController(tools, history, governance, agents, config)
        async for chunk in controller.chat(client, message, system_prompt):
            print(chunk, end='')
    """

    def __init__(
        self,
        tools: ToolBridgeProtocol,
        history: HistoryProtocol,
        governance: GovernanceProtocol,
        agents: AgentManagerProtocol,
        agent_registry: Dict[str, Any],
        config: Optional[ChatConfig] = None,
    ) -> None:
        """Initialize chat controller.

        Args:
            tools: Tool bridge for executing tools
            history: History manager for context
            governance: Governance observer
            agents: Agent manager for routing
            agent_registry: Registry of available agents
            config: Chat configuration
        """
        self.tools = tools
        self.history = history
        self.governance = governance
        self.agents = agents
        self.agent_registry = agent_registry
        self.config = config or ChatConfig()

        self._parallel_executor = ParallelToolExecutor(
            tool_executor=self._execute_single_tool,
            max_parallel=self.config.max_parallel_tools,
        )

    async def _execute_single_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single tool call."""
        try:
            result = await self.tools.execute(tool_name, **arguments)
            return {"success": True, "tool_name": tool_name, "data": result}
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"success": False, "tool_name": tool_name, "error": str(e)}

    async def _execute_tools_parallel(
        self, tool_calls: List[Dict[str, Any]]
    ) -> ParallelExecutionResult:
        """Execute tool calls with dependency-aware parallelism."""
        return await self._parallel_executor.execute_batch(tool_calls)

    def _format_tool_result(self, result: Dict[str, Any]) -> Tuple[str, str]:
        """Format a tool result for display and LLM feedback."""
        tool_name = result.get("tool_name", "unknown")

        if result.get("success"):
            display = tool_success_markup(tool_name)
            feedback = f"Tool {tool_name} succeeded: {result.get('data', 'OK')}"
        else:
            error = result.get("error", "Unknown error")
            display = tool_error_markup(tool_name, error)
            feedback = f"Tool {tool_name} failed: {error}"

        return display, feedback

    async def _try_agent_routing(
        self, message: str
    ) -> Optional[Tuple[str, float, Any]]:
        """Try to route message to an agent.

        Returns:
            Tuple of (agent_name, confidence, agent_info) or None
        """
        if not self.config.auto_route_enabled:
            return None

        routing = self.agents.router.route(message)
        if routing:
            agent_name, confidence = routing
            agent_info = self.agent_registry.get(agent_name)
            return agent_name, confidence, agent_info

        return None

    async def _run_agentic_loop(
        self,
        client: LLMClientProtocol,
        message: str,
        system_prompt: str,
    ) -> AsyncIterator[str]:
        """Run the agentic tool execution loop.

        Args:
            client: LLM client
            message: Current message
            system_prompt: System instructions

        Yields:
            Response chunks
        """
        current_message = message

        for iteration in range(self.config.max_tool_iterations):
            # Stream from LLM
            response_chunks: List[str] = []
            stream_filter = StreamFilter()

            async for chunk in client.stream(
                current_message,
                system_prompt=system_prompt,
                context=self.history.get_context(),
                tools=self.tools.get_schemas_for_llm(),
            ):
                response_chunks.append(chunk)
                filtered_chunk = stream_filter.process_chunk(chunk)

                if filtered_chunk and not filtered_chunk.startswith("[TOOL_CALL:"):
                    yield filtered_chunk

            # Flush remaining
            remaining = stream_filter.flush()
            if remaining and not remaining.startswith("[TOOL_CALL:"):
                yield remaining

            # Check for tool calls
            accumulated = "".join(response_chunks)
            tool_calls = ToolCallParser.extract(accumulated)

            if not tool_calls:
                break

            # Execute tools in parallel
            exec_result = await self._execute_tools_parallel(tool_calls)

            # Yield results
            tool_feedbacks: List[str] = []
            for call_id in sorted(
                exec_result.results.keys(),
                key=lambda x: int(x.split("_")[1])
            ):
                result = exec_result.results[call_id]
                display, feedback = self._format_tool_result(result)
                yield f"{display}\n"
                tool_feedbacks.append(feedback)

            # Show parallel stats
            if (
                self.config.show_parallel_stats
                and len(tool_calls) > 1
                and exec_result.parallelism_factor > 1.0
            ):
                yield (
                    f"\n⚡ *Parallel: {exec_result.wave_count} waves, "
                    f"{exec_result.parallelism_factor:.1f}x speedup "
                    f"({exec_result.execution_time_ms:.0f}ms)*\n"
                )

            # Prepare next iteration
            current_message = (
                "Tool execution results:\n"
                + "\n".join(tool_feedbacks)
                + "\n\nContinue or summarize."
            )
            yield "\n"

    async def chat(
        self,
        client: LLMClientProtocol,
        message: str,
        system_prompt: str,
        provider_name: str = "",
        skip_routing: bool = False,
    ) -> AsyncIterator[str]:
        """Execute a chat interaction.

        Args:
            client: LLM client to use
            message: User message
            system_prompt: System instructions
            provider_name: Provider name for display
            skip_routing: Skip agent routing

        Yields:
            Response chunks for streaming display
        """
        # Show provider indicator
        if self.config.show_provider_indicator and provider_name:
            yield f"[Using {provider_name.upper()}]\n"

        # Add to history
        self.history.add_command(message)
        self.history.add_context("user", message)

        # Governance observation
        if self.config.show_governance_alerts:
            gov_report = self.governance.observe("chat", message)
            if hasattr(self.governance.config, "alerts") and self.governance.config.alerts:
                if "CRITICAL" in gov_report or "HIGH" in gov_report:
                    yield f"{gov_report}\n\n"

        # Try agent routing
        if not skip_routing:
            routing = await self._try_agent_routing(message)
            if routing:
                agent_name, confidence, agent_info = routing

                yield f"{agent_routing_markup(agent_name, confidence)}\n"
                if agent_info and hasattr(agent_info, "description"):
                    yield f"   *{agent_info.description}*\n\n"

                # Delegate to agent
                async for chunk in self.agents.invoke(agent_name, message):
                    yield chunk
                return

            # Show routing suggestion if ambiguous
            suggestion = self.agents.router.get_routing_suggestion(message)
            if suggestion:
                yield f"{suggestion}\n\n"

        # Run agentic loop
        async for chunk in self._run_agentic_loop(client, message, system_prompt):
            yield chunk

        # Add response to context
        self.history.add_context("assistant", "[Response completed]")
