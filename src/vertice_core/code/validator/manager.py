"""Code Validator implementation."""

from __future__ import annotations
import time
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from .types import ValidationLevel, CheckType, Check, ValidationResult, EditValidation
from .checks import check_syntax, check_lsp, check_imports
from .backup import BackupManager
from ..ast import ASTEditor, get_ast_editor
from ..lsp import LSPClient, get_lsp_client

logger = logging.getLogger(__name__)


class CodeValidator:
    """Validates code using LSP diagnostics and AST analysis."""

    def __init__(
        self,
        workspace_root: Optional[str] = None,
        lsp_client: Optional[LSPClient] = None,
        ast_editor: Optional[ASTEditor] = None,
    ):
        self.workspace_root = Path(workspace_root) if workspace_root else Path.cwd()
        self._lsp_client = lsp_client
        self._ast_editor = ast_editor or get_ast_editor()
        self.backup_manager = BackupManager(self.workspace_root)
        self._custom_validators: Dict[str, Callable] = {}
        self._stats = {"validations": 0, "errors_caught": 0, "rollbacks": 0}

    async def _get_lsp_client(self) -> Optional[LSPClient]:
        if self._lsp_client is None:
            try:
                self._lsp_client = get_lsp_client(str(self.workspace_root))
            except Exception as e:
                logger.warning(f"Could not initialize LSP client: {e}")
                return None
        return self._lsp_client

    def _get_language(self, filepath: str) -> Optional[str]:
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

    def _module_exists(self, module_name: str) -> bool:
        try:
            import importlib.util

            return importlib.util.find_spec(module_name) is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False

    async def validate(
        self,
        filepath: str,
        content: Optional[str] = None,
        level: ValidationLevel = ValidationLevel.LSP_BASIC,
    ) -> ValidationResult:
        self._stats["validations"] += 1
        start_time = time.time()
        checks: List[Check] = []
        errors: List[str] = []
        warnings: List[str] = []
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
        syntax_check = await check_syntax(content, language, self._ast_editor)
        checks.append(syntax_check)
        if not syntax_check.passed:
            errors.extend(syntax_check.details)
        if level in (
            ValidationLevel.LSP_BASIC,
            ValidationLevel.LSP_FULL,
            ValidationLevel.COMPREHENSIVE,
        ):
            lsp = await self._get_lsp_client()
            lsp_check = await check_lsp(filepath, content, level, lsp)
            checks.append(lsp_check)
            if not lsp_check.passed:
                for detail in lsp_check.details:
                    if "error" in detail.lower():
                        errors.append(detail)
                    else:
                        warnings.append(detail)
        if level == ValidationLevel.COMPREHENSIVE and language == "python":
            import_check = await check_imports(content, self._module_exists)
            checks.append(import_check)
            if not import_check.passed:
                errors.extend(import_check.details)
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
            valid=valid, checks=checks, errors=errors, warnings=warnings, duration_ms=duration_ms
        )

    async def validate_edit(
        self,
        filepath: str,
        old_content: str,
        new_content: str,
        level: ValidationLevel = ValidationLevel.LSP_BASIC,
    ) -> EditValidation:
        validation_before = await self.validate(filepath, old_content, level)
        validation_after = await self.validate(filepath, new_content, level)
        old_errors = set(validation_before.errors)
        new_errors_set = set(validation_after.errors)
        introduced = list(new_errors_set - old_errors)
        fixed = list(old_errors - new_errors_set)
        can_apply = len(introduced) == 0
        if can_apply:
            recommendation = (
                f"Edit improves code: fixed {len(fixed)} error(s)"
                if fixed
                else "Edit is safe to apply"
            )
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

    def backup_file(self, *args, **kwargs):
        return self.backup_manager.backup_file(*args, **kwargs)

    def get_backup(self, *args, **kwargs):
        return self.backup_manager.get_backup(*args, **kwargs)

    async def rollback(self, *args, **kwargs):
        res = await self.backup_manager.rollback(*args, **kwargs)
        if res:
            self._stats["rollbacks"] += 1
        return res

    def clear_backup(self, *args, **kwargs):
        return self.backup_manager.clear_backup(*args, **kwargs)

    def clear_all_backups(self, *args, **kwargs):
        return self.backup_manager.clear_all_backups(*args, **kwargs)

    async def safe_edit(
        self,
        filepath: str,
        old_content: str,
        new_content: str,
        auto_rollback: bool = True,
        level: ValidationLevel = ValidationLevel.LSP_BASIC,
    ) -> Tuple[bool, EditValidation]:
        self.backup_file(filepath, old_content)
        validation = await self.validate_edit(filepath, old_content, new_content, level)
        if validation.can_apply:
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
            if auto_rollback:
                logger.warning(f"Edit introduces {len(validation.new_errors)} errors, not applying")
            return False, validation

    def register_validator(self, name: str, validator: Callable) -> None:
        self._custom_validators[name] = validator

    def unregister_validator(self, name: str) -> bool:
        return self._custom_validators.pop(name, None) is not None

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "backups_held": len(self.backup_manager._backups),
            "custom_validators": len(self._custom_validators),
        }

    async def close(self) -> None:
        if self._lsp_client:
            await self._lsp_client.close()
        self.backup_manager.clear_all_backups()
