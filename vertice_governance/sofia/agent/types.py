"""
Sofia Agent Types - Core enums.

SofiaState and CounselType enums.
"""

from __future__ import annotations

from enum import Enum, auto


class SofiaState(Enum):
    """Estados possiveis de SOFIA."""

    LISTENING = auto()      # Ouvindo ativamente
    REFLECTING = auto()     # Refletindo (Sistema 2)
    QUESTIONING = auto()    # Fazendo perguntas socraticas
    DISCERNING = auto()     # Em processo de discernimento
    COUNSELING = auto()     # Oferecendo conselho
    LEARNING = auto()       # Aprendendo de feedback


class CounselType(Enum):
    """Tipos de aconselhamento que SOFIA oferece."""

    CLARIFYING = auto()     # Ajudando a clarificar
    EXPLORING = auto()      # Explorando perspectivas
    DELIBERATING = auto()   # Deliberacao profunda
    DISCERNING = auto()     # Discernimento espiritual
    SUPPORTING = auto()     # Apoio emocional
    REFERRING = auto()      # Referindo a outros


__all__ = [
    "SofiaState",
    "CounselType",
]
