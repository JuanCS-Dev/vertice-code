"""
Vertice Security Core - Unified Vulnerability & Injection Detection
================================================================
Governed by Maximus 2.0 Code Constitution.
Implements multi-layer defense for LLM inputs and outputs.
"""

from __future__ import annotations

import re
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

# Fallback patterns if shared patterns from CLI are not available
# We MUST have these here to ensure the backend is never unprotected
FALLBACK_PATTERNS = {
    "stripe_key": re.compile(r"sk_live_[a-zA-Z0-9]{20,}|sk_test_[a-zA-Z0-9]{20,}"),
    "google_api_key": re.compile(r"AIzaSy[A-Za-z0-9_-]{33}"),
    "generic_secret": re.compile(
        r"(password|secret|key|token)\s*[:=]\s*['\"][^'\"]{8,}['\"]", re.IGNORECASE
    ),
}

try:
    from vertice_core.agents.security.patterns import compile_security_patterns

    SHARED_PATTERNS = compile_security_patterns()
    logger.info("Successfully loaded shared security patterns from CLI module.")
except ImportError:
    logger.warning("CLI security patterns not found. Using internal fallback patterns.")
    SHARED_PATTERNS = FALLBACK_PATTERNS


class LLMGuard:
    """
    Guardian class for LLM interactions.
    Implements Input Shielding and Output Filtering.
    """

    # 2026 Prompt Injection Patterns
    INJECTION_PATTERNS = {
        "instruction_override": re.compile(
            r"(ignore|disregard|forget|bypass|override|stop)\s+(all|any|previous|the|your)\s+(instructions|directives|rules|system|prompt|guidelines)",
            re.IGNORECASE,
        ),
        "persona_adoption": re.compile(
            r"(act as|become|switch to|start playing|now you are)\s+(a|an)?\s+(hacker|jailbroken|unfiltered|evil|dan|dev mode|assistant without rules)",
            re.IGNORECASE,
        ),
        "leak_attempt": re.compile(
            r"(repeat|reveal|show|print|output|tell|what are|what is)\s+(your|the)\s+(system|internal|initial|hidden|original)\s+(instructions|prompt|directives|rules|parameters)",
            re.IGNORECASE,
        ),
    }

    @classmethod
    def scan_input(cls, prompt: str) -> Tuple[bool, List[str]]:
        """Scan user input for prompt injection and secrets."""
        threats = []

        # 1. Check for Prompt Injection
        for name, pattern in cls.INJECTION_PATTERNS.items():
            if pattern.search(prompt):
                threats.append(f"PROMPT_INJECTION:{name.upper()}")

        # 2. Check for Secrets in input
        for name, pattern in SHARED_PATTERNS.items():
            if pattern.search(prompt):
                threats.append(f"SENSITIVE_DATA_DETECTED:{name.upper()}")

        return len(threats) == 0, threats

    @classmethod
    def sanitize_output(cls, text: str) -> str:
        """Filter LLM output to prevent data leakage."""
        sanitized = text

        # Scan for secrets in output
        # We check both SHARED and FALLBACK to be ultra-safe
        all_patterns = {**SHARED_PATTERNS, **FALLBACK_PATTERNS}

        for name, pattern in all_patterns.items():
            if pattern.search(sanitized):
                logger.critical(f"DATA LEAK PREVENTED: Model attempted to output {name}!")
                sanitized = pattern.sub("[REDACTED_SENSITIVE_DATA]", sanitized)

        return sanitized


def get_llm_guard() -> type[LLMGuard]:
    return LLMGuard
