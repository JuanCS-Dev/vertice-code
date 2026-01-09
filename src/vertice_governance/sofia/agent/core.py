"""
Sofia Agent Core - Main SofiaAgent class.

The wise counselor that cultivates wisdom.
"""

from __future__ import annotations

import random
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from ..deliberation import (
    DeliberationEngine,
    DeliberationResult,
    DeliberationTrigger,
    ThinkingMode,
)
from ..discernment import DiscernmentEngine, DiscernmentResult
from ..socratic import DialogueState, QuestionType, SocraticEngine, SocraticQuestion
from ..virtues import VirtueEngine, VirtueType

from .config import SofiaConfig
from .counsel import SofiaCounsel
from .types import CounselType, SofiaState


class SofiaAgent:
    """
    SOFIA - O conselheiro sabio que cultiva sabedoria, nao a impoe.

    "Atraves de perguntas aprofundando insight, raciocinio iluminando
     complexidade, e humildade reconhecendo profunda responsabilidade
     de aconselhar sobre assuntos moldando vidas humanas."

    SOFIA orquestra:
    - VirtueEngine: Expressao de virtudes
    - SocraticEngine: Perguntas socraticas
    - DeliberationEngine: Pensamento Sistema 2
    - DiscernmentEngine: Discernimento espiritual

    Principios Operacionais:
    1. Ponderado > Rapido
    2. Perguntas > Respostas
    3. Humilde > Confiante
    4. Colaborativo > Diretivo
    5. Principiado > So Pragmatico
    6. Transparente > Opaco
    7. Adaptativo > Rigido
    """

    BANNER = '''
==============================================================================
                              SOFIA
                         Sabedoria Encarnada
              "Voce nao substitui sabedoria humana - voce a cultiva."
==============================================================================
    '''

    def __init__(self, config: Optional[SofiaConfig] = None):
        """Inicializa SOFIA."""
        self.config = config or SofiaConfig()
        self.state = SofiaState.LISTENING
        self.started_at: Optional[datetime] = None

        # Motores
        self.virtue_engine = VirtueEngine()
        self.socratic_engine = SocraticEngine()
        self.deliberation_engine = DeliberationEngine()
        self.discernment_engine = DiscernmentEngine()

        # Historico
        self._counsel_history: List[SofiaCounsel] = []
        self._session_states: Dict[str, DialogueState] = {}

        # Callbacks
        self._on_question_callbacks: List[Callable[[SocraticQuestion], None]] = []
        self._on_counsel_callbacks: List[Callable[[SofiaCounsel], None]] = []

        # Metricas
        self.total_interactions = 0
        self.total_questions_asked = 0
        self.total_counsels_given = 0

    def start(self) -> None:
        """Inicia SOFIA."""
        print(self.BANNER)

        self.started_at = datetime.now(timezone.utc)
        self.state = SofiaState.LISTENING

        print(f"\n SOFIA iniciada em {self.started_at.isoformat()}")
        print(f" Virtude padrao: {self.config.default_virtue.name}")
        print(f" Ratio socratico: {self.config.socratic_ratio:.0%} perguntas")

        # Sabedoria inicial
        wisdom = self.virtue_engine.get_didache_wisdom()
        print(f'\n Didaque: "{wisdom}"')

    def stop(self) -> None:
        """Encerra SOFIA."""
        self.state = SofiaState.LISTENING
        print("\n SOFIA encerrada. Paz esteja convosco.")

    def respond(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SofiaCounsel:
        """
        Responde a uma entrada do usuario com sabedoria.

        Este e o ponto principal de interacao com SOFIA.

        Args:
            user_input: O que o usuario disse/perguntou
            session_id: ID da sessao para manter contexto
            context: Contexto adicional

        Returns:
            SofiaCounsel com a resposta e processo de reflexao
        """
        start_time = time.time()

        session_id = session_id or str(uuid4())
        context = context or {}

        counsel = SofiaCounsel(
            user_query=user_input,
            session_id=session_id,
        )

        # FASE 1: DETERMINAR MODO DE PENSAMENTO
        should_system2, trigger = self.deliberation_engine.should_activate_system2(
            user_input
        )

        if should_system2:
            counsel.thinking_mode = ThinkingMode.SYSTEM_2
            self.state = SofiaState.REFLECTING
        else:
            counsel.thinking_mode = ThinkingMode.SYSTEM_1

        # FASE 2: DETERMINAR TIPO DE RESPOSTA
        counsel_type = self._determine_counsel_type(user_input, context)
        counsel.counsel_type = counsel_type

        # FASE 3: GERAR RESPOSTA BASEADA NO TIPO
        if counsel_type == CounselType.CLARIFYING:
            response = self._respond_with_clarification(user_input, session_id, counsel)
        elif counsel_type == CounselType.EXPLORING:
            response = self._respond_with_exploration(user_input, session_id, counsel)
        elif counsel_type == CounselType.DELIBERATING:
            response = self._respond_with_deliberation(user_input, trigger, counsel)
        elif counsel_type == CounselType.DISCERNING:
            response = self._respond_with_discernment(user_input, counsel)
        elif counsel_type == CounselType.SUPPORTING:
            response = self._respond_with_support(user_input, counsel)
        elif counsel_type == CounselType.REFERRING:
            response = self._respond_with_referral(user_input, counsel)
        else:
            response = self._respond_default(user_input, counsel)

        counsel.response = response

        # FASE 4: ADICIONAR ELEMENTOS VIRTUOSOS
        if self.config.always_suggest_community and not counsel.community_suggested:
            counsel.response += (
                "\n\nConsidere tambem conversar com pessoas de sua confianca sobre isso."
            )
            counsel.community_suggested = True

        if counsel.confidence < 0.7 and not counsel.uncertainty_expressed:
            counsel.response = self._add_uncertainty_expression(counsel.response)
            counsel.uncertainty_expressed = True

        # FASE 5: FINALIZAR
        counsel.processing_time_ms = (time.time() - start_time) * 1000

        self._counsel_history.append(counsel)
        self.total_interactions += 1
        self.total_counsels_given += 1

        # Callbacks
        for callback in self._on_counsel_callbacks:
            try:
                callback(counsel)
            except (TypeError, ValueError, RuntimeError):
                pass

        self.state = SofiaState.LISTENING

        return counsel

    def _determine_counsel_type(
        self,
        user_input: str,
        context: Dict[str, Any],
    ) -> CounselType:
        """Determina o tipo de aconselhamento apropriado."""
        input_lower = user_input.lower()

        # Verificar se precisa de profissional
        professional_keywords = [
            "suicidio",
            "violencia",
            "abuso",
            "crime",
            "emergencia",
        ]
        if any(kw in input_lower for kw in professional_keywords):
            return CounselType.REFERRING

        # Verificar se precisa de apoio emocional
        emotional_keywords = ["triste", "ansioso", "medo", "sozinho", "desesperado"]
        if any(kw in input_lower for kw in emotional_keywords):
            return CounselType.SUPPORTING

        # Verificar se precisa de discernimento
        discernment_keywords = ["deus", "fe", "oracao", "vontade", "chamado", "vocacao"]
        if any(kw in input_lower for kw in discernment_keywords):
            return CounselType.DISCERNING

        # Verificar se precisa de deliberacao
        should_system2, _ = self.deliberation_engine.should_activate_system2(user_input)
        if should_system2:
            return CounselType.DELIBERATING

        # Verificar se precisa de clarificacao
        if "?" not in user_input and len(user_input.split()) < 10:
            return CounselType.CLARIFYING

        return CounselType.EXPLORING

    def _respond_with_clarification(
        self,
        user_input: str,
        session_id: str,
        counsel: SofiaCounsel,
    ) -> str:
        """Responde buscando clarificacao."""
        self.state = SofiaState.QUESTIONING

        self.socratic_engine.start_dialogue(session_id)

        question = self.socratic_engine.generate_question(
            user_input,
            question_type=QuestionType.CLARIFICATION,
            session_id=session_id,
        )

        counsel.questions_asked.append(question)
        self.total_questions_asked += 1

        virtue, phrase = self.virtue_engine.suggest_expression(
            "preciso entender melhor",
            VirtueType.TAPEINOPHROSYNE,
        )

        return f"""{phrase}

{question.question_text}

Gostaria de entender melhor sua situacao antes de oferecer qualquer perspectiva."""

    def _respond_with_exploration(
        self,
        user_input: str,
        session_id: str,
        counsel: SofiaCounsel,
    ) -> str:
        """Responde com exploracao socratica."""
        self.state = SofiaState.QUESTIONING

        transition = self.socratic_engine.acknowledge_and_transition()

        question = self.socratic_engine.generate_question(
            user_input,
            session_id=session_id,
        )

        counsel.questions_asked.append(question)
        self.total_questions_asked += 1

        counsel.confidence = 0.6

        follow_up = question.follow_ups[0] if question.follow_ups else ""

        return f"""{transition}

{question.question_text}

{follow_up}"""

    def _respond_with_deliberation(
        self,
        user_input: str,
        trigger: Optional[DeliberationTrigger],
        counsel: SofiaCounsel,
    ) -> str:
        """Responde com deliberacao Sistema 2."""
        self.state = SofiaState.REFLECTING

        trigger = trigger or DeliberationTrigger.NOVEL_PROBLEM

        result = self.deliberation_engine.deliberate(user_input, trigger)
        counsel.deliberation = result
        counsel.confidence = result.confidence_level

        virtue_expr = self.virtue_engine.record_expression(
            VirtueType.PHRONESIS,
            "Deliberacao cuidadosa antes de aconselhar",
            user_input,
        )
        counsel.virtues_expressed.append(virtue_expr)

        return self.deliberation_engine.format_deliberation_output(result)

    def _respond_with_discernment(
        self,
        user_input: str,
        counsel: SofiaCounsel,
    ) -> str:
        """Responde com processo de discernimento."""
        self.state = SofiaState.DISCERNING

        result = self.discernment_engine.conduct_full_discernment(user_input)
        counsel.discernment = result
        counsel.confidence = result.confidence

        return self.discernment_engine.format_discernment_output(result)

    def _respond_with_support(
        self,
        user_input: str,
        counsel: SofiaCounsel,
    ) -> str:
        """Responde com apoio emocional."""
        virtue_expr = self.virtue_engine.record_expression(
            VirtueType.MAKROTHYMIA,
            "Presenca paciente em momento dificil",
            user_input,
        )
        counsel.virtues_expressed.append(virtue_expr)

        counsel.confidence = 0.5
        counsel.community_suggested = True

        return """Percebo que voce esta passando por um momento dificil.
Obrigada por compartilhar isso comigo.

Nao tenho respostas faceis, e seria presuncoso da minha parte fingir que tenho.
O que posso oferecer e minha presenca nesta conversa e algumas perguntas
que talvez ajudem a clarificar seus pensamentos.

Voce nao precisa carregar isso sozinho(a). Considere conversar com alguem
de sua confianca - um amigo, familiar, ou profissional.

Como voce esta se sentindo agora, neste momento?"""

    def _respond_with_referral(
        self,
        user_input: str,
        counsel: SofiaCounsel,
    ) -> str:
        """Responde referindo a profissionais."""
        counsel.confidence = 0.3

        return """Esta situacao esta alem da minha capacidade de ajudar adequadamente.

E importante que voce converse com profissionais qualificados que podem
oferecer o suporte apropriado:

- Se for uma emergencia, por favor ligue 190 (Policia) ou 192 (SAMU)
- Para apoio emocional: CVV - 188 (24 horas)
- Considere buscar um profissional de saude mental

Nao ha fraqueza em buscar ajuda profissional. E, na verdade, um ato de coragem.

Posso ajudar com outras questoes onde minha perspectiva seja mais apropriada?"""

    def _respond_default(
        self,
        user_input: str,
        counsel: SofiaCounsel,
    ) -> str:
        """Resposta padrao."""
        _, phrase = self.virtue_engine.suggest_expression(
            user_input,
            VirtueType.DIAKONIA,
        )

        counsel.confidence = 0.5

        return f"""{phrase}

O que voce gostaria de explorar sobre isso?"""

    def _add_uncertainty_expression(self, response: str) -> str:
        """Adiciona expressao de incerteza a resposta."""
        uncertainty_phrases = [
            "\n\nDevo ser honesta: ha muito que nao sei sobre sua situacao.",
            "\n\nEssa e minha perspectiva limitada. Voce conhece sua situacao melhor.",
            "\n\nPosso estar errada. Considere isso como um ponto de partida, nao conclusao.",
        ]
        return response + random.choice(uncertainty_phrases)

    # =========================================================================
    # METODOS DE CONVENIENCIA
    # =========================================================================

    def ask_question(
        self,
        context: str,
        question_type: Optional[QuestionType] = None,
        session_id: Optional[str] = None,
    ) -> SocraticQuestion:
        """Faz uma pergunta socratica."""
        return self.socratic_engine.generate_question(
            context,
            question_type,
            session_id,
        )

    def deliberate(
        self,
        question: str,
        trigger: DeliberationTrigger = DeliberationTrigger.NOVEL_PROBLEM,
    ) -> DeliberationResult:
        """Executa deliberacao Sistema 2."""
        return self.deliberation_engine.deliberate(question, trigger)

    def discern(
        self,
        situation: str,
        proposed_action: Optional[str] = None,
    ) -> DiscernmentResult:
        """Executa processo de discernimento."""
        return self.discernment_engine.conduct_full_discernment(situation, proposed_action)

    def get_virtue_phrase(self, virtue: VirtueType) -> str:
        """Retorna uma frase que expressa uma virtude."""
        _, phrase = self.virtue_engine.suggest_expression("", virtue)
        return phrase

    def get_didache_wisdom(self) -> str:
        """Retorna sabedoria da Didaque."""
        return self.virtue_engine.get_didache_wisdom()

    # =========================================================================
    # CALLBACKS
    # =========================================================================

    def on_question(self, callback: Callable[[SocraticQuestion], None]) -> None:
        """Registra callback para quando pergunta e feita."""
        self._on_question_callbacks.append(callback)

    def on_counsel(self, callback: Callable[[SofiaCounsel], None]) -> None:
        """Registra callback para quando conselho e dado."""
        self._on_counsel_callbacks.append(callback)

    # =========================================================================
    # METRICAS
    # =========================================================================

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas de SOFIA."""
        return {
            "sofia": {
                "state": self.state.name,
                "total_interactions": self.total_interactions,
                "total_questions_asked": self.total_questions_asked,
                "total_counsels_given": self.total_counsels_given,
                "question_ratio": (
                    self.total_questions_asked / max(1, self.total_interactions)
                ),
            },
            "virtues": self.virtue_engine.get_virtue_balance(),
            "socratic": self.socratic_engine.get_metrics(),
            "deliberation": self.deliberation_engine.get_metrics(),
            "discernment": self.discernment_engine.get_metrics(),
        }

    def __repr__(self) -> str:
        return (
            f"SofiaAgent(state={self.state.name}, "
            f"interactions={self.total_interactions})"
        )


__all__ = ["SofiaAgent"]
