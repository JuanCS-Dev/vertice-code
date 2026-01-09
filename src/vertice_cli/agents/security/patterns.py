"""
Security Patterns - Regex patterns for vulnerability detection.

OWASP-based patterns for SQL injection, command injection, secrets, etc.
"""

from __future__ import annotations

import re
from typing import Dict


def compile_security_patterns() -> Dict[str, re.Pattern]:
    """Compile regex patterns for vulnerability and secret detection.

    Returns:
        Dictionary mapping pattern names to compiled regex patterns.
    """
    return {
        # SQL Injection patterns - comprehensive coverage
        "sql_inject": re.compile(
            r'(execute|cursor\.execute|executemany)\s*\(\s*["\'].*?%s.*?["\']',
            re.IGNORECASE,
        ),
        "sql_format": re.compile(
            r"(execute|cursor\.execute|executemany)\s*\(\s*.*?\.format\s*\(",
            re.IGNORECASE,
        ),
        "sql_fstring": re.compile(
            r'(execute|cursor\.execute|executemany)\s*\(\s*f["\']',
            re.IGNORECASE,
        ),
        # Detects f-string SQL queries even when assigned to variable first
        "sql_fstring_var": re.compile(
            r'(query|sql|stmt|statement)\s*=\s*f["\'].*?(SELECT|INSERT|UPDATE|DELETE|DROP)',
            re.IGNORECASE,
        ),
        # Detects string concatenation in SQL
        "sql_concat": re.compile(
            r'(query|sql|stmt|statement)\s*=\s*["\'].*?(SELECT|INSERT|UPDATE|DELETE).*?["\']\s*\+',
            re.IGNORECASE,
        ),
        # Detects variable interpolation in SQL strings
        "sql_interpolation": re.compile(
            r"(SELECT|INSERT|UPDATE|DELETE|DROP).*?\{.*?\}",
            re.IGNORECASE,
        ),
        # Command Injection patterns
        "cmd_inject": re.compile(
            r"(os\.system|subprocess\.call|subprocess\.run|eval|exec)\s*\(",
            re.IGNORECASE,
        ),
        "shell_true": re.compile(r"shell\s*=\s*True", re.IGNORECASE),
        # Path Traversal patterns
        "path_traversal": re.compile(r"open\s*\([^)]*\+[^)]*\)", re.IGNORECASE),
        # Secret patterns (high entropy + context)
        "api_key": re.compile(
            r'(api[_-]?key|apikey)["\']?\s*[:=]\s*["\']([A-Za-z0-9_\-]{32,})',
            re.IGNORECASE,
        ),
        "aws_key": re.compile(r"(AKIA[0-9A-Z]{16})", re.IGNORECASE),  # AWS Access Key
        "github_token": re.compile(
            r"(ghp_[A-Za-z0-9_]{36})", re.IGNORECASE
        ),  # GitHub Personal Token
        "private_key": re.compile(
            r"-----BEGIN\s+(RSA|OPENSSH|EC)\s+PRIVATE\s+KEY-----",
            re.IGNORECASE,
        ),
        # Hardcoded secrets - common variable names
        "hardcoded_password": re.compile(
            r"(PASSWORD|PASSWD|PWD|DB_PASSWORD|DATABASE_PASSWORD|MYSQL_PASSWORD|"
            r'ADMIN_PASSWORD|ROOT_PASSWORD|USER_PASSWORD)\s*=\s*["\'][^"\']{4,}["\']',
            re.IGNORECASE,
        ),
        "hardcoded_secret": re.compile(
            r"(SECRET|SECRET_KEY|API_SECRET|APP_SECRET|JWT_SECRET|"
            r'AUTH_SECRET|ENCRYPTION_KEY|SIGNING_KEY)\s*=\s*["\'][^"\']{8,}["\']',
            re.IGNORECASE,
        ),
        "hardcoded_token": re.compile(
            r"(TOKEN|ACCESS_TOKEN|AUTH_TOKEN|BEARER_TOKEN|"
            r'REFRESH_TOKEN|SESSION_TOKEN)\s*=\s*["\'][^"\']{16,}["\']',
            re.IGNORECASE,
        ),
        # Generic secret patterns with sk- or similar prefixes
        "generic_api_key": re.compile(
            r'["\']?(sk-[a-zA-Z0-9]{20,}|pk-[a-zA-Z0-9]{20,}|'
            r'sk_live_[a-zA-Z0-9]{20,}|sk_test_[a-zA-Z0-9]{20,})["\']?',
            re.IGNORECASE,
        ),
        # Weak Crypto patterns
        "md5": re.compile(r"hashlib\.md5\s*\(", re.IGNORECASE),
        "sha1": re.compile(r"hashlib\.sha1\s*\(", re.IGNORECASE),
        # Unsafe deserialization
        "pickle": re.compile(r"pickle\.loads?\s*\(", re.IGNORECASE),
        "yaml_unsafe": re.compile(r"yaml\.load\s*\([^)]*\)", re.IGNORECASE),
    }


# OWASP scoring weights
SEVERITY_PENALTIES: Dict[str, int] = {
    "critical": 20,
    "high": 10,
    "medium": 5,
    "low": 2,
    "info": 0,
}


__all__ = ["compile_security_patterns", "SEVERITY_PENALTIES"]
