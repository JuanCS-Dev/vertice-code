"""
Discernment Types - Core enums.
"""

from __future__ import annotations
from enum import Enum, auto


class DiscernmentPhase(Enum):
    """Fases do processo de discernimento (baseado em Atos 15)."""
    GATHERING = auto()
    DELIBERATION = auto()
    EXPERIENCE = auto()
    TRADITION = auto()
    ELDER_WISDOM = auto()
    SYNTHESIS = auto()
    CONFIRMATION = auto()


class WayType(Enum):
    """Os Dois Caminhos da Didaque."""
    WAY_OF_LIFE = auto()
    WAY_OF_DEATH = auto()
    UNCLEAR = auto()


__all__ = ["DiscernmentPhase", "WayType"]
