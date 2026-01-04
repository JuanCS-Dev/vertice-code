"""
Security Module - Offensive security scanning.

OWASP-compliant security auditing with vulnerability detection,
secret scanning, and dependency analysis.

Submodules:
    - types: Domain models (VulnerabilityType, Vulnerability, etc.)
    - patterns: Security regex patterns
    - detectors: Vulnerability detection methods
    - secrets: Secret/credential detection
    - dependencies: CVE scanning
    - report: Report generation
    - agent: SecurityAgent class
"""

from .types import (
    VulnerabilityType,
    SeverityLevel,
    Vulnerability,
    Secret,
    DependencyVulnerability,
)
from .patterns import compile_security_patterns, SEVERITY_PENALTIES
from .detectors import (
    EvalExecDetector,
    detect_sql_injection,
    detect_command_injection,
    detect_path_traversal,
    detect_weak_crypto,
    detect_unsafe_deserialization,
    detect_eval_usage,
)
from .secrets import detect_secrets
from .dependencies import check_dependencies, map_cvss_to_severity
from .report import (
    calculate_owasp_score,
    generate_report,
    vuln_to_dict,
    secret_to_dict,
    dep_to_dict,
)
from .agent import SecurityAgent

__all__ = [
    # Types
    "VulnerabilityType",
    "SeverityLevel",
    "Vulnerability",
    "Secret",
    "DependencyVulnerability",
    # Patterns
    "compile_security_patterns",
    "SEVERITY_PENALTIES",
    # Detectors
    "EvalExecDetector",
    "detect_sql_injection",
    "detect_command_injection",
    "detect_path_traversal",
    "detect_weak_crypto",
    "detect_unsafe_deserialization",
    "detect_eval_usage",
    # Secrets
    "detect_secrets",
    # Dependencies
    "check_dependencies",
    "map_cvss_to_severity",
    # Report
    "calculate_owasp_score",
    "generate_report",
    "vuln_to_dict",
    "secret_to_dict",
    "dep_to_dict",
    # Agent
    "SecurityAgent",
]
