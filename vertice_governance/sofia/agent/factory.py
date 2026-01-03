"""
Sofia Agent Factory - Factory functions.

create_sofia and quick_start_sofia.
"""

from __future__ import annotations

from typing import Any

from .config import SofiaConfig
from .core import SofiaAgent


def create_sofia(**kwargs: Any) -> SofiaAgent:
    """Cria instancia de SOFIA com configuracao opcional."""
    config = SofiaConfig(**kwargs)
    return SofiaAgent(config=config)


def quick_start_sofia() -> SofiaAgent:
    """Inicio rapido de SOFIA."""
    sofia = create_sofia()
    sofia.start()
    return sofia


__all__ = [
    "create_sofia",
    "quick_start_sofia",
]
