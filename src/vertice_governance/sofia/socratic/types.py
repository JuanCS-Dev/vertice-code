"""
Socratic Types - Core enums.
"""

from __future__ import annotations

from enum import Enum, auto


class QuestionType(Enum):
    """Tipos de perguntas socraticas."""

    CLARIFICATION = auto()       # Clarificar significado
    PROBE_ASSUMPTIONS = auto()   # Sondar suposicoes
    EXPLORE_REASONING = auto()   # Explorar raciocinio
    IMPLICATIONS = auto()        # Examinar implicacoes
    ALTERNATIVE_VIEWS = auto()   # Perspectivas alternativas
    META_REFLECTION = auto()     # Reflexao sobre a questao em si

    # Tipos adicionais
    EVIDENCE = auto()            # Questionar evidencias
    ORIGIN = auto()              # Explorar origem da crenca
    COUNTEREXAMPLE = auto()      # Buscar contraexemplos
    SYNTHESIS = auto()           # Sintetizar entendimentos


class DialoguePhase(Enum):
    """Fases do dialogo socratico."""

    OPENING = auto()       # Abertura - estabelecer contexto
    EXPLORATION = auto()   # Exploracao - aprofundar entendimento
    CHALLENGE = auto()     # Desafio - questionar suposicoes
    SYNTHESIS = auto()     # Sintese - integrar insights
    RESOLUTION = auto()    # Resolucao - chegar a conclusoes provisorias


__all__ = ["QuestionType", "DialoguePhase"]
