"""
Google Jules Integration Module.

Integrates with Google Jules (Autonomous Coding Agent 2026) for:
- Automated code maintenance
- Security vulnerability scanning
- Technical debt management
- Automated PR creation

Part of M11: Autonomous Maintenance with Google Jules.
"""

from jules.service import (
    JulesService,
    get_jules_service,
    JulesConfig,
)
from jules.scanner import (
    CodeScanner,
    ScanResult,
    ScanType,
    VulnerabilityLevel,
)
from jules.github_integration import (
    GitHubIntegration,
    PullRequest,
    Issue,
)

__all__ = [
    # Service
    "JulesService",
    "get_jules_service",
    "JulesConfig",
    # Scanner
    "CodeScanner",
    "ScanResult",
    "ScanType",
    "VulnerabilityLevel",
    # GitHub
    "GitHubIntegration",
    "PullRequest",
    "Issue",
]
