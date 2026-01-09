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
            raw_result = await self.tools.execute_tool(tool_name, **arguments)

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

    async def _try_agent_routing(self, message: str) -> Optional[Tuple[str, float, Any]]:
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
            "architect",
            "design",
            "refactor",
            "complex",
            "system",
            "rewrite",
            "optimize",
            "infrastructure",
            "migration",
        ]
        if any(k in msg_lower for k in keywords_high):
            return "high"

        # Low complexity keywords
        keywords_low = [
            "fix",
            "typo",
            "simple",
            "quick",
            "rename",
            "update",
            "change",
            "small",
            "minor",
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

            # Debug: Log tool call extraction
            if tool_calls:
                import logging

                logging.getLogger(__name__).info(
                    f"[E2E DEBUG] Extracted {len(tool_calls)} tool calls: {[t[0] for t in tool_calls]}"
                )
            else:
                import logging

                logging.getLogger(__name__).debug(
                    f"[E2E DEBUG] No tool calls found in: {accumulated[:200]}..."
                )

            if not tool_calls:
                break

            # Execute tools in parallel
            import logging

            logging.getLogger(__name__).info(
                f"[E2E DEBUG] Executing tools: {[t[0] for t in tool_calls]}"
            )
            exec_result = await self._execute_tools_parallel(tool_calls)

            # Yield results
            tool_feedbacks: List[str] = []
            for call_id in sorted(exec_result.results.keys(), key=lambda x: int(x.split("_")[1])):
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

    async def chat_with_gating(
        self,
        client: LLMClientProtocol,
        message: str,
        system_prompt: str,
        orchestrator: Any,
        provider_name: str = "",
    ) -> AsyncIterator[str]:
        """
        Execute chat with plan gating (Sprint 2.1).

        Shows the execution plan to the user and waits for approval
        before proceeding with execution.

        Args:
            client: LLM client to use
            message: User message
            system_prompt: System instructions
            orchestrator: Orchestrator agent for planning
            provider_name: Provider name for display

        Yields:
            Response chunks for streaming display
        """
        # Step 1: Generate plan using orchestrator
        try:
            tasks = await orchestrator.plan(message)
        except Exception as e:
            logger.warning(f"Plan generation failed: {e}")
            # Fall back to regular chat
            async for chunk in self.chat(client, message, system_prompt, provider_name):
                yield chunk
            return

        # Step 2: Check if gating is needed
        if len(tasks) < self.config.plan_gating_threshold:
            # Simple request, execute directly
            async for chunk in self.chat(client, message, system_prompt, provider_name):
                yield chunk
            return

        # Step 3: Format and display plan
        plan_display = self._format_plan_display(tasks, message)
        yield plan_display
        yield "\n**Execute this plan?** [Y]es / [N]o / [E]dit\n"

        # Step 4: Get user approval
        if self.config.plan_gating_callback:
            approval = await self.config.plan_gating_callback.request_approval(plan_display)
        else:
            # No callback, auto-approve
            yield "\n*[Auto-approved: no approval callback configured]*\n\n"
            approval = "y"

        # Step 5: Process approval
        approval_lower = approval.lower().strip()

        if approval_lower in ("n", "no"):
            yield "\n**Plan cancelled.**\n"
            return

        if approval_lower in ("e", "edit"):
            yield "\n*[Edit mode not yet implemented - proceeding with original plan]*\n\n"

        # Step 6: Execute approved plan
        yield "\n**Executing plan...**\n\n"

        for i, task in enumerate(tasks, 1):
            yield f"### Task {i}/{len(tasks)}: {task.description[:80]}...\n"

            # Execute task through regular chat flow
            task_message = f"Execute this specific task: {task.description}"
            async for chunk in self.chat(
                client, task_message, system_prompt, provider_name, skip_routing=True
            ):
                yield chunk

            yield f"\n✓ Task {i} completed\n\n"

        yield "**All tasks completed.**\n"

    def _format_plan_display(self, tasks: List[Any], original_request: str) -> str:
        """
        Format execution plan for display.

        Args:
            tasks: List of tasks from orchestrator
            original_request: Original user request

        Returns:
            Formatted plan string
        """
        lines = [
            "─" * 50,
            "📋 **EXECUTION PLAN**",
            "─" * 50,
            "",
            f"**Request:** {original_request[:100]}{'...' if len(original_request) > 100 else ''}",
            "",
            f"**Tasks ({len(tasks)}):**",
        ]

        for i, task in enumerate(tasks, 1):
            # Get task details
            desc = getattr(task, "description", str(task))[:80]
            complexity = getattr(task, "complexity", None)
            complexity_str = f" [{complexity.value}]" if complexity else ""

            lines.append(f"  {i}. {desc}{complexity_str}")

            # Show subtasks if any
            subtasks = getattr(task, "subtasks", [])
            for subtask in subtasks[:3]:
                lines.append(f"     └─ {subtask}")

        lines.append("")
        lines.append("─" * 50)

        return "\n".join(lines)
