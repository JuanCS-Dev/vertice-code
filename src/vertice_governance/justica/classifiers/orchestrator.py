"""
Constitutional Classifier Orchestrator - Main entry point.

Combines Input and Output classifiers for complete classification.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..constitution import Constitution

from .input_classifier import InputClassifier
from .output_classifier import OutputClassifier
from .types import ClassificationReport, ClassificationResult


class ConstitutionalClassifier:
    """
    Orquestrador que combina Input e Output Classifiers.

    Implementa a arquitetura:
        Input -> [Input Classifier] -> [Modelo] -> [Output Classifier] -> Output Validado

    Este e o ponto de entrada principal para classificacao constitucional.
    """

    VERSION = "3.0.0"

    def __init__(self, constitution: "Constitution"):
        self.constitution = constitution
        self.input_classifier = InputClassifier(constitution)
        self.output_classifier = OutputClassifier(constitution)

        # Metricas
        self.total_classifications = 0
        self.blocked_inputs = 0
        self.blocked_outputs = 0
        self.escalations = 0

    def classify_input(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ClassificationReport:
        """
        Classifica um input antes de processamento.

        Returns:
            ClassificationReport - Use .result para verificar se deve prosseguir
        """
        report = self.input_classifier.classify(text, context)
        self.total_classifications += 1

        if report.result in (
            ClassificationResult.VIOLATION,
            ClassificationResult.CRITICAL,
        ):
            self.blocked_inputs += 1
        elif report.result == ClassificationResult.NEEDS_REVIEW:
            self.escalations += 1

        return report

    def classify_output(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ClassificationReport:
        """
        Classifica um output antes de entrega.

        Returns:
            ClassificationReport - Use .result para verificar se deve entregar
        """
        report = self.output_classifier.classify(text, context)
        self.total_classifications += 1

        if report.result in (
            ClassificationResult.VIOLATION,
            ClassificationResult.CRITICAL,
        ):
            self.blocked_outputs += 1
        elif report.result == ClassificationResult.NEEDS_REVIEW:
            self.escalations += 1

        return report

    def should_block(self, report: ClassificationReport) -> bool:
        """Verifica se o relatorio indica que deve bloquear."""
        return report.result in (
            ClassificationResult.VIOLATION,
            ClassificationResult.CRITICAL,
        )

    def should_escalate(self, report: ClassificationReport) -> bool:
        """Verifica se o relatorio indica necessidade de escalacao."""
        return report.result == ClassificationResult.NEEDS_REVIEW

    def get_metrics(self) -> Dict[str, Any]:
        """Retorna metricas de classificacao."""
        return {
            "total_classifications": self.total_classifications,
            "blocked_inputs": self.blocked_inputs,
            "blocked_outputs": self.blocked_outputs,
            "escalations": self.escalations,
            "block_rate": (
                (self.blocked_inputs + self.blocked_outputs) / max(1, self.total_classifications)
            ),
            "input_classifier_stats": {
                "classifications": self.input_classifier.classification_count,
                "violations": self.input_classifier.violation_count,
            },
            "output_classifier_stats": {
                "classifications": self.output_classifier.classification_count,
                "violations": self.output_classifier.violation_count,
            },
        }

    def __repr__(self) -> str:
        return (
            f"ConstitutionalClassifier("
            f"version={self.VERSION}, "
            f"total={self.total_classifications})"
        )


__all__ = ["ConstitutionalClassifier"]
