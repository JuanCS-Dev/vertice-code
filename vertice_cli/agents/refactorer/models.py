"""
Refactorer Models - Type-Safe Data Structures for Code Surgery.

This module provides enterprise-grade data models for refactoring operations:
- RefactoringType: Supported refactoring patterns
- ChangeStatus: Lifecycle states for changes
- CodeChange: Atomic code modification
- RefactoringPlan: Complete refactoring blueprint
- ValidationResult: Validation check results

Architecture (Boris Cherny):
    "Types are documentation that never goes out of sync."
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class RefactoringType(str, Enum):
    """Types of refactoring operations.

    Each type represents a well-known refactoring pattern from:
    - Martin Fowler's Refactoring catalog
    - Enterprise code modernization practices
    """

    EXTRACT_METHOD = "extract_method"
    INLINE_METHOD = "inline_method"
    RENAME_SYMBOL = "rename_symbol"
    MOVE_METHOD = "move_method"
    EXTRACT_CLASS = "extract_class"
    INTRODUCE_PARAMETER_OBJECT = "introduce_parameter_object"
    REPLACE_CONDITIONAL = "replace_conditional"
    DECOMPOSE_CONDITIONAL = "decompose_conditional"
    CONSOLIDATE_DUPLICATE_CODE = "consolidate_duplicate_code"
    REMOVE_DEAD_CODE = "remove_dead_code"
    SIMPLIFY_EXPRESSION = "simplify_expression"
    MODERNIZE_SYNTAX = "modernize_syntax"  # e.g., Python 2 → 3


class ChangeStatus(str, Enum):
    """Lifecycle states for code changes.

    Flow: PENDING → STAGED → VALIDATED → COMMITTED
                         ↘ FAILED
                         ↘ ROLLED_BACK
    """

    PENDING = "pending"
    STAGED = "staged"
    VALIDATED = "validated"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class CodeChange:
    """Represents a single atomic code change.

    Attributes:
        id: Unique identifier for this change
        file_path: Target file path
        refactoring_type: Type of refactoring being applied
        original_content: Content before change
        new_content: Content after change
        description: Human-readable description
        line_start: Starting line number
        line_end: Ending line number
        affected_symbols: Symbols affected by this change
        dependencies: IDs of changes this depends on
        status: Current lifecycle status
        validation_results: Results of validation checks
        test_results: Results of test execution
        checkpoint_id: Associated checkpoint for rollback
        created_at: Timestamp of creation
    """

    id: str
    file_path: str
    refactoring_type: RefactoringType
    original_content: str
    new_content: str
    description: str
    line_start: int
    line_end: int
    affected_symbols: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    status: ChangeStatus = ChangeStatus.PENDING
    validation_results: Dict[str, bool] = field(default_factory=dict)
    test_results: Optional[Dict[str, Any]] = None
    checkpoint_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


class RefactoringPlan(BaseModel):
    """Complete refactoring plan with dependencies.

    This is the blueprint for a refactoring operation, containing:
    - All planned changes
    - Execution order (topologically sorted)
    - Impact analysis
    - Risk assessment
    - Rollback strategy
    """

    plan_id: str
    goal: str
    changes: List[Dict[str, Any]] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    affected_files: List[str] = Field(default_factory=list)
    blast_radius: Dict[str, List[str]] = Field(default_factory=dict)
    risk_level: str = "MEDIUM"
    require_tests: bool = True
    require_approval: bool = False
    checkpoints: List[str] = Field(default_factory=list)
    rollback_strategy: str = "incremental"


class ValidationResult(BaseModel):
    """Result of validation checks.

    Aggregates results from multiple validation steps:
    - Syntax validation
    - Semantic validation
    - Reference validation
    """

    passed: bool
    checks: Dict[str, bool] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


@dataclass
class RefactoringAction:
    """RL Action for refactoring decisions.

    Used by the RL policy to represent potential refactoring actions
    with their estimated rewards.
    """

    type: RefactoringType
    target: str
    parameters: Dict[str, Any]
    estimated_reward: float = 0.0


def generate_change_id(data: Dict[str, Any]) -> str:
    """Generate unique ID for a code change.

    Args:
        data: Change data dictionary

    Returns:
        Short hash-based unique ID
    """
    return f"change-{hashlib.md5(str(data).encode()).hexdigest()[:8]}"


def generate_session_id() -> str:
    """Generate unique session ID.

    Returns:
        Timestamp-based unique ID
    """
    timestamp = datetime.now().isoformat()
    return hashlib.md5(timestamp.encode()).hexdigest()[:12]


__all__ = [
    "RefactoringType",
    "ChangeStatus",
    "CodeChange",
    "RefactoringPlan",
    "ValidationResult",
    "RefactoringAction",
    "generate_change_id",
    "generate_session_id",
]
