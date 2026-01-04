"""
SecurityAgent - Backward Compatibility Re-export.

REFACTORED: This module has been split into modular components:
- security/types.py: VulnerabilityType, SeverityLevel, dataclasses
- security/patterns.py: Security pattern definitions
- security/detectors.py: Vulnerability detection methods
- security/secrets.py: Secret detection
- security/dependencies.py: CVE scanning
- security/report.py: Report generation
- security/agent.py: SecurityAgent class

All symbols are re-exported here for backward compatibility.
Import from 'security' subpackage for new code.

Philosophy (Boris Cherny):
    "Security is not a feature. It's a non-negotiable."
"""

# Re-export all public symbols for backward compatibility
from .security import (
    # Types
    VulnerabilityType,
    SeverityLevel,
    Vulnerability,
    Secret,
    DependencyVulnerability,
    # Detectors
    EvalExecDetector,
    # Agent
    SecurityAgent,
)

__all__ = [
    "VulnerabilityType",
    "SeverityLevel",
    "Vulnerability",
    "Secret",
    "DependencyVulnerability",
    "EvalExecDetector",
    "SecurityAgent",
]
