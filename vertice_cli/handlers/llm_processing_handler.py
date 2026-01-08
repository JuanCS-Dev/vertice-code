"""
LLMProcessingHandler - LLM Request Processing and Command Execution.

SCALE & SUSTAIN Phase 1.5 - Semantic Modularization.

Handles:
- LLM-based request processing with streaming
- Command suggestion and extraction
- Safety validation and confirmation
- Shell command execution with environment management
- Graceful error handling with suggestions

Principles:
- Single Responsibility: LLM interaction lifecycle
- Semantic Clarity: Clear separation of processing phases
- Graceful Degradation: Fallback when LLM unavailable

Author: Vertice Team
Date: 2026-01-02
"""

import logging
import os
import re
import shlex
import time
from typing import TYPE_CHECKING, Any, Dict

if TYPE_CHECKING:
    from vertice_cli.shell_main import InteractiveShell

logger = logging.getLogger(__name__)


class LLMProcessingHandler:
    """
    Handler for LLM-based request processing.

    Manages the complete LLM interaction flow:
    1. Process natural language requests
    2. Get command suggestions from LLM
    3. Validate safety and get confirmation
    4. Execute commands with state management
    5. Handle errors gracefully
    """

    def __init__(self, shell: "InteractiveShell"):
        """
        Initialize with shell reference.

        Args:
            shell: The InteractiveShell instance providing access to
                   llm, console, context, workflow_viz, dashboard, etc.
        """
        self.shell = shell
        self.console = shell.console
        self.llm = shell.llm
        self.context = shell.context
        self.workflow_viz = shell.workflow_viz
        self.dashboard = shell.dashboard
        self.session_state = shell.session_state
        self.rich_context = shell.rich_context
        self.state_transition = shell.state_transition
        self.context_engine = shell.context_engine
        self.enhanced_input = shell.enhanced_input

    # =========================================================================
    # Main Processing Methods
    # =========================================================================

    async def process_request_with_llm(self, user_input: str, suggestion_engine) -> None:
        """
        Process user request with LLM using Cursor+Claude+Gemini patterns.

        Cursor: Multi-step breakdown with visual feedback
        Claude: Explicit state machine + tiered safety
        Gemini: Visual hierarchy + typography

        Args:
            user_input: The user's natural language request.
            suggestion_engine: The suggestion engine instance (legacy).
        """
        from rich.text import Text
        from vertice_cli.shell.safety import assess_risk, danger_detector, error_parser
        from vertice_cli.tui.components.workflow_visualizer import StepStatus
        from vertice_cli.tui.components.dashboard import OperationStatus

        # Generate operation ID for dashboard tracking
        op_id = f"llm_request_{int(time.time() * 1000)}"

        # Track user message in session (AIR GAP #2)
        self.session_state.add_message("user", user_input)

        # P2: Build rich context (enhanced)
        context_dict = self.rich_context.build_rich_context(
            include_git=True, include_env=True, include_recent=True
        )

        # Show analyzing status
        text = Text("💭 Analyzing request...", style="cyan")
        self.console.print(text)
        start_time = time.time()

        # PHASE 2: Stream LLM response with visual feedback
        try:
            from vertice_cli.shell.streaming_integration import stream_llm_response

            # Build system prompt (fix - convert list items to strings)
            recent_files_str = ", ".join(
                [
                    str(f) if isinstance(f, dict) else f
                    for f in context_dict.get("recent_files", [])[:5]
                ]
            )

            system_prompt = f"""You are an AI code assistant with access to the following context:

Project: {os.getcwd()}
Recent files: {recent_files_str}
Git status: {context_dict.get("git_status", "N/A")}

Provide clear, actionable suggestions."""

            # Stream the response with visual feedback
            suggestion = await stream_llm_response(
                llm_client=self.llm,
                prompt=user_input,
                console=self.console,
                workflow_viz=None,  # Disabled for now
                context_engine=self.context_engine,
                system_prompt=system_prompt,
            )

        except (RuntimeError, ValueError) as e:
            logger.error("LLM stream failed", exc_info=True)
            self.console.print(f"[red]❌ LLM failed: {e}[/red]")
            self.console.print(
                "[yellow]💡 AI Tip: Check your API key and network connection.[/yellow]"
            )
            return

        elapsed = time.time() - start_time
        self.console.print(f"[dim]✓ Response generated in {elapsed:.1f}s[/dim]")

        # Step 3/3: Show suggestion (Gemini: visual hierarchy)
        self.console.print()
        self.console.print(f"[dim]You:[/dim] {user_input}")
        self.console.print()
        self.console.print("[bold]🤖 AI Suggested action:[/bold]")
        self.console.print(f"   [cyan]{suggestion}[/cyan]")
        self.console.print()

        # P1: Danger detection with visual warnings
        self.workflow_viz.add_step("safety", "Safety check", StepStatus.RUNNING)
        danger_warning = danger_detector.analyze(suggestion)

        if danger_warning:
            self.workflow_viz.update_step_status("safety", StepStatus.WARNING)
            # Show rich visual warning
            warning_panel = danger_detector.get_visual_warning(danger_warning)
            self.console.print(warning_panel)
            self.console.print()

            # Get appropriate confirmation prompt
            prompt_text = danger_detector.format_confirmation_prompt(danger_warning, suggestion)
            self.console.print(prompt_text, end="")

            user_confirmation = input()

            # Validate confirmation
            if not danger_detector.validate_confirmation(
                danger_warning, user_confirmation, suggestion
            ):
                self.console.print("[yellow]❌ Cancelled - confirmation failed[/yellow]")
                return

            self.console.print("[green]✓ Confirmation accepted[/green]")
        else:
            # Old safety system as fallback
            risk = assess_risk(suggestion)
            safety_level = self.get_safety_level(suggestion)

            if safety_level == 2:  # Dangerous (fallback for old system)
                self.console.print("[red]⚠️  DANGEROUS COMMAND[/red]")
                self.console.print(f"[yellow]This will: {risk.description}[/yellow]")
                confirm = input("Type command name to confirm: ").strip()
                if confirm != suggestion.split()[0]:
                    self.console.print("[yellow]Cancelled[/yellow]")
                    return
            elif safety_level == 1:  # Needs confirmation
                self.console.print("[yellow]⚠️  Requires confirmation[/yellow]")
                confirm = input("Execute? [y/N] ").strip().lower()
                if confirm not in ["y", "yes"]:
                    self.console.print("[dim]Cancelled[/dim]")
                    return
            else:  # Safe
                self.console.print("[green]✓ Safe command[/green]")
                confirm = input("Execute? [Y/n] ").strip().lower()
                if not confirm:  # Default yes for safe commands
                    confirm = "y"
                if confirm not in ["y", "yes"]:
                    self.console.print("[dim]Cancelled[/dim]")
                    return

        # [EXECUTING] Run command
        self.state_transition.transition_to("executing")
        self.workflow_viz.update_step_status("safety", StepStatus.COMPLETED)
        self.workflow_viz.add_step("execute", "Executing command", StepStatus.RUNNING)

        # Animated status message (Task 1.5)
        text = Text("[EXECUTING] Running command...", style="cyan")
        self.console.print(text)
        self.console.print()

        try:
            result = await self.execute_command(suggestion)

            # Show result
            if result.get("success"):
                self.state_transition.transition_to("success")
                self.workflow_viz.update_step_status("execute", StepStatus.COMPLETED)

                # Complete dashboard operation (Task 1.6)
                self.dashboard.complete_operation(
                    op_id, OperationStatus.SUCCESS, tokens_used=0, cost=0.0
                )

                # Animated success message (Task 1.5)
                text = Text("✓ Success", style="green bold")
                self.console.print(text)
                if result.get("output"):
                    self.console.print(result["output"])

                # Track assistant response in session (AIR GAP #2)
                response = f"Executed: {suggestion}\nOutput: {result.get('output', '')[:200]}"
                self.session_state.add_message("assistant", response)
                self.session_state.increment_tool_calls()
            else:
                self.state_transition.transition_to("error")
                self.workflow_viz.update_step_status("execute", StepStatus.FAILED)

                # Complete dashboard operation as error (Task 1.6)
                self.dashboard.complete_operation(op_id, OperationStatus.ERROR)

                # Animated error message (Task 1.5)
                text = Text("❌ AI Execution Failed", style="red bold")
                success = False
                self.console.print(text)

                # P1: Intelligent error parsing
                if result.get("error"):
                    error_text = result["error"]
                    self.console.print(f"[red]{error_text}[/red]")
                    self.console.print()

                    # Parse error and show suggestions
                    analysis = error_parser.parse(error_text, suggestion)

                    # Show user-friendly message
                    self.console.print(f"[yellow]🤖 AI: {analysis.user_friendly}[/yellow]")
                    self.console.print()

                    # Show suggestions
                    if analysis.suggestions:
                        self.console.print("[bold]Suggestions:[/bold]")
                        for i, sug in enumerate(analysis.suggestions[:3], 1):
                            self.console.print(f"  {i}. [cyan]{sug}[/cyan]")
                        self.console.print()

                    # Show auto-fix if available
                    if analysis.can_auto_fix and analysis.auto_fix_command:
                        self.console.print(f"[green]Auto-fix: {analysis.auto_fix_command}[/green]")
                        fix = input("Run auto-fix? [y/N] ").strip().lower()
                        if fix == "y":
                            fix_result = await self.execute_command(analysis.auto_fix_command)
                            if fix_result["success"]:
                                self.console.print("[green]✓ Auto-fix completed[/green]")
                                if fix_result["output"]:
                                    self.console.print(fix_result["output"])

        except (IOError, OSError, ValueError) as e:
            logger.error(f"Command execution failed for '{suggestion}'", exc_info=True)
            self.console.print(f"[red]💥 AI Execution failed: {e}[/red]")
            success = False
        except Exception as e:
            # Catch any other unexpected errors and log with stack trace
            logger.error(
                f"An unexpected error occurred during execution of '{suggestion}'", exc_info=True
            )
            self.console.print(f"[red]🚨 AI System error: {e}[/red]")
            success = False
        finally:
            duration = time.time() - start_time
            await insights_collector.observe_command(
                command=user_input,
                duration=duration,
                success=success,
                context={"handler": "llm_processing"},
            )

        # Add to history
        self.context.history.append(user_input)

    # =========================================================================
    # Command Suggestion Methods
    # =========================================================================

    async def get_command_suggestion(self, user_request: str, context: dict) -> str:
        """
        Get command suggestion from LLM.

        Args:
            user_request: The user's request.
            context: Additional context dict.

        Returns:
            Suggested command string.
        """
        if not self.llm:
            # Fallback: basic regex parsing (Claude: graceful degradation)
            return self.fallback_suggest(user_request)

        # P2: Build prompt with RICH context (Cursor: context injection)
        rich_context = self.rich_context.build_rich_context()
        context_str = self.rich_context.format_context_for_llm(rich_context)

        prompt = f"""User request: {user_request}

{context_str}

Suggest ONE shell command to accomplish this task.
Output ONLY the command, no explanation, no markdown."""

        # Call LLM with error handling
        try:
            response = await self.llm.generate(prompt)

            # Handle None or empty response
            if not response:
                return self.fallback_suggest(user_request)

            # Parse command from response
            command = self.extract_command(response)
            return command

        except (RuntimeError, ValueError, AttributeError, ConnectionError):
            self.console.print("[yellow]🔄 AI Fallback: LLM unavailable, using backup[/yellow]")
            return self.fallback_suggest(user_request)

    def fallback_suggest(self, user_request: str) -> str:
        """
        Fallback suggestion using regex (when LLM unavailable).

        Args:
            user_request: The user's request.

        Returns:
            Best-effort command suggestion.
        """
        req_lower = user_request.lower()

        # Simple pattern matching
        if "large file" in req_lower or "big file" in req_lower:
            return "find . -type f -size +100M"
        elif "process" in req_lower and "memory" in req_lower:
            return "ps aux --sort=-%mem | head -10"
        elif "disk" in req_lower and ("space" in req_lower or "usage" in req_lower):
            return "df -h"
        elif "list" in req_lower and "file" in req_lower:
            return "ls -lah"
        else:
            # Truncate huge inputs to prevent memory issues
            max_display = 100
            truncated = (
                user_request[:max_display] + "..."
                if len(user_request) > max_display
                else user_request
            )
            return f"# Could not parse: {truncated}"

    def extract_command(self, llm_response: str) -> str:
        """
        Extract command from LLM response.

        Args:
            llm_response: Raw LLM response text.

        Returns:
            Extracted command string.
        """
        # Handle None or non-string
        if not llm_response or not isinstance(llm_response, str):
            return "# Could not extract command"

        # Remove markdown code blocks
        code_block = re.search(r"```(?:bash|sh)?\s*\n?(.*?)\n?```", llm_response, re.DOTALL)
        if code_block:
            return code_block.group(1).strip()

        # Remove common prefixes
        lines = llm_response.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                # Remove shell prompt prefix if present
                if line.startswith("$"):
                    line = line[1:].strip()
                if line:  # Only return if there's content after stripping
                    return line

        return llm_response.strip() if llm_response else "# Empty response"

    # =========================================================================
    # Safety Methods
    # =========================================================================

    def get_safety_level(self, command: str) -> int:
        """
        Get safety level (Claude pattern: tiered confirmations).

        Args:
            command: The command to assess.

        Returns:
            Safety level: 0=safe, 1=needs confirmation, 2=dangerous
        """
        from vertice_cli.shell.safety import get_safety_level as get_safety_level_fn

        return get_safety_level_fn(command)

    # =========================================================================
    # Command Execution Methods
    # =========================================================================

    async def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Execute shell command and return result.

        Handles special commands (cd, export, unset) internally
        to maintain context state isolation.

        Args:
            command: The shell command to execute.

        Returns:
            Dict with 'success', 'output', and 'error' keys.
        """
        from vertice_cli.tools.exec_hardened import BashCommandTool

        # Handle state changes manually via Context (Thread Safety Fix)
        cmd_parts = command.strip().split()
        if cmd_parts:
            # Handle 'cd'
            if cmd_parts[0] == "cd":
                return self._handle_cd(cmd_parts, command)

            # Handle 'export'
            if cmd_parts[0] == "export":
                return self._handle_export(command)

            # Handle 'unset'
            if cmd_parts[0] == "unset":
                return self._handle_unset(cmd_parts)

        # PHASE 2: Execute with visual feedback
        bash = BashCommandTool()

        # Show execution status (streaming indicator)
        with self.console.status(
            f"[cyan]⚡ AI Executing:[/cyan] {command[:60]}...", spinner="dots"
        ):
            result = await bash.execute(
                command=command,
                interactive=True,
                cwd=self.enhanced_input.context.cwd,
                env=self.enhanced_input.context.env,
            )

        if result.success:
            return {
                "success": True,
                "output": result.data["stdout"],
                "error": result.data.get("stderr"),
            }
        else:
            return {"success": False, "error": result.error or "Command failed"}

    def _handle_cd(self, cmd_parts: list, command: str) -> Dict[str, Any]:
        """Handle cd command by updating context cwd."""
        target_dir = cmd_parts[1] if len(cmd_parts) > 1 else os.path.expanduser("~")
        try:
            # Expand user/vars using CONTEXT env
            for key, val in self.enhanced_input.context.env.items():
                target_dir = target_dir.replace(f"${key}", val)

            target_dir = os.path.expanduser(target_dir)

            # Resolve relative paths against CONTEXT cwd
            if not os.path.isabs(target_dir):
                target_dir = os.path.abspath(
                    os.path.join(self.enhanced_input.context.cwd, target_dir)
                )

            if os.path.isdir(target_dir):
                # Update Context CWD (No os.chdir!)
                self.enhanced_input.context.cwd = target_dir
                self.console.print(
                    f"[dim]📁 AI Navigation: Changed directory to: {target_dir}[/dim]"
                )
                return {"success": True, "output": "", "error": None}
            else:
                return {"success": False, "error": f"cd: no such file or directory: {target_dir}"}
        except OSError as e:
            logger.warning(f"Error handling 'cd {target_dir}': {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _handle_export(self, command: str) -> Dict[str, Any]:
        """Handle export command by updating context env."""
        try:
            # Re-parse with shlex to handle quotes
            parts = shlex.split(command)
            if len(parts) > 1:
                arg = parts[1]
                if "=" in arg:
                    key, val = arg.split("=", 1)

                    # Expand variables using CONTEXT env
                    for env_key, env_val in self.enhanced_input.context.env.items():
                        val = val.replace(f"${env_key}", env_val)

                    # Update Context Env (No os.environ!)
                    self.enhanced_input.context.env[key] = val
                    self.console.print(f"[dim]✓ Exported: {key}={val}[/dim]")
                    return {"success": True, "output": "", "error": None}
            return {"success": False, "error": "Invalid export syntax"}
        except (ValueError, IndexError) as e:
            logger.warning(f"Error handling export '{command}': {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _handle_unset(self, cmd_parts: list) -> Dict[str, Any]:
        """Handle unset command by removing from context env."""
        try:
            if len(cmd_parts) < 2:
                return {"success": False, "error": "unset: not enough arguments"}
            for key in cmd_parts[1:]:
                self.enhanced_input.context.env.pop(key, None)
            return {"success": True, "output": "", "error": None}
        except KeyError as e:
            # This should not happen with pop(key, None), but as a safeguard
            logger.warning(f"Error handling unset '{' '.join(cmd_parts)}': {e}", exc_info=True)
            return {"success": False, "error": f"Failed to unset variable: {e}"}

    # =========================================================================
    # Error Handling Methods
    # =========================================================================

    async def handle_error(self, error: Exception, user_input: str) -> None:
        """
        Handle errors gracefully (Claude pattern: specific error handlers).

        Never crash, always suggest fix.

        Args:
            error: The exception that occurred.
            user_input: The original user input.
        """
        error_type = type(error).__name__

        # Specific handlers
        if isinstance(error, PermissionError):
            self.console.print("[red]🔒 Permission denied[/red]")
            self.console.print(f"[yellow]💡 AI Suggestion: Try: sudo {user_input}[/yellow]")
            success = False
        elif isinstance(error, FileNotFoundError):
            self.console.print("[red]❌ File or command not found[/red]")
            self.console.print(
                "[yellow]💡 Check if the file exists or install the command[/yellow]"
            )
        elif isinstance(error, TimeoutError):
            self.console.print("[red]⏰ Operation timed out[/red]")
            self.console.print(
                "[yellow]💡 AI Diagnosis: Check network or increase timeout[/yellow]"
            )
        else:
            # Generic fallback
            self.console.print(f"[red]❌ Error: {error_type}[/red]")
            self.console.print(f"[dim]{str(error)}[/dim]")
            self.console.print("[yellow]💡 Try rephrasing your request[/yellow]")
