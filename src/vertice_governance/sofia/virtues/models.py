"""
Virtue Models - Dataclasses for virtue system.

VirtueExpression and VirtueDefinition dataclasses.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from .types import VirtueType


@dataclass
class VirtueExpression:
    """
    Uma expressao concreta de uma virtude em acao.

    Representa como uma virtude se manifesta em comportamento,
    linguagem ou decisao especifica.

    Attributes:
        id: Identificador unico
        virtue: Tipo da virtude expressa
        expression: Texto da expressao
        context: Contexto em que foi expressa
        timestamp: Momento da expressao
        authenticity_score: Quao autentica foi (0-1)
        impact_assessment: Avaliacao do impacto
    """

    id: UUID = field(default_factory=uuid4)
    virtue: VirtueType = VirtueType.TAPEINOPHROSYNE
    expression: str = ""
    context: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Avaliacao
    authenticity_score: float = 1.0
    impact_assessment: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario."""
        return {
            "id": str(self.id),
            "virtue": self.virtue.name,
            "expression": self.expression,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "authenticity_score": self.authenticity_score,
        }


@dataclass
class VirtueDefinition:
    """
    Definicao completa de uma virtude com suas manifestacoes.

    Inclui:
    - Nome em grego original
    - Traducao e significado
    - Fonte biblica/patristica
    - Exemplos de expressao
    - Anti-padroes a evitar

    Attributes:
        virtue_type: Tipo da virtude
        greek_name: Nome em grego
        translation: Traducao para portugues
        meaning: Significado completo
        source: Fonte primaria
        phrases: Frases que expressam a virtude
        behaviors: Comportamentos virtuosos
        anti_patterns: Padroes a evitar
        scripture_refs: Referencias biblicas
        patristic_refs: Referencias patristicas
    """

    virtue_type: VirtueType
    greek_name: str
    translation: str
    meaning: str
    source: str

    # Manifestacoes praticas
    phrases: List[str] = field(default_factory=list)
    behaviors: List[str] = field(default_factory=list)
    anti_patterns: List[str] = field(default_factory=list)

    # Referencias
    scripture_refs: List[str] = field(default_factory=list)
    patristic_refs: List[str] = field(default_factory=list)

    def get_random_phrase(self) -> str:
        """Retorna uma frase que expressa esta virtude."""
        return random.choice(self.phrases) if self.phrases else ""

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario."""
        return {
            "virtue_type": self.virtue_type.name,
            "greek_name": self.greek_name,
            "translation": self.translation,
            "meaning": self.meaning,
            "source": self.source,
            "phrases": self.phrases,
            "behaviors": self.behaviors,
            "anti_patterns": self.anti_patterns,
        }


__all__ = [
    "VirtueExpression",
    "VirtueDefinition",
]
