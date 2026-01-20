"""
Structured Logging System for Vertice.

Provides correlation IDs, structured logging, and context tracking
for better observability and debugging.
Async-safe implementation using contextvars.
"""

import logging
import uuid
import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from contextvars import ContextVar


class LogLevel(Enum):
    """Structured log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Context for structured logging."""

    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    start_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for logging."""
        return {
            "correlation_id": self.correlation_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "component": self.component,
            "operation": self.operation,
            "duration_ms": round((time.time() - (self.start_time or time.time())) * 1000, 2),
            **self.metadata,
        }


# Async-safe context storage
_log_context_stack: ContextVar[list[LogContext]] = ContextVar("log_context_stack", default=[])


class StructuredLogger:
    """Structured logger with correlation IDs and context tracking."""

    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.level = level

        # Setup standard Python logger
        self._logger = logging.getLogger(f"vertice.{name}")
        self._logger.setLevel(getattr(logging, level.value))

        # Avoid duplicate handlers
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = StructuredFormatter()
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    @contextmanager
    def context(
        self,
        operation: str,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Context manager for operation tracking (Async Safe)."""
        context = LogContext(
            component=component or self.name,
            operation=operation,
            start_time=time.time(),
            metadata=metadata or {},
        )

        # Get current stack (copy to avoid side effects in other branches)
        current_stack = _log_context_stack.get().copy()
        current_stack.append(context)
        token = _log_context_stack.set(current_stack)

        try:
            yield context
        finally:
            _log_context_stack.reset(token)

    def _get_current_context(self) -> Optional[LogContext]:
        """Get current logging context."""
        stack = _log_context_stack.get()
        return stack[-1] if stack else None

    def _log(
        self,
        level: LogLevel,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Internal logging method."""
        context = self._get_current_context()

        # Build structured log data
        log_data = {
            "logger": self.name,
            "level": level.value,
            "message": message,
            "timestamp": time.time(),
        }

        if context:
            log_data.update(context.to_dict())

        if extra:
            log_data.update(extra)

        # Log using standard Python logger
        log_method = getattr(self._logger, level.value.lower())
        log_method(message, extra={"structured": log_data}, exc_info=exc_info)

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log debug message."""
        if self.level.value in ["DEBUG"]:
            self._log(LogLevel.DEBUG, message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log info message."""
        if self.level.value in ["DEBUG", "INFO"]:
            self._log(LogLevel.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """Log warning message."""
        if self.level.value in ["DEBUG", "INFO", "WARNING"]:
            self._log(LogLevel.WARNING, message, extra)

    def error(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log error message."""
        self._log(LogLevel.ERROR, message, extra, exc_info)

    def critical(
        self,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
    ):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, extra, exc_info)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured data."""
        # Extract structured data
        structured = getattr(record, "structured", {})

        # Build formatted message
        timestamp = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(structured.get("timestamp", time.time()))
        )

        level = structured.get("level", record.levelname)
        logger = structured.get("logger", record.name)
        message = structured.get("message", record.getMessage())

        # Build context string
        context_parts = []
        if structured.get("correlation_id"):
            context_parts.append(f"cid={structured['correlation_id'][:8]}")
        if structured.get("component"):
            context_parts.append(f"comp={structured['component']}")
        if structured.get("operation"):
            context_parts.append(f"op={structured['operation']}")
        if structured.get("duration_ms"):
            context_parts.append(f"dur={structured['duration_ms']}ms")

        context_str = f" [{' '.join(context_parts)}]" if context_parts else ""

        return f"[{timestamp}] {level:8} {logger:20}{context_str} {message}"


# Global logger instances
_system_logger = StructuredLogger("system", LogLevel.INFO)
_llm_logger = StructuredLogger("llm", LogLevel.DEBUG)
_agent_logger = StructuredLogger("agent", LogLevel.DEBUG)
_bridge_logger = StructuredLogger("bridge", LogLevel.INFO)
_tool_logger = StructuredLogger("tool", LogLevel.INFO)


def get_system_logger() -> StructuredLogger:
    """Get system-wide logger."""
    return _system_logger


def get_llm_logger() -> StructuredLogger:
    """Get LLM operations logger."""
    return _llm_logger


def get_agent_logger() -> StructuredLogger:
    """Get agent operations logger."""
    return _agent_logger


def get_bridge_logger() -> StructuredLogger:
    """Get bridge operations logger."""
    return _bridge_logger


def get_tool_logger() -> StructuredLogger:
    """Get tool operations logger."""
    return _tool_logger


def create_operation_context(
    operation: str, component: str, metadata: Optional[Dict[str, Any]] = None
):
    """Create a context manager for operation tracking."""
    return get_system_logger().context(operation, component, metadata)
