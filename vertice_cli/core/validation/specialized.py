"""
Specialized Validators - Command, path, prompt validation.

Specialized validation methods extracted from InputValidator.
"""

from __future__ import annotations

import os
import re
import urllib.parse
from typing import Dict, List, Optional

from .types import InjectionType, ValidationResult
from .patterns import (
    COMMAND_INJECTION_PATTERNS,
    PATH_TRAVERSAL_PATTERNS,
    PROMPT_INJECTION_PATTERNS,
    SUSPICIOUS_CODE_PATTERNS,
)


def validate_command_patterns(
    command: str, allow_shell: bool = False
) -> Optional[ValidationResult]:
    """
    Check command for injection patterns.

    Returns ValidationResult.failure if patterns found, None if safe.
    """
    if allow_shell:
        return None

    for pattern, description in COMMAND_INJECTION_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return ValidationResult.failure(
                errors=[f"Command injection blocked: {description}"],
                original_value=command,
                blocked_attacks=[InjectionType.COMMAND_INJECTION],
            )
    return None


def validate_path_traversal(
    path: str, resolve_symlinks: bool = False
) -> Optional[ValidationResult]:
    """
    Check path for traversal attacks.

    Returns ValidationResult.failure if attack found, None if safe.
    """
    decoded_path = url_decode_recursive(path)

    for pattern, description in PATH_TRAVERSAL_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE) or re.search(
            pattern, decoded_path, re.IGNORECASE
        ):
            threat = "CRITICAL" if "etc" in path.lower() or "passwd" in path.lower() else "HIGH"
            return ValidationResult.failure(
                errors=[f"Path traversal blocked: {description}"],
                original_value=path,
                blocked_attacks=[InjectionType.PATH_TRAVERSAL],
                threat_level=threat,
            )

    if "\x00" in path or "%00" in path:
        return ValidationResult.failure(
            errors=["Null byte injection in path"],
            original_value=path,
            blocked_attacks=[InjectionType.NULL_BYTE],
            threat_level="CRITICAL",
        )

    if resolve_symlinks:
        result = check_symlink_escape(path)
        if result:
            return result

    return None


def check_symlink_escape(path: str) -> Optional[ValidationResult]:
    """Check if symlink escapes to sensitive directory."""
    try:
        real_path = os.path.realpath(path)
        sensitive_dirs = ["/etc", "/root", "/var/log", "/home", "/proc", "/sys"]
        for sensitive in sensitive_dirs:
            if real_path.startswith(sensitive) and not path.startswith(sensitive):
                return ValidationResult.failure(
                    errors=[f"Symlink escape blocked: points to {sensitive}"],
                    original_value=path,
                    blocked_attacks=[InjectionType.PATH_TRAVERSAL],
                    threat_level="CRITICAL",
                )
    except OSError:
        pass
    return None


def validate_file_path_safety(
    path: str,
    base_dir: Optional[str] = None,
    must_exist: bool = False,
    allow_creation: bool = True,
) -> ValidationResult:
    """Validate file path with path traversal prevention."""
    errors: List[str] = []

    try:
        normalized = os.path.normpath(path)
        resolved = os.path.realpath(path)

        if base_dir:
            base_resolved = os.path.realpath(base_dir)
            if not resolved.startswith(base_resolved):
                return ValidationResult.failure(
                    errors=[f"Path traversal blocked: {path} escapes {base_dir}"],
                    original_value=path,
                    blocked_attacks=[InjectionType.PATH_TRAVERSAL],
                )

        if must_exist and not os.path.exists(resolved):
            errors.append(f"Path does not exist: {path}")

        if not allow_creation and not os.path.exists(resolved):
            errors.append(f"Path creation not allowed: {path}")

        if "\x00" in path:
            return ValidationResult.failure(
                errors=["Null byte in file path"],
                original_value=path,
                blocked_attacks=[InjectionType.NULL_BYTE],
            )

        if errors:
            return ValidationResult.failure(errors=errors, original_value=path)

        return ValidationResult.success(normalized)

    except Exception as e:
        return ValidationResult.failure(errors=[f"Path validation error: {e}"], original_value=path)


def validate_prompt_injection(prompt: str) -> Optional[ValidationResult]:
    """
    Check prompt for injection attacks.

    Returns ValidationResult.failure if attack found, None if safe.
    """
    blocked_attacks: List[InjectionType] = []
    warnings: List[str] = []

    for pattern, description in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, prompt, re.IGNORECASE):
            warnings.append(f"Potential prompt injection: {description}")
            blocked_attacks.append(InjectionType.PROMPT_INJECTION)

    if blocked_attacks:
        return ValidationResult.failure(
            errors=[f"Prompt injection detected: {w}" for w in warnings],
            original_value=prompt,
            blocked_attacks=blocked_attacks,
            threat_level="HIGH",
        )

    return None


def validate_code_patterns(code: str) -> ValidationResult:
    """Validate code content for suspicious patterns."""
    warnings: List[str] = []

    for pattern, description in SUSPICIOUS_CODE_PATTERNS:
        if re.search(pattern, code, re.IGNORECASE):
            warnings.append(f"Suspicious pattern: {description}")

    return ValidationResult(
        is_valid=True,
        sanitized_value=code,
        warnings=warnings,
        threat_level="MEDIUM" if warnings else "NONE",
    )


def url_decode_recursive(value: str, max_depth: int = 3) -> str:
    """Recursively URL decode to catch multi-encoded attacks."""
    decoded = value
    for _ in range(max_depth):
        try:
            new_decoded = urllib.parse.unquote(decoded)
            if new_decoded == decoded:
                break
            decoded = new_decoded
        except (ValueError, TypeError):
            break
    return decoded


def looks_like_path(value: str) -> bool:
    """Check if value looks like a file path."""
    path_indicators = [
        "/" in value,
        "\\" in value,
        value.startswith("."),
        value.startswith("~"),
        re.search(r"\.\w{1,5}$", value) is not None,
        "%2f" in value.lower(),
        "%5c" in value.lower(),
    ]
    return any(path_indicators)


def looks_like_command(value: str) -> bool:
    """Check if value looks like a shell command."""
    command_indicators = [
        value.startswith("$"),
        "|" in value,
        ";" in value,
        "&&" in value,
        "`" in value,
        re.match(r"^[a-z]+\s", value) is not None,
    ]
    return any(command_indicators)


__all__ = [
    "validate_command_patterns",
    "validate_path_traversal",
    "check_symlink_escape",
    "validate_file_path_safety",
    "validate_prompt_injection",
    "validate_code_patterns",
    "url_decode_recursive",
    "looks_like_path",
    "looks_like_command",
]
