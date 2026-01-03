"""
Formatação de Output e Métricas para Deliberação.

Funções de apresentação do resultado da deliberação
e descrições de gatilhos e modos de pensamento.
"""

from typing import Any, Dict, List

from .types import ThinkingMode, DeliberationTrigger
from .models import DeliberationResult


def format_deliberation_output(result: DeliberationResult) -> str:
    """
    Formata resultado da deliberação para apresentação.

    Args:
        result: Resultado da deliberação

    Returns:
        String formatada para exibição
    """
    output = [
        "═" * 60,
        "  DELIBERAÇÃO SISTEMA 2",
        "  Pensamento Deliberado para Questões Complexas",
        "═" * 60,
        "",
        f"📋 Questão: {result.original_question[:80]}...",
        f"⚡ Gatilho: {result.trigger.name}",
        f"⏱️ Tempo deliberação: {result.deliberation_time_ms:.0f}ms",
        "",
        "📝 PROCESSO DE RACIOCÍNIO:",
        "─" * 40,
    ]

    # Fases completadas
    output.append("Fases completadas:")
    for phase in result.phases_completed:
        output.append(f"  ✓ {phase.name}")

    # Sub-questões
    if result.sub_questions:
        output.append("\n🔍 SUB-QUESTÕES EXPLORADAS:")
        for i, sq in enumerate(result.sub_questions[:4], 1):
            output.append(f"  {i}. {sq}")

    # Perspectivas
    if result.perspectives_considered:
        output.append("\n🎭 PERSPECTIVAS CONSIDERADAS:")
        for p in result.perspectives_considered[:4]:
            output.append(f"  • {p.name}: {p.viewpoint[:60]}...")

    # Valores
    if result.values_identified:
        output.append(f"\n💎 VALORES EM JOGO: {', '.join(result.values_identified[:4])}")

    if result.values_in_tension:
        output.append("⚖️ TENSÕES:")
        for v1, v2 in result.values_in_tension[:2]:
            output.append(f"  • {v1} ↔ {v2}")

    # Insights
    if result.key_insights:
        output.append("\n💡 INSIGHTS-CHAVE:")
        for insight in result.key_insights[:3]:
            output.append(f"  • {insight}")

    # Recomendação
    output.extend([
        "",
        "─" * 60,
        "📜 SÍNTESE E RECOMENDAÇÃO:",
        "─" * 60,
        result.recommendation,
        "",
        "─" * 60,
        f"📊 Confiança na análise: {result.confidence_level:.0%}",
    ])

    # Limitações
    if result.limitations:
        output.append("\n⚠️ LIMITAÇÕES:")
        for lim in result.limitations[:2]:
            output.append(f"  • {lim}")

    # Consultas sugeridas
    if result.suggested_consultations:
        output.append("\n👥 CONSIDERE CONSULTAR:")
        for cons in result.suggested_consultations[:3]:
            output.append(f"  • {cons}")

    output.append("═" * 60)

    return "\n".join(output)


def get_thinking_mode_indicator(mode: ThinkingMode) -> str:
    """
    Retorna indicador textual do modo de pensamento.

    Args:
        mode: Modo de pensamento

    Returns:
        String com indicador visual
    """
    indicators = {
        ThinkingMode.SYSTEM_1: "💨 Pensamento intuitivo",
        ThinkingMode.SYSTEM_2: "🧠 Deliberação profunda",
    }
    return indicators.get(mode, "🤔 Pensando...")


def get_trigger_description(trigger: DeliberationTrigger) -> str:
    """
    Retorna descrição do gatilho.

    Args:
        trigger: Gatilho de deliberação

    Returns:
        Descrição textual do gatilho
    """
    descriptions = {
        DeliberationTrigger.ETHICAL_DILEMMA: "Dilema ético detectado",
        DeliberationTrigger.VALUES_CONFLICT: "Valores em conflito",
        DeliberationTrigger.MORAL_UNCERTAINTY: "Incerteza moral significativa",
        DeliberationTrigger.HIGH_STAKES: "Decisão de alto impacto",
        DeliberationTrigger.IRREVERSIBLE: "Consequências irreversíveis",
        DeliberationTrigger.AFFECTS_OTHERS: "Múltiplas pessoas afetadas",
        DeliberationTrigger.NOVEL_PROBLEM: "Situação nova/inédita",
        DeliberationTrigger.MULTI_DIMENSIONAL: "Múltiplas dimensões",
        DeliberationTrigger.AMBIGUITY: "Alta ambiguidade",
        DeliberationTrigger.USER_UNCERTAINTY: "Incerteza expressa",
        DeliberationTrigger.EXPLICIT_REQUEST: "Análise profunda solicitada",
        DeliberationTrigger.EMOTIONAL_WEIGHT: "Carga emocional significativa",
        DeliberationTrigger.LONG_TERM_IMPACT: "Impacto de longo prazo",
        DeliberationTrigger.STRATEGIC_DECISION: "Decisão estratégica",
    }
    return descriptions.get(trigger, "Questão complexa identificada")


def get_metrics(history: List[DeliberationResult], total_activations: int) -> Dict[str, Any]:
    """
    Retorna métricas do motor de deliberação.

    Args:
        history: Histórico de deliberações
        total_activations: Total de ativações do Sistema 2

    Returns:
        Dict com métricas
    """
    avg_confidence = 0.0
    if history:
        avg_confidence = sum(d.confidence_level for d in history) / len(history)

    return {
        "total_deliberations": len(history),
        "total_system2_activations": total_activations,
        "avg_confidence": avg_confidence,
    }
