"""
Fases de Síntese da Deliberação (6-7).

Fases de síntese e meta-reflexão:
6. Sintetizar recomendação ponderada
7. Meta-reflexão sobre limitações
"""

from typing import Any, Dict
import random

from .types import DeliberationTrigger
from .models import DeliberationResult
from .constants import SYNTHESIS_TEMPLATES


def synthesize_deliberation(result: DeliberationResult) -> Dict[str, Any]:
    """
    Fase 6: Sintetiza toda a deliberação em insights e recomendação.

    Args:
        result: Resultado parcial da deliberação

    Returns:
        Dict com insights, recomendação, raciocínio e confiança
    """
    insights = []

    # Insight das perspectivas
    if result.perspectives_considered:
        perspectives_summary = ", ".join(
            p.name for p in result.perspectives_considered[:3]
        )
        insights.append(
            f"Múltiplas perspectivas éticas iluminam diferentes aspectos: {perspectives_summary}"
        )

    # Insight das consequências
    if result.consequence_analysis:
        if result.consequence_analysis.reversibility == "irreversible":
            insights.append(
                "Esta é uma decisão com consequências irreversíveis - merece cautela extra"
            )
        elif result.consequence_analysis.reversibility == "easy":
            insights.append(
                "Esta decisão é relativamente reversível - há espaço para experimentar"
            )

    # Insight dos valores
    if result.values_in_tension:
        tension_str = " vs ".join(result.values_in_tension[0])
        insights.append(f"Tensão central identificada: {tension_str}")

    # Insight da sabedoria
    if result.wisdom_applied:
        insights.append(
            "Sabedoria tradicional oferece orientação, mas requer discernimento contextual"
        )

    # Construir cadeia de raciocínio
    reasoning = [
        f"1. A questão foi decomposta em {len(result.sub_questions)} sub-questões",
        f"2. {len(result.perspectives_considered)} perspectivas éticas foram consideradas",
        "3. Consequências em curto, médio e longo prazo foram analisadas",
        f"4. Valores identificados: {', '.join(result.values_identified[:3])}",
        f"5. Trade-offs principais: {result.trade_offs[0] if result.trade_offs else 'nenhum crítico'}",
    ]

    # Recomendação
    recommendation = generate_recommendation(result)

    # Calcular confiança
    confidence = calculate_confidence(result)

    return {
        "insights": insights[:5],
        "recommendation": recommendation,
        "reasoning": reasoning,
        "confidence": confidence,
    }


def generate_recommendation(result: DeliberationResult) -> str:
    """
    Gera recomendação baseada na deliberação.

    Args:
        result: Resultado da deliberação

    Returns:
        String com recomendação formatada
    """
    opener = random.choice(SYNTHESIS_TEMPLATES)

    parts = [opener]

    # Adicionar insight principal
    if result.values_in_tension:
        v1, v2 = result.values_in_tension[0]
        parts.append(
            f"\nEsta decisão envolve equilibrar {v1} e {v2}. "
            "Não há resposta 'certa' universal - depende de seus valores prioritários "
            "neste momento de vida."
        )
    else:
        parts.append(
            "\nEsta é uma decisão multifacetada que merece consideração cuidadosa "
            "de múltiplos ângulos."
        )

    # Adicionar consideração de consequências
    if result.consequence_analysis:
        if result.consequence_analysis.reversibility == "irreversible":
            parts.append(
                "\n\nDada a natureza irreversível desta decisão, recomendo fortemente "
                "conversar com pessoas de sua confiança antes de decidir."
            )
        else:
            parts.append(
                "\n\nHá espaço para ajustes após a decisão inicial, o que permite "
                "aprender com a experiência."
            )

    # Sugestão de próximos passos
    parts.append(
        "\n\nPróximos passos sugeridos:\n"
        "• Reflita sobre qual valor é mais importante para você agora\n"
        "• Converse com alguém de confiança sobre esta situação\n"
        "• Dê tempo para a decisão amadurecer se possível"
    )

    return "".join(parts)


def calculate_confidence(result: DeliberationResult) -> float:
    """
    Calcula nível de confiança na análise.

    Args:
        result: Resultado da deliberação

    Returns:
        Float entre 0.3 e 0.8 representando confiança
    """
    confidence = 0.5  # Base

    # Aumentar por completude
    if len(result.phases_completed) >= 6:
        confidence += 0.1

    # Aumentar por múltiplas perspectivas
    if len(result.perspectives_considered) >= 4:
        confidence += 0.1

    # Diminuir por complexidade
    if len(result.values_in_tension) > 2:
        confidence -= 0.1

    # Diminuir se irreversível (mais cautela)
    if result.consequence_analysis and \
       result.consequence_analysis.reversibility == "irreversible":
        confidence -= 0.1

    # Limitar (nunca muito confiante)
    return max(0.3, min(0.8, confidence))


def meta_reflect(result: DeliberationResult) -> Dict[str, Any]:
    """
    Fase 7: Reflexão sobre limitações e incertezas.

    Args:
        result: Resultado da deliberação

    Returns:
        Dict com incertezas, limitações e consultas sugeridas
    """
    uncertainties = [
        "Não conheço todos os detalhes da sua situação específica",
        "Não posso prever como as pessoas envolvidas reagirão",
        "O contexto completo pode revelar fatores não considerados",
    ]

    limitations = [
        "Esta análise é baseada apenas no que foi compartilhado",
        "Não substitui conselho de profissionais ou pessoas que conhecem você",
        "A decisão final é sua - você conhece sua situação melhor",
    ]

    consultations = [
        "Uma pessoa de confiança que conhece bem você",
        "Alguém com experiência em situação similar",
    ]

    # Adicionar consultas específicas baseadas no contexto
    if result.trigger == DeliberationTrigger.EMOTIONAL_WEIGHT:
        consultations.append("Um profissional de saúde mental, se a angústia persistir")

    if result.trigger in [DeliberationTrigger.ETHICAL_DILEMMA,
                          DeliberationTrigger.VALUES_CONFLICT]:
        consultations.append("Um mentor espiritual ou conselheiro")

    return {
        "uncertainties": uncertainties,
        "limitations": limitations,
        "consultations": consultations[:4],
    }
