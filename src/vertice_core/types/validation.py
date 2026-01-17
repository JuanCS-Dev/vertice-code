# Validation and constraints types - Domain level

from __future__ import annotations

from typing import Any, List, Literal, TypedDict


class ValidationRule(TypedDict):
    """A validation rule for input."""

    field: str
    rule: Literal["required", "type", "range", "pattern", "custom"]
    constraint: Any
    error_message: str


class ValidationResult(TypedDict):
    """Result of validation."""

    valid: bool
    errors: List[str]
    warnings: List[str]
