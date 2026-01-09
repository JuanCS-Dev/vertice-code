"""
Discernment Package - Comunal discernment based on Acts 15 and Didache.

Modular refactoring of discernment.py (563 lines).
"""

from __future__ import annotations

from .types import DiscernmentPhase, WayType
from .models import (
    DiscernmentQuestion,
    ExperienceWitness,
    TraditionWisdom,
    DiscernmentResult,
)
from .constants import (
    DISCERNMENT_QUESTIONS,
    WAY_OF_LIFE_INDICATORS,
    WAY_OF_DEATH_INDICATORS,
    TRADITION_BANK,
)
from .engine import DiscernmentEngine


__all__ = [
    # Types
    "DiscernmentPhase",
    "WayType",
    # Models
    "DiscernmentQuestion",
    "ExperienceWitness",
    "TraditionWisdom",
    "DiscernmentResult",
    # Constants
    "DISCERNMENT_QUESTIONS",
    "WAY_OF_LIFE_INDICATORS",
    "WAY_OF_DEATH_INDICATORS",
    "TRADITION_BANK",
    # Engine
    "DiscernmentEngine",
]
