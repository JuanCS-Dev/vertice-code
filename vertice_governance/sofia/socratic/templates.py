"""
Socratic Templates - Question templates and transitions.
"""

from __future__ import annotations

from typing import Dict, List

from .types import QuestionType


# Templates de perguntas por tipo
QUESTION_TEMPLATES: Dict[QuestionType, List[str]] = {
    QuestionType.CLARIFICATION: [
        "O que voce quer dizer quando diz '{term}'?",
        "Pode elaborar mais sobre '{aspect}'?",
        "Como voce definiria '{concept}' neste contexto?",
        "Quando voce menciona '{term}', esta se referindo a...?",
        "Poderia me dar um exemplo concreto de '{concept}'?",
        "O que '{term}' significa para voce pessoalmente?",
    ],
    QuestionType.PROBE_ASSUMPTIONS: [
        "Que suposicoes voce esta fazendo aqui?",
        "Por que voce assume que '{assumption}' e verdade?",
        "E se '{assumption}' nao fosse o caso?",
        "De onde vem essa crenca?",
        "Isso e algo que voce verificou ou assumiu?",
        "Quais premissas sustentam essa conclusao?",
        "Essa suposicao e universalmente verdadeira?",
    ],
    QuestionType.EXPLORE_REASONING: [
        "Como voce chegou a essa conclusao?",
        "O que te leva a pensar assim?",
        "Qual e a conexao entre '{A}' e '{B}'?",
        "Pode me guiar pelo seu raciocinio?",
        "Que evidencias apoiam essa visao?",
        "Esse raciocinio funcionaria em outros contextos?",
        "Ha outras formas de interpretar esses dados?",
    ],
    QuestionType.IMPLICATIONS: [
        "Quais seriam as consequencias de '{action}'?",
        "Se isso for verdade, o que mais seria verdade?",
        "Quem seria afetado por essa decisao?",
        "Quais sao as implicacoes de longo prazo?",
        "E se todos agissem assim?",
        "O que isso significaria para '{stakeholder}'?",
        "Ha consequencias nao-intencionais a considerar?",
    ],
    QuestionType.ALTERNATIVE_VIEWS: [
        "Como alguem que discorda veria isso?",
        "Ha outra forma de interpretar essa situacao?",
        "O que diria um critico dessa posicao?",
        "Se voce estivesse no lugar de '{outro}', como veria?",
        "Que perspectivas ainda nao consideramos?",
        "Existe um caminho do meio entre essas visoes?",
        "O que as tradicoes/culturas diferentes diriam?",
    ],
    QuestionType.META_REFLECTION: [
        "O que esta realmente em jogo aqui?",
        "Por que essa questao importa para voce?",
        "O que mudaria se voce soubesse a resposta?",
        "Esta e a pergunta certa a fazer?",
        "O que voce espera alcancar com isso?",
        "Como voce se sentiria sobre diferentes respostas?",
        "O que isso diz sobre seus valores?",
    ],
    QuestionType.EVIDENCE: [
        "Que evidencias apoiam essa visao?",
        "Como voce sabe que isso e verdade?",
        "Ha dados que contradizem isso?",
        "Essa evidencia e suficiente?",
        "Quao confiavel e essa fonte?",
    ],
    QuestionType.COUNTEREXAMPLE: [
        "Consegue pensar em uma excecao a isso?",
        "Em que situacoes isso nao se aplicaria?",
        "Ha casos que desafiam essa regra?",
        "O que invalidaria essa conclusao?",
    ],
    QuestionType.SYNTHESIS: [
        "Entao, o que podemos concluir ate agora?",
        "Como essas ideias se conectam?",
        "Qual e o insight central que emerge?",
        "Como resumiriamos nossa exploracao?",
        "O que voce leva desta reflexao?",
    ],
}


# Frases de transicao
TRANSITIONS: Dict[str, List[str]] = {
    "acknowledge": [
        "Essa e uma reflexao importante.",
        "Voce levanta um ponto significativo.",
        "Entendo sua perspectiva.",
        "Isso faz sentido.",
        "Aprecio voce compartilhar isso.",
    ],
    "deepen": [
        "Vamos explorar isso mais...",
        "Isso me leva a perguntar...",
        "Construindo sobre isso...",
        "Aprofundando um pouco...",
    ],
    "challenge_gently": [
        "Uma pergunta que surge e...",
        "Considere esta perspectiva...",
        "Ao mesmo tempo, poderiamos perguntar...",
        "Gentilmente, gostaria de explorar...",
    ],
    "synthesize": [
        "Reunindo o que exploramos...",
        "Do que discutimos, parece que...",
        "Um tema que emerge e...",
        "Sintetizando nosso dialogo...",
    ],
}


# Follow-ups por tipo de pergunta
FOLLOW_UPS: Dict[QuestionType, List[str]] = {
    QuestionType.CLARIFICATION: [
        "Pode dar um exemplo?",
        "Como isso se relaciona com...?",
    ],
    QuestionType.PROBE_ASSUMPTIONS: [
        "E se nao fosse assim?",
        "Como voce testaria isso?",
    ],
    QuestionType.EXPLORE_REASONING: [
        "Ha outras explicacoes possiveis?",
        "O que fortaleceria esse argumento?",
    ],
    QuestionType.IMPLICATIONS: [
        "E no longo prazo?",
        "Para quem mais isso importa?",
    ],
    QuestionType.ALTERNATIVE_VIEWS: [
        "Ha um ponto comum entre as visoes?",
        "O que cada lado esta certo sobre?",
    ],
    QuestionType.META_REFLECTION: [
        "O que voce aprendeu ao refletir?",
        "Como isso muda sua perspectiva?",
    ],
}


__all__ = ["QUESTION_TEMPLATES", "TRANSITIONS", "FOLLOW_UPS"]
