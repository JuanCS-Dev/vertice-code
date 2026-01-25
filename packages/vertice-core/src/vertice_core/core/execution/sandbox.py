"""
Execution Sandbox based on Python resource limits.
Provides a safer environment for agent-executed code.
"""

import asyncio
import logging
import resource
import shlex
import os
from typing import Dict, List, Optional, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False
    resource_limit_hit: bool = False


class SandboxExecution:
    """Executes commands with resource limits."""

    def __init__(
        self,
        cpu_time_limit: int = 30,  # seconds (increased for test suites)
        memory_limit_mb: int = 1024,  # MB (increased for import overhead)
        max_file_size_mb: int = 50,  # MB output
    ):
        self.cpu_time_limit = cpu_time_limit
        self.memory_limit_mb = memory_limit_mb
        self.max_file_size_mb = max_file_size_mb

    def _set_limits(self):
        """Callback to set limits in the child process."""
        try:
            # CPU Time
            # Soft limit sends SIGXCPU, Hard limit sends SIGKILL
            resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_time_limit, self.cpu_time_limit + 5))

            # Memory (AS - Address Space)
            # Warning: extensive imports (like pytorch/tensorflow) can hit this easily
            mem_bytes = self.memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))

            # File size (fsize) - prevent disk filling
            file_bytes = self.max_file_size_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_bytes, file_bytes))

            # Restore signals just in case
            import signal

            signal.signal(signal.SIGPIPE, signal.SIG_DFL)

        except ValueError:
            # Limits might be too high for system, ignore but log
            # We can't log here easily as it's a preexec_fn in child
            pass

    async def run(
        self,
        command: Union[str, List[str]],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> ExecutionResult:
        """Run command in sandbox."""

        if isinstance(command, str):
            args = shlex.split(command)
        else:
            args = command

        # Inherit current env but add overrides
        current_env = os.environ.copy()
        if env:
            current_env.update(env)

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=current_env,
                cwd=cwd,
                preexec_fn=self._set_limits,  # Enforce limits
                limit=1024 * 1024,  # Buffer limit
            )

            try:
                # Add a slightly larger timeout for asyncio to catch the SIGXCPU signal logic
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=self.cpu_time_limit + 5
                )

                return ExecutionResult(
                    returncode=process.returncode or 0,
                    stdout=stdout.decode("utf-8", errors="replace"),
                    stderr=stderr.decode("utf-8", errors="replace"),
                    timed_out=False,
                )

            except asyncio.TimeoutError:
                try:
                    process.kill()
                    await process.wait()
                except ProcessLookupError:
                    pass

                return ExecutionResult(
                    returncode=-1,
                    stdout="",
                    stderr="Execution timed out (Sandbox enforcement)",
                    timed_out=True,
                )

        except Exception as e:
            logger.error(f"Sandbox execution failed: {e}")
            return ExecutionResult(
                returncode=-1,
                stdout="",
                stderr=f"Sandbox error: {str(e)}",
                resource_limit_hit=True,
            )
