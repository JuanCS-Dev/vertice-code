"""
Security Report Generator - OWASP-compliant security reports.

Generates human-readable reports and serializes findings.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .types import (
    DependencyVulnerability,
    Secret,
    SeverityLevel,
    Vulnerability,
)
from .patterns import SEVERITY_PENALTIES


def calculate_owasp_score(
    vulnerabilities: List[Vulnerability],
    secrets: List[Secret],
    dep_vulns: List[DependencyVulnerability],
) -> int:
    """Calculate OWASP compliance score (0-100).

    Scoring:
        - Start at 100
        - Deduct points based on severity
        - Minimum score: 0

    Args:
        vulnerabilities: List of code vulnerabilities.
        secrets: List of exposed secrets.
        dep_vulns: List of dependency vulnerabilities.

    Returns:
        OWASP compliance score (0-100).
    """
    score = 100

    # Deduct for code vulnerabilities
    for vuln in vulnerabilities:
        score -= SEVERITY_PENALTIES.get(vuln.severity.value, 0)

    # Deduct for exposed secrets (always critical)
    score -= len(secrets) * SEVERITY_PENALTIES["critical"]

    # Deduct for dependency vulnerabilities
    for dep in dep_vulns:
        score -= SEVERITY_PENALTIES.get(dep.severity.value, 0)

    return max(0, score)


def generate_report(
    vulnerabilities: List[Vulnerability],
    secrets: List[Secret],
    dep_vulns: List[DependencyVulnerability],
    owasp_score: int,
) -> str:
    """Generate human-readable security report.

    Args:
        vulnerabilities: List of code vulnerabilities.
        secrets: List of exposed secrets.
        dep_vulns: List of dependency vulnerabilities.
        owasp_score: Calculated OWASP compliance score.

    Returns:
        Formatted security report as string.
    """
    report = []
    report.append("=" * 80)
    report.append("SECURITY AUDIT REPORT")
    report.append("=" * 80)
    report.append("")

    # OWASP Score
    report.append(f"OWASP COMPLIANCE SCORE: {owasp_score}/100")
    if owasp_score >= 90:
        report.append("   Status: EXCELLENT")
    elif owasp_score >= 70:
        report.append("   Status: GOOD (minor issues)")
    elif owasp_score >= 50:
        report.append("   Status: FAIR (needs attention)")
    else:
        report.append("   Status: CRITICAL (immediate action required)")
    report.append("")

    # Vulnerabilities
    report.append(f"CODE VULNERABILITIES: {len(vulnerabilities)}")
    if vulnerabilities:
        for vuln in sorted(vulnerabilities, key=lambda v: list(SeverityLevel).index(v.severity)):
            report.append(f"   [{vuln.severity.value.upper()}] {vuln.type.value}")
            report.append(f"      File: {vuln.file}:{vuln.line}")
            report.append(f"      Code: {vuln.code_snippet}")
            report.append(f"      Fix:  {vuln.remediation}")
            report.append("")

    # Secrets
    report.append(f"EXPOSED SECRETS: {len(secrets)}")
    if secrets:
        for secret in secrets:
            report.append(f"   [CRITICAL] {secret.type}")
            report.append(f"      File: {secret.file}:{secret.line}")
            report.append(f"      Confidence: {secret.confidence * 100:.0f}%")
            report.append("")

    # Dependencies
    report.append(f"VULNERABLE DEPENDENCIES: {len(dep_vulns)}")
    if dep_vulns:
        for dep in dep_vulns:
            report.append(f"   [{dep.severity.value.upper()}] {dep.package}=={dep.version}")
            report.append(f"      CVE: {dep.cve_id}")
            if dep.fixed_version:
                report.append(f"      Fix: Upgrade to {dep.fixed_version}")
            report.append("")

    report.append("=" * 80)

    return "\n".join(report)


def vuln_to_dict(vuln: Vulnerability) -> Dict[str, Any]:
    """Convert Vulnerability to dict for serialization.

    Args:
        vuln: Vulnerability instance.

    Returns:
        Dictionary representation.
    """
    return {
        "type": vuln.type.value,
        "severity": vuln.severity.value,
        "file": vuln.file,
        "line": vuln.line,
        "code": vuln.code_snippet,
        "description": vuln.description,
        "remediation": vuln.remediation,
        "cwe_id": vuln.cwe_id,
    }


def secret_to_dict(secret: Secret) -> Dict[str, Any]:
    """Convert Secret to dict for serialization.

    Args:
        secret: Secret instance.

    Returns:
        Dictionary representation.
    """
    return {
        "type": secret.type,
        "file": secret.file,
        "line": secret.line,
        "confidence": secret.confidence,
    }


def dep_to_dict(dep: DependencyVulnerability) -> Dict[str, Any]:
    """Convert DependencyVulnerability to dict for serialization.

    Args:
        dep: DependencyVulnerability instance.

    Returns:
        Dictionary representation.
    """
    return {
        "package": dep.package,
        "version": dep.version,
        "cve_id": dep.cve_id,
        "severity": dep.severity.value,
        "description": dep.description,
        "fixed_version": dep.fixed_version,
    }


__all__ = [
    "calculate_owasp_score",
    "generate_report",
    "vuln_to_dict",
    "secret_to_dict",
    "dep_to_dict",
]
