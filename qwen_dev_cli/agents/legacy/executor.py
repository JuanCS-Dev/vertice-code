"""
SimpleExecutorAgent - Direct bash command execution with Gemini 2.5 best practices.

Based on:
- Google Gemini API Function Calling Guide (Nov 2025)
- Anthropic Claude Code Best Practices (Nov 2025)

Design Principles:
1. Single-purpose: Execute bash commands directly
2. Minimal context: No planning, just execution
3. Strong typing: Explicit parameter validation
4. Error resilience: Graceful failure handling
5. Security-first: Allowlist-based permissions (Claude Code pattern)

Permission System (Nov 2025 Claude Code Best Practice):
- Allowlist > Blocklist: Default deny, explicit allow
- Runtime approval flow for write operations
- File-based settings (.maestro/permissions.json)
- Safe YOLO mode: --dangerously-skip-permissions
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass

from .base import (
    BaseAgent,
    AgentTask,
    AgentResponse,
    AgentCapability,
    AgentRole
)
from ..core.llm import LLMClient
from ..core.mcp_client import MCPClient
from ..permissions import PermissionManager, PermissionLevel

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Structured command execution result"""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command: str
    execution_time: float


class SimpleExecutorAgent(BaseAgent):
    """
    Lightweight executor for direct bash commands.

    Permission System (Claude Code Nov 2025 Pattern):
    - Allowlist: Safe read-only commands always permitted
    - Ask User: Write operations require runtime approval
    - Always Deny: Destructive operations blocked

    Use Cases:
    - System queries ("list processes", "show disk usage")
    - File system operations ("find files", "check directory")
    - Quick utilities ("date", "whoami", "pwd")

    NOT for:
    - Complex workflows (use PlannerAgent)
    - Code refactoring (use RefactorerAgent)
    - Code review (use ReviewerAgent)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        mcp_client: MCPClient,
        safe_mode: bool = True,
        approval_callback: Optional[Callable[[str], bool]] = None
    ):
        """Initialize SimpleExecutorAgent.

        Args:
            llm_client: LLM client for intent understanding
            mcp_client: MCP client for tool access
            safe_mode: If True, use allowlist-based permissions
            approval_callback: Function to prompt user for approval (cmd -> bool)
        """
        super().__init__(
            role=AgentRole.PLANNER,  # Using PLANNER role for command planning
            capabilities=[
                AgentCapability.BASH_EXEC,
                AgentCapability.READ_ONLY
            ],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt="You are a bash command executor. Convert user intents to safe bash commands."
        )

        self.safe_mode = safe_mode
        self.approval_callback = approval_callback

        # NEW: PermissionManager v2.0 (Claude Code + OWASP pattern)
        self.permission_manager = PermissionManager(safe_mode=safe_mode)

    async def execute(self, task: AgentTask) -> AgentResponse:
        """Execute bash command directly.

        Flow (Claude Code Nov 2025 + Gemini 2.5 ReAct pattern):
        1. Understand user intent with LLM
        2. Generate bash command
        3. Check permission level (allowlist pattern)
        4. Request approval if needed (ASK_USER)
        5. Execute via BashCommandTool
        6. Return structured result

        Args:
            task: User request

        Returns:
            AgentResponse with command output
        """
        try:
            # Step 1: Use LLM to convert intent → bash command
            bash_command = await self._intent_to_command(task.request)

            # Step 2: Check permission via PermissionManager v2.0
            if self.safe_mode:
                permission_level, reason = self.permission_manager.check_permission(
                    "Bash",
                    {"command": bash_command}
                )

                if permission_level == PermissionLevel.DENY:
                    return AgentResponse(
                        success=False,
                        data={},
                        error=f"🛑 {reason}",
                        reasoning=f"Command blocked: {bash_command}"
                    )

                elif permission_level == PermissionLevel.ASK:
                    # Request approval from user (async callback)
                    if not self.approval_callback:
                        return AgentResponse(
                            success=False,
                            data={},
                            error=f"⚠️  Command requires approval but no callback configured: {bash_command}",
                            reasoning=f"Permission required: {reason}"
                        )

                    # Callback is async, await it
                    import inspect
                    if inspect.iscoroutinefunction(self.approval_callback):
                        approved = await self.approval_callback(bash_command)
                    else:
                        # Fallback for sync callbacks
                        approved = self.approval_callback(bash_command)

                    if not approved:
                        return AgentResponse(
                            success=False,
                            data={},
                            error=f"❌ User denied permission to execute: {bash_command}",
                            reasoning="User rejected command approval prompt"
                        )

                    # Check if user selected "always allow"
                    if hasattr(self.approval_callback, '__self__'):
                        callback_self = self.approval_callback.__self__
                        if hasattr(callback_self, '_last_approval_always'):
                            if callback_self._last_approval_always:
                                # Add to allowlist (Claude Code "always allow" pattern)
                                pattern = f"Bash({bash_command})"
                                self.permission_manager.add_to_allowlist(pattern)
                                # Reset flag
                                callback_self._last_approval_always = False

            # Step 3: Execute command
            result = await self._execute_command(bash_command)

            # Step 4: Format response
            if result.success:
                return AgentResponse(
                    success=True,
                    data={
                        "command": result.command,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.exit_code,
                        "execution_time": result.execution_time
                    },
                    reasoning=f"✅ Executed: {bash_command}"
                )
            else:
                return AgentResponse(
                    success=False,
                    data={
                        "command": result.command,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "exit_code": result.exit_code
                    },
                    error=result.stderr or f"Command failed with exit code {result.exit_code}",
                    reasoning=f"Command: {bash_command}"
                )

        except Exception as e:
            logger.exception(f"Executor failed: {e}")
            return AgentResponse(
                success=False,
                data={},
                error=str(e),
                reasoning="Exception during execution"
            )

    async def _intent_to_command(self, user_request: str) -> str:
        """Convert user intent to bash command using LLM.

        Best Practice (Gemini 2.5):
        - Low temperature (0.0) for deterministic output
        - Clear instructions with examples
        - Strong typing (return single string)

        Args:
            user_request: Natural language request

        Returns:
            Bash command string
        """
        prompt = f"""Convert this user request to a SINGLE bash command.

USER REQUEST: {user_request}

CRITICAL RULES:
1. Return ONLY the bash command, NO explanation or markdown
2. Use FULL commands with proper flags
3. For processes: ALWAYS use `ps aux` (NOT `jobs`, NOT `ps -ef`)
4. For background processes: `ps aux | grep -v grep` or `ps aux --sort=-pid`
5. Use `df -h` for disk usage
6. Use `find` instead of `locate`
7. Prefer simple, direct commands over complex pipes

EXAMPLES:
- "list running processes" → ps aux
- "processos ativos" → ps aux
- "background processes" → ps aux --sort=-pid
- "show disk usage" → df -h
- "what's my username" → whoami
- "current directory" → pwd
- "find python files" → find . -name "*.py"
- "list files" → ls -lah

IMPORTANT:
- If user asks about "background" or "processos ativos", use `ps aux`
- NEVER use `jobs` unless user explicitly says "shell jobs"
- NEVER add explanatory text

COMMAND:"""

        # Use LLM with low temperature for determinism
        # BaseAgent uses llm_client, not llm
        response = await self._call_llm(
            prompt=prompt,
            temperature=0.0,  # Gemini best practice
            max_tokens=100
        )

        # Extract command (strip any markdown formatting)
        command = response.strip()
        if command.startswith('```'):
            # Remove code block markers
            lines = command.split('\n')
            command = '\n'.join([l for l in lines if not l.startswith('```')])
            command = command.strip()

        return command


    async def _execute_command(self, command: str) -> CommandResult:
        """Execute bash command via BashCommandTool.

        Gemini Best Practice:
        - Return structured responses
        - Include execution status and output
        - Provide context for error handling

        Args:
            command: Bash command to execute

        Returns:
            CommandResult with structured output
        """
        import time

        start_time = time.time()

        try:
            # Execute via BashCommandTool
            result = await self._execute_tool(
                "bash_command",
                {"command": command}
            )

            execution_time = time.time() - start_time

            # Parse result
            if result.get("success"):
                return CommandResult(
                    success=True,
                    stdout=result.get("stdout", ""),
                    stderr=result.get("stderr", ""),
                    exit_code=result.get("exit_code", 0),
                    command=command,
                    execution_time=execution_time
                )
            else:
                return CommandResult(
                    success=False,
                    stdout=result.get("stdout", ""),
                    stderr=result.get("error", "Unknown error"),
                    exit_code=result.get("exit_code", 1),
                    command=command,
                    execution_time=execution_time
                )

        except Exception as e:
            execution_time = time.time() - start_time
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                exit_code=-1,
                command=command,
                execution_time=execution_time
            )

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

    async def execute_streaming(self, task: AgentTask):
        """Execute with streaming LLM response for 30 FPS.

        Yields status updates:
        - {"type": "thinking", "text": <token>} - LLM generating command
        - {"type": "command", "text": <bash_command>} - Final command
        - {"type": "result", "data": <AgentResponse>} - Execution result
        """
        try:
            # Step 1: Stream LLM intent → command conversion
            prompt = f"""Convert this user request to a SINGLE bash command.

USER REQUEST: {task.request}

CRITICAL RULES:
1. Return ONLY the bash command, NO explanation or markdown
2. Use FULL commands with proper flags
3. For processes: ALWAYS use `ps aux` (NOT `jobs`, NOT `ps -ef`)
4. For background processes: `ps aux | grep -v grep` or `ps aux --sort=-pid`
5. Use `df -h` for disk usage
6. Use `find` instead of `locate`
7. Prefer simple, direct commands over complex pipes

EXAMPLES:
- "list running processes" → ps aux
- "processos ativos" → ps aux
- "background processes" → ps aux --sort=-pid
- "show disk usage" → df -h
- "what's my username" → whoami
- "current directory" → pwd
- "find python files" → find . -name "*.py"
- "list files" → ls -lah

IMPORTANT:
- If user asks about "background" or "processos ativos", use `ps aux`
- NEVER use `jobs` unless user explicitly says "shell jobs"
- NEVER add explanatory text

COMMAND:"""

            # Stream tokens as LLM generates command
            command_buffer = []
            async for token in self._stream_llm(
                prompt=prompt,
                temperature=0.0,
                max_tokens=100
            ):
                command_buffer.append(token)
                yield {"type": "thinking", "text": token}

            # Extract final command
            bash_command = ''.join(command_buffer).strip()
            if bash_command.startswith('```'):
                lines = bash_command.split('\n')
                bash_command = '\n'.join([l for l in lines if not l.startswith('```')])
                bash_command = bash_command.strip()

            yield {"type": "command", "text": bash_command}

            # Step 2: Permission check
            if self.safe_mode:
                permission_level, reason = self.permission_manager.check_permission(
                    "Bash",
                    {"command": bash_command}
                )

                if permission_level == PermissionLevel.DENY:
                    yield {
                        "type": "result",
                        "data": AgentResponse(
                            success=False,
                            data={},
                            error=f"🛑 {reason}",
                            reasoning=f"Command blocked: {bash_command}"
                        )
                    }
                    return

                elif permission_level == PermissionLevel.ASK:
                    if not self.approval_callback:
                        yield {
                            "type": "result",
                            "data": AgentResponse(
                                success=False,
                                data={},
                                error=f"⚠️ Command requires approval but no callback configured: {bash_command}",
                                reasoning=f"Permission required: {reason}"
                            )
                        }
                        return

                    # Request approval
                    import inspect
                    if inspect.iscoroutinefunction(self.approval_callback):
                        approved = await self.approval_callback(bash_command)
                    else:
                        approved = self.approval_callback(bash_command)

                    if not approved:
                        yield {
                            "type": "result",
                            "data": AgentResponse(
                                success=False,
                                data={},
                                error=f"❌ User denied permission to execute: {bash_command}",
                                reasoning="User rejected command approval prompt"
                            )
                        }
                        return

                    # Check "always allow" flag
                    if hasattr(self.approval_callback, '__self__'):
                        callback_self = self.approval_callback.__self__
                        if hasattr(callback_self, '_last_approval_always'):
                            if callback_self._last_approval_always:
                                pattern = f"Bash({bash_command})"
                                self.permission_manager.add_to_allowlist(pattern)
                                callback_self._last_approval_always = False

            # Step 3: Execute command (no streaming for bash)
            result = await self._execute_command(bash_command)

            # Step 4: Return result
            if result.success:
                yield {
                    "type": "result",
                    "data": AgentResponse(
                        success=True,
                        data={
                            "command": result.command,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "exit_code": result.exit_code,
                            "execution_time": result.execution_time
                        },
                        reasoning=f"✅ Executed: {bash_command}"
                    )
                }
            else:
                yield {
                    "type": "result",
                    "data": AgentResponse(
                        success=False,
                        data={
                            "command": result.command,
                            "stdout": result.stdout,
                            "stderr": result.stderr,
                            "exit_code": result.exit_code
                        },
                        error=result.stderr or f"Command failed with exit code {result.exit_code}",
                        reasoning=f"Command: {bash_command}"
                    )
                }

        except Exception as e:
            logger.exception(f"Executor streaming failed: {e}")
            yield {
                "type": "result",
                "data": AgentResponse(
                    success=False,
                    data={},
                    error=str(e),
                    reasoning="Exception during streaming execution"
                )
            }
