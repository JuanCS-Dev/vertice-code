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
    # Remote managed execution (optional; fail-closed by default).
    # Set to "vertex_code_execution" to enable Vertex AI managed sandbox execution.
    remote_executor: Optional[str] = None
    vertex_project: Optional[str] = None
    vertex_location: str = "global"
    vertex_model: str = "gemini-3-flash-preview"


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
        if self.config.remote_executor == "vertex_code_execution":
            if not self.config.vertex_project:
                raise ValueError("vertex_project must be set when remote_executor is enabled")

            from app.sandbox.vertex_code_execution import (
                VertexCodeExecutionConfig,
                execute_python_via_vertex_code_execution,
            )

            effective_timeout = float(timeout or self.config.max_execution_time)
            return await execute_python_via_vertex_code_execution(
                code=code,
                timeout=effective_timeout,
                config=VertexCodeExecutionConfig(
                    project=self.config.vertex_project,
                    location=self.config.vertex_location,
                    model=self.config.vertex_model,
                ),
            )

        raise LocalCodeExecutionDisabledError(
            "Local code execution is disabled. Configure remote execution via Vertex AI Code Interpreter."
        )
