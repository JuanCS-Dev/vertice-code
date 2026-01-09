"""
Socratic Package - Socratic method implementation.

Modular refactoring of socratic.py (534 lines).
"""

from __future__ import annotations

from .types import QuestionType, DialoguePhase
from .models import SocraticQuestion, DialogueState
from .templates import QUESTION_TEMPLATES, TRANSITIONS, FOLLOW_UPS
from .engine import SocraticEngine


__all__ = [
    # Types
    "QuestionType",
    "DialoguePhase",
    # Models
    "SocraticQuestion",
    "DialogueState",
    # Templates
    "QUESTION_TEMPLATES",
    "TRANSITIONS",
    "FOLLOW_UPS",
    # Engine
    "SocraticEngine",
]
