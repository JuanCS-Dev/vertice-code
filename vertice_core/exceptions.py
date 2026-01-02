"""
Vertice Core Exception Hierarchy.

SCALE & SUSTAIN Phase 2.2/2.3 - Exception Consolidation (Fixed).

This module defines the canonical base exceptions for vertice_core.
It does NOT import from vertice_cli to avoid circular dependencies.

Architecture:
    vertice_core/exceptions.py  (base - this file)
         ↓
    vertice_cli/core/exceptions.py (extends with rich context)
         ↓
    vertice_tui (uses CLI exceptions)

Usage:
    from vertice_core.exceptions import (
        VerticeError,
        ValidationError,
        NetworkError,
    )

Author: Vertice Team
Date: 2026-01-02
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


# =============================================================================
# BASE TYPES (no external dependencies)
# =============================================================================

FilePath = Union[str, Path]


class ErrorCategory(str, Enum):
    """Category of error for recovery strategies."""
    SYNTAX = "syntax"
    IMPORT = "import"
    TYPE = "type"
    RUNTIME = "runtime"
    PERMISSION = "permission"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    TOOL = "tool"
    AGENT = "agent"
    RESILIENCE = "resilience"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ErrorContext:
    """Immutable context for an error."""
    category: ErrorCategory = ErrorCategory.UNKNOWN
    file: Optional[FilePath] = None
    line: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestions: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# BASE EXCEPTION
# =============================================================================

class VerticeError(Exception):
    """Base exception for all Vertice framework errors.

    All custom exceptions should inherit from this base class.
    Provides structured error information and recovery hints.

    Attributes:
        message: Human-readable error description
        context: Structured error context (optional)
        recoverable: Whether the error can be recovered from
        cause: The underlying exception that caused this error
    """

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        recoverable: bool = False,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.context = context
        self.recoverable = recoverable
        self.cause = cause

    def __str__(self) -> str:
        """Human-readable error message."""
        parts = [self.message]

        if self.context:
            if self.context.file:
                parts.append(f"File: {self.context.file}")
            if self.context.line:
                location = f"Line: {self.context.line}"
                if self.context.column:
                    location += f", Column: {self.context.column}"
                parts.append(location)
            if self.context.code_snippet:
                parts.append(f"Code:\n{self.context.code_snippet}")
            if self.context.suggestions:
                parts.append("Suggestions:")
                parts.extend(f"  - {s}" for s in self.context.suggestions)

        if self.cause:
            parts.append(f"Caused by: {self.cause}")

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize error to dictionary."""
        result: Dict[str, Any] = {
            'type': self.__class__.__name__,
            'message': self.message,
            'recoverable': self.recoverable,
        }

        if self.context:
            result['context'] = {
                'category': self.context.category.value,
                'file': str(self.context.file) if self.context.file else None,
                'line': self.context.line,
                'column': self.context.column,
                'suggestions': list(self.context.suggestions),
                'metadata': self.context.metadata,
            }

        if self.cause:
            result['cause'] = str(self.cause)

        return result


# =============================================================================
# VALIDATION & CONFIGURATION
# =============================================================================

class ValidationError(VerticeError):
    """Input validation error."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        constraint: Optional[str] = None,
    ):
        metadata = {}
        if field:
            metadata['field'] = field
        if value is not None:
            metadata['value'] = str(value)
        if constraint:
            metadata['constraint'] = constraint

        suggestions: List[str] = ["Check input format and constraints"]
        if field:
            suggestions.append(f"Field '{field}' is invalid")
        if constraint:
            suggestions.append(f"Constraint: {constraint}")

        context = ErrorContext(
            category=ErrorCategory.VALIDATION,
            metadata=metadata,
            suggestions=tuple(suggestions),
        )
        super().__init__(message, context, recoverable=True)


class ConfigurationError(VerticeError):
    """Configuration error."""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[FilePath] = None,
    ):
        metadata = {}
        if config_key:
            metadata['config_key'] = config_key

        suggestions = [
            "Check configuration file syntax",
            "Verify all required fields are set",
        ]
        if config_key:
            suggestions.insert(0, f"Invalid configuration key: {config_key}")

        context = ErrorContext(
            category=ErrorCategory.CONFIGURATION,
            file=config_file,
            metadata=metadata,
            suggestions=tuple(suggestions),
        )
        super().__init__(message, context, recoverable=True)


# =============================================================================
# NETWORK & RESILIENCE
# =============================================================================

class NetworkError(VerticeError):
    """Network-related error."""

    def __init__(
        self,
        message: str,
        url: Optional[str] = None,
        status_code: Optional[int] = None,
        cause: Optional[Exception] = None,
    ):
        metadata = {}
        if url:
            metadata['url'] = url
        if status_code:
            metadata['status_code'] = status_code

        context = ErrorContext(
            category=ErrorCategory.NETWORK,
            metadata=metadata,
            suggestions=(
                "Check network connection",
                "Verify API endpoint is correct",
                "Check if API key is valid",
            ),
        )
        super().__init__(message, context, recoverable=True, cause=cause)


class TimeoutError(VerticeError):
    """Operation timed out."""

    def __init__(
        self,
        message: str,
        timeout_seconds: float,
        operation: str,
    ):
        context = ErrorContext(
            category=ErrorCategory.TIMEOUT,
            metadata={
                'timeout': timeout_seconds,
                'operation': operation,
            },
            suggestions=(
                f"Increase timeout (current: {timeout_seconds}s)",
                "Check if operation is hung",
                "Retry with exponential backoff",
            ),
        )
        super().__init__(message, context, recoverable=True)


class RateLimitError(NetworkError):
    """API rate limit exceeded."""

    def __init__(
        self,
        provider: str,
        retry_after: Optional[int] = None,
    ):
        message = f"Rate limit exceeded for {provider}"
        if retry_after:
            message += f". Retry after {retry_after} seconds"

        super().__init__(
            message,
            url=None,
            status_code=429,
        )
        self.provider = provider
        self.retry_after = retry_after


class CircuitOpenError(VerticeError):
    """Circuit breaker is open, requests blocked."""

    def __init__(
        self,
        circuit_name: str,
        reset_time: Optional[float] = None,
    ):
        message = f"Circuit breaker '{circuit_name}' is open"
        if reset_time:
            message += f". Reset in {reset_time:.1f}s"

        context = ErrorContext(
            category=ErrorCategory.RESILIENCE,
            metadata={
                'circuit': circuit_name,
                'reset_time': reset_time,
            },
            suggestions=(
                "Wait for circuit to reset",
                "Check underlying service health",
            ),
        )
        super().__init__(message, context, recoverable=True)
        self.circuit_name = circuit_name
        self.reset_time = reset_time


# =============================================================================
# TOOL & AGENT
# =============================================================================

class ToolError(VerticeError):
    """Tool execution error."""

    def __init__(
        self,
        message: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        metadata = {'tool': tool_name}
        if arguments:
            metadata['arguments'] = arguments

        context = ErrorContext(
            category=ErrorCategory.TOOL,
            metadata=metadata,
            suggestions=(
                "Check tool arguments are correct",
                f"See documentation for tool '{tool_name}'",
            ),
        )
        super().__init__(message, context, recoverable=True, cause=cause)


class ToolNotFoundError(ToolError):
    """Tool not found in registry."""

    def __init__(self, tool_name: str):
        super().__init__(
            f"Tool not found: {tool_name}",
            tool_name=tool_name,
        )


class AgentError(VerticeError):
    """Agent execution error."""

    def __init__(
        self,
        message: str,
        agent_id: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        metadata = {}
        if agent_id:
            metadata['agent_id'] = agent_id

        context = ErrorContext(
            category=ErrorCategory.AGENT,
            metadata=metadata,
            suggestions=(
                "Check agent configuration",
                "Verify agent capabilities",
            ),
        )
        super().__init__(message, context, recoverable=True, cause=cause)


class CapabilityViolationError(AgentError):
    """Agent attempted to use unauthorized capability."""

    def __init__(self, agent_id: str, capability: str, message: str = ""):
        full_message = f"Agent '{agent_id}' lacks capability '{capability}'"
        if message:
            full_message += f": {message}"
        super().__init__(full_message, agent_id=agent_id)
        self.capability = capability


class AgentTimeoutError(AgentError):
    """Agent execution timed out."""

    def __init__(self, agent_id: str, timeout: float):
        super().__init__(
            f"Agent '{agent_id}' timed out after {timeout}s",
            agent_id=agent_id,
        )
        self.timeout = timeout


# =============================================================================
# RESOURCE
# =============================================================================

class ResourceError(VerticeError):
    """Resource constraint error."""

    def __init__(
        self,
        message: str,
        resource_type: str,
        limit: Optional[Any] = None,
        current: Optional[Any] = None,
    ):
        metadata = {'resource_type': resource_type}
        if limit is not None:
            metadata['limit'] = limit
        if current is not None:
            metadata['current'] = current

        suggestions = [f"Reduce {resource_type} usage"]
        if limit and current:
            suggestions.insert(0, f"Current: {current}, Limit: {limit}")

        context = ErrorContext(
            category=ErrorCategory.RESOURCE,
            metadata=metadata,
            suggestions=tuple(suggestions),
        )
        super().__init__(message, context, recoverable=True)


class TokenLimitError(ResourceError):
    """Token limit exceeded."""

    def __init__(self, current_tokens: int, max_tokens: int):
        super().__init__(
            f"Token limit exceeded: {current_tokens}/{max_tokens}",
            resource_type="tokens",
            limit=max_tokens,
            current=current_tokens,
        )


# =============================================================================
# LLM
# =============================================================================

class LLMError(VerticeError):
    """LLM-related error."""

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        cause: Optional[Exception] = None,
    ):
        metadata = {}
        if provider:
            metadata['provider'] = provider
        if model:
            metadata['model'] = model

        context = ErrorContext(
            category=ErrorCategory.NETWORK,
            metadata=metadata,
            suggestions=(
                "Check API key is valid",
                "Verify network connection",
                "Try a different provider",
            ),
        )
        super().__init__(message, context, recoverable=True, cause=cause)


# =============================================================================
# BACKWARD COMPATIBILITY ALIASES
# =============================================================================

# Legacy name from vertice_cli
QwenError = VerticeError

# Legacy name from vertice_core/types
QwenCoreError = VerticeError


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Types
    "FilePath",
    "ErrorCategory",
    "ErrorContext",
    # Base
    "VerticeError",
    # Validation
    "ValidationError",
    "ConfigurationError",
    # Network & Resilience
    "NetworkError",
    "TimeoutError",
    "RateLimitError",
    "CircuitOpenError",
    # Tool & Agent
    "ToolError",
    "ToolNotFoundError",
    "AgentError",
    "CapabilityViolationError",
    "AgentTimeoutError",
    # Resource
    "ResourceError",
    "TokenLimitError",
    # LLM
    "LLMError",
    # Backward compat
    "QwenError",
    "QwenCoreError",
]
