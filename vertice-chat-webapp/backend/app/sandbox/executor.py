"""
Sandbox executor (RCE hard-block).

The 2026 Google-Native architecture must not execute arbitrary Python locally in the API container.
Any code execution capability must be provided by a managed sandbox (Vertex AI Code Interpreter).

This module intentionally keeps the public surface area (types + class) for compatibility, but disables
local execution completely.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


class LocalCodeExecutionDisabledError(RuntimeError):
    """Raised when local code execution is attempted inside the API container."""


@dataclass
class SandboxConfig:
    """Sandbox configuration (kept for API compatibility)."""

    allowed_read_dirs: List[str]
    allowed_write_dirs: List[str]
    allowed_hosts: List[str]
    block_network: bool = False
    max_execution_time: int = 30  # seconds
    max_memory_mb: int = 512
    max_cpu_percent: int = 50


@dataclass
class ExecutionResult:
    """Code execution result (kept for API compatibility)."""

    stdout: str
    stderr: str
    exit_code: Optional[int]
    execution_time: float
    error: Optional[str] = None


class SandboxExecutor:
    """
    Disabled sandbox executor.

    Instantiation is allowed (to preserve imports/config validation), but any attempt to execute code
    raises LocalCodeExecutionDisabledError.
    """

    def __init__(self, config: SandboxConfig) -> None:
        if config.max_execution_time <= 0:
            raise ValueError("max_execution_time must be positive")
        if config.max_memory_mb <= 0:
            raise ValueError("max_memory_mb must be positive")
        if not (1 <= config.max_cpu_percent <= 100):
            raise ValueError("max_cpu_percent must be between 1 and 100")
        self.config = config

    async def execute_python(
        self, code: str, working_dir: Optional[str] = None, timeout: Optional[float] = None
    ) -> ExecutionResult:
        raise LocalCodeExecutionDisabledError(
            "Local code execution is disabled. Use Vertex AI Code Interpreter (managed) instead."
        )
