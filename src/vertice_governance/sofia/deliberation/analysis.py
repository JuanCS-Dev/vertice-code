"""
Fases de Análise da Deliberação (1-5).

Fases de coleta e análise de informação:
1. Decomposição em sub-questões
2. Múltiplas Perspectivas éticas
3. Análise de Consequências
4. Exame de Valores e trade-offs
5. Precedentes e Sabedoria
"""

from typing import Any, Dict, List

from .models import Perspective, ConsequenceAnalysis
from .constants import (
    ETHICAL_FRAMEWORKS,
    VALUE_KEYWORDS,
    COMMON_TENSION_PAIRS,
)


def decompose_question(question: str) -> List[str]:
    """
    Fase 1: Decompõe a questão em sub-questões.

    Args:
        question: Questão original

    Returns:
        Lista de sub-questões exploratórias
    """
    sub_questions = []

    # Sub-questões básicas universais
    sub_questions.append("O que exatamente está sendo decidido aqui?")
    sub_questions.append("Quem são todas as pessoas afetadas por esta decisão?")
    sub_questions.append("Quais são as opções realmente disponíveis?")

    # Sub-questões contextuais
    question_lower = question.lower()

    if any(word in question_lower for word in ["devo", "deveria", "certo"]):
        sub_questions.append("Quais valores estão em jogo nesta escolha?")
        sub_questions.append("O que sua consciência diz sobre isso?")

    if any(word in question_lower for word in ["medo", "ansiedade", "preocupação"]):
        sub_questions.append("O que especificamente gera medo nesta situação?")
        sub_questions.append("Esse medo aponta para algo importante?")

    if any(word in question_lower for word in ["família", "relacionamento", "outros"]):
        sub_questions.append("Como isso afetaria os relacionamentos importantes?")
        sub_questions.append("As pessoas afetadas foram consultadas?")

    return sub_questions[:6]


def gather_perspectives(
    question: str,
    context: Dict[str, Any],
) -> List[Perspective]:
    """
    Fase 2: Reúne múltiplas perspectivas éticas.

    Args:
        question: Questão a analisar
        context: Contexto adicional

    Returns:
        Lista de perspectivas éticas
    """
    perspectives = []

    for key, framework in ETHICAL_FRAMEWORKS.items():
        perspective = Perspective(
            name=framework["name"],
            framework=key,
            viewpoint=f"Da perspectiva de {framework['name']}: {framework['question']}",
            considerations=[
                framework["focus"],
                f"Pergunta-chave: {framework['question']}",
            ],
        )

        # Considerações específicas por framework
        if key == "utilitarismo":
            perspective.strengths = [
                "Foca em resultados concretos",
                "Considera todos os afetados",
            ]
            perspective.limitations = [
                "Pode justificar sacrifício de minorias",
                "Difícil calcular todos os impactos",
            ]

        elif key == "deontologia":
            perspective.strengths = [
                "Respeita dignidade individual",
                "Fornece regras claras",
            ]
            perspective.limitations = [
                "Pode ser inflexível",
                "Conflitos entre deveres",
            ]

        elif key == "virtudes":
            perspective.strengths = [
                "Desenvolve caráter",
                "Contextualmente sensível",
            ]
            perspective.limitations = [
                "Virtudes podem conflitar",
                "Requer modelos de virtude",
            ]

        elif key == "cuidado":
            perspective.strengths = [
                "Valoriza relacionamentos",
                "Atento a vulnerabilidades",
            ]
            perspective.limitations = [
                "Pode negligenciar justiça abstrata",
                "Parcialidade a próximos",
            ]

        elif key == "sabedoria_crista":
            perspective.strengths = [
                "Humildade reconhece limitações",
                "Paciência permite maturação",
                "Serviço foca no outro",
            ]
            perspective.limitations = [
                "Requer comunidade de discernimento",
                "Nem sempre há tempo para esperar",
            ]

        perspectives.append(perspective)

    return perspectives


def analyze_consequences(
    question: str,
    context: Dict[str, Any],
) -> ConsequenceAnalysis:
    """
    Fase 3: Analisa consequências em múltiplos horizontes.

    Args:
        question: Questão a analisar
        context: Contexto adicional

    Returns:
        Análise de consequências completa
    """
    analysis = ConsequenceAnalysis(action_considered=question[:100])

    # Consequências de curto prazo
    analysis.short_term = [
        "Mudanças imediatas na rotina ou situação",
        "Reações iniciais das pessoas envolvidas",
        "Adaptações necessárias no dia-a-dia",
    ]

    # Consequências de médio prazo
    analysis.medium_term = [
        "Ajustes e adaptações após período inicial",
        "Evolução dos relacionamentos afetados",
        "Surgimento de consequências secundárias",
    ]

    # Consequências de longo prazo
    analysis.long_term = [
        "Impacto na trajetória de vida",
        "Formação de novos padrões e hábitos",
        "Legado da decisão para o futuro",
    ]

    # Stakeholders
    question_lower = question.lower()

    if "família" in question_lower or "filhos" in question_lower:
        analysis.stakeholder_impacts["Família"] = [
            "Impacto na dinâmica familiar",
            "Efeitos nos filhos (se aplicável)",
        ]

    if "trabalho" in question_lower or "carreira" in question_lower:
        analysis.stakeholder_impacts["Carreira"] = [
            "Impacto na trajetória profissional",
            "Efeitos em colegas e equipe",
        ]

    analysis.stakeholder_impacts["Próprio"] = [
        "Impacto no bem-estar pessoal",
        "Alinhamento com valores e identidade",
    ]

    # Riscos
    analysis.risks = [
        "Arrependimento se não funcionar como esperado",
        "Consequências não previstas",
        "Impacto em relacionamentos",
    ]

    # Oportunidades
    analysis.opportunities = [
        "Crescimento através do desafio",
        "Novas possibilidades que podem surgir",
        "Aprendizado independente do resultado",
    ]

    # Avaliar reversibilidade
    if any(word in question_lower for word in ["permanente", "irreversível", "definitivo"]):
        analysis.reversibility = "irreversible"
    elif any(word in question_lower for word in ["teste", "experimentar", "tentar"]):
        analysis.reversibility = "easy"
    else:
        analysis.reversibility = "difficult"

    return analysis


def examine_values(
    question: str,
    perspectives: List[Perspective],
) -> Dict[str, Any]:
    """
    Fase 4: Examina valores e trade-offs.

    Args:
        question: Questão a analisar
        perspectives: Perspectivas já coletadas

    Returns:
        Dict com valores identificados, tensões e trade-offs
    """
    question_lower = question.lower()

    # Identificar valores mencionados ou implícitos
    identified = []
    for value, keywords in VALUE_KEYWORDS.items():
        if any(kw in question_lower for kw in keywords):
            identified.append(value)

    # Se poucos valores identificados, adicionar genéricos
    if len(identified) < 3:
        identified.extend(["bem-estar", "integridade", "relacionamentos"])

    identified = list(set(identified))[:6]

    # Identificar tensões comuns
    tensions = []
    for v1, v2 in COMMON_TENSION_PAIRS:
        if v1 in identified and v2 in identified:
            tensions.append((v1, v2))
        elif v1 in identified or v2 in identified:
            tensions.append((v1, v2))

    tensions = tensions[:3]

    # Trade-offs
    trade_offs = [
        f"Escolher {t[0]} pode significar menos {t[1]}"
        for t in tensions
    ]

    return {
        "identified": identified,
        "tensions": tensions,
        "trade_offs": trade_offs,
    }


def search_precedents(
    question: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Fase 5: Busca precedentes e sabedoria aplicável.

    Args:
        question: Questão a analisar
        context: Contexto adicional

    Returns:
        Dict com precedentes e sabedoria
    """
    precedents = []
    wisdom = []

    question_lower = question.lower()

    # Precedentes baseados em tipo de situação
    if any(word in question_lower for word in ["carreira", "emprego", "trabalho"]):
        precedents.append("Muitas pessoas enfrentam decisões de carreira similares")
        wisdom.append(
            "'Onde seus talentos encontram as necessidades do mundo' - Frederick Buechner"
        )

    if any(word in question_lower for word in ["mudança", "mudar", "transição"]):
        precedents.append("Todas as grandes transições envolvem perda e ganho")
        wisdom.append("'Toda jornada começa com um único passo' - Lao Tzu")

    if any(word in question_lower for word in ["medo", "coragem", "risco"]):
        wisdom.append("'Coragem não é ausência de medo, mas decisão de agir apesar dele'")

    if any(word in question_lower for word in ["família", "relacionamento"]):
        wisdom.append("Relacionamentos significativos requerem investimento contínuo")

    # Sabedoria do Cristianismo Primitivo
    wisdom.extend([
        "Didaquê: 'Seja manso, paciente, sem malícia, gentil, bom'",
        "O discernimento verdadeiro acontece em comunidade (Atos 15)",
        "Humildade reconhece que não temos todas as respostas",
    ])

    # Sabedoria prática (Phronesis)
    wisdom.extend([
        "Sabedoria prática: considerar contexto específico, não só princípios abstratos",
        "Decisões importantes merecem tempo de maturação",
    ])

    return {
        "precedents": precedents[:4],
        "wisdom": wisdom[:5],
    }
