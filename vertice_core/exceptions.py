"""
Vertice Core Unified Exception Hierarchy.

SCALE & SUSTAIN Phase 2.2 - Exception Consolidation.

This module provides a unified exception hierarchy for the Vertice framework.
All modules should import exceptions from here for consistency.

Hierarchy:
- VerticeError (base)
  - ValidationError
  - NetworkError
    - RateLimitError
    - TimeoutError
  - ToolError
    - ToolNotFoundError
  - AgentError
    - CapabilityViolationError
    - AgentTimeoutError
  - ResourceError
    - TokenLimitError
    - MemoryLimitError
  - ConfigurationError
  - LLMError
  - ResilienceError (from core.resilience)
    - TransientError
    - PermanentError
    - CircuitOpenError

Usage:
    from vertice_core.exceptions import (
        VerticeError,
        ValidationError,
        NetworkError,
        ToolError,
    )

Author: Vertice Team
Date: 2026-01-02
"""

from __future__ import annotations

# =============================================================================
# RE-EXPORTS FROM CANONICAL LOCATIONS
# =============================================================================

# CLI Exception Hierarchy (most comprehensive)
# Using alias for brand consistency: QwenError -> VerticeError
from vertice_cli.core.exceptions import (
    # Base
    QwenError as VerticeError,
    ErrorContext,
    # Code execution
    SyntaxError as VerticeSyntaxError,  # Avoid shadowing builtin
    ImportError as VerticeImportError,   # Avoid shadowing builtin
    TypeError as VerticeTypeError,       # Avoid shadowing builtin
    RuntimeError as VerticeRuntimeError, # Avoid shadowing builtin
    # File system
    FileNotFoundError as VerticeFileNotFoundError,  # Avoid shadowing builtin
    PermissionError as VerticePermissionError,      # Avoid shadowing builtin
    FileAlreadyExistsError,
    # Network
    NetworkError,
    TimeoutError as VerticeTimeoutError,  # Avoid shadowing builtin
    RateLimitError as CLIRateLimitError,
    # Resources
    ResourceError,
    TokenLimitError,
    MemoryLimitError,
    # Validation
    ValidationError,
    ConfigurationError,
    # LLM
    LLMError,
    LLMValidationError,
    # Tools
    ToolError,
    ToolNotFoundError,
)

# Resilience exceptions (from core.resilience)
from core.resilience import (
    ResilienceError,
    TransientError,
    PermanentError,
    RateLimitError as ResilienceRateLimitError,
    CircuitOpenError,
)

# Domain exceptions (from vertice_core.types)
from vertice_core.types.exceptions import (
    QwenCoreError,
    CapabilityViolationError,
    TaskValidationError,
    AgentTimeoutError,
)

# Client exceptions
from vertice_core.clients.vertice_client import (
    VerticeClientError,
    AllProvidersExhaustedError,
    RateLimitError as ClientRateLimitError,
)

# =============================================================================
# UNIFIED ALIASES (for new code)
# =============================================================================

# Prefer these names for new code
AgentError = QwenCoreError  # Alias for consistency


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Base
    "VerticeError",
    "ErrorContext",

    # Code execution (prefixed to avoid shadowing builtins)
    "VerticeSyntaxError",
    "VerticeImportError",
    "VerticeTypeError",
    "VerticeRuntimeError",

    # File system
    "VerticeFileNotFoundError",
    "VerticePermissionError",
    "FileAlreadyExistsError",

    # Network
    "NetworkError",
    "VerticeTimeoutError",
    "CLIRateLimitError",

    # Resources
    "ResourceError",
    "TokenLimitError",
    "MemoryLimitError",

    # Validation
    "ValidationError",
    "ConfigurationError",

    # LLM
    "LLMError",
    "LLMValidationError",

    # Tools
    "ToolError",
    "ToolNotFoundError",

    # Resilience
    "ResilienceError",
    "TransientError",
    "PermanentError",
    "ResilienceRateLimitError",
    "CircuitOpenError",

    # Domain/Agent
    "QwenCoreError",  # Legacy
    "AgentError",     # Preferred alias
    "CapabilityViolationError",
    "TaskValidationError",
    "AgentTimeoutError",

    # Client
    "VerticeClientError",
    "AllProvidersExhaustedError",
    "ClientRateLimitError",
]
