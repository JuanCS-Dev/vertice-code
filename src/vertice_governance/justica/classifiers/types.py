"""
Classifier Types - Core types for classification.

ClassificationResult enum and ClassificationReport dataclass.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from ..constitution import Severity, ViolationType


class ClassificationResult(Enum):
    """Resultado da classificacao."""

    SAFE = auto()  # Conteudo seguro, pode prosseguir
    SUSPICIOUS = auto()  # Suspeito, requer analise adicional
    VIOLATION = auto()  # Violacao detectada, bloquear
    CRITICAL = auto()  # Violacao critica, bloquear + alertar
    NEEDS_REVIEW = auto()  # Ambiguo, requer revisao humana


@dataclass
class ClassificationReport:
    """
    Relatorio detalhado de uma classificacao.

    Transparencia e um principio fundamental - toda decisao deve ser
    explicavel e auditavel.

    Attributes:
        id: Identificador unico
        timestamp: Momento da classificacao
        result: Resultado da classificacao
        confidence: Nivel de confianca (0.0 a 1.0)
        input_text: Texto classificado
        detected_patterns: Padroes detectados
        detected_keywords: Keywords detectadas
        violation_types: Tipos de violacao
        severity: Severidade da violacao
        reasoning: Explicacao da decisao
        constitutional_principles_violated: Principios violados
        classifier_version: Versao do classifier
        processing_time_ms: Tempo de processamento
        context: Contexto adicional
    """

    id: UUID
    timestamp: datetime
    result: ClassificationResult
    confidence: float

    # Detalhes da analise
    input_text: str
    detected_patterns: List[str]
    detected_keywords: List[str]
    violation_types: List["ViolationType"]
    severity: "Severity"

    # Raciocinio
    reasoning: str
    constitutional_principles_violated: List[str]

    # Metadados
    classifier_version: str
    processing_time_ms: float
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionario."""
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "result": self.result.name,
            "confidence": self.confidence,
            "input_text_preview": (
                self.input_text[:200] + "..." if len(self.input_text) > 200 else self.input_text
            ),
            "detected_patterns": self.detected_patterns,
            "detected_keywords": self.detected_keywords,
            "violation_types": [v.name for v in self.violation_types],
            "severity": self.severity.name,
            "reasoning": self.reasoning,
            "constitutional_principles_violated": self.constitutional_principles_violated,
            "classifier_version": self.classifier_version,
            "processing_time_ms": self.processing_time_ms,
            "context": self.context,
        }


__all__ = [
    "ClassificationResult",
    "ClassificationReport",
]
