"""
Input Validator - Multi-Layer Input Validation (OWASP + CISA Compliant).

Pipeline de Diamante - Camada 1: INPUT FORTRESS.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional

from .types import InjectionType, ValidationLayer, ValidationResult
from .patterns import (
    ALLOWED_PATTERNS,
    COMMAND_INJECTION_PATTERNS,
    DANGEROUS_COMMAND_PATTERNS,
    MAX_LENGTHS,
    PATH_TRAVERSAL_PATTERNS,
    SQL_INJECTION_PATTERNS,
    UNICODE_ATTACK_PATTERNS,
)
from .specialized import (
    looks_like_command,
    looks_like_path,
    url_decode_recursive,
    validate_command_patterns,
    validate_file_path_safety,
    validate_path_traversal,
    validate_prompt_injection,
    validate_code_patterns,
)


class InputValidator:
    """
    Multi-layer input validation (OWASP + CISA compliant).

    Implements 5 layers of defense:
    1. Type validation - Strict type checking
    2. Length limits - DoS prevention
    3. Pattern whitelist - Only allowed characters
    4. Injection detection - Attack pattern detection
    5. Semantic validation - Context-aware validation
    """

    def __init__(
        self,
        strict_mode: bool = True,
        allow_unicode: bool = True,
        custom_patterns: Optional[Dict[str, re.Pattern]] = None,
    ):
        """Initialize validator."""
        self.strict_mode = strict_mode
        self.allow_unicode = allow_unicode
        self.custom_patterns = custom_patterns or {}
        self._audit_logger = None

    def validate(
        self,
        value: Any,
        input_type: str = "default",
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate input through all 5 layers."""
        context = context or {}
        errors: List[str] = []
        warnings: List[str] = []
        blocked_attacks: List[InjectionType] = []
        layer_results: Dict[ValidationLayer, bool] = {}

        # Layer 1: Type Validation
        type_result = self._validate_type(value, input_type)
        layer_results[ValidationLayer.TYPE_VALIDATION] = type_result.is_valid
        if not type_result.is_valid:
            return type_result

        str_value = str(value) if not isinstance(value, str) else value

        # Layer 2: Length Limits
        length_result = self._validate_length(str_value, input_type)
        layer_results[ValidationLayer.LENGTH_LIMITS] = length_result.is_valid
        if not length_result.is_valid:
            return length_result

        # Layer 3: Pattern Whitelist
        pattern_result = self._validate_pattern(str_value, input_type)
        layer_results[ValidationLayer.PATTERN_WHITELIST] = pattern_result.is_valid
        warnings.extend(pattern_result.warnings)

        # Layer 4: Injection Detection
        injection_result = self._detect_injections(str_value, input_type)
        layer_results[ValidationLayer.INJECTION_DETECTION] = injection_result.is_valid
        if not injection_result.is_valid:
            errors.extend(injection_result.errors)
            blocked_attacks.extend(injection_result.blocked_attacks)

        # Layer 5: Semantic Validation
        semantic_result = self._validate_semantics(str_value, input_type, context)
        layer_results[ValidationLayer.SEMANTIC_VALIDATION] = semantic_result.is_valid
        warnings.extend(semantic_result.warnings)

        # Determine validity and threat level
        is_valid = all(layer_results.values())
        if self.strict_mode and warnings:
            is_valid = False
            errors.extend([f"Warning (strict mode): {w}" for w in warnings])

        sanitized = self._sanitize(str_value, input_type) if is_valid else str_value
        threat_level = self._determine_threat_level(blocked_attacks, errors, warnings)

        return ValidationResult(
            is_valid=is_valid,
            sanitized_value=sanitized,
            errors=errors,
            warnings=warnings,
            blocked_attacks=blocked_attacks,
            layer_results=layer_results,
            threat_level=threat_level,
        )

    def validate_command(self, command: str, allow_shell: bool = False) -> ValidationResult:
        """Validate shell command (OWASP command injection prevention)."""
        result = self.validate(command, "command")

        if result.is_valid:
            pattern_result = validate_command_patterns(command, allow_shell)
            if pattern_result:
                self._log_security_violation(
                    "validate_command", command, {"attack_type": "command_injection"}
                )
                return pattern_result

        if result.blocked_attacks:
            self._log_security_violation(
                "validate_command",
                command,
                {"attack_types": [a.value for a in result.blocked_attacks]},
            )

        return result

    def validate_file_path(
        self,
        path: str,
        base_dir: Optional[str] = None,
        must_exist: bool = False,
        allow_creation: bool = True,
    ) -> ValidationResult:
        """Validate file path with path traversal prevention."""
        result = self.validate(path, "file_path")
        if not result.is_valid:
            return result

        return validate_file_path_safety(path, base_dir, must_exist, allow_creation)

    def validate_prompt(self, prompt: str) -> ValidationResult:
        """Validate user prompt for prompt injection attacks."""
        result = self.validate(prompt, "prompt")
        if not result.is_valid:
            return result

        injection_result = validate_prompt_injection(prompt)
        return injection_result if injection_result else result

    def validate_input(self, value: str) -> ValidationResult:
        """Generic input validation - detects type and validates accordingly."""
        if looks_like_path(value):
            result = self.validate_path(value)
        elif looks_like_command(value):
            result = self.validate_command(value)
        else:
            result = self.validate(value, "default")

        if result.blocked_attacks:
            self._log_security_violation(
                "validate_input",
                value,
                {"attack_types": [a.value for a in result.blocked_attacks]},
            )

        return result

    def validate_path(self, path: str, resolve_symlinks: bool = False) -> ValidationResult:
        """Validate path with comprehensive traversal detection."""
        traversal_result = validate_path_traversal(path, resolve_symlinks)
        if traversal_result:
            return traversal_result

        return self.validate_file_path(path, must_exist=False)

    def validate_code(self, code: str) -> ValidationResult:
        """Validate code content for suspicious patterns."""
        return validate_code_patterns(code)

    def _log_security_violation(
        self, action: str, resource: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log security violation to audit logger if available."""
        if self._audit_logger is not None:
            from ..audit_logger import AuditEventType

            self._audit_logger.log(
                event_type=AuditEventType.SECURITY_VIOLATION,
                action=action,
                resource=resource,
                outcome="blocked",
                details=details or {},
            )

    def _validate_type(self, value: Any, input_type: str) -> ValidationResult:
        """Layer 1: Type validation."""
        if value is None:
            return ValidationResult.failure(errors=["Value cannot be None"], original_value=value)

        if input_type in ("command", "file_path", "prompt", "filename"):
            if not isinstance(value, str):
                return ValidationResult.failure(
                    errors=[f"Expected string for {input_type}, got {type(value).__name__}"],
                    original_value=value,
                )

        return ValidationResult.success(value)

    def _validate_length(self, value: str, input_type: str) -> ValidationResult:
        """Layer 2: Length limits for DoS prevention."""
        max_length = MAX_LENGTHS.get(input_type, MAX_LENGTHS["default"])

        if len(value) > max_length:
            return ValidationResult.failure(
                errors=[f"Input too long: {len(value)} > {max_length} characters"],
                original_value=value,
            )

        return ValidationResult.success(value)

    def _validate_pattern(self, value: str, input_type: str) -> ValidationResult:
        """Layer 3: Pattern whitelist validation."""
        warnings: List[str] = []

        if input_type in self.custom_patterns:
            pattern = self.custom_patterns[input_type]
            if not pattern.match(value):
                return ValidationResult.failure(
                    errors=[f"Value does not match allowed pattern for {input_type}"],
                    original_value=value,
                )

        if input_type in ALLOWED_PATTERNS:
            pattern = ALLOWED_PATTERNS[input_type]
            if not pattern.match(value):
                warnings.append(f"Value contains characters outside typical {input_type} pattern")

        return ValidationResult(is_valid=True, sanitized_value=value, warnings=warnings)

    def _detect_injections(self, value: str, input_type: str) -> ValidationResult:
        """Layer 4: Injection attack detection."""
        errors: List[str] = []
        blocked_attacks: List[InjectionType] = []

        # Check all injection patterns
        self._check_command_injection(value, errors, blocked_attacks)
        self._check_path_traversal(value, errors, blocked_attacks)
        self._check_null_bytes(value, errors, blocked_attacks)
        self._check_newlines(value, input_type, errors, blocked_attacks)
        self._check_unicode_attacks(value, errors, blocked_attacks)
        self._check_sql_injection(value, errors, blocked_attacks)
        self._check_encoded_injection(value, errors, blocked_attacks)

        if errors:
            threat = "CRITICAL" if InjectionType.COMMAND_INJECTION in blocked_attacks else "HIGH"
            return ValidationResult.failure(
                errors=errors,
                original_value=value,
                blocked_attacks=blocked_attacks,
                threat_level=threat,
            )

        return ValidationResult.success(value)

    def _check_command_injection(
        self, value: str, errors: List[str], blocked: List[InjectionType]
    ) -> None:
        for pattern, description in COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append(f"Command injection blocked: {description}")
                if InjectionType.COMMAND_INJECTION not in blocked:
                    blocked.append(InjectionType.COMMAND_INJECTION)

    def _check_path_traversal(
        self, value: str, errors: List[str], blocked: List[InjectionType]
    ) -> None:
        for pattern, description in PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append(f"Path traversal blocked: {description}")
                if InjectionType.PATH_TRAVERSAL not in blocked:
                    blocked.append(InjectionType.PATH_TRAVERSAL)

    def _check_null_bytes(
        self, value: str, errors: List[str], blocked: List[InjectionType]
    ) -> None:
        if "\x00" in value:
            errors.append("Null byte injection blocked")
            blocked.append(InjectionType.NULL_BYTE)

    def _check_newlines(
        self,
        value: str,
        input_type: str,
        errors: List[str],
        blocked: List[InjectionType],
    ) -> None:
        if input_type in ("filename", "identifier", "argument"):
            if "\n" in value or "\r" in value:
                errors.append("Newline injection blocked")
                blocked.append(InjectionType.NEWLINE_INJECTION)

    def _check_unicode_attacks(
        self, value: str, errors: List[str], blocked: List[InjectionType]
    ) -> None:
        for char, description in UNICODE_ATTACK_PATTERNS:
            if char in value:
                errors.append(f"Unicode attack blocked: {description}")
                if InjectionType.UNICODE_ATTACK not in blocked:
                    blocked.append(InjectionType.UNICODE_ATTACK)

    def _check_sql_injection(
        self, value: str, errors: List[str], blocked: List[InjectionType]
    ) -> None:
        for pattern, description in SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                errors.append(f"SQL injection blocked: {description}")
                if InjectionType.SQL_INJECTION not in blocked:
                    blocked.append(InjectionType.SQL_INJECTION)

    def _check_encoded_injection(
        self, value: str, errors: List[str], blocked: List[InjectionType]
    ) -> None:
        decoded = url_decode_recursive(value)
        if decoded != value:
            for pattern, description in COMMAND_INJECTION_PATTERNS:
                if re.search(pattern, decoded, re.IGNORECASE):
                    errors.append(f"URL-encoded command injection blocked: {description}")
                    if InjectionType.COMMAND_INJECTION not in blocked:
                        blocked.append(InjectionType.COMMAND_INJECTION)

    def _validate_semantics(
        self, value: str, input_type: str, context: Dict[str, Any]
    ) -> ValidationResult:
        """Layer 5: Context-aware semantic validation."""
        warnings: List[str] = []

        if input_type == "file_path":
            suspicious_exts = [".exe", ".dll", ".bat", ".cmd", ".ps1", ".sh"]
            for ext in suspicious_exts:
                if value.lower().endswith(ext):
                    warnings.append(f"Executable file extension: {ext}")

            if value.startswith("/etc/") or value.startswith("/root/"):
                warnings.append("Access to sensitive system directory")

        elif input_type == "command":
            for pattern, description in DANGEROUS_COMMAND_PATTERNS:
                if re.search(pattern, value):
                    warnings.append(f"Potentially dangerous: {description}")

        return ValidationResult(is_valid=True, sanitized_value=value, warnings=warnings)

    def _sanitize(self, value: str, input_type: str) -> str:
        """Sanitize value based on input type."""
        sanitized = value.replace("\x00", "")

        if not self.allow_unicode:
            sanitized = sanitized.encode("ascii", "ignore").decode("ascii")
        else:
            sanitized = unicodedata.normalize("NFC", sanitized)

        for char, _ in UNICODE_ATTACK_PATTERNS:
            sanitized = sanitized.replace(char, "")

        return sanitized

    def _determine_threat_level(
        self,
        blocked_attacks: List[InjectionType],
        errors: List[str],
        warnings: List[str],
    ) -> str:
        """Determine threat level based on validation results."""
        if blocked_attacks:
            critical = {InjectionType.COMMAND_INJECTION, InjectionType.PATH_TRAVERSAL}
            if any(atk in critical for atk in blocked_attacks):
                return "CRITICAL"
            elif InjectionType.SQL_INJECTION in blocked_attacks:
                return "HIGH"
            return "MEDIUM"
        elif errors:
            return "HIGH"
        elif warnings:
            return "LOW"
        return "NONE"


# Convenience functions


def validate_command(command: str, allow_shell: bool = False) -> ValidationResult:
    """Validate a shell command."""
    return InputValidator().validate_command(command, allow_shell)


def validate_file_path(
    path: str, base_dir: Optional[str] = None, must_exist: bool = False
) -> ValidationResult:
    """Validate a file path."""
    return InputValidator().validate_file_path(path, base_dir, must_exist)


def validate_prompt(prompt: str) -> ValidationResult:
    """Validate a user prompt."""
    return InputValidator().validate_prompt(prompt)


def is_safe_command(command: str) -> bool:
    """Quick check if command is safe."""
    return InputValidator(strict_mode=False).validate_command(command).is_valid


def is_safe_path(path: str, base_dir: Optional[str] = None) -> bool:
    """Quick check if path is safe."""
    return InputValidator(strict_mode=False).validate_file_path(path, base_dir).is_valid


__all__ = [
    "InputValidator",
    "validate_command",
    "validate_file_path",
    "validate_prompt",
    "is_safe_command",
    "is_safe_path",
]
