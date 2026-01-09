"""
ToolExecutionHandler - Tool Execution and Recovery Handler.

SCALE & SUSTAIN Phase 1.4 - Semantic Modularization.

Handles:
- Tool execution with error recovery
- LLM-based tool call processing
- Conversation context integration
- Workflow visualization integration

Principles:
- Single Responsibility: Tool execution lifecycle
- Semantic Clarity: Clear separation of execution phases
- Scalability: Easy to add new execution strategies

Author: Vertice Team
Date: 2026-01-02
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional


if TYPE_CHECKING:
    from vertice_cli.shell_main import InteractiveShell

logger = logging.getLogger(__name__)


@dataclass
class ErrorResult:
    """Represents an error result from tool execution."""

    success: bool = False
    data: str = ""
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ToolExecutionHandler:
    """
    Handler for tool execution lifecycle.

    Manages the complete tool execution flow:
    1. Parse LLM response for tool calls
    2. Execute tools with recovery
    3. Track results in conversation
    4. Update workflow visualization
    """

    def __init__(self, shell: "InteractiveShell"):
        """
        Initialize with shell reference.

        Args:
            shell: The InteractiveShell instance providing access to
                   registry, console, conversation, recovery engine, etc.
        """
        self.shell = shell
        self.console = shell.console
        self.registry = shell.registry
        self.conversation = shell.conversation
        self.recovery_engine = shell.recovery_engine
        self.context = shell.context
        self.workflow_viz = shell.workflow_viz
        self.dashboard = shell.dashboard
        self.llm = shell.llm

    # =========================================================================
    # Main Execution Methods
    # =========================================================================

    async def process_tool_calls(self, user_input: str) -> str:
        """
        Process user input and execute tools via LLM.

        This is the main entry point for tool-based interactions.
        Integrates with conversation context (Phase 2.3).

        Args:
            user_input: The user's natural language request.

        Returns:
            String result of tool execution or LLM response.
        """
        logger.info("Starting tool call processing for user input.")
        # Start new conversation turn
        turn = self.conversation.start_turn(user_input)

        try:
            # Phase 4: Request Amplification
            # Amplify vague requests with context (Task 8.2: Context injection)
            from vertice_cli.core.request_amplifier import RequestAmplifier

            # Build context from shell state
            amplifier_context = {
                "cwd": self.context.cwd,
                "recent_files": (
                    list(self.context.read_files)[-5:] if self.context.read_files else []
                ),
                "modified_files": (
                    list(self.context.modified_files) if self.context.modified_files else []
                ),
                "git_branch": getattr(self.context, "git_branch", None),
            }

            amplifier = RequestAmplifier(context=amplifier_context)
            amplified_req = await amplifier.analyze(user_input)

            # Task 8.4: Show clarifying questions for low confidence
            if amplified_req.confidence < 0.6 and amplified_req.suggested_questions:
                self.console.print("[yellow]Preciso de mais detalhes / Need more details:[/yellow]")
                for q in amplified_req.suggested_questions[:2]:
                    self.console.print(f"  • {q}")

            # Use amplified request if confidence is high, otherwise use original
            final_input = amplified_req.amplified if amplified_req.confidence > 0.5 else user_input
            logger.debug(
                "Amplified request (confidence: %.2f): '%s'",
                amplified_req.confidence,
                final_input,
            )

            # Show amplification info if different from original
            if amplified_req.amplified != user_input and amplified_req.confidence > 0.5:
                self.console.print(f"[dim]Context: {amplified_req.amplified}[/dim]")

            # Phase 9: Complexity Analysis - Auto-invoke think for complex tasks
            from vertice_cli.core.complexity_analyzer import analyze_complexity
            from vertice_cli.core.intent_classifier import Intent

            # Map string intent to enum
            intent_map = {i.value: i for i in Intent}
            detected_intent = intent_map.get(amplified_req.detected_intent, Intent.GENERAL)

            complexity = analyze_complexity(
                user_input, intent=detected_intent, confidence=amplified_req.confidence
            )
            logger.debug("Complexity analysis score: %.2f", complexity.score)

            # Auto-invoke think for complex tasks
            if complexity.needs_thinking:
                self.console.print(
                    f"[cyan]Pensando... / Thinking... (complexidade/complexity: {complexity.score:.0%})[/cyan]"
                )
                # Prepend think prompt to request
                final_input = f"{complexity.suggested_think_prompt}\n\nAgora execute / Now execute: {final_input}"

            # Build prompt and get LLM response (may include native tool_calls)
            response = await self._get_llm_tool_response(final_input, turn)

            # Extract text content for conversation tracking
            response_text = (
                response.get("content", "") if isinstance(response, dict) else str(response)
            )
            tokens_used = (
                response.get("tokens_used", len(response_text) // 4)
                if isinstance(response, dict)
                else len(response_text) // 4
            )

            # Add LLM response to turn
            self.conversation.add_llm_response(turn, response_text, tokens_used=tokens_used)

            # Try to parse as tool calls (handles both native and text-based)
            tool_calls = self._parse_tool_calls(response)

            if tool_calls:
                logger.info("Found %d tool calls. Proceeding with execution.", len(tool_calls))
                # Add tool calls to turn and execute
                self.conversation.add_tool_calls(turn, tool_calls)
                return await self.execute_tool_calls(tool_calls, turn)

            # If not tool calls, return as regular response
            logger.info("No tool calls found in LLM response.")
            from vertice_cli.core.conversation import ConversationState

            self.conversation.transition_state(ConversationState.IDLE, "text_response_only")
            return response_text

        except (ValueError, TypeError, AttributeError) as e:
            logger.error("Error processing tool calls for input: '%s'", user_input, exc_info=True)
            # Mark error in turn
            turn.error = str(e)
            turn.error_category = "system"
            from vertice_cli.core.conversation import ConversationState

            self.conversation.transition_state(
                ConversationState.ERROR, f"exception: {type(e).__name__}"
            )
            return f"Error processing tool request: {e}"

    async def execute_tool_calls(self, tool_calls: List[Dict[str, Any]], turn) -> str:
        """
        Execute a sequence of tool calls with conversation tracking.

        Args:
            tool_calls: List of tool call dictionaries with 'tool' and 'args'.
            turn: Current conversation turn for tracking.

        Returns:
            Joined string of all tool execution results.
        """
        from vertice_cli.tui.components.workflow_visualizer import StepStatus
        from vertice_cli.tui.components.dashboard import Operation, OperationStatus
        from vertice_cli.tui.components.status import StatusBadge, StatusLevel

        results = []
        logger.info("Executing batch of %d tool calls.", len(tool_calls))

        # Start workflow for multiple tools
        if len(tool_calls) > 1:
            self.workflow_viz.start_workflow(f"Execute {len(tool_calls)} tools")

        for i, call in enumerate(tool_calls):
            tool_name = call.get("tool", "")
            args = call.get("args", {})
            logger.debug("Executing tool '%s' with args: %s", tool_name, args)

            # Add workflow step
            step_id = f"tool_{tool_name}_{i}"
            dependencies = [f"tool_{tool_calls[i-1].get('tool', '')}_{i-1}"] if i > 0 else []
            self.workflow_viz.add_step(
                step_id, f"Execute {tool_name}", StepStatus.PENDING, dependencies=dependencies
            )

            # Get tool from registry
            tool = self.registry.get(tool_name)
            if not tool:
                error_msg = f"Unknown tool: {tool_name}"
                results.append(f"[red]x[/red] {error_msg}")
                self.workflow_viz.update_step_status(step_id, StepStatus.FAILED)
                self.conversation.add_tool_result(
                    turn, tool_name, args, None, success=False, error=error_msg
                )
                continue

            # Start executing step
            self.workflow_viz.update_step_status(step_id, StepStatus.RUNNING)

            # Add operation to dashboard
            op_id = f"{tool_name}_{i}_{int(time.time() * 1000)}"
            operation = Operation(
                id=op_id,
                type=tool_name,
                description=f"{tool_name}({', '.join(f'{k}={v}' for k, v in list(args.items())[:2])})",
                status=OperationStatus.RUNNING,
            )
            self.dashboard.add_operation(operation)

            # Show status badge
            args_str = ", ".join(f"{k}={v}" for k, v in args.items() if len(str(v)) < 50)
            status = StatusBadge(f"{tool_name}({args_str})", StatusLevel.PROCESSING, show_icon=True)
            self.console.print(status.render())

            # Prepare tool arguments
            args = self._prepare_tool_args(tool_name, args)

            # Execute tool with recovery
            result = await self.execute_with_recovery(tool, tool_name, args, turn)

            if not result:
                logger.warning("Tool '%s' failed permanently after recovery attempts.", tool_name)
                results.append(f"[red]x[/red] {tool_name} failed after recovery attempts")
                self.workflow_viz.update_step_status(step_id, StepStatus.FAILED)
                self.dashboard.complete_operation(op_id, OperationStatus.ERROR)
                continue

            # Update workflow and dashboard based on result
            if result.success:
                logger.info("Tool '%s' executed successfully.", tool_name)
                self.workflow_viz.update_step_status(step_id, StepStatus.COMPLETED)
                self.dashboard.complete_operation(
                    op_id,
                    OperationStatus.SUCCESS,
                    tokens_used=(
                        result.metadata.get("tokens", 0) if hasattr(result, "metadata") else 0
                    ),
                    cost=result.metadata.get("cost", 0.0) if hasattr(result, "metadata") else 0.0,
                )
            else:
                logger.warning("Tool '%s' execution failed.", tool_name)
                self.workflow_viz.update_step_status(step_id, StepStatus.FAILED)
                self.dashboard.complete_operation(op_id, OperationStatus.ERROR)

            # Render result using shell's result renderer
            summary = self.shell._result_renderer.render(tool_name, result, args)
            results.append(summary)

        # Complete workflow and show visualization if failures
        if len(tool_calls) > 1:
            self.workflow_viz.complete_workflow()
            if any(
                step.status == StepStatus.FAILED
                for step in self.workflow_viz.current_workflow.steps
            ):
                viz = self.workflow_viz.render_workflow()
                self.console.print("\n")
                self.console.print(viz)

        return "\n".join(results)

    async def execute_with_self_correction(
        self, tool_calls: List[Dict], max_corrections: int = 2, turn: Any = None
    ) -> str:
        """Execute tools with self-correction loop.

        This method attempts to execute tool calls and, if failures occur,
        automatically generates corrections and retries.
        """
        for attempt in range(max_corrections + 1):
            # Execute current batch of tool calls
            results = await self.execute_tool_calls(tool_calls, turn)

            # Simple validation: check if results contain error indicators
            # In a real implementation, this would be more sophisticated
            has_errors = "[red]x[/red]" in results or "Error:" in results

            if not has_errors:
                return results

            # If we have errors and retries left, attempt correction
            if attempt < max_corrections:
                self.console.print(
                    f"[yellow]Attempting self-correction (attempt {attempt+1}/{max_corrections})...[/yellow]"
                )

                # Ask LLM for correction based on errors
                correction_prompt = f"""
Previous tool calls failed.
Tool Calls: {json.dumps(tool_calls)}
Results/Errors: {results}

Please generate corrected tool calls to fix these errors.
"""
                try:
                    # Get correction from LLM
                    response = await self._get_llm_tool_response(correction_prompt, turn)
                    new_tool_calls = self._parse_tool_calls(response)

                    if new_tool_calls:
                        self.console.print(
                            f"[green]Generated {len(new_tool_calls)} corrected tool calls[/green]"
                        )
                        tool_calls = new_tool_calls
                        continue
                    else:
                        self.console.print(
                            "[yellow]Could not generate corrected tool calls[/yellow]"
                        )
                        break
                except (ValueError, json.JSONDecodeError) as e:
                    logger.error("Self-correction LLM call failed", exc_info=True)
                    self.console.print(f"[red]Self-correction failed: {e}[/red]")
                    break

        return results

    # =========================================================================
    # Recovery Methods
    # =========================================================================

    async def execute_with_recovery(
        self, tool, tool_name: str, args: Dict[str, Any], turn
    ) -> Optional[Any]:
        """
        Execute tool with error recovery loop.

        Args:
            tool: The tool instance to execute.
            tool_name: Name of the tool.
            args: Arguments for tool execution.
            turn: Current conversation turn.

        Returns:
            Tool result or None if all recovery attempts fail.
        """
        max_attempts = self.recovery_engine.max_attempts
        logger.info("Executing tool '%s' with up to %d recovery attempts.", tool_name, max_attempts)

        for attempt in range(1, max_attempts + 1):
            result, success = await self._attempt_tool_execution(
                tool, tool_name, args, turn, attempt
            )

            if success:
                if attempt > 1:
                    logger.info(
                        "Successfully recovered tool '%s' on attempt %d.", tool_name, attempt
                    )
                    self.console.print(f"[green]Recovered on attempt {attempt}[/green]")
                return result

            # Try recovery if not last attempt
            if attempt < max_attempts:
                corrected_args = await self._handle_execution_failure(
                    tool_name, args, result, turn, attempt, max_attempts
                )
                if corrected_args:
                    args = corrected_args
            else:
                logger.error(
                    "Tool '%s' failed after %d attempts. No more retries.",
                    tool_name,
                    max_attempts,
                )
                self.console.print(f"[red]x {tool_name} failed after {max_attempts} attempts[/red]")
                return None

        return None

    async def _attempt_tool_execution(
        self, tool, tool_name: str, args: Dict[str, Any], turn, attempt: int
    ) -> tuple:
        """
        Execute single tool attempt and track result.

        Returns:
            Tuple of (result, success_bool).
        """
        logger.debug("Attempt %d: Executing '%s' with args: %s", attempt, tool_name, args)
        try:
            result = await tool.execute(**args)

            # Track tool call
            self.context.track_tool_call(tool_name, args, result)

            # Track in conversation
            self.conversation.add_tool_result(
                turn,
                tool_name,
                args,
                result,
                success=result.success,
                error=None if result.success else str(result.data),
            )

            return result, result.success

        except (TypeError, ValueError, AttributeError) as e:
            logger.warning(
                "Tool '%s' raised a validation or type error on attempt %d",
                tool_name,
                attempt,
                exc_info=True,
            )
            self.conversation.add_tool_result(
                turn, tool_name, args, None, success=False, error=str(e)
            )
            return ErrorResult(success=False, data=str(e)), False
        except Exception as e:
            logger.error(
                "Tool '%s' raised an unexpected exception on attempt %d",
                tool_name,
                attempt,
                exc_info=True,
            )

            # Track exception
            self.conversation.add_tool_result(
                turn, tool_name, args, None, success=False, error=str(e)
            )

            return ErrorResult(success=False, data=str(e)), False

    async def _handle_execution_failure(
        self, tool_name: str, args: Dict[str, Any], result, turn, attempt: int, max_attempts: int
    ) -> Optional[Dict[str, Any]]:
        """
        Handle tool execution failure and attempt recovery.

        Returns:
            Corrected arguments dict or None if recovery fails.
        """
        from vertice_cli.core.recovery import ErrorCategory, create_recovery_context

        error_msg = str(result.data) if result else "Unknown error"
        logger.info(
            "Handling execution failure for '%s' (attempt %d/%d).",
            tool_name,
            attempt,
            max_attempts,
        )
        self.console.print(
            f"[yellow]Attempting recovery for {tool_name} "
            f"(attempt {attempt}/{max_attempts})[/yellow]"
        )

        try:
            # Build recovery context
            recovery_ctx = create_recovery_context(
                error=error_msg,
                tool_name=tool_name,
                args=args,
                category=ErrorCategory.PARAMETER_ERROR,
            )

            # Get diagnosis from LLM
            diagnosis = await self.recovery_engine.diagnose_error(
                recovery_ctx, self.conversation.get_recent_context(max_turns=3)
            )
            logger.debug("Recovery diagnosis: %s", diagnosis)

            if diagnosis:
                self.console.print(f"[dim]Diagnosis: {diagnosis}[/dim]")

            # Attempt parameter correction
            corrected = await self.recovery_engine.attempt_recovery(recovery_ctx, self.registry)

            if corrected and "args" in corrected:
                logger.info("Recovery generated corrected parameters for '%s'.", tool_name)
                self.console.print("[green]Generated corrected parameters[/green]")
                return corrected["args"]
            else:
                logger.warning("Recovery failed to find a correction for '%s'.", tool_name)
                self.console.print("[yellow]No correction found[/yellow]")
                return None

        except (ValueError, TypeError) as e:
            logger.error("Recovery engine failed", exc_info=True)
            self.console.print(f"[red]Recovery error: {e}[/red]")
            return None

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_llm_tool_response(self, user_input: str, turn) -> Dict[str, Any]:
        """
        Get LLM response for tool call processing.

        Uses native function calling when available (Vertex AI, Gemini).
        Falls back to prompt-based tool calling for other providers.

        Returns:
            Dict with 'content', 'tokens_used', and optionally 'tool_calls'.
        """
        tool_schemas = self.registry.get_schemas()

        # Build system prompt (simplified when using native function calling)
        system_prompt = f"""You are an AI code assistant with access to tools for file operations, git, search, and execution.

Current context:
- Working directory: {self.context.cwd}
- Modified files: {list(self.context.modified_files) if self.context.modified_files else 'none'}
- Read files: {list(self.context.read_files) if self.context.read_files else 'none'}
- Conversation turns: {len(self.conversation.turns)}
- Context usage: {self.conversation.context_window.get_usage_percentage():.0%}

INSTRUCTIONS:
1. Analyze the user's request carefully
2. Use the available tools when needed to complete tasks
3. For code-related requests, prefer using tools over generating code directly"""

        # Build messages with conversation context
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last 3 turns)
        context_messages = self.conversation.get_context_for_llm(include_last_n=3)
        messages.extend(context_messages)

        # Add current user input
        messages.append({"role": "user", "content": user_input})

        # Try native function calling first (Vertex AI, Gemini)
        try:
            response = await self.llm.generate_async(
                messages=messages,
                tools=tool_schemas,  # Native function calling
                tool_config="AUTO",
                temperature=0.1,
                max_tokens=2000,
            )

            # If native tool_calls were returned, use them
            if isinstance(response, dict) and response.get("tool_calls"):
                logger.debug(
                    "Native function calling returned %d tool calls", len(response["tool_calls"])
                )
                return response

        except (RuntimeError, ValueError) as e:
            logger.debug("Native function calling not available: %s", e, exc_info=True)

        # Fallback to prompt-based tool calling
        tool_list = [f"- {schema['name']}: {schema['description']}" for schema in tool_schemas]

        fallback_system_prompt = f"""{system_prompt}

Available tools ({len(tool_schemas)} total):
{chr(10).join(tool_list)}

If you need to use tools, respond ONLY with a JSON array of tool calls:
[{{"tool": "tool_name", "args": {{"param": "value"}}}}]

If no tools needed, respond with helpful text."""

        messages[0] = {"role": "system", "content": fallback_system_prompt}

        response = await self.llm.generate_async(
            messages=messages, temperature=0.1, max_tokens=2000
        )

        return response

    def _parse_tool_calls(self, response: Any) -> Optional[List[Dict[str, Any]]]:
        """
        Parse tool calls from LLM response.

        Supports both:
        - Native function calling (dict with 'tool_calls' key)
        - Legacy text parsing (JSON array in text)

        Args:
            response: Either a dict (native) or string (legacy)

        Returns:
            List of tool call dicts or None if parsing fails.
        """
        # Native function calling response (from generate_async)
        if isinstance(response, dict):
            if "tool_calls" in response:
                # Convert from native format to internal format
                return [
                    {"tool": call.get("name"), "args": call.get("arguments", call.get("args", {}))}
                    for call in response["tool_calls"]
                ]
            # Also check content for text-based response
            response_text = response.get("content", "")
        else:
            response_text = str(response)

        # Legacy text parsing fallback
        return self._parse_tool_calls_from_text(response_text)

    def _parse_tool_calls_from_text(self, response_text: str) -> Optional[List[Dict[str, Any]]]:
        """
        Parse tool calls from text response (legacy fallback).

        Args:
            response_text: Text potentially containing JSON tool calls

        Returns:
            List of tool call dicts or None if parsing fails.
        """
        try:
            if "[" in response_text and "]" in response_text:
                start = response_text.index("[")
                end = response_text.rindex("]") + 1
                json_str = response_text[start:end]
                tool_calls = json.loads(json_str)

                if isinstance(tool_calls, list) and tool_calls:
                    return tool_calls
        except (json.JSONDecodeError, ValueError) as e:
            logger.debug("Response is not tool calls JSON: %s", e)

        return None

    def _prepare_tool_args(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare tool arguments with context injection.

        Some tools require additional context from the shell.
        """
        # Session context for context tools
        if tool_name in ["getcontext", "savesession"]:
            args["session_context"] = self.context

        # Console and preview for file tools
        if tool_name in ["write_file", "edit_file"]:
            args["console"] = self.console
            args["preview"] = getattr(self.context, "preview_enabled", True)

        # Semantic search configuration
        if tool_name == "search_files" and getattr(self.shell, "_indexer_initialized", False):
            args["semantic"] = args.get("semantic", True)
            args["indexer"] = self.shell.indexer

        return args
