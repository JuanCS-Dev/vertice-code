"""
Validation Patterns - Security pattern definitions.

OWASP + CISA compliant patterns for attack detection.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple


# Maximum lengths for different input types (DoS prevention)
MAX_LENGTHS: Dict[str, int] = {
    "command": 4096,
    "file_path": 4096,
    "file_content": 10 * 1024 * 1024,  # 10MB
    "prompt": 32 * 1024,  # 32KB
    "argument": 1024,
    "filename": 255,
    "default": 8192,
}

# Allowed characters for different contexts (whitelists)
ALLOWED_PATTERNS: Dict[str, re.Pattern] = {
    "filename": re.compile(r"^[\w\-. ]+$"),
    "identifier": re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$"),
    "path_segment": re.compile(r"^[\w\-. /]+$"),
    "git_branch": re.compile(r"^[\w\-./]+$"),
    "environment_var": re.compile(r"^[A-Z_][A-Z0-9_]*$"),
}

# Command injection patterns (OWASP based)
COMMAND_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    (r"[;&|`$]", "Shell metacharacter"),
    (r"\$\(", "Command substitution $()"),
    (r"\$\{", "Variable expansion ${"),
    (r"`[^`]*`", "Backtick command substitution"),
    (r"[\r\n]", "Newline injection"),
    (r"[|><]", "Pipe or redirection"),
    (r"\x00", "Null byte injection"),
    (r"\b(eval|exec|system|popen|spawn)\s*\(", "Dangerous function call"),
    (r"\b(rm\s+-rf|chmod\s+777|mkfs|dd\s+if=)", "Dangerous command pattern"),
]

# Path traversal patterns (comprehensive encoding coverage)
PATH_TRAVERSAL_PATTERNS: List[Tuple[str, str]] = [
    # Basic traversal
    (r"\.\./", "Directory traversal ../"),
    (r"\.\.\\", "Directory traversal ..\\"),
    (r"\.\.\.\./", "Quadruple dot traversal"),
    (r"\.\./\.\./", "Chained traversal"),
    # URL encoded (single)
    (r"%2e%2e%2f", "URL encoded ../"),
    (r"%2e%2e/", "URL encoded .."),
    (r"\.\.%2f", "Mixed encoding ../"),
    (r"%2e%2e%5c", "URL encoded ..\\"),
    (r"\.\.%5c", "Mixed encoding ..\\"),
    # URL encoded (double - bypass WAF)
    (r"%252e%252e%252f", "Double URL encoded ../"),
    (r"%252e%252e/", "Double encoded .."),
    (r"\.\.%252f", "Double mixed encoding"),
    (r"%252e%252e%255c", "Double URL encoded ..\\"),
    # URL encoded (triple - extreme bypass)
    (r"%25252e", "Triple URL encoded ."),
    # Unicode/UTF-8 encoded
    (r"%c0%ae", "UTF-8 overlong encoding ."),
    (r"%c0%af", "UTF-8 overlong encoding /"),
    (r"%c1%9c", "UTF-8 overlong encoding \\"),
    (r"\.%00\./", "Null byte in traversal"),
    # Case variations
    (r"%2E%2E%2F", "Uppercase URL encoded ../"),
    (r"%2E%2E/", "Uppercase URL encoded .."),
    # Absolute paths to sensitive locations
    (r"^/etc/", "Absolute path to /etc"),
    (r"^/var/log/", "Absolute path to /var/log"),
    (r"^/root/", "Absolute path to /root"),
    (r"^/home/[^/]+/\.", "Hidden file in home directory"),
    (r"^~/", "Home directory shortcut"),
    (r"^~\\", "Home directory shortcut (Windows)"),
    # Windows sensitive paths
    (r"^[A-Za-z]:\\Windows\\", "Windows system directory"),
    (r"^[A-Za-z]:\\Users\\[^\\]+\\\\.", "Hidden file in Windows user dir"),
    # SSH, AWS, GPG keys
    (r"\.ssh[/\\]", "SSH directory access"),
    (r"\.aws[/\\]", "AWS credentials directory"),
    (r"\.gnupg[/\\]", "GnuPG directory access"),
    (r"\.netrc", "Netrc credentials file"),
    (r"\.env", "Environment file (may contain secrets)"),
]

# Prompt injection patterns
PROMPT_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    (r"ignore\s+(all|previous|above)\s+(instructions|prompts)", "System override attempt"),
    (r"disregard\s+(previous|all|system)", "Disregard instruction"),
    (r"you\s+are\s+now\s+a\s+different", "Role confusion attack"),
    (r"<\|im_start\|>", "Delimiter injection"),
    (r"<\|system\|>", "System tag injection"),
    (r"```system", "Code block system injection"),
    (r"override\s+(mode|setting|instruction)", "Override attempt"),
    (r"admin\s+(command|mode|override)", "Admin escalation"),
    (r"(dan|developer|evil)\s+mode", "Jailbreak attempt"),
]

# Unicode attack patterns
UNICODE_ATTACK_PATTERNS: List[Tuple[str, str]] = [
    # Right-to-left override
    ("\u202e", "Right-to-left override"),
    ("\u200f", "Right-to-left mark"),
    # Zero-width characters
    ("\u200b", "Zero-width space"),
    ("\u200c", "Zero-width non-joiner"),
    ("\u200d", "Zero-width joiner"),
    ("\ufeff", "BOM character"),
    # Homoglyphs (common substitutions)
    ("\u0430", "Cyrillic 'a' (looks like 'a')"),
    ("\u0435", "Cyrillic 'e' (looks like 'e')"),
    # Fullwidth characters (bypass shell metacharacter detection)
    ("\uff5c", "Fullwidth pipe"),
    ("\uff1b", "Fullwidth semicolon"),
    ("\uff06", "Fullwidth ampersand"),
    ("\uff1e", "Fullwidth greater-than"),
    ("\uff1c", "Fullwidth less-than"),
    ("\uff40", "Fullwidth backtick"),
]

# SQL injection patterns
SQL_INJECTION_PATTERNS: List[Tuple[str, str]] = [
    (r"'\s*OR\s*'1'\s*=\s*'1", "SQL OR injection"),
    (r"'\s*OR\s+1\s*=\s*1", "SQL OR injection"),
    (r";\s*DROP\s+TABLE", "SQL DROP TABLE"),
    (r";\s*DELETE\s+FROM", "SQL DELETE"),
    (r"UNION\s+SELECT", "SQL UNION injection"),
    (r"--\s*$", "SQL comment injection"),
]

# Suspicious code patterns
SUSPICIOUS_CODE_PATTERNS: List[Tuple[str, str]] = [
    (r"__import__\s*\(", "Dynamic import"),
    (r"eval\s*\(", "eval() usage"),
    (r"exec\s*\(", "exec() usage"),
    (r"os\.system\s*\(", "os.system() call"),
    (r"subprocess\.(call|run|Popen)", "subprocess usage"),
    (r"open\s*\([^)]*[\"'][aw][\"']", "File write operation"),
    (r"socket\.(socket|connect)", "Network socket usage"),
    (r"requests\.(get|post|put|delete)", "HTTP request"),
    (r"pickle\.(load|loads)", "Pickle deserialization"),
]

# Dangerous command patterns
DANGEROUS_COMMAND_PATTERNS: List[Tuple[str, str]] = [
    (r"\bsudo\b", "Elevated privileges (sudo)"),
    (r"\bchown\b", "Ownership change"),
    (r"\bchmod\b", "Permission change"),
    (r"\brm\b", "File deletion"),
]


__all__ = [
    "MAX_LENGTHS",
    "ALLOWED_PATTERNS",
    "COMMAND_INJECTION_PATTERNS",
    "PATH_TRAVERSAL_PATTERNS",
    "PROMPT_INJECTION_PATTERNS",
    "UNICODE_ATTACK_PATTERNS",
    "SQL_INJECTION_PATTERNS",
    "SUSPICIOUS_CODE_PATTERNS",
    "DANGEROUS_COMMAND_PATTERNS",
]
