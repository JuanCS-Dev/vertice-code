"""
Advanced Input Validation System for Vertice-Code.

Provides comprehensive sanitization, validation, and security checks
for all input interfaces to prevent injection attacks and data corruption.
"""

import re
import logging
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from urllib.parse import urlparse
import html

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of input validation."""

    is_valid: bool
    sanitized_data: Optional[Any] = None
    error_message: Optional[str] = None
    warnings: List[str] = None
    security_score: float = 1.0  # 0.0 = dangerous, 1.0 = safe

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class AdvancedInputValidator:
    """
    Comprehensive input validation and sanitization system.

    Features:
    - SQL injection prevention
    - XSS protection
    - Command injection blocking
    - Path traversal prevention
    - Malformed data detection
    - Type coercion safety
    - Size limits enforcement
    """

    def __init__(self):
        # Dangerous patterns for various attack vectors
        self.dangerous_patterns = {
            "sql_injection": re.compile(
                r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|JOIN)\b.*\b(FROM|INTO|WHERE|VALUES|TABLE|DATABASE)\b)",
                re.IGNORECASE | re.DOTALL,
            ),
            "command_injection": re.compile(r"[;&|`$(){}[\]<>\'\"\\]", re.MULTILINE),
            "path_traversal": re.compile(r"(\.\./|\.\.\\|~|\.\.)", re.IGNORECASE),
            "xss_attempts": re.compile(
                r"(<script|<iframe|<object|<embed|<form|<input|<meta|<link)", re.IGNORECASE
            ),
            "null_bytes": re.compile(r"\x00"),
            "control_chars": re.compile(r"[\x00-\x1F\x7F-\x9F]"),
        }

        # Size limits
        self.size_limits = {
            "string": 10 * 1024 * 1024,  # 10MB
            "list": 10000,  # 10k items
            "dict": 1000,  # 1k keys
            "nested_depth": 10,  # Max nesting depth
        }

    def validate_chat_message(self, message: str) -> ValidationResult:
        """Validate chat message input."""
        if not isinstance(message, str):
            return ValidationResult(
                is_valid=False, error_message="Message must be a string", security_score=0.0
            )

        if not message.strip():
            return ValidationResult(
                is_valid=False, error_message="Message cannot be empty", security_score=0.5
            )

        sanitized = self._sanitize_text(message)
        security_score = self._calculate_security_score(sanitized)

        # Check for dangerous patterns
        warnings = []
        for attack_type, pattern in self.dangerous_patterns.items():
            if pattern.search(sanitized):
                warnings.append(f"Potential {attack_type.replace('_', ' ')} detected")
                security_score *= 0.1

        # Length validation
        if len(sanitized) > self.size_limits["string"]:
            return ValidationResult(
                is_valid=False,
                error_message=f"Message too long: {len(sanitized)} > {self.size_limits['string']}",
                security_score=0.0,
            )

        return ValidationResult(
            is_valid=True,
            sanitized_data=sanitized,
            warnings=warnings,
            security_score=security_score,
        )

    def validate_file_path(self, path: str) -> ValidationResult:
        """Validate file path for security."""
        if not isinstance(path, str):
            return ValidationResult(
                is_valid=False, error_message="Path must be a string", security_score=0.0
            )

        # Check for path traversal
        if self.dangerous_patterns["path_traversal"].search(path):
            return ValidationResult(
                is_valid=False, error_message="Path traversal detected", security_score=0.0
            )

        # Check for null bytes
        if self.dangerous_patterns["null_bytes"].search(path):
            return ValidationResult(
                is_valid=False, error_message="Null bytes in path", security_score=0.0
            )

        # Sanitize path
        sanitized = path.strip()

        # Check length
        if len(sanitized) > 4096:  # Max path length
            return ValidationResult(
                is_valid=False, error_message="Path too long", security_score=0.0
            )

        return ValidationResult(is_valid=True, sanitized_data=sanitized, security_score=0.8)

    def validate_command(self, command: str) -> ValidationResult:
        """Validate shell command for execution."""
        if not isinstance(command, str):
            return ValidationResult(
                is_valid=False, error_message="Command must be a string", security_score=0.0
            )

        # Check for dangerous patterns
        if self.dangerous_patterns["command_injection"].search(command):
            return ValidationResult(
                is_valid=False,
                error_message="Command injection pattern detected",
                security_score=0.0,
            )

        # Check for SQL patterns in commands (might indicate confusion)
        if self.dangerous_patterns["sql_injection"].search(command):
            return ValidationResult(
                is_valid=False,
                error_message="SQL patterns in command - possible confusion",
                security_score=0.1,
            )

        # Basic command validation
        command = command.strip()
        if not command:
            return ValidationResult(
                is_valid=False, error_message="Empty command", security_score=0.5
            )

        # Check command length
        if len(command) > 8192:  # Reasonable command length limit
            return ValidationResult(
                is_valid=False, error_message="Command too long", security_score=0.0
            )

        return ValidationResult(is_valid=True, sanitized_data=command, security_score=0.9)

    def validate_json_data(self, data: Any, max_depth: int = None) -> ValidationResult:
        """Validate JSON-like data structures."""
        if max_depth is None:
            max_depth = self.size_limits["nested_depth"]

        try:
            size_score = self._validate_data_size(data, max_depth, 0)
            security_score = self._scan_data_for_threats(data)

            if size_score < 0:
                return ValidationResult(
                    is_valid=False,
                    error_message="Data structure too large or deeply nested",
                    security_score=0.0,
                )

            return ValidationResult(
                is_valid=True, sanitized_data=data, security_score=min(size_score, security_score)
            )

        except Exception as e:
            return ValidationResult(
                is_valid=False, error_message=f"Data validation failed: {e}", security_score=0.0
            )

    def validate_url(self, url: str) -> ValidationResult:
        """Validate URL for security."""
        if not isinstance(url, str):
            return ValidationResult(
                is_valid=False, error_message="URL must be a string", security_score=0.0
            )

        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ["http", "https", "ftp"]:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Unsupported URL scheme: {parsed.scheme}",
                    security_score=0.3,
                )

            # Check for dangerous characters in path/query
            dangerous_path = parsed.path + parsed.query
            if self.dangerous_patterns["command_injection"].search(dangerous_path):
                return ValidationResult(
                    is_valid=False, error_message="Dangerous characters in URL", security_score=0.0
                )

            return ValidationResult(is_valid=True, sanitized_data=url, security_score=0.8)

        except Exception as e:
            return ValidationResult(
                is_valid=False, error_message=f"Invalid URL: {e}", security_score=0.0
            )

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text input."""
        if not isinstance(text, str):
            return str(text)

        # Remove control characters (except newlines/tabs)
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]", "", text)

        # Escape HTML entities
        text = html.escape(text, quote=False)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text.strip())

        return text

    def _calculate_security_score(self, text: str) -> float:
        """Calculate security score for text (0.0 = dangerous, 1.0 = safe)."""
        score = 1.0

        # Length penalty (very long text might hide attacks)
        if len(text) > 10000:
            score *= 0.8
        elif len(text) > 100000:
            score *= 0.5

        # Entropy check (highly random text might be encoded attacks)
        entropy = self._calculate_text_entropy(text)
        if entropy > 0.9:  # Very high entropy
            score *= 0.7

        return max(0.0, min(1.0, score))

    def _calculate_text_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text."""
        if not text:
            return 0.0

        from collections import Counter
        import math

        char_counts = Counter(text)
        text_length = len(text)

        entropy = 0.0
        for count in char_counts.values():
            probability = count / text_length
            entropy -= probability * math.log2(probability)

        # Normalize to 0-1 range (max entropy for ASCII is ~7 bits)
        return entropy / 7.0

    def _validate_data_size(self, data: Any, max_depth: int, current_depth: int) -> float:
        """Validate data structure size and return size score."""
        if current_depth > max_depth:
            return -1.0  # Too deep

        if isinstance(data, str):
            if len(data) > self.size_limits["string"]:
                return -1.0
            return 1.0
        elif isinstance(data, list):
            if len(data) > self.size_limits["list"]:
                return -1.0
            score = 1.0
            for item in data:
                item_score = self._validate_data_size(item, max_depth, current_depth + 1)
                if item_score < 0:
                    return -1.0
                score = min(score, item_score)
            return score
        elif isinstance(data, dict):
            if len(data) > self.size_limits["dict"]:
                return -1.0
            score = 1.0
            for key, value in data.items():
                if not isinstance(key, str) or len(key) > 256:
                    return -1.0
                item_score = self._validate_data_size(value, max_depth, current_depth + 1)
                if item_score < 0:
                    return -1.0
                score = min(score, item_score)
            return score
        else:
            # Other types are generally safe
            return 1.0

    def _scan_data_for_threats(self, data: Any) -> float:
        """Scan data structure for security threats."""
        if isinstance(data, str):
            score = 1.0
            for pattern_name, pattern in self.dangerous_patterns.items():
                if pattern.search(data):
                    score *= 0.1  # Severe penalty for threats
            return score
        elif isinstance(data, (list, tuple)):
            score = 1.0
            for item in data:
                score = min(score, self._scan_data_for_threats(item))
            return score
        elif isinstance(data, dict):
            score = 1.0
            for key, value in data.items():
                if isinstance(key, str):
                    score = min(score, self._scan_data_for_threats(key))
                score = min(score, self._scan_data_for_threats(value))
            return score
        else:
            return 1.0


# Global instance
_input_validator = AdvancedInputValidator()


def get_input_validator() -> AdvancedInputValidator:
    """Get global input validator instance."""
    return _input_validator


def validate_chat_message(message: str) -> ValidationResult:
    """Convenience function for chat message validation."""
    return _input_validator.validate_chat_message(message)


def validate_file_path(path: str) -> ValidationResult:
    """Convenience function for file path validation."""
    return _input_validator.validate_file_path(path)


def validate_command(command: str) -> ValidationResult:
    """Convenience function for command validation."""
    return _input_validator.validate_command(command)
