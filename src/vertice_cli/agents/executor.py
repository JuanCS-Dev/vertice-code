"""
NextGen CLI Code Executor Agent - Backward Compatibility Re-export.

REFACTORED: This module has been split into modular components:
- executor/types.py: Enums and dataclasses
- executor/security.py: AdvancedSecurityValidator
- executor/engine.py: CodeExecutionEngine
- executor/agent.py: NextGenExecutorAgent

All symbols are re-exported here for backward compatibility.
Import from 'executor' subpackage for new code.
"""

# Re-export all public symbols for backward compatibility
from .executor import (
    # Types
    ExecutionMode,
    SecurityLevel,
    CommandCategory,
    ExecutionMetrics,
    CommandResult,
    # Security
    AdvancedSecurityValidator,
    # Engine
    CodeExecutionEngine,
    # Agent
    NextGenExecutorAgent,
    ExecutorAgent,
)

__all__ = [
    "ExecutionMode",
    "SecurityLevel",
    "CommandCategory",
    "ExecutionMetrics",
    "CommandResult",
    "AdvancedSecurityValidator",
    "CodeExecutionEngine",
    "NextGenExecutorAgent",
    "ExecutorAgent",
]
