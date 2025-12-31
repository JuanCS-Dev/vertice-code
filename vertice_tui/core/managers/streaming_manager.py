"""
StreamingManager - Core streaming and tool execution loop.

Extracted from Bridge as part of Phase 5.1 TUI Lightweight refactoring.

Implements Anthropic's "single-threaded master loop" pattern:
- Simple, predictable control flow
- Tool calls executed in waves (parallel when independent)
- Streaming response with filtered output

References:
- Anthropic: https://www.zenml.io/llmops-database/claude-code-agent-architecture
- Google Style: https://google.github.io/styleguide/pyguide.html
- Facade Pattern: https://refactoring.guru/design-patterns/facade

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Protocol, Tuple

from ..llm_client import ToolCallParser
from ..parsing.stream_filter import StreamFilter
from ..formatting import tool_success_markup, tool_error_markup, agent_routing_markup
from ..parallel_executor import ParallelToolExecutor, ParallelExecutionResult

logger = logging.getLogger(__name__)


class LLMClientProtocol(Protocol):
    """Protocol for LLM clients (Gemini, Prometheus, Maximus)."""

    async def stream(
        self,
        message: str,
        system_prompt: str,
        context: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
    ) -> AsyncIterator[str]:
        """Stream response from LLM."""
        ...


class ToolBridgeProtocol(Protocol):
    """Protocol for tool bridge."""

    def get_schemas_for_llm(self) -> List[Dict[str, Any]]:
        """Get tool schemas for LLM."""
        ...

    async def execute(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute a tool."""
        ...


class AgentManagerProtocol(Protocol):
    """Protocol for agent manager."""

    @property
    def router(self) -> Any:
        """Get the router."""
        ...

    async def invoke(self, agent_name: str, message: str) -> AsyncIterator[str]:
        """Invoke an agent."""
        ...


class StreamingConfig:
    """Configuration for streaming behavior."""

    def __init__(
        self,
        max_tool_iterations: int = 5,
        max_parallel_tools: int = 5,
        show_provider_indicator: bool = True,
        show_parallel_stats: bool = True,
    ):
        """Initialize streaming configuration.

        Args:
            max_tool_iterations: Maximum tool call iterations per chat
            max_parallel_tools: Maximum concurrent tool executions
            show_provider_indicator: Show which provider is being used
            show_parallel_stats: Show parallel execution statistics
        """
        self.max_tool_iterations = max_tool_iterations
        self.max_parallel_tools = max_parallel_tools
        self.show_provider_indicator = show_provider_indicator
        self.show_parallel_stats = show_parallel_stats


class StreamingManager:
    """
    Manages streaming chat with agentic tool execution.

    Implements the core "master loop" pattern:
    1. Stream LLM response
    2. Detect tool calls
    3. Execute tools (parallel when possible)
    4. Feed results back to LLM
    5. Repeat until no more tool calls

    Usage:
        manager = StreamingManager(tools, agents, config)
        async for chunk in manager.stream_chat(client, message, system_prompt, context):
            print(chunk, end='')
    """

    def __init__(
        self,
        tools: ToolBridgeProtocol,
        agents: AgentManagerProtocol,
        config: Optional[StreamingConfig] = None,
    ):
        """Initialize streaming manager.

        Args:
            tools: Tool bridge for executing tools
            agents: Agent manager for routing
            config: Streaming configuration
        """
        self.tools = tools
        self.agents = agents
        self.config = config or StreamingConfig()
        self._parallel_executor = ParallelToolExecutor(
            tool_executor=self._execute_single_tool,
            max_parallel=self.config.max_parallel_tools,
        )

    async def _execute_single_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single tool call.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            result = await self.tools.execute(tool_name, **arguments)
            return {"success": True, "tool_name": tool_name, "data": result}
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            return {"success": False, "tool_name": tool_name, "error": str(e)}

    async def _execute_tools_parallel(
        self, tool_calls: List[Dict[str, Any]]
    ) -> ParallelExecutionResult:
        """Execute tool calls with dependency-aware parallelism.

        Args:
            tool_calls: List of tool calls to execute

        Returns:
            Parallel execution result with timing stats
        """
        return await self._parallel_executor.execute_batch(tool_calls)

    def _format_tool_result(self, result: Dict[str, Any]) -> Tuple[str, str]:
        """Format a tool result for display and LLM feedback.

        Args:
            result: Tool execution result

        Returns:
            Tuple of (display_markup, llm_feedback)
        """
        tool_name = result.get("tool_name", "unknown")

        if result.get("success"):
            display = tool_success_markup(tool_name)
            feedback = f"Tool {tool_name} succeeded: {result.get('data', 'OK')}"
        else:
            error = result.get("error", "Unknown error")
            display = tool_error_markup(tool_name, error)
            feedback = f"Tool {tool_name} failed: {error}"

        return display, feedback

    async def stream_chat(
        self,
        client: LLMClientProtocol,
        message: str,
        system_prompt: str,
        context: List[Dict[str, str]],
        provider_name: str = "",
    ) -> AsyncIterator[str]:
        """Stream chat with agentic tool execution loop.

        This is the core "master loop" that:
        1. Streams LLM response
        2. Detects and executes tool calls
        3. Feeds results back for continuation
        4. Repeats until complete

        Args:
            client: LLM client to use
            message: User message
            system_prompt: System instructions
            context: Conversation context
            provider_name: Name of provider (for display)

        Yields:
            Response chunks for streaming display
        """
        # Show provider indicator
        if self.config.show_provider_indicator and provider_name:
            yield f"[Using {provider_name.upper()}]\n"

        # Agentic loop - process tool calls iteratively
        current_message = message

        for iteration in range(self.config.max_tool_iterations):
            # Stream from LLM
            response_chunks: List[str] = []
            stream_filter = StreamFilter()

            async for chunk in client.stream(
                current_message,
                system_prompt=system_prompt,
                context=context,
                tools=self.tools.get_schemas_for_llm(),
            ):
                response_chunks.append(chunk)

                # Filter chunk to prevent raw JSON leakage
                filtered_chunk = stream_filter.process_chunk(chunk)

                # Don't yield tool call markers directly
                if filtered_chunk and not filtered_chunk.startswith("[TOOL_CALL:"):
                    yield filtered_chunk

            # Flush any remaining text in filter
            remaining = stream_filter.flush()
            if remaining and not remaining.startswith("[TOOL_CALL:"):
                yield remaining

            # Accumulate and check for tool calls
            accumulated = "".join(response_chunks)
            tool_calls = ToolCallParser.extract(accumulated)

            if not tool_calls:
                # No tool calls - we're done
                break

            # Execute tool calls with parallel execution
            exec_result = await self._execute_tools_parallel(tool_calls)

            # Yield results in order for consistent UI
            tool_feedbacks: List[str] = []
            for call_id in sorted(
                exec_result.results.keys(), key=lambda x: int(x.split("_")[1])
            ):
                result = exec_result.results[call_id]
                display, feedback = self._format_tool_result(result)
                yield f"{display}\n"
                tool_feedbacks.append(feedback)

            # Show parallel execution stats
            if (
                self.config.show_parallel_stats
                and len(tool_calls) > 1
                and exec_result.parallelism_factor > 1.0
            ):
                yield (
                    f"\n⚡ *Parallel execution: {exec_result.wave_count} waves, "
                    f"{exec_result.parallelism_factor:.1f}x speedup "
                    f"({exec_result.execution_time_ms:.0f}ms)*\n"
                )

            # Prepare next iteration message with tool results
            current_message = (
                "Tool execution results:\n"
                + "\n".join(tool_feedbacks)
                + "\n\nContinue or summarize."
            )

            yield "\n"  # Spacing between iterations

    async def stream_with_routing(
        self,
        client: LLMClientProtocol,
        message: str,
        system_prompt: str,
        context: List[Dict[str, str]],
        provider_name: str = "",
        auto_route: bool = True,
        agent_registry: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """Stream chat with optional agent routing.

        Enhanced streaming that first checks if message should be
        routed to a specialized agent.

        Args:
            client: LLM client to use
            message: User message
            system_prompt: System instructions
            context: Conversation context
            provider_name: Name of provider (for display)
            auto_route: Whether to auto-route to agents
            agent_registry: Registry of available agents

        Yields:
            Response chunks for streaming display
        """
        # Check for agent routing
        if auto_route and hasattr(self.agents, "router"):
            routing = self.agents.router.route(message)
            if routing:
                agent_name, confidence = routing
                agent_info = (agent_registry or {}).get(agent_name)

                # Show routing decision
                yield f"{agent_routing_markup(agent_name, confidence)}\n"
                if agent_info and hasattr(agent_info, "description"):
                    yield f"   *{agent_info.description}*\n\n"

                # Delegate to agent
                async for chunk in self.agents.invoke(agent_name, message):
                    yield chunk
                return

            # Check for ambiguous routing suggestion
            if hasattr(self.agents.router, "get_routing_suggestion"):
                suggestion = self.agents.router.get_routing_suggestion(message)
                if suggestion:
                    yield f"{suggestion}\n\n"

        # Fall through to regular streaming
        async for chunk in self.stream_chat(
            client, message, system_prompt, context, provider_name
        ):
            yield chunk
