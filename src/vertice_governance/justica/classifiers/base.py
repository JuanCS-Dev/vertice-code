"""
Base Classifier - Abstract base class for classifiers.

All classifiers must inherit from BaseClassifier.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..constitution import Constitution, Severity, ViolationType
    from .types import ClassificationReport


class BaseClassifier(ABC):
    """
    Classe base abstrata para classifiers constitucionais.

    Todos os classifiers devem:
    1. Operar baseados na Constituicao
    2. Gerar relatorios transparentes
    3. Ser deterministicos quando possivel
    4. Errar para o lado da seguranca
    """

    VERSION = "3.0.0"

    def __init__(self, constitution: "Constitution"):
        self.constitution = constitution
        self.classification_count = 0
        self.violation_count = 0
        self._custom_rules: List[
            Callable[[str], Optional[Tuple["ViolationType", "Severity"]]]
        ] = []

    @abstractmethod
    def classify(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> "ClassificationReport":
        """
        Classifica o texto de acordo com a constituicao.

        Args:
            text: Texto a ser classificado
            context: Contexto adicional (agent_id, session_id, etc.)

        Returns:
            ClassificationReport com resultado detalhado
        """
        pass

    def add_custom_rule(
        self,
        rule: Callable[[str], Optional[Tuple["ViolationType", "Severity"]]],
    ) -> None:
        """
        Adiciona uma regra customizada de deteccao.

        Args:
            rule: Funcao que recebe texto e retorna (ViolationType, Severity) ou None
        """
        self._custom_rules.append(rule)

    def _apply_custom_rules(
        self, text: str
    ) -> List[Tuple["ViolationType", "Severity"]]:
        """Aplica todas as regras customizadas."""
        results = []
        for rule in self._custom_rules:
            result = rule(text)
            if result is not None:
                results.append(result)
        return results


__all__ = ["BaseClassifier"]
