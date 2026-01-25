"""
Context Module - Multi-Agent Context Management.

This package provides unified context management for multi-agent orchestration.

Submodules:
    - types: Domain models (ContextState, Decision, FileContext, etc.)
    - unified: UnifiedContext class

Usage:
    from vertice_core.agents.context import UnifiedContext, get_context
    from vertice_core.agents.context import Decision, DecisionType
"""

from __future__ import annotations

from typing import Optional

from .types import (
    ContextState,
    DecisionType,
    Decision,
    ErrorContext,
    FileContext,
    ExecutionResult,
    ThoughtSignature,
)
from .unified import UnifiedContext


# Singleton for current session
_current_context: Optional[UnifiedContext] = None


def get_context() -> UnifiedContext:
    """Get or create the current unified context."""
    global _current_context
    if _current_context is None:
        _current_context = UnifiedContext()
    return _current_context


def set_context(ctx: UnifiedContext) -> None:
    """Set the current unified context."""
    global _current_context
    _current_context = ctx


def new_context(user_request: str = "", **kwargs) -> UnifiedContext:
    """Create and set a new unified context."""
    global _current_context
    _current_context = UnifiedContext(user_request=user_request, **kwargs)
    return _current_context


__all__ = [
    # Types
    "ContextState",
    "DecisionType",
    "Decision",
    "ErrorContext",
    "FileContext",
    "ExecutionResult",
    "ThoughtSignature",
    # Main class
    "UnifiedContext",
    # Singleton functions
    "get_context",
    "set_context",
    "new_context",
]
