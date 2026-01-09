"""
Validation Types - Domain models for input validation.

Enums and dataclasses for validation results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional


class ValidationLayer(Enum):
    """Validation layers for defense in depth."""

    TYPE_VALIDATION = auto()
    LENGTH_LIMITS = auto()
    PATTERN_WHITELIST = auto()
    INJECTION_DETECTION = auto()
    SEMANTIC_VALIDATION = auto()


class InjectionType(Enum):
    """Types of injection attacks detected."""

    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    SQL_INJECTION = "sql_injection"
    PROMPT_INJECTION = "prompt_injection"
    NULL_BYTE = "null_byte"
    NEWLINE_INJECTION = "newline_injection"
    TEMPLATE_INJECTION = "template_injection"
    UNICODE_ATTACK = "unicode_attack"


@dataclass
class ValidationResult:
    """Result of multi-layer input validation."""

    is_valid: bool
    sanitized_value: Any
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blocked_attacks: List[InjectionType] = field(default_factory=list)
    layer_results: Dict[ValidationLayer, bool] = field(default_factory=dict)
    threat_level: str = "NONE"

    @property
    def error(self) -> str:
        """Get first error message or empty string."""
        return self.errors[0] if self.errors else ""

    @classmethod
    def success(cls, value: Any, warnings: Optional[List[str]] = None) -> "ValidationResult":
        """Create successful validation result."""
        return cls(
            is_valid=True,
            sanitized_value=value,
            warnings=warnings or [],
            layer_results={layer: True for layer in ValidationLayer},
        )

    @classmethod
    def failure(
        cls,
        errors: List[str],
        original_value: Any = None,
        blocked_attacks: Optional[List[InjectionType]] = None,
        threat_level: str = "HIGH",
    ) -> "ValidationResult":
        """Create failed validation result."""
        return cls(
            is_valid=False,
            sanitized_value=original_value,
            errors=errors,
            blocked_attacks=blocked_attacks or [],
            threat_level=threat_level,
        )


class Required:
    """Validator that checks if a parameter is present and not None."""

    def __init__(self, field_name: str):
        self.field_name = field_name

    def __call__(self, value: Any) -> ValidationResult:
        if value is None or value == "":
            return ValidationResult.failure(
                errors=[f"Required field '{self.field_name}' is missing"],
                original_value=value,
                threat_level="LOW",
            )
        return ValidationResult.success(value)


class TypeCheck:
    """Validator that checks if a parameter is of expected type(s)."""

    def __init__(self, expected_types: type | tuple, field_name: str):
        self.expected_types = expected_types
        self.field_name = field_name

    def __call__(self, value: Any) -> ValidationResult:
        if value is None:
            return ValidationResult.success(value)
        if not isinstance(value, self.expected_types):
            return ValidationResult.failure(
                errors=[
                    f"Field '{self.field_name}' must be {self.expected_types}, got {type(value).__name__}"
                ],
                original_value=value,
                threat_level="LOW",
            )
        return ValidationResult.success(value)


__all__ = [
    "ValidationLayer",
    "InjectionType",
    "ValidationResult",
    "Required",
    "TypeCheck",
]
