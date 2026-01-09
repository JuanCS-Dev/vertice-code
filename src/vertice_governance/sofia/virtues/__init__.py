"""
Virtues Package - The virtues of SOFIA.

Fundamentos do Cristianismo Primitivo (Pre-Niceia) antes de 325 d.C.

"Seja manso, paciente, sem malicia, gentil, bom. Nao se exalte."
                              - Didaque (50-120 d.C.)

As quatro virtudes fundamentais:
1. TAPEINOPHROSYNE (Humildade)
2. MAKROTHYMIA (Paciencia)
3. DIAKONIA (Servico)
4. PRAOTES (Mansidao)

Plus virtudes meta:
- PHRONESIS (Prudencia/Sabedoria Pratica)
- FORTITUDE (Coragem)

Modulos:
    types: VirtueType enum
    models: VirtueExpression, VirtueDefinition dataclasses
    definitions: Definicoes de todas as virtudes
    engine: VirtueEngine main class

Exemplo de uso:
    >>> from vertice_governance.sofia.virtues import VirtueEngine, VirtueType
    >>> engine = VirtueEngine()
    >>> virtue, phrase = engine.suggest_expression("preciso de ajuda")
    >>> print(f"{virtue.name}: {phrase}")
"""

from __future__ import annotations

# Types
from .types import VirtueType

# Models
from .models import VirtueDefinition, VirtueExpression

# Engine
from .engine import VirtueEngine


__all__ = [
    # Types
    "VirtueType",
    # Models
    "VirtueExpression",
    "VirtueDefinition",
    # Engine
    "VirtueEngine",
]
