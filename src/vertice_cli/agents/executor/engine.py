"""
Code Execution Engine - Multi-backend execution support.

Supports: Local, Docker, E2B (cloud sandbox).
Single responsibility: Execute commands with retries and error recovery.
"""

from __future__ import annotations

import asyncio
import logging
import shlex
import time
import uuid
from contextlib import suppress
from typing import Any, Dict, Optional

from .types import CommandResult, ExecutionMode

logger = logging.getLogger(__name__)


class CodeExecutionEngine:
    """
    Advanced code execution with multiple backend support.

    Features:
    - Multiple execution modes (Local, Docker, E2B)
    - Automatic retries with exponential backoff
    - Resource limits enforcement
    - Timeout handling
    """

    def __init__(
        self,
        mode: ExecutionMode = ExecutionMode.LOCAL,
        timeout: float = 30.0,
        max_retries: int = 3,
        resource_limits: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize code execution engine.

        Args:
            mode: Execution environment mode
            timeout: Maximum execution time in seconds
            max_retries: Number of retry attempts
            resource_limits: Resource constraints (memory, CPU)
        """
        self.mode = mode
        self.timeout = timeout
        self.max_retries = max_retries
        self.resource_limits = resource_limits or {
            "max_memory_mb": 512,
            "max_cpu_percent": 50,
        }
        self.logger = logging.getLogger(__name__)

    async def execute(self, command: str, trace_id: Optional[str] = None) -> CommandResult:
        """Execute command with retries and error recovery."""
        trace_id = trace_id or str(uuid.uuid4())

        for attempt in range(self.max_retries):
            try:
                if self.mode == ExecutionMode.LOCAL:
                    result = await self._execute_local(command, trace_id)
                elif self.mode == ExecutionMode.DOCKER:
                    result = await self._execute_docker(command, trace_id)
                elif self.mode == ExecutionMode.E2B:
                    result = await self._execute_e2b(command, trace_id)
                else:
                    raise ValueError(f"Unsupported execution mode: {self.mode}")

                result.retries = attempt
                return result

            except asyncio.TimeoutError:
                self.logger.warning(
                    f"Execution timeout (attempt {attempt + 1}/{self.max_retries})",
                    extra={"trace_id": trace_id},
                )
                if attempt == self.max_retries - 1:
                    return CommandResult(
                        success=False,
                        stdout="",
                        stderr=f"Execution timed out after {self.timeout}s",
                        exit_code=-1,
                        command=command,
                        execution_time=self.timeout,
                        trace_id=trace_id,
                        retries=attempt + 1,
                    )
                # Exponential backoff
                await asyncio.sleep(2**attempt)

            except Exception as e:
                self.logger.error(
                    f"Execution error: {e}",
                    extra={"trace_id": trace_id},
                    exc_info=True,
                )
                if attempt == self.max_retries - 1:
                    return CommandResult(
                        success=False,
                        stdout="",
                        stderr=str(e),
                        exit_code=-1,
                        command=command,
                        execution_time=0.0,
                        trace_id=trace_id,
                        retries=attempt + 1,
                    )

        # Should not reach here, but satisfy type checker
        return CommandResult(
            success=False,
            stdout="",
            stderr="Max retries exceeded",
            exit_code=-1,
            command=command,
            execution_time=0.0,
            trace_id=trace_id,
            retries=self.max_retries,
        )

    async def _execute_local(self, command: str, trace_id: str) -> CommandResult:
        """Execute command locally with subprocess."""
        start_time = time.time()

        # On Unix, asyncio subprocesses depend on a child watcher that is bound to the
        # current event loop. With function-scoped loops (e.g., in pytest-asyncio),
        # the watcher can remain attached to a closed loop after a timeout/cancel,
        # causing subsequent subprocess waits to hang. Re-attach defensively.
        with suppress(Exception):
            watcher = asyncio.get_child_watcher()
            watcher.attach_loop(asyncio.get_running_loop())

        # SECURITY: Use create_subprocess_exec with shlex.split for safety
        args = shlex.split(command)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.timeout)

            execution_time = time.time() - start_time

            return CommandResult(
                success=(process.returncode == 0),
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=process.returncode or 0,
                command=command,
                execution_time=execution_time,
                trace_id=trace_id,
            )

        except asyncio.TimeoutError:
            with suppress(ProcessLookupError):
                process.kill()
            # Ensure subprocess pipes are closed to avoid leaked transports when the loop closes.
            with suppress(Exception):
                await process.communicate()
            raise

    async def _execute_docker(self, command: str, trace_id: str) -> CommandResult:
        """Execute command in Docker container."""
        docker_cmd = (
            f"docker run --rm --memory={self.resource_limits['max_memory_mb']}m "
            f"--cpus={self.resource_limits['max_cpu_percent'] / 100} "
            f"alpine:latest sh -c '{command}'"
        )

        return await self._execute_local(docker_cmd, trace_id)

    async def _execute_e2b(self, command: str, trace_id: str) -> CommandResult:
        """Execute in E2B cloud sandbox (stub for now)."""
        self.logger.warning("E2B execution not implemented, falling back to local")
        return await self._execute_local(command, trace_id)


__all__ = ["CodeExecutionEngine"]
