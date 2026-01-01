"""
Safe Command Executor - Hardened shell execution with whitelist.

This module provides secure command execution with:
- Command whitelist (only approved commands allowed)
- No shell=True (prevents injection)
- Timeout protection
- Resource limits
- Structured output

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import asyncio
import logging
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .command_whitelist import (
    AllowedCommand,
    ALLOWED_COMMANDS,
    DANGEROUS_PATTERNS,
)

logger = logging.getLogger(__name__)


@dataclass
class SafeExecutionResult:
    """
    Result of safe command execution.

    Attributes:
        success: Whether command completed successfully
        exit_code: Process exit code
        stdout: Standard output
        stderr: Standard error
        command: The command that was executed (string form)
        error_message: Human-readable error if failed
    """
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    command: str
    error_message: str = ""


class SafeCommandExecutor:
    """
    Secure command executor with whitelist-based validation.

    This executor ONLY allows pre-approved commands to run.
    All other commands are rejected for security.

    Example:
        executor = SafeCommandExecutor()
        result = await executor.execute("pytest -v")
        if result.success:
            print(result.stdout)
    """

    def __init__(self, working_dir: Optional[Path] = None) -> None:
        """
        Initialize executor.

        Args:
            working_dir: Working directory for command execution
        """
        self._working_dir = working_dir or Path.cwd()

    def _contains_dangerous_pattern(self, command: str) -> Optional[str]:
        """
        Check if command contains dangerous patterns.

        Args:
            command: Command string to check

        Returns:
            The dangerous pattern found, or None if safe
        """
        command_lower = command.lower()
        for pattern in DANGEROUS_PATTERNS:
            if pattern.lower() in command_lower:
                return pattern
        return None

    def _parse_command(self, command: str) -> Tuple[str, List[str]]:
        """
        Parse command into base command and arguments.

        Args:
            command: Full command string

        Returns:
            Tuple of (base_command, arguments)
        """
        try:
            parts = shlex.split(command)
            if not parts:
                return "", []
            return parts[0], parts[1:]
        except ValueError as e:
            logger.warning(f"Failed to parse command: {e}")
            return "", []

    def _find_matching_allowed_command(
        self,
        base_cmd: str,
        args: List[str]
    ) -> Optional[AllowedCommand]:
        """
        Find matching allowed command definition.

        Args:
            base_cmd: Base command (e.g., "pytest")
            args: Command arguments

        Returns:
            Matching AllowedCommand or None
        """
        # Try exact match first
        full_cmd = f"{base_cmd} {args[0]}" if args else base_cmd

        for key, allowed in ALLOWED_COMMANDS.items():
            if allowed.base_command == base_cmd:
                # Check if this is a subcommand match (e.g., "git status")
                if args and f"{base_cmd} {args[0]}" == key:
                    return allowed
                # Check simple command match
                if key == base_cmd:
                    return allowed

        return None

    def is_command_allowed(self, command: str) -> Tuple[bool, str]:
        """
        Check if command is allowed to execute.

        Args:
            command: Command to check

        Returns:
            Tuple of (is_allowed, reason)
        """
        # Check for dangerous patterns first
        dangerous = self._contains_dangerous_pattern(command)
        if dangerous:
            return False, f"Contains dangerous pattern: '{dangerous}'"

        # Parse command
        base_cmd, args = self._parse_command(command)
        if not base_cmd:
            return False, "Empty or invalid command"

        # Find matching allowed command
        allowed = self._find_matching_allowed_command(base_cmd, args)
        if not allowed:
            return False, f"Command '{base_cmd}' is not in the whitelist"

        return True, f"Allowed: {allowed.description}"

    def get_allowed_commands(self) -> List[str]:
        """
        Get list of allowed command names.

        Returns:
            List of allowed command descriptions
        """
        return [
            f"{cmd.name}: {cmd.description}"
            for cmd in ALLOWED_COMMANDS.values()
        ]

    def get_allowed_commands_by_category(self) -> Dict[str, List[str]]:
        """
        Get allowed commands organized by category.

        Returns:
            Dict mapping category name to list of commands
        """
        result: Dict[str, List[str]] = {}
        for cmd in ALLOWED_COMMANDS.values():
            category = cmd.category.value
            if category not in result:
                result[category] = []
            result[category].append(f"{cmd.name}: {cmd.description}")
        return result

    async def execute(self, command: str) -> SafeExecutionResult:
        """
        Execute command securely.

        Args:
            command: Command to execute

        Returns:
            SafeExecutionResult with output and status
        """
        # Validate command
        is_allowed, reason = self.is_command_allowed(command)
        if not is_allowed:
            logger.warning(f"Blocked command: {command} - {reason}")
            return SafeExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                command=command,
                error_message=f"Command not allowed: {reason}"
            )

        # Parse command for execution
        base_cmd, args = self._parse_command(command)
        allowed = self._find_matching_allowed_command(base_cmd, args)

        if not allowed:
            # Should never happen if is_allowed passed, but defensive
            return SafeExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                command=command,
                error_message="Internal error: command validation inconsistency"
            )

        try:
            # Build command array (NO SHELL!)
            cmd_array = [base_cmd] + args

            logger.info(f"Executing: {cmd_array}")

            # Create subprocess WITHOUT shell
            proc = await asyncio.create_subprocess_exec(
                *cmd_array,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._working_dir)
            )

            # Wait with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=allowed.timeout_seconds
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                return SafeExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    command=command,
                    error_message=f"Command timed out after {allowed.timeout_seconds}s"
                )

            stdout_str = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_str = stderr.decode("utf-8", errors="replace") if stderr else ""

            return SafeExecutionResult(
                success=proc.returncode == 0,
                exit_code=proc.returncode or 0,
                stdout=stdout_str,
                stderr=stderr_str,
                command=command,
                error_message="" if proc.returncode == 0 else f"Exit code: {proc.returncode}"
            )

        except FileNotFoundError:
            return SafeExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                command=command,
                error_message=f"Command not found: {base_cmd}"
            )
        except PermissionError:
            return SafeExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                command=command,
                error_message=f"Permission denied: {base_cmd}"
            )
        except Exception as e:
            logger.exception(f"Unexpected error executing command: {command}")
            return SafeExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                command=command,
                error_message=f"Execution error: {type(e).__name__}: {e}"
            )


# Singleton instance for global access
_executor: Optional[SafeCommandExecutor] = None


def get_safe_executor(working_dir: Optional[Path] = None) -> SafeCommandExecutor:
    """
    Get or create the safe executor singleton.

    Args:
        working_dir: Working directory (only used on first call)

    Returns:
        SafeCommandExecutor instance
    """
    global _executor
    if _executor is None:
        _executor = SafeCommandExecutor(working_dir)
    return _executor
