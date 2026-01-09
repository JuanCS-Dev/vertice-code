"""
Secret Detector - Exposed secrets and credentials detection.

Pattern-based detection of API keys, tokens, and credentials.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List

from .types import Secret

logger = logging.getLogger(__name__)


async def detect_secrets(
    target: Path,
    patterns: Dict[str, re.Pattern],
) -> List[Secret]:
    """Detect exposed secrets using pattern matching.

    Args:
        target: File or directory to scan.
        patterns: Compiled regex patterns.

    Returns:
        List of detected secrets.
    """
    secrets: List[Secret] = []

    if target.is_file():
        files = [target]
    else:
        # Scan common config files + source code
        file_patterns = ["*.py", "*.json", "*.yaml", "*.yml", "*.env", ".env*"]
        files = []
        for pattern in file_patterns:
            files.extend(target.rglob(pattern))

    for file in files:
        try:
            with open(file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for i, line in enumerate(lines, 1):
                secrets.extend(_check_line_for_secrets(file, i, line, patterns))

        except (OSError, UnicodeDecodeError) as e:
            logger.debug(f"Skipping {file} in secret scan: {e}")
            continue

    return secrets


def _check_line_for_secrets(
    file: Path,
    line_num: int,
    line: str,
    patterns: Dict[str, re.Pattern],
) -> List[Secret]:
    """Check a single line for secret patterns.

    Args:
        file: Path to the file.
        line_num: Line number (1-indexed).
        line: Line content.
        patterns: Compiled regex patterns.

    Returns:
        List of detected secrets in this line.
    """
    secrets = []

    # API Keys
    match = patterns["api_key"].search(line)
    if match:
        secrets.append(
            Secret(
                type="api_key",
                file=str(file),
                line=line_num,
                pattern=match.group(2),
                confidence=0.9,
            )
        )

    # AWS Keys
    match = patterns["aws_key"].search(line)
    if match:
        secrets.append(
            Secret(
                type="aws_access_key",
                file=str(file),
                line=line_num,
                pattern=match.group(1),
                confidence=1.0,
            )
        )

    # GitHub Tokens
    match = patterns["github_token"].search(line)
    if match:
        secrets.append(
            Secret(
                type="github_token",
                file=str(file),
                line=line_num,
                pattern=match.group(1),
                confidence=1.0,
            )
        )

    # Private Keys
    match = patterns["private_key"].search(line)
    if match:
        secrets.append(
            Secret(
                type="private_key",
                file=str(file),
                line=line_num,
                pattern="[PRIVATE KEY DETECTED]",
                confidence=1.0,
            )
        )

    # Hardcoded passwords
    match = patterns["hardcoded_password"].search(line)
    if match:
        secrets.append(
            Secret(
                type="hardcoded_password",
                file=str(file),
                line=line_num,
                pattern=f"{match.group(1)}=[REDACTED]",
                confidence=0.95,
            )
        )

    # Hardcoded secrets
    match = patterns["hardcoded_secret"].search(line)
    if match:
        secrets.append(
            Secret(
                type="hardcoded_secret",
                file=str(file),
                line=line_num,
                pattern=f"{match.group(1)}=[REDACTED]",
                confidence=0.95,
            )
        )

    # Hardcoded tokens
    match = patterns["hardcoded_token"].search(line)
    if match:
        secrets.append(
            Secret(
                type="hardcoded_token",
                file=str(file),
                line=line_num,
                pattern=f"{match.group(1)}=[REDACTED]",
                confidence=0.9,
            )
        )

    # Generic API keys (sk-, pk-, etc)
    match = patterns["generic_api_key"].search(line)
    if match:
        # Mask the key for security
        key = match.group(1)
        masked = key[:6] + "..." + key[-4:] if len(key) > 10 else "[REDACTED]"
        secrets.append(
            Secret(
                type="generic_api_key",
                file=str(file),
                line=line_num,
                pattern=masked,
                confidence=0.85,
            )
        )

    return secrets


__all__ = ["detect_secrets"]
