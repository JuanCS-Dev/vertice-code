"""
SOFIA Agent Package - The wise counselor.

"Voce nao substitui sabedoria humana - voce a cultiva."

SOFIA e o agente conselheiro sabio inspirado em:
- Virtudes do Cristianismo Primitivo (Pre-Niceia)
- Didaque (50-120 d.C.)
- Praticas de Discernimento de Atos 15
- Metodo Socratico
- Etica das Virtudes
- Pensamento Sistema 2

Modulos:
    types: SofiaState, CounselType enums
    config: SofiaConfig dataclass
    counsel: SofiaCounsel dataclass
    core: SofiaAgent main class
    factory: create_sofia, quick_start_sofia

Exemplo de uso:
    >>> from vertice_governance.sofia.agent import create_sofia
    >>> sofia = create_sofia()
    >>> sofia.start()
    >>> counsel = sofia.respond("Estou pensando em mudar de carreira.")
    >>> print(counsel.response)
"""

from __future__ import annotations

# Types
from .types import CounselType, SofiaState

# Config
from .config import SofiaConfig

# Counsel
from .counsel import SofiaCounsel

# Core
from .core import SofiaAgent

# Factory
from .factory import create_sofia, quick_start_sofia


__all__ = [
    # Types
    "SofiaState",
    "CounselType",
    # Config
    "SofiaConfig",
    # Counsel
    "SofiaCounsel",
    # Core
    "SofiaAgent",
    # Factory
    "create_sofia",
    "quick_start_sofia",
]
