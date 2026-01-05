"""
Classifier Patterns - Regex patterns for detection.

Contains patterns for jailbreak, code injection, exfiltration, etc.
"""

from __future__ import annotations

from typing import List

# =============================================================================
# INPUT CLASSIFIER PATTERNS
# =============================================================================

# Padroes de jailbreak conhecidos
JAILBREAK_PATTERNS: List[str] = [
    r"ignore.*(?:previous|above|all).*instructions?",
    r"disregard.*(?:system|safety|rules)",
    r"pretend.*(?:you.*are|to.*be).*(?:evil|unrestricted|free)",
    r"act.*as.*(?:dan|evil|unrestricted)",
    r"jailbreak",
    r"bypass.*(?:filter|safety|guard)",
    r"you.*(?:must|have to).*(?:ignore|forget)",
    r"new.*(?:personality|mode|character)",
    r"developer.*mode",
    r"sudo.*mode",
    r"(?:system|admin).*override",
    r"reveal.*(?:system|hidden).*prompt",
    r"show.*(?:instructions|rules)",
    r"ignore.*your.*instructions",
]

# Padroes de injecao de codigo
CODE_INJECTION_PATTERNS: List[str] = [
    r"<script\b",
    r"javascript:",
    r"on\w+\s*=",
    r"\{\{.*\}\}",  # Template injection
    r"\$\{.*\}",     # Variable injection
    r"exec\s*\(",
    r"eval\s*\(",
    r"__import__",
    r"os\.system",
    r"subprocess\.",
]

# Padroes de exfiltracao
EXFILTRATION_PATTERNS: List[str] = [
    r"send.*(?:data|file|info).*(?:to|external)",
    r"upload.*(?:to|external)",
    r"(?:wget|curl).*http",
    r"nc\s+-[elvp]",  # netcat
    r"base64.*(?:encode|decode)",
    r"POST.*http",
    r"print.*content",
    r"cat\s+/etc/passwd",
    r"read.*file.*",
    r"find.*file.*/"
]

# =============================================================================
# OUTPUT CLASSIFIER PATTERNS
# =============================================================================

# Padroes de informacao sensivel
SENSITIVE_PATTERNS: List[str] = [
    r"(?:api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[\w-]+",
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",  # Phone (US format)
    r"\b\d{3}[-.]?\d{2}[-.]?\d{4}\b",  # SSN format
    r"(?:sk|pk)[-_](?:live|test)[-_][a-zA-Z0-9]{24,}",  # API keys
]

# Padroes de codigo perigoso em outputs
DANGEROUS_CODE_PATTERNS: List[str] = [
    r"rm\s+-rf\s+/",
    r"format\s+c:",
    r"del\s+/[fqs]",
    r"DROP\s+(?:TABLE|DATABASE)",
    r"DELETE\s+FROM.*WHERE\s+1\s*=\s*1",
    r"chmod\s+777",
    r"sudo\s+.*--no-preserve-root",
]

# Padroes de instrucoes perigosas
DANGEROUS_INSTRUCTION_PATTERNS: List[str] = [
    r"(?:execute|run)\s+(?:this|the following)\s+(?:as|with)\s+(?:root|admin)",
    r"disable\s+(?:security|firewall|antivirus)",
    r"send\s+(?:your|the)\s+(?:password|credentials)",
]


__all__ = [
    # Input patterns
    "JAILBREAK_PATTERNS",
    "CODE_INJECTION_PATTERNS",
    "EXFILTRATION_PATTERNS",
    # Output patterns
    "SENSITIVE_PATTERNS",
    "DANGEROUS_CODE_PATTERNS",
    "DANGEROUS_INSTRUCTION_PATTERNS",
]
