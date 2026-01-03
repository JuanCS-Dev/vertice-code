"""
Sofia Agent Counsel - Counsel dataclass.

SofiaCounsel represents a piece of advice from SOFIA.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from ..deliberation import DeliberationResult, ThinkingMode
    from ..discernment import DiscernmentResult
    from ..socratic import SocraticQuestion
    from ..virtues import VirtueExpression

from .types import CounselType


@dataclass
class SofiaCounsel:
    """
    Um conselho oferecido por SOFIA.

    Contem nao apenas o conselho em si, mas todo o processo
    de reflexao que levou a ele - transparencia total.

    Attributes:
        id: Identificador unico
        timestamp: Momento do conselho
        user_query: Pergunta do usuario
        session_id: ID da sessao
        counsel_type: Tipo de aconselhamento
        thinking_mode: Modo de pensamento usado
        virtues_expressed: Virtudes expressas
        questions_asked: Perguntas socraticas feitas
        deliberation: Resultado de deliberacao (se houve)
        discernment: Resultado de discernimento (se houve)
        response: Resposta final
        confidence: Nivel de confianca
        uncertainty_expressed: Se incerteza foi expressa
        community_suggested: Se comunidade foi sugerida
        processing_time_ms: Tempo de processamento
    """

    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Contexto
    user_query: str = ""
    session_id: Optional[str] = None
    counsel_type: CounselType = CounselType.EXPLORING

    # Processo
    thinking_mode: Optional["ThinkingMode"] = None
    virtues_expressed: List["VirtueExpression"] = field(default_factory=list)
    questions_asked: List["SocraticQuestion"] = field(default_factory=list)
    deliberation: Optional["DeliberationResult"] = None
    discernment: Optional["DiscernmentResult"] = None

    # Resposta
    response: str = ""
    confidence: float = 0.5
    uncertainty_expressed: bool = True
    community_suggested: bool = True

    # Meta
    processing_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionario."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "counsel_type": self.counsel_type.name,
            "thinking_mode": self.thinking_mode.name if self.thinking_mode else None,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "questions_count": len(self.questions_asked),
            "community_suggested": self.community_suggested,
        }


__all__ = ["SofiaCounsel"]
