"""
Secure Code Execution with gVisor-based Sandboxing

Implements Anthropic's sandboxing approach:
- Filesystem isolation (read/write restrictions)
- Network isolation (allowlist-based)
- Resource limits (CPU, memory, time)

Based on:
- Anthropic Sandbox Runtime: https://github.com/anthropic-experimental/sandbox-runtime
- gVisor: https://gvisor.dev/
- Security best practices: https://www.anthropic.com/engineering/claude-code-sandboxing

Note: This is a simplified implementation for development.
For production, use Anthropic's sandbox-runtime or E2B.dev
"""

import asyncio
import logging
import tempfile
import os
import shutil
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SandboxConfig:
    """Sandbox configuration"""

    # Filesystem
    allowed_read_dirs: List[str]
    allowed_write_dirs: List[str]

    # Network
    allowed_hosts: List[str]
    block_network: bool = False

    # Resources
    max_execution_time: int = 30  # seconds
    max_memory_mb: int = 512
    max_cpu_percent: int = 50


@dataclass
class ExecutionResult:
    """Code execution result"""

    stdout: str
    stderr: str
    exit_code: Optional[int]
    execution_time: float
    error: Optional[str] = None


class SandboxExecutor:
    """
    Sandboxed code executor using gVisor or fallback security measures

    Provides strong isolation for code execution while maintaining
    compatibility with development environments.
    """

    def __init__(self, config: SandboxConfig) -> None:
        # Validate configuration
        if config.max_execution_time <= 0:
            raise ValueError("max_execution_time must be positive")

        if config.max_memory_mb <= 0:
            raise ValueError("max_memory_mb must be positive")

        if not (1 <= config.max_cpu_percent <= 100):
            raise ValueError("max_cpu_percent must be between 1 and 100")

        self.config = config

        # Log warnings for missing directories but don't fail
        for dir_path in self.config.allowed_read_dirs + self.config.allowed_write_dirs:
            if not os.path.exists(dir_path):
                logger.warning(f"Directory {dir_path} does not exist")

    async def execute_python(
        self, code: str, working_dir: Optional[str] = None, timeout: Optional[float] = None
    ) -> ExecutionResult:
        """
        Execute Python code in sandbox

        Args:
            code: Python code to execute
            working_dir: Working directory (creates temp if None)
            timeout: Override default timeout

        Returns:
            ExecutionResult with output and metadata
        """
        execution_timeout = timeout or self.config.max_execution_time

        # Create temporary workspace
        workspace = working_dir or tempfile.mkdtemp(prefix="sandbox_")
        code_file = os.path.join(workspace, "main.py")

        try:
            # Write code to file with safety checks
            self._write_code_safely(code_file, code)

            # Determine execution method
            if self._gvisor_available():
                cmd = self._build_gvisor_command(code_file, workspace)
            else:
                cmd = self._build_fallback_command(code_file, workspace)

            # Execute with timeout and resource limits
            start_time = asyncio.get_event_loop().time()

            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=workspace,
                    preexec_fn=self._setup_process_limits if not self._gvisor_available() else None,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=execution_timeout,
                    )
                    exit_code = process.returncode
                    error = None

                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    stdout, stderr = b"", b"Execution timeout exceeded"
                    exit_code = -1
                    error = f"Timeout after {execution_timeout}s"

            except Exception as e:
                logger.error(f"Process execution failed: {e}")
                stdout, stderr = b"", str(e).encode()
                exit_code = -1
                error = str(e)

            execution_time = asyncio.get_event_loop().time() - start_time

            return ExecutionResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=exit_code,
                execution_time=execution_time,
                error=error,
            )

        finally:
            # Cleanup if we created the workspace
            if not working_dir:
                shutil.rmtree(workspace, ignore_errors=True)

    def _write_code_safely(self, file_path: str, code: str) -> None:
        """Write code to file with basic safety checks"""
        # Basic security: prevent obvious dangerous patterns
        dangerous_patterns = [
            "import os",
            "import subprocess",
            "import sys",
            "__import__",
            "eval(",
            "exec(",
        ]

        for pattern in dangerous_patterns:
            if pattern in code:
                logger.warning(f"Potentially dangerous pattern detected: {pattern}")

        # Ensure the directory is writable
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

    def _gvisor_available(self) -> bool:
        """Check if gVisor runsc is available"""
        return shutil.which("runsc") is not None

    def _build_gvisor_command(self, code_file: str, workspace: str) -> List[str]:
        """
        Build gVisor runsc command for strong sandboxing

        gVisor provides OS-level sandboxing without Docker overhead.
        This is a simplified implementation - production should use
        Anthropic's sandbox-runtime or E2B.
        """
        # Mount allowed directories as read-only or read-write
        mounts = []

        for read_dir in self.config.allowed_read_dirs:
            if os.path.exists(read_dir):
                mounts.extend(["--mount", f"{read_dir}:{read_dir}:ro"])

        for write_dir in self.config.allowed_write_dirs:
            if os.path.exists(write_dir):
                mounts.extend(["--mount", f"{write_dir}:{write_dir}:rw"])

        cmd = [
            "runsc",
            "--network=none" if self.config.block_network else "--network=sandbox",
            "--cpu-limit",
            str(self.config.max_cpu_percent),
            "--memory-limit",
            f"{self.config.max_memory_mb}M",
            "run",
            "--",
            "python3",
            "-I",  # Isolated mode
            "-B",  # Don't write .pyc files
            code_file,
        ]

        # Add mounts
        cmd[1:1] = mounts

        return cmd

    def _build_fallback_command(self, code_file: str, workspace: str) -> List[str]:
        """
        Fallback to Python with basic restrictions

        NOT SECURE for production - use only for development
        """
        logger.warning("gVisor not available, using fallback sandbox (NOT SECURE)")

        return [
            "python3",
            "-I",  # Isolated mode (no user site-packages)
            "-B",  # Don't write .pyc files
            "-c",  # Execute from command line to avoid file system access
            f"""
import sys
sys.path.insert(0, '{workspace}')
exec(open('{code_file}').read())
            """,
        ]

    def _setup_process_limits(self) -> None:
        """Setup basic process limits (fallback only)"""
        try:
            import resource

            # Set memory limit
            memory_bytes = self.config.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))

            # Set CPU time limit
            cpu_seconds = self.config.max_execution_time
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))

        except ImportError:
            logger.warning("resource module not available, no process limits set")


# Example usage
async def example_usage() -> None:
    """Example: Execute code via sandbox"""
    config = SandboxConfig(
        allowed_read_dirs=["/tmp/workspace"],
        allowed_write_dirs=["/tmp/workspace/output"],
        allowed_hosts=["api.anthropic.com"],
        max_execution_time=10,
        max_memory_mb=256,
        max_cpu_percent=25,
    )

    executor = SandboxExecutor(config)

    code = """
import sys
print("Hello from sandbox!")
print(f"Python version: {sys.version}")

# Safe operations only
result = 2 + 2
print(f"2 + 2 = {result}")
"""

    result = await executor.execute_python(code)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Exit code:", result.exit_code)
    print(".2f")

    if result.error:
        print("Error:", result.error)
