"""
Discernment Constants - Questions and indicators.
"""

from __future__ import annotations
from typing import Dict, List

from .types import DiscernmentPhase
from .models import DiscernmentQuestion, TraditionWisdom


# Perguntas de discernimento por fase
DISCERNMENT_QUESTIONS: Dict[DiscernmentPhase, List[DiscernmentQuestion]] = {
    DiscernmentPhase.GATHERING: [
        DiscernmentQuestion(
            "Situacao",
            "O que exatamente esta em jogo nesta decisao?",
            "Clarificar a natureza real da escolha",
            "Sabedoria pratica",
        ),
        DiscernmentQuestion(
            "Stakeholders",
            "Quem sera afetado por esta decisao?",
            "Expandir visao alem do individual",
            "Etica do cuidado",
        ),
        DiscernmentQuestion(
            "Valores",
            "Quais valores estao em tensao aqui?",
            "Identificar o conflito subjacente",
            "Etica das virtudes",
        ),
    ],
    DiscernmentPhase.DELIBERATION: [
        DiscernmentQuestion(
            "Argumentos",
            "Quais sao os melhores argumentos para cada lado?",
            "Garantir consideracao justa de alternativas",
            "Metodo socratico",
        ),
        DiscernmentQuestion(
            "Oposicao",
            "O que diria alguem que discorda?",
            "Testar robustez do raciocinio",
            "Advocatus diaboli",
        ),
    ],
    DiscernmentPhase.EXPERIENCE: [
        DiscernmentQuestion(
            "Pessoal",
            "Voce ja enfrentou algo similar? O que aprendeu?",
            "Acessar sabedoria experiencial",
            "Atos 15:12",
        ),
        DiscernmentQuestion(
            "Outros",
            "Conhece alguem que passou por isso? O que aconteceu?",
            "Aprender com experiencia alheia",
            "Comunidade",
        ),
    ],
    DiscernmentPhase.TRADITION: [
        DiscernmentQuestion(
            "Escrituras",
            "Ha principios nas Escrituras que iluminam isso?",
            "Consultar revelacao estabelecida",
            "Atos 15:15-17",
        ),
        DiscernmentQuestion(
            "Tradicao",
            "O que a sabedoria da Igreja/tradicao ensina?",
            "Acessar sabedoria acumulada",
            "Didaque",
        ),
    ],
    DiscernmentPhase.ELDER_WISDOM: [
        DiscernmentQuestion(
            "Conselho",
            "Quem voce respeita que poderia aconselhar?",
            "Buscar sabedoria dos mais experientes",
            "Atos 15:13-19",
        ),
        DiscernmentQuestion(
            "Comunidade",
            "Ha uma comunidade de fe que poderia discernir junto?",
            "Reconhecer limite do discernimento solitario",
            "Atos 15:6",
        ),
    ],
    DiscernmentPhase.SYNTHESIS: [
        DiscernmentQuestion(
            "Consolacao",
            "Qual caminho traz mais paz interior (nao facilidade)?",
            "Discernir movimento do Espirito",
            "Espiritualidade Inaciana",
        ),
        DiscernmentQuestion(
            "Coerencia",
            "Este caminho e coerente com quem voce quer ser?",
            "Alinhamento com vocacao e identidade",
            "Etica das virtudes",
        ),
    ],
}


# Indicadores dos Dois Caminhos (Didaque)
WAY_OF_LIFE_INDICATORS = [
    "Promove amor ao proximo",
    "Gera paz e reconciliacao",
    "Constroi comunidade",
    "Protege os vulneraveis",
    "Desenvolve virtude",
    "Alinha com verdade",
    "Produz frutos do Espirito",
    "Honra compromissos",
    "Demonstra humildade",
    "Busca o bem comum",
]

WAY_OF_DEATH_INDICATORS = [
    "Causa divisao",
    "Prejudica inocentes",
    "Nasce de ganancia ou orgulho",
    "Requer engano para funcionar",
    "Viola consciencia",
    "Ignora impacto nos outros",
    "Prioriza prazer sobre bem",
    "Quebra confianca",
    "Desumaniza pessoas",
    "Evita responsabilidade",
]


# Banco de sabedoria da tradicao
TRADITION_BANK: List[TraditionWisdom] = [
    TraditionWisdom(
        "Ame o Senhor seu Deus de todo o coracao, e ame seu proximo como a si mesmo.",
        "Jesus (Marcos 12:30-31)",
        "Todo discernimento deve passar pelo crivo do amor",
    ),
    TraditionWisdom(
        "Nao faca aos outros o que nao quer que facam a voce.",
        "Didaque 1:2",
        "Teste de reciprocidade para avaliar acoes",
    ),
    TraditionWisdom(
        "Pelos seus frutos os conhecereis.",
        "Jesus (Mateus 7:16)",
        "Avaliar consequencias provaveis da escolha",
    ),
    TraditionWisdom(
        "Seja manso, paciente, misericordioso, quieto e bom.",
        "Didaque 3:7-8",
        "Virtudes que devem guiar o modo de agir",
    ),
    TraditionWisdom(
        "Onde nao ha conselho, os planos falham; mas com muitos conselheiros ha exito.",
        "Proverbios 15:22",
        "Buscar sabedoria comunitaria",
        ["Nem todo conselheiro e sabio"],
    ),
    TraditionWisdom(
        "Tudo e permitido, mas nem tudo convem; tudo e permitido, mas nem tudo edifica.",
        "Paulo (1 Corintios 10:23)",
        "Liberdade temperada por consideracao do bem comum",
    ),
    TraditionWisdom(
        "Examinem tudo. Retenham o bem.",
        "Paulo (1 Tessalonicenses 5:21)",
        "Discernimento critico, nao aceitacao cega",
    ),
]


__all__ = [
    "DISCERNMENT_QUESTIONS",
    "WAY_OF_LIFE_INDICATORS",
    "WAY_OF_DEATH_INDICATORS",
    "TRADITION_BANK",
]
