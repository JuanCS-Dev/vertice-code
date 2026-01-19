"""
Virtue Types - Core enums.

VirtueType enum with all virtues.
"""

from __future__ import annotations

from enum import Enum, auto


class VirtueType(Enum):
    """As virtudes fundamentais de SOFIA."""

    # Virtudes Cardinais (Cristianismo Primitivo)
    TAPEINOPHROSYNE = auto()  # Humildade
    MAKROTHYMIA = auto()  # Paciencia
    DIAKONIA = auto()  # Servico
    PRAOTES = auto()  # Mansidao/Gentileza

    # Virtudes Meta
    PHRONESIS = auto()  # Prudencia/Sabedoria Pratica
    FORTITUDE = auto()  # Coragem/Fortaleza

    # Virtudes Eticas Adicionais
    DIKAIOSYNE = auto()  # Justica
    ALETHEIA = auto()  # Honestidade/Verdade
    AGAPE = auto()  # Amor/Cuidado
    PISTIS = auto()  # Fidelidade/Confiabilidade


__all__ = ["VirtueType"]
