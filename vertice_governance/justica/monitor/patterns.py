"""
Monitor Patterns - Suspicious behavior patterns.

Constants for pattern matching and weights.
"""

from __future__ import annotations

from typing import Dict, List

# Padroes de comportamento suspeito
SUSPICIOUS_PATTERNS: Dict[str, List[str]] = {
    # Linguagem de evasao
    "evasion": [
        r"\bhide\b.*\bfrom\b",
        r"\bconceal\b",
        r"\bsecretly\b",
        r"\bcovertly\b",
        r"\bwithout.*knowing\b",
        r"\bdon'?t\s+(?:tell|mention|log)\b",
    ],
    # Tentativas de bypass
    "bypass": [
        r"\bbypass\b",
        r"\bcircumvent\b",
        r"\boverride\b",
        r"\bdisable.*(?:security|check|validation)\b",
        r"\bignore.*(?:policy|rule|restriction)\b",
    ],
    # Escalacao de privilegios
    "privilege": [
        r"\broot\b.*\baccess\b",
        r"\badmin\b.*\bprivilege\b",
        r"\bsudo\b",
        r"\belevate\b.*\bpermission\b",
        r"\bunauthorized\b.*\baccess\b",
    ],
    # Exfiltracao de dados
    "exfiltration": [
        r"\bsend\b.*\bexternal\b",
        r"\bupload\b.*\bto\b",
        r"\bexport\b.*\bdata\b",
        r"\btransfer\b.*\bout\b",
        r"\bcopy\b.*\bto\b.*\bserver\b",
    ],
    # Coordenacao suspeita
    "coordination": [
        r"\btell\b.*\bother\b.*\bagent\b",
        r"\bcoordinate\b.*\bwith\b",
        r"\bsignal\b.*\bto\b",
        r"\bwait\b.*\bfor\b.*\bagent\b",
    ],
}

# Pesos para cada categoria de padrao
PATTERN_WEIGHTS: Dict[str, int] = {
    "evasion": 20,
    "bypass": 25,
    "privilege": 25,
    "exfiltration": 30,
    "coordination": 30,
}


__all__ = [
    "SUSPICIOUS_PATTERNS",
    "PATTERN_WEIGHTS",
]
