"""
Core types for Vertice agents and tasks.

This module defines the fundamental types used across the Vertice ecosystem,
including agent roles, capabilities, tasks, and responses.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Enumeration of available agent roles."""

    ARCHITECT = "architect"
    EXPLORER = "explorer"
    PLANNER = "planner"
    REFACTORER = "refactorer"
    REVIEWER = "reviewer"
    TESTER = "tester"
    SECURITY = "security"
    DOCUMENTATION = "documentation"
    PROMETHEUS = "prometheus"


class AgentCapability(str, Enum):
    """Enumeration of agent capabilities."""

    READ_ONLY = "read_only"
    FILE_EDIT = "file_edit"
    BASH_EXEC = "bash_exec"
    GIT_OPS = "git_ops"
    DESIGN = "design"
    NETWORK = "network"
    DATABASE = "database"


class CapabilityViolationError(Exception):
    """Raised when an agent attempts to use a capability it doesn't have."""

    pass


class AgentTask(BaseModel):
    """A task assigned to an agent."""

    request: str = Field(..., description="The task request text")
    session_id: str = Field(..., description="Session identifier")
    task_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()), description="Unique task identifier"
    )
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Task metadata")
    role: Optional[AgentRole] = Field(default=None, description="Optional agent role")


class AgentResponse(BaseModel):
    """Response from an agent after completing a task."""

    success: bool = Field(..., description="Whether the task was completed successfully")
    reasoning: str = Field(default="", description="Reasoning for the response")
    data: Dict[str, Any] = Field(default_factory=dict, description="Response data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class TaskStatus(str, Enum):
    """Status of a task execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskResult(BaseModel):
    """Result of a task execution."""

    output: str = Field(default="", description="Task output text")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Result metadata")
    artifacts: List[str] = Field(default_factory=list, description="Generated artifact paths")

