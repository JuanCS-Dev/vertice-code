"""
Executor Types - Domain models for code execution.

Enums and dataclasses for the executor agent.
Single responsibility: Define execution-related data structures.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class ExecutionMode(Enum):
    """Execution environment modes."""

    LOCAL = "local"  # Direct execution (fast, less secure)
    DOCKER = "docker"  # Docker container (secure, isolated)
    E2B = "e2b"  # E2B cloud sandbox (highest security)


class SecurityLevel(Enum):
    """Security enforcement levels."""

    PERMISSIVE = 0  # Allow all (development only)
    STANDARD = 1  # Allowlist + user approval
    STRICT = 2  # Allowlist only, no approval
    PARANOID = 3  # Strict + command rewriting + LLM validation


class CommandCategory(Enum):
    """Command risk classification."""

    SAFE_READ = "safe_read"  # ls, cat, pwd, whoami
    SAFE_WRITE = "safe_write"  # mkdir, touch (in allowed dirs)
    PRIVILEGED = "privileged"  # sudo, systemctl
    NETWORK = "network"  # curl, wget, ssh
    DESTRUCTIVE = "destructive"  # rm, dd, mkfs
    EXECUTION = "execution"  # bash, python, eval
    UNKNOWN = "unknown"  # Unclassified


@dataclass
class ExecutionMetrics:
    """Performance and usage metrics."""

    execution_count: int = 0
    total_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    token_usage: Dict[str, int] = field(
        default_factory=lambda: {"input": 0, "output": 0, "total": 0}
    )
    avg_latency: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

    def update(self, success: bool, exec_time: float, tokens: int = 0) -> None:
        """Update metrics after execution."""
        self.execution_count += 1
        self.total_time += exec_time
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
        self.token_usage["total"] += tokens
        self.avg_latency = (
            self.total_time / self.execution_count if self.execution_count > 0 else 0.0
        )
        self.last_updated = datetime.now()


@dataclass
class CommandResult:
    """Enhanced command execution result with full context."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command: str
    execution_time: float
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    security_checks: Dict[str, bool] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    retries: int = 0


__all__ = [
    "ExecutionMode",
    "SecurityLevel",
    "CommandCategory",
    "ExecutionMetrics",
    "CommandResult",
]
