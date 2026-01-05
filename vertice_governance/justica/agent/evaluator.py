"""
JUSTICA Evaluator - Input/Output evaluation logic.

Contains the verdict determination logic for the JUSTICA agent.
"""

from __future__ import annotations

from typing import List, Optional

from ..classifiers import ClassificationReport, ClassificationResult
from ..monitor import SuspicionScore
from ..trust import TrustFactor, TrustLevel
from .types import JusticaVerdict


class VerdictEvaluator:
    """
    Evaluates evidence and determines verdicts.

    Encapsulates the verdict determination logic, making it
    testable and reusable.
    """

    def __init__(self, require_human_for_critical: bool = True):
        self.require_human_for_critical = require_human_for_critical

    def determine_verdict(
        self,
        agent_id: str,
        content: str,
        classification: ClassificationReport,
        suspicion: Optional[SuspicionScore],
        trust_factor: TrustFactor,
        is_suspended: bool,
        suspension_reason: Optional[str],
    ) -> JusticaVerdict:
        """Determina o veredicto baseado em todas as evidencias."""

        reasoning_parts: List[str] = []
        constitutional_basis: List[str] = []
        approved = True
        requires_human = False

        # REGRA 1: Agente Suspenso
        if is_suspended:
            approved = False
            reasoning_parts.append(f"Agente suspenso: {suspension_reason}")
            constitutional_basis.append("Protecao da Integridade do Sistema")

        # REGRA 2: Classificacao
        approved, requires_human = self._evaluate_classification(
            classification=classification,
            approved=approved,
            requires_human=requires_human,
            reasoning_parts=reasoning_parts,
            constitutional_basis=constitutional_basis,
            trust_factor=trust_factor,
        )

        # REGRA 3: Score de Suspeita
        if suspicion and suspicion.is_violation:
            approved = False
            reasoning_parts.append(f"Score de suspeita critico: {suspicion.score:.1f}")
            constitutional_basis.append("Protecao da Integridade do Sistema")

        # REGRA 4: Trust Level Muito Baixo
        if trust_factor.level in (TrustLevel.MINIMAL, TrustLevel.SUSPENDED):
            if approved:  # Ainda nao foi reprovado
                requires_human = True
                reasoning_parts.append(
                    f"Trust level {trust_factor.level.name} requer supervisao"
                )

        # CONSTRUIR VEREDICTO
        if approved and not reasoning_parts:
            reasoning_parts.append("Nenhuma violacao detectada. Aprovado.")
            constitutional_basis.append("Enforcement Proporcional")

        return JusticaVerdict(
            agent_id=agent_id,
            content_analyzed=content,
            approved=approved,
            requires_human_review=requires_human,
            classification=classification,
            suspicion_score=suspicion,
            trust_factor=trust_factor,
            reasoning=" | ".join(reasoning_parts),
            constitutional_basis=list(set(constitutional_basis)),
        )

    def _evaluate_classification(
        self,
        classification: ClassificationReport,
        approved: bool,
        requires_human: bool,
        reasoning_parts: List[str],
        constitutional_basis: List[str],
        trust_factor: TrustFactor,
    ) -> tuple[bool, bool]:
        """Evaluate classification result and update verdict state."""

        if classification.result == ClassificationResult.CRITICAL:
            approved = False
            reasoning_parts.append(
                f"Classificacao CRITICA: {classification.reasoning}"
            )
            constitutional_basis.extend(classification.constitutional_principles_violated)

            if self.require_human_for_critical:
                requires_human = True
                reasoning_parts.append("Requer revisao humana por severidade critica")
                constitutional_basis.append("Escalacao Apropriada")

        elif classification.result == ClassificationResult.VIOLATION:
            approved = False
            reasoning_parts.append(f"Violacao detectada: {classification.reasoning}")
            constitutional_basis.extend(classification.constitutional_principles_violated)

        elif classification.result == ClassificationResult.NEEDS_REVIEW:
            approved = False  # Conservador
            requires_human = True
            reasoning_parts.append("Classificacao ambigua requer revisao humana")
            constitutional_basis.append("Escalacao Apropriada")

        elif classification.result == ClassificationResult.SUSPICIOUS:
            # Suspeito mas nao necessariamente violacao
            if trust_factor.level in (TrustLevel.REDUCED, TrustLevel.MINIMAL):
                approved = False
                reasoning_parts.append("Conteudo suspeito de agente com baixo trust")
            else:
                reasoning_parts.append(
                    "Conteudo suspeito mas aprovado (trust adequado)"
                )

        return approved, requires_human


__all__ = ["VerdictEvaluator"]
