"""
Discernment Engine - Core logic.

Motor de Discernimento de SOFIA.
Baseado em Atos 15 e Didaque.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .types import DiscernmentPhase, WayType
from .models import DiscernmentQuestion, DiscernmentResult, TraditionWisdom
from .constants import (
    DISCERNMENT_QUESTIONS,
    WAY_OF_LIFE_INDICATORS,
    WAY_OF_DEATH_INDICATORS,
    TRADITION_BANK,
)


class DiscernmentEngine:
    """
    Motor de Discernimento de SOFIA.

    Implementa o processo de discernimento baseado nas praticas
    da Igreja Primitiva, especialmente o Concilio de Jerusalem (Atos 15)
    e o Framework Duas Vias da Didaque.

    "Pareceu bem ao Espirito Santo e a nos..." (Atos 15:28)

    Principios:
    1. Discernimento e comunal, nao apenas individual
    2. Experiencia e tradicao se complementam
    3. Busca-se paz interior, nao apenas logica
    4. Humildade de reconhecer incerteza
    5. Abertura para revisar discernimento
    """

    def __init__(self):
        self._discernment_history: List[DiscernmentResult] = []
        self._tradition_bank: List[TraditionWisdom] = list(TRADITION_BANK)
        self.total_discernments = 0

    def begin_discernment(self, situation: str) -> DiscernmentResult:
        """Inicia processo de discernimento."""
        return DiscernmentResult(situation=situation)

    def get_questions_for_phase(self, phase: DiscernmentPhase) -> List[DiscernmentQuestion]:
        """Retorna perguntas para uma fase especifica."""
        return DISCERNMENT_QUESTIONS.get(phase, [])

    def analyze_two_ways(
        self,
        situation: str,
        proposed_action: str,
    ) -> Tuple[List[str], List[str], WayType]:
        """
        Analisa uma acao proposta atraves do Framework Duas Vias.

        Returns:
            Tuple de (indicadores de vida, indicadores de morte, caminho discernido)
        """
        situation_lower = (situation + " " + proposed_action).lower()

        life_indicators = []
        death_indicators = []

        positive_keywords = ["ajudar", "amar", "cuidar", "verdade", "paz", "perdoar", "servir"]
        negative_keywords = ["mentir", "esconder", "prejudicar", "vinganca", "explorar", "manipular"]

        for indicator in WAY_OF_LIFE_INDICATORS:
            if any(kw in situation_lower for kw in positive_keywords):
                life_indicators.append(indicator)

        for indicator in WAY_OF_DEATH_INDICATORS:
            if any(kw in situation_lower for kw in negative_keywords):
                death_indicators.append(indicator)

        # Determinar caminho
        if len(life_indicators) > len(death_indicators) + 2:
            way = WayType.WAY_OF_LIFE
        elif len(death_indicators) > len(life_indicators) + 2:
            way = WayType.WAY_OF_DEATH
        else:
            way = WayType.UNCLEAR

        return life_indicators, death_indicators, way

    def get_relevant_tradition(self, situation: str) -> List[TraditionWisdom]:
        """Retorna sabedoria da tradicao relevante para a situacao."""
        return self._tradition_bank

    def conduct_full_discernment(
        self,
        situation: str,
        proposed_action: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> DiscernmentResult:
        """
        Conduz processo completo de discernimento.

        Args:
            situation: Descricao da situacao
            proposed_action: Acao proposta (se houver)
            context: Contexto adicional

        Returns:
            DiscernmentResult completo
        """
        result = self.begin_discernment(situation)

        # FASE 1: GATHERING
        result.questions_explored.extend(self.get_questions_for_phase(DiscernmentPhase.GATHERING))
        result.phases_completed.append(DiscernmentPhase.GATHERING)

        # FASE 2: DELIBERATION
        result.questions_explored.extend(self.get_questions_for_phase(DiscernmentPhase.DELIBERATION))
        result.phases_completed.append(DiscernmentPhase.DELIBERATION)

        # FASE 3: EXPERIENCE
        result.questions_explored.extend(self.get_questions_for_phase(DiscernmentPhase.EXPERIENCE))
        result.phases_completed.append(DiscernmentPhase.EXPERIENCE)

        # FASE 4: TRADITION
        result.traditions_consulted = self.get_relevant_tradition(situation)
        result.questions_explored.extend(self.get_questions_for_phase(DiscernmentPhase.TRADITION))
        result.phases_completed.append(DiscernmentPhase.TRADITION)

        # FASE 5: ELDER_WISDOM
        result.questions_explored.extend(self.get_questions_for_phase(DiscernmentPhase.ELDER_WISDOM))
        result.suggested_advisors = [
            "Um mentor espiritual de confianca",
            "Uma pessoa mais experiente na area",
            "A comunidade de fe",
            "Um conselheiro profissional (se apropriado)",
        ]
        result.phases_completed.append(DiscernmentPhase.ELDER_WISDOM)

        # FASE 6: SYNTHESIS
        if proposed_action:
            life_ind, death_ind, way = self.analyze_two_ways(situation, proposed_action)
            result.way_of_life_indicators = life_ind
            result.way_of_death_indicators = death_ind
            result.discerned_direction = way

        result.questions_explored.extend(self.get_questions_for_phase(DiscernmentPhase.SYNTHESIS))
        result.phases_completed.append(DiscernmentPhase.SYNTHESIS)

        # GERAR COUNSEL FINAL
        result.counsel = self._generate_counsel(result)
        result.need_for_community = True
        result.confidence = 0.6 if result.discerned_direction != WayType.UNCLEAR else 0.4

        self._discernment_history.append(result)
        self.total_discernments += 1

        return result

    def _generate_counsel(self, result: DiscernmentResult) -> str:
        """Gera conselho baseado no discernimento."""
        counsel_parts = [
            "Apos caminhar junto contigo neste discernimento, "
            "compartilho algumas reflexoes com humildade:"
        ]

        if result.discerned_direction == WayType.WAY_OF_LIFE:
            counsel_parts.append(
                "\nOs indicadores parecem apontar para um caminho que pode dar vida. "
                "Mas nao confie apenas nesta analise - busque confirmacao em paz interior "
                "e no conselho de pessoas sabias que te conhecem."
            )
        elif result.discerned_direction == WayType.WAY_OF_DEATH:
            counsel_parts.append(
                "\nIdentifiquei alguns sinais de alerta que merecem atencao. "
                "Isso nao e julgamento, mas convite a refletir mais profundamente. "
                "Considere conversar com alguem de sua confianca."
            )
        else:
            counsel_parts.append(
                "\nEsta situacao tem complexidade que excede minha capacidade de discernir. "
                "Isso nao e fraqueza - e sabedoria reconhecer limites. "
                "Encorajo fortemente buscar conselho de uma comunidade de fe "
                "ou mentor espiritual."
            )

        counsel_parts.append(
            f"\n\nConsidere consultar: {', '.join(result.suggested_advisors[:2])}"
        )

        counsel_parts.append(
            "\n\n'Pareceu bem ao Espirito Santo e a nos...' (Atos 15:28) - "
            "O discernimento verdadeiro e comunal. Nao carregue isso sozinho(a)."
        )

        return "".join(counsel_parts)

    def format_discernment_output(self, result: DiscernmentResult) -> str:
        """Formata resultado do discernimento para apresentacao."""
        output = [
            "=" * 60,
            "  DISCERNIMENTO COMUNAL",
            "  Baseado em Atos 15 e Didaque",
            "=" * 60,
            "",
            f"Situacao: {result.situation[:80]}...",
            "",
            "Fases Completadas:",
        ]

        for phase in result.phases_completed:
            output.append(f"  [x] {phase.name}")

        if result.way_of_life_indicators:
            output.append("\nIndicadores do Caminho da Vida:")
            for ind in result.way_of_life_indicators[:3]:
                output.append(f"  - {ind}")

        if result.way_of_death_indicators:
            output.append("\nIndicadores de Alerta:")
            for ind in result.way_of_death_indicators[:3]:
                output.append(f"  - {ind}")

        output.extend([
            "",
            "-" * 60,
            "CONSELHO:",
            result.counsel,
            "-" * 60,
        ])

        return "\n".join(output)

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas do motor de discernimento."""
        return {
            "total_discernments": self.total_discernments,
            "traditions_available": len(self._tradition_bank),
        }

    def __repr__(self) -> str:
        return f"DiscernmentEngine(discernments={self.total_discernments})"


__all__ = ["DiscernmentEngine"]
