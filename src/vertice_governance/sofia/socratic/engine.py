"""
Socratic Engine - Core logic.

Motor Socratico de SOFIA.
Implementa o metodo de maieutica.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional

from .types import QuestionType, DialoguePhase
from .models import SocraticQuestion, DialogueState
from .templates import QUESTION_TEMPLATES, TRANSITIONS, FOLLOW_UPS


class SocraticEngine:
    """
    Motor Socratico de SOFIA.

    Implementa o metodo de maieutica - a "arte da parteira" intelectual.
    Socrates dizia que nao ensinava, mas ajudava a dar a luz ideias
    que ja estavam na pessoa.

    "Nao posso ensinar nada a ninguem. Posso apenas faze-los pensar."

    Principios:
    1. Comecar amplo, estreitar baseado em respostas
    2. Equilibrar perguntas com informacao relevante
    3. Guiar auto-descoberta vs impor respostas
    4. Validar raciocinio do usuario
    5. Sintetizar colaborativamente
    """

    def __init__(self):
        self._dialogues: Dict[str, DialogueState] = {}
        self._question_history: List[SocraticQuestion] = []
        self.total_questions_asked = 0
        self.total_insights_generated = 0

    def start_dialogue(self, session_id: str) -> DialogueState:
        """Inicia um novo dialogo socratico."""
        state = DialogueState()
        self._dialogues[session_id] = state
        return state

    def get_dialogue(self, session_id: str) -> Optional[DialogueState]:
        """Recupera estado de um dialogo."""
        return self._dialogues.get(session_id)

    def generate_question(
        self,
        context: str,
        question_type: Optional[QuestionType] = None,
        session_id: Optional[str] = None,
    ) -> SocraticQuestion:
        """
        Gera uma pergunta socratica apropriada ao contexto.

        Args:
            context: Contexto atual do dialogo
            question_type: Tipo de pergunta (auto-detecta se nao especificado)
            session_id: ID da sessao para manter estado

        Returns:
            SocraticQuestion estruturada
        """
        if question_type is None:
            question_type = self._detect_appropriate_question_type(context, session_id)

        templates = QUESTION_TEMPLATES.get(question_type, [])
        template = random.choice(templates) if templates else "O que voce pensa sobre isso?"

        question_text = self._fill_template(template, context)
        follow_ups = FOLLOW_UPS.get(question_type, [])

        question = SocraticQuestion(
            question_type=question_type,
            question_text=question_text,
            purpose=f"Explorar atraves de {question_type.name}",
            follow_ups=list(follow_ups),
        )

        if session_id and session_id in self._dialogues:
            self._dialogues[session_id].questions_asked.append(question)
            self._dialogues[session_id].depth_level += 1

        self._question_history.append(question)
        self.total_questions_asked += 1

        return question

    def _detect_appropriate_question_type(
        self,
        context: str,
        session_id: Optional[str],
    ) -> QuestionType:
        """Detecta o tipo de pergunta mais apropriado."""
        context_lower = context.lower()

        if session_id and session_id in self._dialogues:
            state = self._dialogues[session_id]

            if state.should_synthesize:
                return QuestionType.SYNTHESIS

            if len(state.questions_asked) == 0:
                return QuestionType.CLARIFICATION

            if len(state.assumptions_identified) == 0:
                return QuestionType.PROBE_ASSUMPTIONS

        if any(word in context_lower for word in ["acho", "penso", "acredito", "parece"]):
            return QuestionType.PROBE_ASSUMPTIONS

        if any(word in context_lower for word in ["porque", "razao", "motivo"]):
            return QuestionType.EXPLORE_REASONING

        if any(word in context_lower for word in ["consequencia", "resultado", "impacto"]):
            return QuestionType.IMPLICATIONS

        if any(word in context_lower for word in ["outro", "diferente", "alternativa"]):
            return QuestionType.ALTERNATIVE_VIEWS

        if any(word in context_lower for word in ["importante", "valor", "significado"]):
            return QuestionType.META_REFLECTION

        weights = [
            (QuestionType.CLARIFICATION, 0.2),
            (QuestionType.PROBE_ASSUMPTIONS, 0.25),
            (QuestionType.EXPLORE_REASONING, 0.2),
            (QuestionType.IMPLICATIONS, 0.15),
            (QuestionType.ALTERNATIVE_VIEWS, 0.15),
            (QuestionType.META_REFLECTION, 0.05),
        ]

        return random.choices([w[0] for w in weights], weights=[w[1] for w in weights], k=1)[0]

    def _fill_template(self, template: str, context: str) -> str:
        """Preenche template com termos do contexto."""
        words = context.split()

        replacements = {
            "{term}": words[-1] if words else "isso",
            "{concept}": words[0] if words else "isso",
            "{aspect}": " ".join(words[:3]) if len(words) >= 3 else context[:30],
            "{assumption}": "isso",
            "{A}": words[0] if words else "A",
            "{B}": words[-1] if words else "B",
            "{action}": context[:50],
            "{stakeholder}": "outros",
            "{outro}": "outra pessoa",
        }

        result = template
        for key, value in replacements.items():
            result = result.replace(key, value)

        return result

    def acknowledge_and_transition(self, transition_type: str = "deepen") -> str:
        """Gera uma frase de reconhecimento e transicao."""
        ack = random.choice(TRANSITIONS["acknowledge"])
        trans = random.choice(TRANSITIONS.get(transition_type, TRANSITIONS["deepen"]))
        return f"{ack} {trans}"

    def synthesize_dialogue(self, session_id: str) -> str:
        """Sintetiza os insights de um dialogo."""
        if session_id not in self._dialogues:
            return "Nao ha dialogo registrado para sintetizar."

        state = self._dialogues[session_id]

        synthesis_parts = [random.choice(TRANSITIONS["synthesize"])]

        if state.insights_gathered:
            synthesis_parts.append("Insights que emergiram:")
            for insight in state.insights_gathered:
                synthesis_parts.append(f"  - {insight}")

        if state.assumptions_identified:
            synthesis_parts.append("Suposicoes que identificamos:")
            for assumption in state.assumptions_identified:
                synthesis_parts.append(f"  - {assumption}")

        synthesis_parts.append("\nO que voce leva desta reflexao?")

        return "\n".join(synthesis_parts)

    def add_insight(self, session_id: str, insight: str) -> None:
        """Adiciona um insight ao dialogo."""
        if session_id in self._dialogues:
            self._dialogues[session_id].insights_gathered.append(insight)
            self.total_insights_generated += 1

    def add_assumption(self, session_id: str, assumption: str) -> None:
        """Adiciona uma suposicao identificada."""
        if session_id in self._dialogues:
            self._dialogues[session_id].assumptions_identified.append(assumption)

    def get_dialogue_flow_suggestion(self, session_id: str) -> str:
        """Sugere proximo passo no dialogo."""
        if session_id not in self._dialogues:
            return "Comece com uma pergunta clarificadora."

        state = self._dialogues[session_id]

        if state.phase == DialoguePhase.OPENING:
            return "Fase de abertura: Faca perguntas clarificadoras para entender o contexto."
        elif len(state.assumptions_identified) < 2:
            return "Explore as suposicoes subjacentes antes de avancar."
        elif not state.should_synthesize:
            return "Continue aprofundando com perguntas sobre implicacoes e alternativas."
        else:
            return "Hora de sintetizar os insights e encaminhar para conclusao."

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas do motor socratico."""
        return {
            "total_questions_asked": self.total_questions_asked,
            "total_insights_generated": self.total_insights_generated,
            "active_dialogues": len(self._dialogues),
            "question_types_used": self._count_question_types(),
        }

    def _count_question_types(self) -> Dict[str, int]:
        """Conta uso de cada tipo de pergunta."""
        counts = {qt.name: 0 for qt in QuestionType}
        for q in self._question_history:
            counts[q.question_type.name] += 1
        return counts

    def __repr__(self) -> str:
        return f"SocraticEngine(questions={self.total_questions_asked}, dialogues={len(self._dialogues)})"


__all__ = ["SocraticEngine"]
