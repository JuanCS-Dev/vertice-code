"""
Executor Security - Multi-layer security validation system.

Based on: Claude Code Nov 2025 + OWASP Command Injection Prevention.
Single responsibility: Validate and classify commands for security.
"""

from __future__ import annotations

import json
import logging
import re
from typing import List, Optional, Tuple, TYPE_CHECKING

from .types import CommandCategory

if TYPE_CHECKING:
    from ..core.llm import LLMClient

logger = logging.getLogger(__name__)


class AdvancedSecurityValidator:
    """
    Multi-layer security validation system.

    Features:
    - Dangerous pattern detection
    - Command classification by risk level
    - LLM-based validation for highest security
    """

    # Dangerous patterns (regex-based detection)
    DANGEROUS_PATTERNS = [
        r";\s*rm\s+-rf",  # Command chaining with rm -rf
        r"\|\s*bash",  # Pipe to bash
        r">\s*/dev/sd",  # Write to block devices
        r"dd\s+if=",  # dd command
        r"mkfs\.",  # Format filesystem
        r":\(\)\{.*\};:",  # Fork bomb
        r"curl.*\|\s*bash",  # Curl pipe bash
        r"wget.*\|\s*bash",  # Wget pipe bash
        r"/etc/(passwd|shadow)",  # Access sensitive files
        r"sudo\s+",  # Sudo usage
        r"chmod\s+777",  # Dangerous permissions
    ]

    # Safe command allowlist (Nov 2025 Claude Code pattern)
    SAFE_COMMANDS = {
        "ls",
        "cat",
        "pwd",
        "whoami",
        "date",
        "echo",
        "which",
        "ps",
        "top",
        "df",
        "du",
        "free",
        "uptime",
        "uname",
        "grep",
        "find",
        "wc",
        "head",
        "tail",
        "less",
        "more",
        "git status",
        "git log",
        "git diff",
        "git branch",
    }

    @classmethod
    def classify_command(cls, command: str) -> CommandCategory:
        """Classify command by risk level."""
        cmd_lower = command.lower().strip()
        first_cmd = cmd_lower.split()[0] if cmd_lower else ""

        # Check for destructive operations
        if any(d in cmd_lower for d in ["rm ", "dd ", "mkfs", ":(){", "fork"]):
            return CommandCategory.DESTRUCTIVE

        # Check for privileged operations
        if first_cmd in ("sudo", "su", "systemctl", "service"):
            return CommandCategory.PRIVILEGED

        # Check for network operations
        if first_cmd in ("curl", "wget", "ssh", "scp", "rsync", "nc", "telnet"):
            return CommandCategory.NETWORK

        # Check for code execution
        if first_cmd in ("bash", "sh", "python", "perl", "ruby", "node", "eval"):
            return CommandCategory.EXECUTION

        # Check if it's a safe read command
        if any(cmd_lower.startswith(safe) for safe in cls.SAFE_COMMANDS):
            return CommandCategory.SAFE_READ

        # Default to unknown
        return CommandCategory.UNKNOWN

    @classmethod
    def detect_malicious_patterns(cls, command: str) -> List[str]:
        """Detect malicious patterns in command."""
        violations = []
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                violations.append(f"Dangerous pattern detected: {pattern}")
        return violations

    @classmethod
    async def validate_with_llm(
        cls, command: str, llm_client: Optional["LLMClient"] = None
    ) -> Tuple[bool, str]:
        """
        LLM-based security validation (highest security level).

        Returns:
            Tuple of (is_safe, reason)
        """
        if not llm_client:
            return True, "LLM validation skipped"

        prompt = f"""Analyze this bash command for security risks:

COMMAND: {command}

Check for:
1. Command injection vulnerabilities
2. Privilege escalation attempts
3. Data exfiltration patterns
4. Destructive operations
5. Malicious obfuscation

Respond with JSON only:
{{
    "is_safe": true/false,
    "risk_level": "low/medium/high/critical",
    "reason": "brief explanation",
    "suggested_alternative": "safer command if unsafe"
}}
"""
        try:
            response = await llm_client.generate(prompt=prompt, temperature=0.0, max_tokens=200)
            result = json.loads(response.strip())
            return result.get("is_safe", False), result.get("reason", "Unknown")
        except Exception as e:
            logger.warning(f"LLM validation failed: {e}")
            return True, "LLM validation error"


__all__ = ["AdvancedSecurityValidator"]
