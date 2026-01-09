"""Types and enums for code validation."""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationLevel(str, Enum):
    """Level of validation to perform."""

    SYNTAX_ONLY = "syntax_only"
    LSP_BASIC = "lsp_basic"
    LSP_FULL = "lsp_full"
    COMPREHENSIVE = "comprehensive"


class CheckType(str, Enum):
    """Types of validation checks."""

    SYNTAX = "syntax"
    LSP_ERRORS = "lsp_errors"
    LSP_WARNINGS = "lsp_warnings"
    IMPORTS = "imports"
    TYPE_CHECK = "type_check"
    CUSTOM = "custom"


@dataclass
class Check:
    """A single validation check result."""

    check_type: CheckType
    passed: bool
    message: str = ""
    details: List[str] = field(default_factory=list)
    severity: str = "error"

    @property
    def is_error(self) -> bool:
        return not self.passed and self.severity == "error"


@dataclass
class ValidationResult:
    """Result of validating code."""

    valid: bool
    checks: List[Check] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def error_count(self) -> int:
        return len(self.errors)

    @property
    def warning_count(self) -> int:
        return len(self.warnings)

    def get_check(self, check_type: CheckType) -> Optional[Check]:
        for check in self.checks:
            if check.check_type == check_type:
                return check
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "duration_ms": self.duration_ms,
            "checks": [
                {"type": c.check_type.value, "passed": c.passed, "message": c.message}
                for c in self.checks
            ],
        }


@dataclass
class EditValidation:
    """Result of validating an edit operation."""

    can_apply: bool
    validation_before: ValidationResult
    validation_after: Optional[ValidationResult] = None
    new_errors: List[str] = field(default_factory=list)
    fixed_errors: List[str] = field(default_factory=list)
    recommendation: str = ""

    @property
    def introduced_errors(self) -> bool:
        return len(self.new_errors) > 0

    @property
    def improved_code(self) -> bool:
        return len(self.fixed_errors) > 0 and not self.introduced_errors


@dataclass
class FileBackup:
    """Backup of a file for rollback."""

    filepath: str
    content: str
    content_hash: str
    created_at: float = field(default_factory=time.time)
