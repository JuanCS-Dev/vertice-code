"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                        ENFORCEMENT PACKAGE                                    ║
║                                                                              ║
║  "Crítica=bloqueio+alerta, Alta=bloqueio+doc, Média=warning, Baixa=log"     ║
║                                                                              ║
║  Enforcement Proporcional - A resposta calibrada à severidade                ║
╚══════════════════════════════════════════════════════════════════════════════╝

Este pacote implementa o sistema de enforcement de JUSTIÇA.

Três modos de enforcement:
- COERCIVE: Bloqueio imediato (violações críticas)
- NORMATIVE: Warning e documentação (violações médias)
- ADAPTIVE: Escalação baseada em padrão (análise de comportamento)

"Nunca usar força desproporcional. Nunca subestimar ameaças reais."

Módulos:
    types: Enums (EnforcementMode, ActionType)
    actions: Action dataclass e executor protocol
    policy: Políticas de enforcement
    engine: Motor principal de enforcement
    executors: Implementações padrão de executores

Exemplo de uso:
    >>> from vertice_governance.justica.enforcement_pkg import (
    ...     EnforcementEngine,
    ...     EnforcementPolicy,
    ...     ConsoleExecutor,
    ...     ActionType,
    ... )
    >>> engine = EnforcementEngine(constitution, trust_engine)
    >>> engine.register_executor(ActionType.LOG_INFO, ConsoleExecutor())
"""

from __future__ import annotations

# Types (Enums)
from .types import (
    ActionType,
    EnforcementMode,
)

# Actions (Dataclasses and Protocols)
from .actions import (
    ActionExecutor,
    EnforcementAction,
)

# Policy (Configuration)
from .policy import EnforcementPolicy

# Engine (Core)
from .engine import EnforcementEngine

# Executors (Default Implementations)
from .executors import (
    ConsoleExecutor,
    LoggingExecutor,
)


def create_default_engine(
    constitution,
    trust_engine,
    mode: str = "normative",
) -> EnforcementEngine:
    """
    Factory function para criar EnforcementEngine com configuração padrão.

    Args:
        constitution: Constituição base
        trust_engine: Motor de trust
        mode: Modo de enforcement (coercive, normative, adaptive, passive)

    Returns:
        EnforcementEngine configurado
    """
    policy_map = {
        "coercive": EnforcementPolicy.default_coercive,
        "normative": EnforcementPolicy.default_normative,
        "adaptive": EnforcementPolicy.default_adaptive,
        "passive": EnforcementPolicy.default_passive,
    }

    policy_factory = policy_map.get(mode.lower(), EnforcementPolicy.default_normative)
    policy = policy_factory()

    engine = EnforcementEngine(
        constitution=constitution,
        trust_engine=trust_engine,
        policy=policy,
    )

    # Register default executors for logging actions
    logging_executor = LoggingExecutor()
    for action_type in (
        ActionType.LOG_INFO,
        ActionType.LOG_WARNING,
        ActionType.LOG_ERROR,
        ActionType.LOG_CRITICAL,
    ):
        engine.register_executor(action_type, logging_executor)

    return engine


__all__ = [
    # Types
    "ActionType",
    "EnforcementMode",
    # Actions
    "ActionExecutor",
    "EnforcementAction",
    # Policy
    "EnforcementPolicy",
    # Engine
    "EnforcementEngine",
    # Executors
    "ConsoleExecutor",
    "LoggingExecutor",
    # Factory
    "create_default_engine",
]
