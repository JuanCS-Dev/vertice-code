# CLI-specific types - Interface layer

from __future__ import annotations

from typing import Any, Callable, List, Optional, TypedDict, TypeAlias
from datetime import datetime
from enum import Enum

# Import domain types for extension
from vertice_core.types import FilePath, JSONDict, MessageList, ErrorInfo, RecoveryStrategy


# ============================================================================
# CONTEXT & STATE TYPES (CLI-specific)
# ============================================================================


class ContextEntry(TypedDict):
    """Single entry in the CLI execution context."""

    key: str
    value: Any
    timestamp: datetime
    source: str


class SessionState(TypedDict):
    """Complete CLI session state for persistence."""

    session_id: str
    cwd: FilePath
    history: List[str]
    conversation: MessageList
    context: JSONDict
    files_read: List[FilePath]
    files_modified: List[FilePath]
    tool_calls_count: int
    created_at: datetime
    last_activity: datetime


# ============================================================================
# WORKFLOW & ORCHESTRATION TYPES (CLI-specific)
# ============================================================================


class WorkflowStep(TypedDict):
    """Single step in a CLI workflow."""

    id: str
    name: str
    tool: str
    arguments: JSONDict
    depends_on: List[str]
    timeout_seconds: float
    retry_policy: Optional[RecoveryStrategy]


class WorkflowDefinition(TypedDict):
    """Complete CLI workflow definition."""

    id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    rollback_steps: Optional[List[WorkflowStep]]


class WorkflowState(str, Enum):
    """State of a CLI workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class WorkflowExecution(TypedDict):
    """State of a CLI workflow execution."""

    workflow_id: str
    state: WorkflowState
    current_step: Optional[str]
    completed_steps: List[str]
    failed_step: Optional[str]
    error: Optional[ErrorInfo]
    started_at: datetime
    completed_at: Optional[datetime]


# ============================================================================
# CONFIGURATION TYPES (CLI-specific)
# ============================================================================


class ProviderConfig(TypedDict, total=False):
    """Configuration for a CLI LLM provider."""

    api_key: str
    base_url: str
    model: str
    timeout: float
    max_retries: int


class AppConfig(TypedDict, total=False):
    """CLI application configuration."""

    # LLM providers
    hf_token: str
    nebius_api_key: str
    gemini_api_key: str
    ollama_enabled: bool

    # Models
    hf_model: str
    gemini_model: str

    # Limits
    max_context_tokens: int
    max_output_tokens: int

    # Features
    enable_sandbox: bool
    enable_hooks: bool
    enable_recovery: bool


# ============================================================================
# CALLBACK TYPES (CLI-specific)
# ============================================================================

ProgressCallback: TypeAlias = Callable[[float, str], None]
ErrorCallback: TypeAlias = Callable[[ErrorInfo], None]
TokenCallback: TypeAlias = Callable[[int, int], None]  # (input_tokens, output_tokens)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ContextEntry",
    "SessionState",
    "WorkflowStep",
    "WorkflowDefinition",
    "WorkflowState",
    "WorkflowExecution",
    "ProviderConfig",
    "AppConfig",
    "ProgressCallback",
    "ErrorCallback",
    "TokenCallback",
]
