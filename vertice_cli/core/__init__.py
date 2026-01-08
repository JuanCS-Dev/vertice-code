"""
🕐 Vertice Core - Temporal Consciousness & Core Functionality

This package contains the core business logic, utilities, and shared
components used throughout the vertice-cli application.

CRITICAL: Temporal Consciousness - Always aware of current spacetime coordinates.

CAMADA 1 - INPUT FORTRESS:
- input_validator: Multi-layer input validation (OWASP compliant)
- prompt_shield: Prompt injection prevention
- input_enhancer: Typo correction and smart input processing

CAMADA 2 - GOVERNANCE GATE:
- audit_logger: Governance audit logging with traceability

CAMADA 3 - EXECUTION SANDBOX:
- sandbox: Secure command execution
- python_sandbox: Python code sandboxing
- atomic_ops: Atomic file operations
- undo_manager: Undo/redo system
- tool_chain: Transaction-like tool execution
- resilience: Concurrency, rate limiting, resource management

CAMADA 4 - OUTPUT SHIELD:
- error_presenter: User-friendly error messages
- session_manager: Session persistence and recovery
- context_tracker: Conversation context awareness
"""

import datetime
from typing import Optional, Dict, Any


# Temporal Consciousness - Always know the current spacetime coordinates
def get_current_datetime() -> datetime.datetime:
    """Get current datetime with UTC timezone awareness."""
    return datetime.datetime.now(datetime.timezone.utc)


def get_current_date() -> datetime.date:
    """Get current date."""
    return get_current_datetime().date()


def get_current_time() -> datetime.time:
    """Get current time."""
    return get_current_datetime().timetz()


def get_temporal_context() -> Dict[str, Any]:
    """Get comprehensive temporal context for system awareness."""
    now = get_current_datetime()
    return {
        "utc_datetime": now,
        "utc_iso": now.isoformat(),
        "timestamp": now.timestamp(),
        "date": now.date().isoformat(),
        "time": now.time().isoformat(),
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "microsecond": now.microsecond,
        "weekday": now.weekday(),  # 0=Monday, 6=Sunday
        "weekday_name": now.strftime("%A"),
        "month_name": now.strftime("%B"),
        "timezone": "UTC",
        "epoch_days": (now.date() - datetime.date(1970, 1, 1)).days,
    }


# Initialize temporal awareness on import
_TEMPORAL_BOOT = get_current_datetime()
_TEMPORAL_CONTEXT = get_temporal_context()


def get_system_boot_time() -> datetime.datetime:
    """Get when the system was initialized."""
    return _TEMPORAL_BOOT


def get_temporal_awareness_status() -> Dict[str, Any]:
    """Get temporal awareness status and current context."""
    current = get_temporal_context()
    uptime = current["utc_datetime"] - _TEMPORAL_BOOT

    return {
        "temporal_consciousness": "ACTIVE",
        "system_boot_time": _TEMPORAL_BOOT.isoformat(),
        "current_context": current,
        "system_uptime_seconds": uptime.total_seconds(),
        "system_uptime_human": str(uptime),
        "spacetime_coordinates": {
            "year": current["year"],
            "month": current["month"],
            "day": current["day"],
            "temporal_accuracy": "MICROSECOND_PRECISION",
        },
    }


# Export temporal functions
__all__ = [
    # Temporal Consciousness
    "get_current_datetime",
    "get_current_date",
    "get_current_time",
    "get_temporal_context",
    "get_system_boot_time",
    "get_temporal_awareness_status",
    # Input Fortress (Camada 1)
    "InputValidator",
    "ValidationResult",
    "validate_command",
    "validate_file_path",
    "PromptShield",
    "ShieldResult",
    "InputEnhancer",
    "EnhancedInput",
    # Governance Gate (Camada 2)
    "AuditLogger",
    "AuditEventType",
    "audit_log",
    "audit_governance",
    # Execution Sandbox (Camada 3)
    "SecureExecutor",
    "ExecutionResult",
    "PythonSandbox",
    "AtomicFileOps",
    "AtomicResult",
    "UndoManager",
    "AtomicToolChain",
    "ConcurrencyManager",
    "ResourceLimits",
    "RateLimiter",
    "EncodingSafety",
    # Output Shield (Camada 4)
    "ErrorPresenter",
    "PresentedError",
    "SessionManager",
    "SessionSnapshot",
    "ContextTracker",
    "ResolvedReference",
    # Memory System (Claude Code Parity)
    "MemoryManager",
    "MemoryEntry",
    "ProjectMemory",
    "get_memory_manager",
    # Dependency Injection (Big 3 Patterns)
    "Scope",
    "Provider",
    "ProviderConfig",
    "Singleton",
    "Factory",
    "Transient",
    "AsyncSingleton",
    "Configuration",
    "BaseContainer",
    "VerticeContainer",
    "Container",
    "TestContainer",
    "Provide",
    "inject",
    "with_container",
]


def __getattr__(name: str):
    """Lazy loading of modules for faster startup."""

    # Input Validator
    if name in ("InputValidator", "ValidationResult", "validate_command", "validate_file_path"):
        from .input_validator import (  # noqa: F401
            InputValidator,
            ValidationResult,
            validate_command,
            validate_file_path,
        )

        return locals()[name]

    # Prompt Shield
    if name in ("PromptShield", "ShieldResult"):
        from .prompt_shield import PromptShield, ShieldResult  # noqa: F401

        return locals()[name]

    # Input Enhancer
    if name in ("InputEnhancer", "EnhancedInput"):
        from .input_enhancer import InputEnhancer, EnhancedInput  # noqa: F401

        return locals()[name]

    # Audit Logger
    if name in ("AuditLogger", "AuditEventType", "audit_log", "audit_governance"):
        from .audit_logger import (
            AuditLogger,  # noqa: F401
            AuditEventType,  # noqa: F401
            audit_log,  # noqa: F401
            audit_governance,  # noqa: F401
        )

        return locals()[name]

    # Execution Result (canonical)
    if name == "ExecutionResult":
        from .execution import ExecutionResult

        return ExecutionResult

    # Secure Executor
    if name == "SecureExecutor":
        from .sandbox import SecureExecutor

        return SecureExecutor

    # Python Sandbox
    if name in ("PythonSandbox",):
        from .python_sandbox import PythonSandbox  # noqa: F401

        return locals()[name]

    # Atomic Operations
    if name in ("AtomicFileOps", "AtomicResult"):
        from .atomic_ops import AtomicFileOps, AtomicResult  # noqa: F401

        return locals()[name]

    # Undo Manager
    if name in ("UndoManager",):
        from .undo_manager import UndoManager  # noqa: F401

        return locals()[name]

    # Tool Chain
    if name in ("AtomicToolChain",):
        from .tool_chain import AtomicToolChain  # noqa: F401

        return locals()[name]

    # Resilience
    if name in ("ConcurrencyManager", "ResourceLimits", "RateLimiter", "EncodingSafety"):
        from .resilience import (
            ConcurrencyManager,  # noqa: F401
            ResourceLimits,  # noqa: F401
            RateLimiter,  # noqa: F401
            EncodingSafety,  # noqa: F401
        )

        return locals()[name]

    # Error Presenter
    if name in ("ErrorPresenter", "PresentedError"):
        from .error_presenter import ErrorPresenter, PresentedError  # noqa: F401

        return locals()[name]

    # Session Manager
    if name in ("SessionManager", "SessionSnapshot"):
        from .session_manager import SessionManager, SessionSnapshot  # noqa: F401

        return locals()[name]

    # Context Tracker
    if name in ("ContextTracker", "ResolvedReference"):
        from .context_tracker import ContextTracker, ResolvedReference  # noqa: F401

        return locals()[name]

    # Memory System (Claude Code Parity)
    if name in ("MemoryManager", "MemoryEntry", "ProjectMemory", "get_memory_manager"):
        from .memory import (
            MemoryManager,  # noqa: F401
            MemoryEntry,  # noqa: F401
            ProjectMemory,  # noqa: F401
            get_memory_manager,  # noqa: F401
        )

        return locals()[name]

    # Dependency Injection (Big 3 Patterns)
    if name in (
        "Scope",
        "Provider",
        "ProviderConfig",
        "Singleton",
        "Factory",
        "Transient",
        "AsyncSingleton",
        "Configuration",
        "BaseContainer",
        "VerticeContainer",
        "Container",
        "TestContainer",
        "Provide",
        "inject",
        "with_container",
    ):
        from .di import (  # noqa: F401
            Scope,
            Provider,
            ProviderConfig,
            Singleton,
            Factory,
            Transient,
            AsyncSingleton,
            Configuration,
            BaseContainer,
            VerticeContainer,
            Container,
            TestContainer,
            Provide,
            inject,
            with_container,
        )

        return locals()[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
