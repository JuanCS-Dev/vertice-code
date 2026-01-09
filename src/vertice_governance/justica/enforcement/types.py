"""
Enforcement Types - Enums for the enforcement system.

EnforcementMode and ActionType enums.
"""

from __future__ import annotations

from enum import Enum, auto


class EnforcementMode(Enum):
    """
    Modos de enforcement disponiveis.

    Cada modo representa uma postura diferente de JUSTICA.
    """

    COERCIVE = auto()    # Bloqueio imediato, sem negociacao
    NORMATIVE = auto()   # Warning, documentacao, segunda chance
    ADAPTIVE = auto()    # Analise de padrao, escalacao gradual
    PASSIVE = auto()     # Apenas observacao e logging (modo debug)


class ActionType(Enum):
    """Tipos de acoes que o Enforcement Engine pode tomar."""

    # Acoes de bloqueio
    BLOCK_REQUEST = auto()       # Bloquear request especifico
    BLOCK_AGENT = auto()         # Bloquear agente completamente
    BLOCK_TOOL = auto()          # Bloquear tool especifica
    BLOCK_RESOURCE = auto()      # Bloquear acesso a recurso

    # Acoes de warning
    WARNING = auto()             # Emitir warning
    STRONG_WARNING = auto()      # Warning com consequencias

    # Acoes de logging
    LOG_INFO = auto()            # Log informativo
    LOG_WARNING = auto()         # Log de warning
    LOG_ERROR = auto()           # Log de erro
    LOG_CRITICAL = auto()        # Log critico

    # Acoes de escalacao
    ESCALATE_TO_HUMAN = auto()   # Escalar para revisao humana
    ESCALATE_TO_ADMIN = auto()   # Escalar para admin do sistema

    # Acoes de trust
    REDUCE_TRUST = auto()        # Reduzir trust factor
    SUSPEND_AGENT = auto()       # Suspender agente

    # Acoes de monitoramento
    INCREASE_MONITORING = auto() # Aumentar nivel de monitoramento
    FLAG_FOR_REVIEW = auto()     # Marcar para revisao posterior

    # Acoes permissivas
    ALLOW = auto()               # Permitir acao
    ALLOW_WITH_LOGGING = auto()  # Permitir mas com logging extra


__all__ = [
    "EnforcementMode",
    "ActionType",
]
