"""
Modelos de dados para o Sistema de Deliberação.

Dataclasses que representam perspectivas, análises de consequências,
e resultados completos do processo de deliberação.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from .types import DeliberationPhase, DeliberationTrigger


@dataclass
class Perspective:
    """
    Uma perspectiva ética sobre a questão.

    Representa um ângulo de análise baseado em um framework
    ético ou stakeholder específico.
    """

    id: UUID = field(default_factory=uuid4)
    name: str = ""
    framework: str = ""  # Utilitarismo, Deontologia, Virtudes, Cuidado, etc.
    viewpoint: str = ""
    considerations: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    weight: float = 1.0  # Peso relativo desta perspectiva

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "framework": self.framework,
            "viewpoint": self.viewpoint[:100],
            "considerations": self.considerations[:3],
            "weight": self.weight,
        }


@dataclass
class ConsequenceAnalysis:
    """
    Análise de consequências de uma ação.

    Examina impactos em múltiplos horizontes temporais
    e para diferentes stakeholders.
    """

    id: UUID = field(default_factory=uuid4)
    action_considered: str = ""

    # Horizontes temporais
    short_term: List[str] = field(default_factory=list)  # Dias/semanas
    medium_term: List[str] = field(default_factory=list)  # Meses
    long_term: List[str] = field(default_factory=list)  # Anos

    # Impactos por stakeholder
    stakeholder_impacts: Dict[str, List[str]] = field(default_factory=dict)

    # Riscos e oportunidades
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    unintended_consequences: List[str] = field(default_factory=list)

    # Reversibilidade
    reversibility: str = "unknown"  # "easy", "difficult", "irreversible", "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "action": self.action_considered[:50],
            "short_term": self.short_term[:2],
            "long_term": self.long_term[:2],
            "risks": self.risks[:2],
            "reversibility": self.reversibility,
        }


@dataclass
class DeliberationResult:
    """
    Resultado completo do processo de deliberação Sistema 2.

    Contém todo o processo de raciocínio, não apenas a conclusão,
    mantendo transparência total sobre como se chegou à recomendação.
    """

    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Entrada
    original_question: str = ""
    trigger: DeliberationTrigger = DeliberationTrigger.NOVEL_PROBLEM

    # Processo
    phases_completed: List[DeliberationPhase] = field(default_factory=list)
    sub_questions: List[str] = field(default_factory=list)
    perspectives_considered: List[Perspective] = field(default_factory=list)
    consequence_analysis: Optional[ConsequenceAnalysis] = None

    # Valores e Trade-offs
    values_identified: List[str] = field(default_factory=list)
    values_in_tension: List[Tuple[str, str]] = field(default_factory=list)
    trade_offs: List[str] = field(default_factory=list)

    # Sabedoria e Precedentes
    relevant_precedents: List[str] = field(default_factory=list)
    wisdom_applied: List[str] = field(default_factory=list)

    # Síntese
    key_insights: List[str] = field(default_factory=list)
    recommendation: str = ""
    reasoning_chain: List[str] = field(default_factory=list)

    # Meta
    confidence_level: float = 0.5  # 0-1
    uncertainty_areas: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    suggested_consultations: List[str] = field(default_factory=list)

    # Tempo de processamento
    deliberation_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "trigger": self.trigger.name,
            "phases_completed": [p.name for p in self.phases_completed],
            "perspectives_count": len(self.perspectives_considered),
            "confidence_level": self.confidence_level,
            "key_insights": self.key_insights[:3],
        }
