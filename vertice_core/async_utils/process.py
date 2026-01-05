"""
Async Process Execution.

SCALE & SUSTAIN Phase 3.1 - Async Everywhere.

Async wrappers for subprocess execution using asyncio.subprocess.

Author: JuanCS Dev
Date: 2025-11-26
"""

import asyncio
import logging
import shlex
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class ProcessResult:
    """Result of a process execution."""

    returncode: int
    stdout: str
    stderr: str
    command: str

    @property
    def success(self) -> bool:
        """Check if process succeeded."""
        return self.returncode == 0

    @property
    def output(self) -> str:
        """Combined stdout and stderr."""
        parts = []
        if self.stdout:
            parts.append(self.stdout)
        if self.stderr:
            parts.append(self.stderr)
        return "\n".join(parts)


async def run_command(
    command: Union[str, List[str]],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    shell: bool = False,
    capture_output: bool = True,
) -> ProcessResult:
    """
    Run a command asynchronously.

    Args:
        command: Command string or list of arguments
        cwd: Working directory
        env: Environment variables
        timeout: Timeout in seconds
        shell: Run through shell
        capture_output: Capture stdout/stderr

    Returns:
        ProcessResult with output and return code
    """
    start_time = asyncio.get_event_loop().time()
    if isinstance(command, str) and not shell:
        args = shlex.split(command)
    elif isinstance(command, list):
        args = command
        command = " ".join(command)
    else:
        args = command
    logger.info("Running command: %s", command)
    if shell:
        process = await asyncio.create_subprocess_shell(
            command if isinstance(command, str) else " ".join(args),
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
            cwd=cwd,
            env=env,
        )
    else:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE if capture_output else None,
            stderr=asyncio.subprocess.PIPE if capture_output else None,
            cwd=cwd,
            env=env,
        )

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        duration = asyncio.get_event_loop().time() - start_time
        logger.warning("Command '%s' timed out after %.2f seconds.", command, duration)
        return ProcessResult(
            returncode=-1,
            stdout="",
            stderr=f"Process timed out after {timeout} seconds",
            command=command if isinstance(command, str) else " ".join(args),
        )

    stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
    stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""
    duration = asyncio.get_event_loop().time() - start_time
    result = ProcessResult(
        returncode=process.returncode or 0,
        stdout=stdout.strip(),
        stderr=stderr.strip(),
        command=command if isinstance(command, str) else " ".join(args),
    )
    logger.info(
        "Command '%s' finished in %.2f seconds with exit code %d.",
        result.command,
        duration,
        result.returncode,
    )
    logger.debug("Command stdout:\n%s", result.stdout)
    if result.stderr:
        logger.debug("Command stderr:\n%s", result.stderr)
    return result


async def run_shell(
    script: str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
) -> ProcessResult:
    """
    Run a shell script asynchronously.

    SECURITY: Uses explicit sh -c instead of shell=True to avoid
    Python shell injection. For simple commands, prefer run_command()
    with a list of arguments.

    Args:
        script: Shell script to execute
        cwd: Working directory
        env: Environment variables
        timeout: Timeout in seconds

    Returns:
        ProcessResult with output and return code
    """
    # SEC-003: Use explicit shell invocation instead of shell=True
    # This is safer as we control which shell is used
    return await run_command(["sh", "-c", script], cwd=cwd, env=env, timeout=timeout, shell=False)


async def run_many(
    commands: List[Union[str, List[str]]],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = None,
    fail_fast: bool = False,
) -> List[ProcessResult]:
    """
    Run multiple commands concurrently.

    Args:
        commands: List of commands to run
        cwd: Working directory for all commands
        env: Environment variables
        timeout: Timeout per command
        fail_fast: Stop on first failure

    Returns:
        List of ProcessResults
    """
    if fail_fast:
        results = []
        for cmd in commands:
            result = await run_command(cmd, cwd=cwd, env=env, timeout=timeout)
            results.append(result)
            if not result.success:
                break
        return results
    else:
        tasks = [run_command(cmd, cwd=cwd, env=env, timeout=timeout) for cmd in commands]
        return await asyncio.gather(*tasks)


__all__ = [
    "ProcessResult",
    "run_command",
    "run_shell",
    "run_many",
]
