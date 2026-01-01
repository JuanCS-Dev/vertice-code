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
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from ..llm_client import ToolCallParser
from ..parsing.stream_filter import StreamFilter
from ..formatting import (
    tool_success_markup,
    tool_error_markup,
    agent_routing_markup,
)
from ..parallel_executor import ParallelExecutionResult, ParallelToolExecutor

from .types import (
    ChatConfig,
    LLMClientProtocol,
    ToolBridgeProtocol,
    HistoryProtocol,
    GovernanceProtocol,
    AgentManagerProtocol,
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
            self._execute_single_tool,
            max_parallel=self.config.max_parallel_tools,
        )

    async def _execute_single_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single tool call with observation masking.

        Applies ObservationMasker to compress verbose tool outputs,
        reducing context usage by 60-80% while preserving errors.
        """
        from ..context import mask_tool_output

        try:
            raw_result = await self.tools.execute(tool_name, **arguments)

            # Apply observation masking (research-backed: zero cost, equal quality)
            masked = mask_tool_output(
                output=str(raw_result),
                tool_name=tool_name,
                preserve_errors=True,
            )

            return {
                "success": True,
                "tool_name": tool_name,
                "data": raw_result,  # Full result for immediate use
                "masked": masked.content,  # Compressed for history
                "compression_ratio": masked.compression_ratio,
                "tokens_saved": masked.tokens_saved,
            }
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

    def _determine_thinking_level(self, message: str) -> str:
        """Determine thinking level based on task complexity (Gemini 3 pattern).

        Args:
            message: User message to analyze

        Returns:
            Thinking level: "minimal", "low", "medium", or "high"
        """
        msg_lower = message.lower()

        # High complexity keywords
        keywords_high = [
            "architect", "design", "refactor", "complex", "system",
            "rewrite", "optimize", "infrastructure", "migration"
        ]
        if any(k in msg_lower for k in keywords_high):
            return "high"

        # Low complexity keywords
        keywords_low = [
            "fix", "typo", "simple", "quick", "rename", "update",
            "change", "small", "minor"
        ]
        if any(k in msg_lower for k in keywords_low):
            return "low"

        # Minimal complexity
        keywords_minimal = ["hello", "hi", "help", "what", "how"]
        if any(k in msg_lower for k in keywords_minimal) and len(msg_lower) < 20:
            return "minimal"

        return "medium"

    async def _run_agentic_loop(
        self,
        client: LLMClientProtocol,
        message: str,
        system_prompt: str,
    ) -> AsyncIterator[str]:
        """Run the agentic tool execution loop with ThoughtSignatures.

        Implements Gemini 3-style reasoning continuity:
        - Creates thought signature at start
        - Updates after each tool execution
        - Maintains reasoning chain across iterations

        Args:
            client: LLM client
            message: Current message
            system_prompt: System instructions

        Yields:
            Response chunks
        """
        from ..context import get_thought_manager, ThinkingLevel

        # Initialize thought signature for this reasoning chain
        thought_manager = get_thought_manager()
        thinking_level = ThinkingLevel(self._determine_thinking_level(message))
        thought_manager.set_thinking_level(thinking_level)

        # Create initial signature
        current_signature = thought_manager.create_signature(
            reasoning=f"Starting task: {message[:200]}",
            insights=["User requested task"],
            next_action="Analyze and respond",
            level=thinking_level,
        )
        logger.debug(f"Created thought signature: {current_signature.signature_id}")

        current_message = message
        insights_collected: List[str] = []
        iterations_completed = 0

        for iteration in range(self.config.max_tool_iterations):
            iterations_completed = iteration + 1
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

            # Collect insights from tool execution
            for feedback in tool_feedbacks:
                if "succeeded" in feedback.lower():
                    insights_collected.append(f"Step {iteration+1}: {feedback[:100]}")

            # Update thought signature with new insights
            current_signature = thought_manager.create_signature(
                reasoning=f"Iteration {iteration+1}: Executed {len(tool_calls)} tools",
                insights=insights_collected[-5:],  # Keep last 5 insights
                next_action="Continue execution or summarize",
                level=thinking_level,
            )

            # Prepare next iteration
            current_message = (
                "Tool execution results:\n"
                + "\n".join(tool_feedbacks)
                + "\n\nContinue or summarize."
            )
            yield "\n"

        # Final signature with conclusion
        if iterations_completed > 0:
            thought_manager.create_signature(
                reasoning=f"Completed task after {iterations_completed} iterations",
                insights=insights_collected[-5:] if insights_collected else ["Task completed"],
                next_action="Task complete",
                level=thinking_level,
            )

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
