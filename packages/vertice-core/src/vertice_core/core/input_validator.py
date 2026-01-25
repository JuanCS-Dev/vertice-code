"""
Input Validator - Multi-Layer Input Validation - Backward Compatibility Re-export.

REFACTORED: This module has been split into modular components:
- validation/types.py: ValidationLayer, InjectionType, ValidationResult
- validation/patterns.py: Security pattern definitions
- validation/validator.py: Core InputValidator class

All symbols are re-exported here for backward compatibility.
Import from 'validation' subpackage for new code.

Pipeline de Diamante - Camada 1: INPUT FORTRESS
OWASP + CISA Compliant input validation.
"""

# Re-export all public symbols for backward compatibility
from .validation import (
    ValidationLayer,
    InjectionType,
    ValidationResult,
    InputValidator,
    validate_command,
    validate_file_path,
    validate_prompt,
    is_safe_command,
    is_safe_path,
)

__all__ = [
    "ValidationLayer",
    "InjectionType",
    "ValidationResult",
    "InputValidator",
    "validate_command",
    "validate_file_path",
    "validate_prompt",
    "is_safe_command",
    "is_safe_path",
]
