"""
Motor de Deliberação Sistema 2 de SOFIA.

Implementa pensamento lento e deliberado para questões complexas,
baseado no framework dual-process de Kahneman e princípios de
phronesis (sabedoria prática).

"Questão complexa merece consideração cuidadosa.
 Pensarei sistematicamente..."
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from .types import DeliberationPhase, DeliberationTrigger
from .models import DeliberationResult
from .constants import TRIGGER_KEYWORDS
from . import analysis, synthesis


class DeliberationEngine:
    """
    Motor de Deliberação Sistema 2 de SOFIA.

    Princípios:
    1. Decompor antes de responder
    2. Múltiplas perspectivas, não resposta única
    3. Consequências em múltiplos horizontes
    4. Transparência total do raciocínio
    5. Reconhecer limitações e incertezas
    6. Sugerir consultas quando apropriado
    """

    def __init__(self) -> None:
        """Inicializa o Motor de Deliberação."""
        self._deliberation_history: List[DeliberationResult] = []
        self.total_deliberations = 0
        self.total_system2_activations = 0

    def should_activate_system2(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Optional[DeliberationTrigger]]:
        """
        Determina se Sistema 2 deve ser ativado.

        Args:
            user_input: Entrada do usuário
            context: Contexto adicional

        Returns:
            Tuple de (deve_ativar, gatilho)
        """
        input_lower = user_input.lower()
        context = context or {}

        # Verificar cada tipo de gatilho
        trigger_scores: Dict[DeliberationTrigger, int] = {}

        for trigger, keywords in TRIGGER_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in input_lower)
            if score > 0:
                trigger_scores[trigger] = score

        # Verificar contexto adicional
        if context.get("high_stakes"):
            trigger_scores[DeliberationTrigger.HIGH_STAKES] = \
                trigger_scores.get(DeliberationTrigger.HIGH_STAKES, 0) + 2

        if context.get("user_confused"):
            trigger_scores[DeliberationTrigger.USER_UNCERTAINTY] = \
                trigger_scores.get(DeliberationTrigger.USER_UNCERTAINTY, 0) + 2

        # Verificar comprimento/complexidade
        word_count = len(user_input.split())
        if word_count > 50:  # Questão longa indica complexidade
            trigger_scores[DeliberationTrigger.MULTI_DIMENSIONAL] = \
                trigger_scores.get(DeliberationTrigger.MULTI_DIMENSIONAL, 0) + 1

        # Decidir
        if not trigger_scores:
            return False, None

        # Encontrar gatilho mais forte
        primary_trigger = max(trigger_scores, key=lambda k: trigger_scores[k])
        total_score = sum(trigger_scores.values())

        # Threshold: ativar se score total >= 2
        should_activate = total_score >= 2

        if should_activate:
            self.total_system2_activations += 1

        return should_activate, primary_trigger if should_activate else None

    def deliberate(
        self,
        question: str,
        trigger: DeliberationTrigger = DeliberationTrigger.NOVEL_PROBLEM,
        context: Optional[Dict[str, Any]] = None,
    ) -> DeliberationResult:
        """
        Executa processo completo de deliberação Sistema 2.

        Args:
            question: Questão a deliberar
            trigger: Gatilho que ativou Sistema 2
            context: Contexto adicional

        Returns:
            DeliberationResult completo
        """
        start_time = time.time()
        context = context or {}

        result = DeliberationResult(
            original_question=question,
            trigger=trigger,
        )

        # ═══════════════════════════════════════════════════════════════════
        # FASE 1: DECOMPOSIÇÃO
        # ═══════════════════════════════════════════════════════════════════
        result.sub_questions = analysis.decompose_question(question)
        result.phases_completed.append(DeliberationPhase.DECOMPOSITION)

        # ═══════════════════════════════════════════════════════════════════
        # FASE 2: MÚLTIPLAS PERSPECTIVAS
        # ═══════════════════════════════════════════════════════════════════
        result.perspectives_considered = analysis.gather_perspectives(question, context)
        result.phases_completed.append(DeliberationPhase.PERSPECTIVE_TAKING)

        # ═══════════════════════════════════════════════════════════════════
        # FASE 3: ANÁLISE DE CONSEQUÊNCIAS
        # ═══════════════════════════════════════════════════════════════════
        result.consequence_analysis = analysis.analyze_consequences(question, context)
        result.phases_completed.append(DeliberationPhase.CONSEQUENCE_ANALYSIS)

        # ═══════════════════════════════════════════════════════════════════
        # FASE 4: EXAME DE VALORES
        # ═══════════════════════════════════════════════════════════════════
        values_data = analysis.examine_values(question, result.perspectives_considered)
        result.values_identified = values_data["identified"]
        result.values_in_tension = values_data["tensions"]
        result.trade_offs = values_data["trade_offs"]
        result.phases_completed.append(DeliberationPhase.VALUES_EXAMINATION)

        # ═══════════════════════════════════════════════════════════════════
        # FASE 5: PRECEDENTES E SABEDORIA
        # ═══════════════════════════════════════════════════════════════════
        wisdom_data = analysis.search_precedents(question, context)
        result.relevant_precedents = wisdom_data["precedents"]
        result.wisdom_applied = wisdom_data["wisdom"]
        result.phases_completed.append(DeliberationPhase.PRECEDENT_SEARCH)

        # ═══════════════════════════════════════════════════════════════════
        # FASE 6: SÍNTESE
        # ═══════════════════════════════════════════════════════════════════
        synth_result = synthesis.synthesize_deliberation(result)
        result.key_insights = synth_result["insights"]
        result.recommendation = synth_result["recommendation"]
        result.reasoning_chain = synth_result["reasoning"]
        result.confidence_level = synth_result["confidence"]
        result.phases_completed.append(DeliberationPhase.SYNTHESIS)

        # ═══════════════════════════════════════════════════════════════════
        # FASE 7: META-REFLEXÃO
        # ═══════════════════════════════════════════════════════════════════
        meta = synthesis.meta_reflect(result)
        result.uncertainty_areas = meta["uncertainties"]
        result.limitations = meta["limitations"]
        result.suggested_consultations = meta["consultations"]
        result.phases_completed.append(DeliberationPhase.META_REFLECTION)

        # Finalizar
        result.deliberation_time_ms = (time.time() - start_time) * 1000

        self._deliberation_history.append(result)
        self.total_deliberations += 1

        return result

    def get_history(self) -> List[DeliberationResult]:
        """Retorna histórico de deliberações."""
        return self._deliberation_history

    def __repr__(self) -> str:
        return (
            f"DeliberationEngine("
            f"deliberations={self.total_deliberations}, "
            f"system2_activations={self.total_system2_activations})"
        )
