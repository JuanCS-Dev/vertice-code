"""
Dependency Scanner - CVE scanning for vulnerable dependencies.

Uses pip-audit to check for known vulnerabilities.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import List

from .types import DependencyVulnerability, SeverityLevel

logger = logging.getLogger(__name__)


async def check_dependencies(target: Path) -> List[DependencyVulnerability]:
    """Check dependencies for known CVEs using pip-audit.

    Args:
        target: File or directory to scan for requirements.txt.

    Returns:
        List of dependency vulnerabilities found.
    """
    dep_vulns = []

    # Find requirements.txt
    req_file = _find_requirements_file(target)
    if not req_file:
        return dep_vulns

    try:
        # Run pip-audit
        result = subprocess.run(
            ["pip-audit", "-r", str(req_file), "--format", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            # pip-audit returns empty JSON on no vulns
            data = json.loads(result.stdout)
            for vuln in data.get("vulnerabilities", []):
                dep_vulns.append(
                    DependencyVulnerability(
                        package=vuln["name"],
                        version=vuln["version"],
                        cve_id=vuln["id"],
                        severity=map_cvss_to_severity(vuln.get("cvss", 0)),
                        description=vuln.get("description", "No description"),
                        fixed_version=vuln.get("fixed_version"),
                    )
                )

    except subprocess.TimeoutExpired:
        logger.warning("pip-audit timed out")
    except FileNotFoundError:
        logger.debug("pip-audit not installed")
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse pip-audit output: {e}")

    return dep_vulns


def _find_requirements_file(target: Path) -> Path | None:
    """Find requirements.txt file in target.

    Args:
        target: File or directory to search.

    Returns:
        Path to requirements file or None if not found.
    """
    if target.is_file() and target.name == "requirements.txt":
        return target
    elif target.is_dir():
        candidates = list(target.glob("requirements*.txt"))
        if candidates:
            return candidates[0]
    return None


def map_cvss_to_severity(cvss_score: float) -> SeverityLevel:
    """Map CVSS score to severity level.

    Args:
        cvss_score: CVSS score (0.0-10.0).

    Returns:
        Corresponding severity level.
    """
    if cvss_score >= 9.0:
        return SeverityLevel.CRITICAL
    elif cvss_score >= 7.0:
        return SeverityLevel.HIGH
    elif cvss_score >= 4.0:
        return SeverityLevel.MEDIUM
    elif cvss_score > 0.0:
        return SeverityLevel.LOW
    else:
        return SeverityLevel.INFO


__all__ = ["check_dependencies", "map_cvss_to_severity"]
