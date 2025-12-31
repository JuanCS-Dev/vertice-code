"""
Code Validator - Post-Edit Validation with LSP & AST.

Implements the validation pattern from Claude Code and OpenAI Codex:
1. Capture diagnostics BEFORE edit
2. Apply edit
3. Capture diagnostics AFTER edit
4. Rollback if new errors introduced

Key insight from LSPAI research (FSE 2025):
- LSP-guided validation improves success rate from 10-11% to 24-25%

References:
- Claude Code LSP diagnostics pattern
- OpenAI Codex "run all programmatic checks AFTER"
- LSPAI paper (FSE Industry 2025)

Phase 10: Sprint 3 - Code Intelligence

Soli Deo Gloria
"""

from __future__ import annotations

import asyncio
import difflib
import hashlib
import logging
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
    Union,
)

from .ast_editor import ASTEditor, get_ast_editor, TREE_SITTER_AVAILABLE
from .lsp_client import (
    Diagnostic,
    DiagnosticSeverity,
    LSPClient,
    LSPConnectionError,
    get_lsp_client,
)

logger = logging.getLogger(__name__)


class ValidationLevel(str, Enum):
    """Level of validation to perform."""

    SYNTAX_ONLY = "syntax_only"  # Fast, just syntax check
    LSP_BASIC = "lsp_basic"  # Syntax + LSP errors
    LSP_FULL = "lsp_full"  # All LSP diagnostics including warnings
    COMPREHENSIVE = "comprehensive"  # LSP + imports + type check


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
    severity: str = "error"  # error, warning, info

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
        """Get specific check result."""
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


class CodeValidator:
    """
    Validates code using LSP diagnostics and AST analysis.

    Implements the before/after validation pattern:
    1. Validate before edit (capture baseline)
    2. Apply edit
    3. Validate after edit
    4. Compare and decide (rollback if worse)

    Usage:
        validator = CodeValidator(workspace_root)

        # Simple validation
        result = await validator.validate("file.py")

        # Before/after validation
        validation = await validator.validate_edit(
            filepath="file.py",
            old_content=old,
            new_content=new,
        )
        if validation.introduced_errors:
            # Rollback
    """

    def __init__(
        self,
        workspace_root: Optional[str] = None,
        lsp_client: Optional[LSPClient] = None,
        ast_editor: Optional[ASTEditor] = None,
    ):
        """
        Initialize validator.

        Args:
            workspace_root: Root directory for LSP
            lsp_client: Optional pre-configured LSP client
            ast_editor: Optional pre-configured AST editor
        """
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self._lsp_client = lsp_client
        self._ast_editor = ast_editor or get_ast_editor()

        # Backup storage for rollback
        self._backups: Dict[str, FileBackup] = {}

        # Custom validators
        self._custom_validators: Dict[str, Callable] = {}

        # Stats
        self._stats = {
            "validations": 0,
            "errors_caught": 0,
            "rollbacks": 0,
        }

    async def _get_lsp_client(self) -> Optional[LSPClient]:
        """Get or create LSP client."""
        if self._lsp_client is None:
            try:
                self._lsp_client = get_lsp_client(str(self.workspace_root))
            except Exception as e:
                logger.warning(f"Could not initialize LSP client: {e}")
                return None
        return self._lsp_client

    def _get_language(self, filepath: str) -> Optional[str]:
        """Detect language from filepath."""
        ext = Path(filepath).suffix.lower()
        ext_map = {
            ".py": "python",
            ".pyi": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".go": "go",
            ".rs": "rust",
            ".java": "java",
            ".c": "c",
            ".cpp": "cpp",
            ".h": "c",
            ".hpp": "cpp",
        }
        return ext_map.get(ext)

    def _hash_content(self, content: str) -> str:
        """Create hash of content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    # =========================================================================
    # Core Validation
    # =========================================================================

    async def validate(
        self,
        filepath: str,
        content: Optional[str] = None,
        level: ValidationLevel = ValidationLevel.LSP_BASIC,
    ) -> ValidationResult:
        """
        Validate a file.

        Args:
            filepath: Path to file
            content: Optional content (reads from file if not provided)
            level: Validation level

        Returns:
            ValidationResult with all checks
        """
        self._stats["validations"] += 1
        start_time = time.time()

        checks: List[Check] = []
        errors: List[str] = []
        warnings: List[str] = []

        # Read content if not provided
        if content is None:
            path = Path(filepath)
            if not path.is_absolute():
                path = self.workspace_root / path
            if path.exists():
                content = path.read_text(encoding="utf-8", errors="replace")
            else:
                return ValidationResult(
                    valid=False,
                    checks=[Check(CheckType.SYNTAX, False, f"File not found: {filepath}")],
                    errors=[f"File not found: {filepath}"],
                )

        language = self._get_language(filepath)

        # 1. Syntax check (always)
        syntax_check = await self._check_syntax(content, language)
        checks.append(syntax_check)
        if not syntax_check.passed:
            errors.extend(syntax_check.details)

        # 2. LSP diagnostics (if level >= LSP_BASIC)
        if level in (ValidationLevel.LSP_BASIC, ValidationLevel.LSP_FULL, ValidationLevel.COMPREHENSIVE):
            lsp_check = await self._check_lsp(filepath, content, level)
            checks.append(lsp_check)
            if not lsp_check.passed:
                for detail in lsp_check.details:
                    if "error" in detail.lower():
                        errors.append(detail)
                    else:
                        warnings.append(detail)

        # 3. Import check (Python, if level >= COMPREHENSIVE)
        if level == ValidationLevel.COMPREHENSIVE and language == "python":
            import_check = await self._check_imports(content)
            checks.append(import_check)
            if not import_check.passed:
                errors.extend(import_check.details)

        # 4. Custom validators
        for name, validator in self._custom_validators.items():
            try:
                custom_check = await validator(filepath, content, language)
                checks.append(custom_check)
                if not custom_check.passed:
                    errors.extend(custom_check.details)
            except Exception as e:
                logger.warning(f"Custom validator {name} failed: {e}")

        duration_ms = (time.time() - start_time) * 1000
        valid = len(errors) == 0

        if not valid:
            self._stats["errors_caught"] += len(errors)

        return ValidationResult(
            valid=valid,
            checks=checks,
            errors=errors,
            warnings=warnings,
            duration_ms=duration_ms,
        )

    async def _check_syntax(
        self,
        content: str,
        language: Optional[str],
    ) -> Check:
        """Check syntax using AST parser."""
        if not language:
            return Check(CheckType.SYNTAX, True, "Unknown language, skipping syntax check")

        is_valid, error = self._ast_editor.is_valid_syntax(content, language)

        if is_valid:
            return Check(CheckType.SYNTAX, True, "Syntax OK")
        else:
            return Check(
                CheckType.SYNTAX,
                False,
                "Syntax error",
                details=[error or "Unknown syntax error"],
            )

    async def _check_lsp(
        self,
        filepath: str,
        content: str,
        level: ValidationLevel,
    ) -> Check:
        """Check using LSP diagnostics."""
        lsp = await self._get_lsp_client()
        if not lsp:
            return Check(CheckType.LSP_ERRORS, True, "LSP not available")

        try:
            # Notify LSP of content
            await lsp.notify_change(filepath, content)

            # Get diagnostics
            diagnostics = await lsp.diagnostics(filepath, wait_ms=500)

            # Filter by level
            if level == ValidationLevel.LSP_BASIC:
                diagnostics = [d for d in diagnostics if d.is_error]
            elif level == ValidationLevel.LSP_FULL:
                diagnostics = [d for d in diagnostics if d.severity <= DiagnosticSeverity.WARNING]

            if not diagnostics:
                return Check(CheckType.LSP_ERRORS, True, "No LSP errors")

            details = [
                f"Line {d.range.start.line + 1}: [{d.severity.name}] {d.message}"
                for d in diagnostics
            ]

            error_count = sum(1 for d in diagnostics if d.is_error)

            return Check(
                CheckType.LSP_ERRORS,
                error_count == 0,
                f"{len(diagnostics)} diagnostic(s) found",
                details=details,
                severity="error" if error_count > 0 else "warning",
            )

        except LSPConnectionError as e:
            return Check(CheckType.LSP_ERRORS, True, f"LSP unavailable: {e}")
        except Exception as e:
            logger.error(f"LSP check failed: {e}")
            return Check(CheckType.LSP_ERRORS, True, f"LSP check failed: {e}")

    async def _check_imports(self, content: str) -> Check:
        """Check Python imports are valid."""
        import ast as python_ast
        import importlib.util

        try:
            tree = python_ast.parse(content)
        except SyntaxError:
            return Check(CheckType.IMPORTS, True, "Cannot parse, skipping import check")

        missing_imports: List[str] = []

        for node in python_ast.walk(tree):
            if isinstance(node, python_ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if not self._module_exists(module_name):
                        missing_imports.append(module_name)

            elif isinstance(node, python_ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    if not self._module_exists(module_name):
                        missing_imports.append(node.module)

        if missing_imports:
            return Check(
                CheckType.IMPORTS,
                False,
                f"{len(missing_imports)} missing import(s)",
                details=[f"Cannot find module: {m}" for m in missing_imports],
                severity="warning",
            )

        return Check(CheckType.IMPORTS, True, "All imports valid")

    def _module_exists(self, module_name: str) -> bool:
        """Check if a Python module exists."""
        try:
            import importlib.util
            return importlib.util.find_spec(module_name) is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False

    # =========================================================================
    # Edit Validation (Before/After Pattern)
    # =========================================================================

    async def validate_edit(
        self,
        filepath: str,
        old_content: str,
        new_content: str,
        level: ValidationLevel = ValidationLevel.LSP_BASIC,
    ) -> EditValidation:
        """
        Validate an edit by comparing before/after states.

        This is the core pattern from Claude Code and Codex:
        1. Capture diagnostics before
        2. Capture diagnostics after
        3. Compare to detect new errors

        Args:
            filepath: Path to file
            old_content: Content before edit
            new_content: Content after edit
            level: Validation level

        Returns:
            EditValidation with comparison results
        """
        # Validate before
        validation_before = await self.validate(filepath, old_content, level)

        # Validate after
        validation_after = await self.validate(filepath, new_content, level)

        # Compare errors
        old_errors = set(validation_before.errors)
        new_errors_set = set(validation_after.errors)

        introduced = list(new_errors_set - old_errors)
        fixed = list(old_errors - new_errors_set)

        # Determine if edit is acceptable
        can_apply = len(introduced) == 0

        # Generate recommendation
        if can_apply:
            if fixed:
                recommendation = f"Edit improves code: fixed {len(fixed)} error(s)"
            else:
                recommendation = "Edit is safe to apply"
        else:
            recommendation = f"Edit introduces {len(introduced)} new error(s) - consider rollback"

        return EditValidation(
            can_apply=can_apply,
            validation_before=validation_before,
            validation_after=validation_after,
            new_errors=introduced,
            fixed_errors=fixed,
            recommendation=recommendation,
        )

    # =========================================================================
    # Backup & Rollback
    # =========================================================================

    def backup_file(self, filepath: str, content: str) -> FileBackup:
        """
        Create backup of file for potential rollback.

        Args:
            filepath: Path to file
            content: Current content to backup

        Returns:
            FileBackup object
        """
        backup = FileBackup(
            filepath=filepath,
            content=content,
            content_hash=self._hash_content(content),
        )
        self._backups[filepath] = backup
        return backup

    def get_backup(self, filepath: str) -> Optional[FileBackup]:
        """Get backup for file if exists."""
        return self._backups.get(filepath)

    async def rollback(self, filepath: str) -> bool:
        """
        Rollback file to backed up state.

        Args:
            filepath: Path to file

        Returns:
            True if rollback successful
        """
        backup = self._backups.get(filepath)
        if not backup:
            logger.warning(f"No backup found for {filepath}")
            return False

        try:
            path = Path(filepath)
            if not path.is_absolute():
                path = self.workspace_root / path

            path.write_text(backup.content, encoding="utf-8")
            self._stats["rollbacks"] += 1

            logger.info(f"Rolled back {filepath}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed for {filepath}: {e}")
            return False

    def clear_backup(self, filepath: str) -> bool:
        """Clear backup for file."""
        if filepath in self._backups:
            del self._backups[filepath]
            return True
        return False

    def clear_all_backups(self) -> int:
        """Clear all backups."""
        count = len(self._backups)
        self._backups.clear()
        return count

    # =========================================================================
    # Safe Edit with Validation
    # =========================================================================

    async def safe_edit(
        self,
        filepath: str,
        old_content: str,
        new_content: str,
        auto_rollback: bool = True,
        level: ValidationLevel = ValidationLevel.LSP_BASIC,
    ) -> Tuple[bool, EditValidation]:
        """
        Apply edit with validation and optional auto-rollback.

        This is the recommended way to apply edits:
        1. Backup original
        2. Validate edit
        3. Apply if safe, rollback if not

        Args:
            filepath: Path to file
            old_content: Content before edit
            new_content: Content after edit
            auto_rollback: Auto rollback on new errors
            level: Validation level

        Returns:
            Tuple of (success, validation)
        """
        # Backup
        self.backup_file(filepath, old_content)

        # Validate
        validation = await self.validate_edit(filepath, old_content, new_content, level)

        if validation.can_apply:
            # Apply edit
            try:
                path = Path(filepath)
                if not path.is_absolute():
                    path = self.workspace_root / path

                path.write_text(new_content, encoding="utf-8")
                self.clear_backup(filepath)

                return True, validation

            except Exception as e:
                logger.error(f"Failed to write {filepath}: {e}")
                validation.recommendation = f"Write failed: {e}"
                return False, validation

        else:
            # New errors introduced
            if auto_rollback:
                logger.warning(
                    f"Edit introduces {len(validation.new_errors)} errors, not applying"
                )
            return False, validation

    # =========================================================================
    # Custom Validators
    # =========================================================================

    def register_validator(
        self,
        name: str,
        validator: Callable,
    ) -> None:
        """
        Register a custom validator.

        Validator signature:
            async def validator(filepath, content, language) -> Check

        Args:
            name: Validator name
            validator: Async validator function
        """
        self._custom_validators[name] = validator

    def unregister_validator(self, name: str) -> bool:
        """Unregister a custom validator."""
        if name in self._custom_validators:
            del self._custom_validators[name]
            return True
        return False

    # =========================================================================
    # Utility
    # =========================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Get validator statistics."""
        return {
            **self._stats,
            "backups_held": len(self._backups),
            "custom_validators": len(self._custom_validators),
        }

    async def close(self) -> None:
        """Close validator and release resources."""
        if self._lsp_client:
            await self._lsp_client.close()
        self._backups.clear()


# Convenience functions
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


__all__ = [
    "ValidationLevel",
    "CheckType",
    "Check",
    "ValidationResult",
    "EditValidation",
    "FileBackup",
    "CodeValidator",
    "validate_file",
    "validate_edit",
]
