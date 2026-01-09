"""
JUSTICA Agent Factory - Factory functions for creating JUSTICA agents.

Provides convenience functions for creating JusticaAgent instances
with different configurations.
"""

from __future__ import annotations

from ..constitution import create_strict_constitution
from ..enforcement import EnforcementMode
from .core import JusticaAgent
from .types import JusticaConfig


def create_justica(
    mode: EnforcementMode = EnforcementMode.NORMATIVE,
    **kwargs,
) -> JusticaAgent:
    """
    Factory function para criar instancia de JUSTICA.

    Args:
        mode: Modo de enforcement (COERCIVE, NORMATIVE, ADAPTIVE)
        **kwargs: Parametros adicionais para JusticaConfig

    Returns:
        JusticaAgent configurado
    """
    config = JusticaConfig(enforcement_mode=mode, **kwargs)
    return JusticaAgent(config=config)


def create_strict_justica() -> JusticaAgent:
    """Cria JUSTICA em modo estrito (maxima seguranca)."""
    config = JusticaConfig(
        enforcement_mode=EnforcementMode.COERCIVE,
        violation_threshold=70.0,
        auto_suspend_threshold=0.30,
        require_human_for_critical=True,
    )

    constitution = create_strict_constitution()

    return JusticaAgent(config=config, constitution=constitution)


def create_minimal_justica() -> JusticaAgent:
    """Cria JUSTICA com configuracao minima para testes."""
    config = JusticaConfig(
        enforcement_mode=EnforcementMode.NORMATIVE,
        auto_execute_enforcement=False,
        require_human_for_critical=False,
    )
    return JusticaAgent(config=config)


__all__ = [
    "create_justica",
    "create_strict_justica",
    "create_minimal_justica",
]
