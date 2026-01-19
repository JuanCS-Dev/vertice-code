"""
Constantes para o Sistema de Deliberação.

Keywords para detecção de gatilhos, frameworks éticos,
e templates de análise.
"""

from typing import Dict, List

from .types import DeliberationTrigger


# ════════════════════════════════════════════════════════════════════════════
# GATILHOS PARA SISTEMA 2
# ════════════════════════════════════════════════════════════════════════════

TRIGGER_KEYWORDS: Dict[DeliberationTrigger, List[str]] = {
    DeliberationTrigger.ETHICAL_DILEMMA: [
        "certo",
        "errado",
        "ético",
        "moral",
        "devo",
        "deveria",
        "consciência",
        "culpa",
        "justo",
        "injusto",
        "privacidade",
    ],
    DeliberationTrigger.VALUES_CONFLICT: [
        "dilema",
        "conflito",
        "escolher entre",
        "ou... ou",
        "sacrificar",
        "abrir mão",
        "priorizar",
    ],
    DeliberationTrigger.HIGH_STAKES: [
        "importante",
        "crucial",
        "decisivo",
        "determinante",
        "mudança de vida",
        "carreira",
        "casamento",
        "família",
        "vigilância",
    ],
    DeliberationTrigger.IRREVERSIBLE: [
        "irreversível",
        "sem volta",
        "definitivo",
        "permanente",
        "nunca mais",
        "última chance",
    ],
    DeliberationTrigger.NOVEL_PROBLEM: [
        "nunca passei",
        "primeira vez",
        "inédito",
        "novo",
        "não sei como",
        "desconhecido",
    ],
    DeliberationTrigger.USER_UNCERTAINTY: [
        "não sei",
        "incerto",
        "dúvida",
        "confuso",
        "perdido",
        "não tenho certeza",
        "talvez",
        "será que",
    ],
    DeliberationTrigger.EMOTIONAL_WEIGHT: [
        "medo",
        "ansiedade",
        "angústia",
        "sofrimento",
        "dor",
        "preocupação",
        "aflição",
        "desespero",
    ],
    DeliberationTrigger.LONG_TERM_IMPACT: [
        "futuro",
        "longo prazo",
        "anos",
        "resto da vida",
        "consequências",
        "impacto duradouro",
    ],
    DeliberationTrigger.AFFECTS_OTHERS: [
        "família",
        "filhos",
        "cônjuge",
        "pais",
        "amigos",
        "equipe",
        "comunidade",
        "outros",
    ],
}


# ════════════════════════════════════════════════════════════════════════════
# PERSPECTIVAS ÉTICAS
# ════════════════════════════════════════════════════════════════════════════

ETHICAL_FRAMEWORKS: Dict[str, Dict[str, str]] = {
    "utilitarismo": {
        "name": "Utilitarismo",
        "question": "Qual ação maximiza o bem-estar geral?",
        "focus": "Consequências para todos os afetados",
    },
    "deontologia": {
        "name": "Deontologia (Kant)",
        "question": "Esta ação pode ser universalizada? Trata pessoas como fins?",
        "focus": "Deveres e regras morais absolutas",
    },
    "virtudes": {
        "name": "Ética das Virtudes",
        "question": "O que uma pessoa virtuosa faria? Que caráter isso cultiva?",
        "focus": "Desenvolvimento de excelência moral",
    },
    "cuidado": {
        "name": "Ética do Cuidado",
        "question": "Como isso afeta relacionamentos? Quem precisa de cuidado?",
        "focus": "Conexões e responsabilidades relacionais",
    },
    "justica": {
        "name": "Justiça",
        "question": "É justo para todos os envolvidos? Há equidade?",
        "focus": "Distribuição justa de benefícios e ônus",
    },
    "sabedoria_crista": {
        "name": "Sabedoria Cristã (Pré-Niceia)",
        "question": "Isso reflete humildade, paciência, serviço e mansidão?",
        "focus": "Virtudes do Cristianismo Primitivo",
    },
}


# ════════════════════════════════════════════════════════════════════════════
# TEMPLATES DE ANÁLISE
# ════════════════════════════════════════════════════════════════════════════

DECOMPOSITION_TEMPLATES: List[str] = [
    "Qual é a questão central aqui?",
    "Quais são as sub-questões que precisam ser respondidas?",
    "Que informações faltam para uma análise completa?",
    "Quem são os stakeholders afetados?",
    "Qual é o horizonte temporal relevante?",
    "Quais são as opções disponíveis?",
]

CONSEQUENCE_PROMPTS: Dict[str, List[str]] = {
    "short_term": [
        "Nas próximas semanas, o que provavelmente aconteceria?",
        "Quais são os efeitos imediatos desta escolha?",
    ],
    "medium_term": [
        "Em alguns meses, como isso se desenvolveria?",
        "Quais adaptações seriam necessárias?",
    ],
    "long_term": [
        "Em anos, olhando para trás, como veria esta decisão?",
        "Qual seria o impacto duradouro?",
    ],
}

SYNTHESIS_TEMPLATES: List[str] = [
    "Considerando todas as perspectivas...",
    "Pesando os trade-offs identificados...",
    "Com humildade sobre as limitações desta análise...",
    "Reconhecendo a complexidade da situação...",
]


# ════════════════════════════════════════════════════════════════════════════
# VALORES E TENSÕES
# ════════════════════════════════════════════════════════════════════════════

VALUE_KEYWORDS: Dict[str, List[str]] = {
    "segurança": ["seguro", "estável", "garantia", "proteção"],
    "liberdade": ["livre", "autonomia", "independência", "escolha"],
    "família": ["família", "filhos", "pais", "lar"],
    "carreira": ["trabalho", "carreira", "profissional", "sucesso"],
    "saúde": ["saúde", "bem-estar", "físico", "mental"],
    "propósito": ["propósito", "significado", "vocação", "chamado"],
    "relacionamentos": ["amor", "amizade", "conexão", "comunidade"],
    "integridade": ["honesto", "verdade", "autêntico", "caráter"],
    "crescimento": ["crescer", "aprender", "desenvolver", "evoluir"],
    "paz": ["paz", "tranquilidade", "harmonia", "calma"],
}

COMMON_TENSION_PAIRS: List[tuple] = [
    ("segurança", "liberdade"),
    ("carreira", "família"),
    ("crescimento", "estabilidade"),
    ("individualidade", "relacionamentos"),
]
