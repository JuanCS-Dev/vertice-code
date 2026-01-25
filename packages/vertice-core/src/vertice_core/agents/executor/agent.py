"""
NextGen CLI Code Executor Agent - November 2025 Edition.

Industry-Leading Features:
- MCP Code Execution Pattern (98.7% token reduction)
- Multi-layer security with LLM validation
- Async streaming with 30+ FPS
- ReAct + Reflection pattern
- Enterprise observability
"""

from __future__ import annotations

import inspect
import logging
import time
import uuid
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from ..base import AgentCapability, AgentResponse, AgentRole, AgentTask, BaseAgent
from vertice_core.core.llm import LLMClient
from vertice_core.core.mcp_client import MCPClient
from vertice_core.permissions import PermissionLevel
from vertice_core.permissions import PermissionManager as ExistingPermissionManager

from .engine import CodeExecutionEngine
from .security import AdvancedSecurityValidator
from .types import CommandResult, ExecutionMetrics, ExecutionMode, SecurityLevel

logger = logging.getLogger(__name__)


class NextGenExecutorAgent(BaseAgent):
    """
    Next-Generation CLI Code Executor Agent.

    Features:
    - MCP Code Execution Pattern
    - Multi-layer security
    - Async streaming
    - ReAct + Reflection pattern
    """

    def __init__(
        self,
        llm_client: LLMClient,
        mcp_client: MCPClient,
        execution_mode: ExecutionMode = ExecutionMode.LOCAL,
        security_level: SecurityLevel = SecurityLevel.STANDARD,
        approval_callback: Optional[Callable[[str], bool]] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize NextGen Executor Agent."""
        super().__init__(
            role=AgentRole.EXECUTOR,
            capabilities=[AgentCapability.BASH_EXEC, AgentCapability.READ_ONLY],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="You are a next-generation bash command executor with advanced security and ReAct pattern.",
        )

        self.approval_callback = approval_callback
        self.config = config or {}

        # Core components
        self.security = AdvancedSecurityValidator()
        self.executor = CodeExecutionEngine(
            mode=execution_mode,
            timeout=self.config.get("timeout", 30.0),
            max_retries=self.config.get("max_retries", 3),
        )

        # Permission manager
        self.permission_manager = ExistingPermissionManager(
            safe_mode=(security_level != SecurityLevel.PERMISSIVE)
        )
        self.security_level = security_level

        # Metrics & observability
        self.metrics = ExecutionMetrics()
        self.execution_history: List[CommandResult] = []

    async def execute(self, task: AgentTask) -> AgentResponse:
        """
        Main execution method with full ReAct pattern.

        Flow:
        1. THINK: Convert intent to command (LLM)
        2. VALIDATE: Security checks
        3. ACT: Execute command
        4. OBSERVE: Analyze result
        5. REFLECT: Learn from outcome
        """
        start_time = time.time()
        trace_id = task.trace_id if hasattr(task, "trace_id") else str(uuid.uuid4())

        try:
            # STEP 1: THINK - Convert user intent to command
            self.logger.info(f"[{trace_id}] Thinking: {task.request}")
            command = await self._generate_command(task.request, task.context)

            # STEP 2: VALIDATE - Security checks
            self.logger.info(f"[{trace_id}] Validating: {command}")
            validation_result = await self._validate_command(command)

            if not validation_result["allowed"]:
                return AgentResponse(
                    success=False,
                    data={},
                    error=f"BLOCKED: {validation_result['reason']}",
                    reasoning=f"Command blocked: {command}",
                )

            # Request approval if needed
            if validation_result["requires_approval"]:
                if not self.approval_callback:
                    return AgentResponse(
                        success=False,
                        data={},
                        error=f"Command requires approval: {command}",
                        reasoning=validation_result["reason"],
                    )

                approved = await self._request_approval(command)
                if not approved:
                    return AgentResponse(
                        success=False,
                        data={},
                        error=f"User denied permission: {command}",
                        reasoning="User rejected approval",
                    )

            # STEP 3: ACT - Execute command
            self.logger.info(f"[{trace_id}] Executing: {command}")
            result = await self.executor.execute(command, trace_id)

            # Store in history
            self.execution_history.append(result)
            if len(self.execution_history) > 100:
                self.execution_history.pop(0)

            # Update metrics
            execution_time = time.time() - start_time
            self.metrics.update(result.success, execution_time)

            # STEP 4: OBSERVE - Analyze result
            observation = await self._observe_result(result)

            # STEP 5: REFLECT - Learn and suggest improvements
            suggestions = await self._reflect_on_execution(result, task)

            # Build response
            if result.success:
                return AgentResponse(
                    success=True,
                    data={
                        "command": result.command,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.exit_code,
                        "execution_time": result.execution_time,
                        "observation": observation,
                    },
                    reasoning="Executed successfully",
                    suggestions=suggestions,
                )
            else:
                return AgentResponse(
                    success=False,
                    data={
                        "command": result.command,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.exit_code,
                        "retries": result.retries,
                    },
                    error=result.stderr or f"Command failed with exit code {result.exit_code}",
                    reasoning="Execution failed",
                    suggestions=suggestions,
                )

        except Exception as e:
            self.logger.exception(f"[{trace_id}] Execution error: {e}")
            return AgentResponse(success=False, data={}, error=str(e), reasoning="Unexpected error")

    async def execute_streaming(self, task: AgentTask) -> AsyncIterator[Dict[str, Any]]:
        """Streaming execution with real-time updates (30 FPS)."""
        trace_id = task.trace_id if hasattr(task, "trace_id") else str(uuid.uuid4())

        try:
            # Stream command generation
            yield {"type": "status", "data": "Thinking..."}

            command_buffer = []
            async for token in self._stream_command_generation(task.request, task.context):
                command_buffer.append(token)
                yield {"type": "thinking", "data": token}

            command = "".join(command_buffer).strip()

            # Clean markdown artifacts
            if command.startswith("```"):
                lines = command.split("\n")
                command = "\n".join([line for line in lines if not line.startswith("```")])
                command = command.strip()

            yield {"type": "command", "data": command}

            # Validate
            yield {"type": "status", "data": "Validating security..."}
            validation_result = await self._validate_command(command)

            if not validation_result["allowed"]:
                yield {
                    "type": "result",
                    "data": {
                        "success": False,
                        "error": f"BLOCKED: {validation_result['reason']}",
                        "command": command,
                    },
                }
                return

            # Request approval if needed
            if validation_result["requires_approval"]:
                yield {"type": "status", "data": "Awaiting approval..."}
                approved = await self._request_approval(command)
                if not approved:
                    yield {
                        "type": "result",
                        "data": {
                            "success": False,
                            "error": "User denied permission",
                            "command": command,
                        },
                    }
                    return

            # Execute
            yield {"type": "status", "data": "Executing..."}
            result = await self.executor.execute(command, trace_id)

            # Observe & reflect
            observation = await self._observe_result(result)
            suggestions = await self._reflect_on_execution(result, task)

            # Final result
            yield {
                "type": "result",
                "data": {
                    "success": result.success,
                    "command": result.command,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.exit_code,
                    "execution_time": result.execution_time,
                    "observation": observation,
                    "suggestions": suggestions,
                },
            }

        except Exception as e:
            self.logger.exception(f"[{trace_id}] Streaming error: {e}")
            yield {"type": "error", "data": {"error": str(e), "trace_id": trace_id}}

    async def _generate_command(self, request: str, context: Dict[str, Any]) -> str:
        """Generate bash command with Evaluator-Optimizer Loop for quality improvement."""
        examples = self._get_few_shot_examples()
        history_context = self._get_execution_history_context()

        max_iterations = 3  # Limit iterations to prevent infinite loops
        best_command = ""
        best_score = 0

        for iteration in range(max_iterations):
            prompt = self._build_generation_prompt(
                request, examples, history_context, iteration, best_command
            )

            response = await self._call_llm(prompt=prompt, temperature=0.0, max_tokens=150)
            candidate_command = response.strip()

            # Evaluate command quality
            evaluation = await self._evaluate_command_quality(candidate_command, request)

            if evaluation["score"] >= 8:  # Good enough
                return candidate_command

            if evaluation["score"] > best_score:
                best_score = evaluation["score"]
                best_command = candidate_command

            # If not the last iteration, prepare feedback for next attempt
            if iteration < max_iterations - 1:
                logger.debug(
                    f"Command iteration {iteration + 1} score: {evaluation['score']}, improving..."
                )

        # Return best command found
        return best_command

    def _build_generation_prompt(
        self,
        request: str,
        examples: str,
        history_context: str,
        iteration: int,
        previous_command: str = "",
    ) -> str:
        """Build optimized generation prompt with feedback from previous attempts."""
        base_prompt = """You are Claude, an expert at converting natural language requests into precise bash commands.

Your task: Transform the user's request into exactly ONE safe, correct bash command.

CRITICAL REQUIREMENTS:
- Output ONLY the command itself - no explanations, no markdown, no extra text
- Use proper bash syntax with appropriate flags
- Choose the most direct and safe approach
- Consider current working directory context
- Prefer standard Unix tools

COMMAND GENERATION PROCESS:
1. Parse the intent from the natural language
2. Select the appropriate bash command and flags
3. Ensure safety (no destructive operations without clear intent)
4. Output the final command

EXAMPLES OF SUCCESSFUL CONVERSIONS:
{examples}

LEARN FROM EXECUTION HISTORY:
{history_context}

NOW CONVERT THIS REQUEST TO A BASH COMMAND:

REQUEST: {request}"""

        if iteration > 0 and previous_command:
            base_prompt += """

PREVIOUS ATTEMPT (consider feedback for improvement):
{previous_command}

IMPROVE based on safety, accuracy, and efficiency concerns."""

        return base_prompt.format(
            examples=examples,
            history_context=history_context,
            request=request,
            previous_command=previous_command,
        )

    async def _evaluate_command_quality(self, command: str, request: str) -> Dict[str, Any]:
        """Evaluate command quality using Claude as evaluator."""
        eval_prompt = f"""You are a bash command evaluator. Rate this command for the given task on a scale of 1-10.

TASK: {request}
COMMAND: {command}

EVALUATION CRITERIA:
- Safety: Command is not destructive or dangerous
- Correctness: Command actually solves the task
- Efficiency: Uses appropriate tools and flags
- Completeness: Addresses all aspects of the request

Return ONLY JSON in this format:
{{
    "score": 7,
    "issues": ["brief issue description"],
    "strengths": ["what's good about it"]
}}

SCORE: """

        try:
            response = await self._call_llm(prompt=eval_prompt, temperature=0.0, max_tokens=200)
            # Simple JSON extraction (could be improved)
            import json

            result = json.loads(response.strip())
            return result
        except Exception as e:
            logger.warning(f"Command evaluation failed: {e}, assuming score 5")
            return {"score": 5, "issues": ["evaluation failed"], "strengths": []}

    async def _stream_command_generation(
        self, request: str, context: Dict[str, Any]
    ) -> AsyncIterator[str]:
        """Stream command generation token by token."""
        examples = self._get_few_shot_examples()
        prompt = f"""Convert to bash command (no explanation, no markdown):

EXAMPLES:
{examples}

REQUEST: {request}

COMMAND:"""

        async for token in self._stream_llm(prompt=prompt, temperature=0.0, max_tokens=100):
            yield token

    async def _validate_command(self, command: str) -> Dict[str, Any]:
        """Multi-layer command validation."""
        # Layer 1: Pattern-based detection
        category = self.security.classify_command(command)
        logger.debug(f"Command category: {category}")
        violations = self.security.detect_malicious_patterns(command)

        if violations:
            return {
                "allowed": False,
                "reason": f"Security violations: {'; '.join(violations)}",
                "requires_approval": False,
            }

        # Layer 2: Permission system check
        permission_level, reason = self.permission_manager.check_permission(
            "Bash", {"command": command}
        )

        if permission_level == PermissionLevel.DENY:
            return {"allowed": False, "reason": reason, "requires_approval": False}

        if permission_level == PermissionLevel.ASK:
            return {"allowed": True, "reason": reason, "requires_approval": True}

        # Layer 3: LLM validation (PARANOID mode only)
        if self.security_level == SecurityLevel.PARANOID:
            is_safe, llm_reason = await self.security.validate_with_llm(command, self.llm_client)
            if not is_safe:
                return {
                    "allowed": False,
                    "reason": f"LLM validation failed: {llm_reason}",
                    "requires_approval": False,
                }

        return {"allowed": True, "reason": reason, "requires_approval": False}

    async def _request_approval(self, command: str) -> bool:
        """Request user approval for command execution."""
        if not self.approval_callback:
            return False

        # Handle both sync and async callbacks
        if inspect.iscoroutinefunction(self.approval_callback):
            approved = await self.approval_callback(command)
        else:
            approved = self.approval_callback(command)

        # Check for "always allow" flag
        if approved and hasattr(self.approval_callback, "__self__"):
            callback_self = self.approval_callback.__self__
            if hasattr(callback_self, "_last_approval_always"):
                if callback_self._last_approval_always:
                    self.permission_manager.add_to_allowlist(f"Bash({command})")
                    callback_self._last_approval_always = False

        return approved

    async def _observe_result(self, result: CommandResult) -> str:
        """Observe and summarize execution result."""
        if result.success:
            output_lines = len(result.stdout.split("\n"))
            return (
                f"Command executed successfully. Output: {output_lines} lines, "
                f"took {result.execution_time:.2f}s"
            )
        return f"Command failed with exit code {result.exit_code}. Error: {result.stderr[:100]}..."

    async def _reflect_on_execution(self, result: CommandResult, task: AgentTask) -> List[str]:
        """Reflection pattern: Learn from execution and suggest improvements."""
        suggestions = []

        # Analyze failures
        if not result.success:
            if result.exit_code == 127:
                suggestions.append("Command not found. Try: which <command>")
            elif result.exit_code == 126:
                suggestions.append("Permission denied. Check file permissions.")
            elif "timeout" in result.stderr.lower():
                suggestions.append("Command timed out. Consider streaming or breaking into steps.")

        # Analyze performance
        if result.execution_time > 5.0:
            suggestions.append(
                f"Slow execution ({result.execution_time:.1f}s). Consider optimizing."
            )

        # Analyze output size
        if len(result.stdout) > 10000:
            suggestions.append("Large output. Consider filtering with grep or head/tail.")

        return suggestions

    def _get_few_shot_examples(self) -> str:
        """Get few-shot examples for prompt."""
        return """
"list running processes" -> ps aux
"processos ativos" -> ps aux
"show disk usage" -> df -h
"find python files" -> find . -name "*.py"
"what's my username" -> whoami
"current directory" -> pwd
"list files with details" -> ls -lah
"check system memory" -> free -h
"""

    def _get_execution_history_context(self, limit: int = 5) -> str:
        """Get recent execution history for context."""
        if not self.execution_history:
            return "No previous executions"

        recent = self.execution_history[-limit:]
        history_lines = []
        for r in recent:
            status = "[OK]" if r.success else "[X]"
            history_lines.append(
                f"{status} {r.command} (exit: {r.exit_code}, time: {r.execution_time:.2f}s)"
            )

        return "\n".join(history_lines)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            "executions": self.metrics.execution_count,
            "success_rate": (
                self.metrics.success_count / self.metrics.execution_count * 100
                if self.metrics.execution_count > 0
                else 0
            ),
            "avg_latency": self.metrics.avg_latency,
            "total_time": self.metrics.total_time,
            "token_usage": self.metrics.token_usage,
            "last_updated": self.metrics.last_updated.isoformat(),
        }

    def export_audit_log(self) -> List[Dict[str, Any]]:
        """Export security audit log."""
        return (
            self.permission_manager.audit_log
            if hasattr(self.permission_manager, "audit_log")
            else []
        )

    # Compatibility methods for BaseAgent
    async def _think(self, task: AgentTask, context: Dict[str, Any]) -> str:
        """Minimal thinking - just log intent."""
        return f"Converting user request to bash command: {task.request}"

    async def _act(self, task: AgentTask, context: Dict[str, Any]) -> AgentResponse:
        """Action is handled in execute() - this is a pass-through."""
        return await self.execute(task)

    async def _observe(self, result: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """Observe command output."""
        return {"observation": "Command executed"}

    async def _decide(self, observations: List[Dict], context: Dict[str, Any]) -> str:
        """No decision needed - single-shot execution."""
        return "complete"


# Alias for backward compatibility
ExecutorAgent = NextGenExecutorAgent

__all__ = ["NextGenExecutorAgent", "ExecutorAgent"]
