"""Code validation system with LSP integration."""

from typing import Optional

from .types import (
    ValidationLevel,
    CheckType,
    Check,
    ValidationResult,
    EditValidation,
    FileBackup,
)
from .backup import BackupManager
from .manager import CodeValidator

__all__ = [
    "ValidationLevel",
    "CheckType",
    "Check",
    "ValidationResult",
    "EditValidation",
    "FileBackup",
    "BackupManager",
    "CodeValidator",
    "validate_file",
    "validate_edit",
]


async def validate_file(
    filepath: str,
    content: Optional[str] = None,
    level: ValidationLevel = ValidationLevel.LSP_BASIC,
) -> ValidationResult:
    """Validate a file."""
    validator = CodeValidator()
    return await validator.validate(filepath, content, level)


async def validate_edit(
    filepath: str,
    old_content: str,
    new_content: str,
    level: ValidationLevel = ValidationLevel.LSP_BASIC,
) -> EditValidation:
    """Validate an edit."""
    validator = CodeValidator()
    return await validator.validate_edit(filepath, old_content, new_content, level)
