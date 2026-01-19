"""
Sofia Agent Config - Configuration dataclass.

SofiaConfig for agent configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from ..virtues import VirtueType


@dataclass
class SofiaConfig:
    """Configuracao do Agente SOFIA."""

    agent_id: str = "sofia-primary"
    name: str = "SOFIA"
    version: str = "3.0.0"

    # Comportamento
    default_virtue: VirtueType = VirtueType.TAPEINOPHROSYNE  # Humildade
    system2_threshold: float = 0.6  # Quando ativar Sistema 2
    socratic_ratio: float = 0.7  # % de perguntas vs respostas

    # Limites
    max_questions_per_topic: int = 5
    always_suggest_community: bool = True
    defer_to_professionals: bool = True

    # Aprendizado
    learn_from_feedback: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "default_virtue": self.default_virtue.name,
            "system2_threshold": self.system2_threshold,
            "socratic_ratio": self.socratic_ratio,
        }


__all__ = ["SofiaConfig"]
