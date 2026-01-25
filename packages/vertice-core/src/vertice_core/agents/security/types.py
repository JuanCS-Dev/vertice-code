"""
Security Types - Domain models for security analysis.

Enums and dataclasses for vulnerability tracking.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class VulnerabilityType(str, Enum):
    """Classification of security vulnerabilities."""

    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    UNSAFE_DESERIALIZATION = "unsafe_deserialization"
    EVAL_USAGE = "eval_usage"
    HARDCODED_SECRET = "hardcoded_secret"
    WEAK_CRYPTO = "weak_crypto"


class SeverityLevel(str, Enum):
    """CVSS-inspired severity classification."""

    CRITICAL = "critical"  # 9.0-10.0
    HIGH = "high"  # 7.0-8.9
    MEDIUM = "medium"  # 4.0-6.9
    LOW = "low"  # 0.1-3.9
    INFO = "info"  # 0.0


@dataclass
class Vulnerability:
    """Represents a single security vulnerability."""

    type: VulnerabilityType
    severity: SeverityLevel
    file: str
    line: int
    code_snippet: str
    description: str
    remediation: str
    cwe_id: Optional[str] = None  # Common Weakness Enumeration


@dataclass
class Secret:
    """Represents an exposed secret/credential."""

    type: str  # "api_key", "aws_key", "github_token", etc.
    file: str
    line: int
    pattern: str
    confidence: float  # 0.0-1.0


@dataclass
class DependencyVulnerability:
    """Represents a vulnerable dependency."""

    package: str
    version: str
    cve_id: str
    severity: SeverityLevel
    description: str
    fixed_version: Optional[str] = None


__all__ = [
    "VulnerabilityType",
    "SeverityLevel",
    "Vulnerability",
    "Secret",
    "DependencyVulnerability",
]
