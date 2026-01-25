"""
Squad Validation - Input validation for DevSquad.

Pipeline Blindado Layer 1: Input validation.
"""

from __future__ import annotations

import logging
import re
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


# Dangerous command patterns
DANGEROUS_PATTERNS: List[str] = [
    r"rm\s+-rf\s+/",  # Destructive commands
    r"sudo\s+rm",  # Sudo destructive
    r">\s*/dev/",  # Write to devices
    r"mkfs\.",  # Format filesystem
    r"dd\s+if=",  # Direct disk write
    r":(){:|:&};:",  # Fork bomb
]


def validate_input(
    request: str,
    max_size: int = 50000,
    patterns: Optional[List[str]] = None,
) -> Tuple[bool, Optional[str]]:
    """
    Validate input request for dangerous patterns.

    Pipeline Blindado - Layer 1: Input Validation

    Args:
        request: User request string
        max_size: Maximum request size in bytes
        patterns: Custom dangerous patterns (uses default if None)

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not request or not request.strip():
        return False, "Empty request not allowed"

    if len(request) > max_size:
        return False, f"Request too large (max {max_size // 1024}KB)"

    # Use default or custom patterns
    check_patterns = patterns if patterns is not None else DANGEROUS_PATTERNS

    # Check for dangerous patterns
    for pattern in check_patterns:
        if re.search(pattern, request, re.IGNORECASE):
            logger.warning(f"Dangerous pattern detected: {pattern}")
            return False, "Request contains potentially dangerous command pattern"

    return True, None


__all__ = [
    "DANGEROUS_PATTERNS",
    "validate_input",
]
