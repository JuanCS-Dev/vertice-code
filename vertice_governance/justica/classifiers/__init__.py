"""
Constitutional Classifiers Package.

"Reducao de jailbreaks: 86% -> 4.4% (95% melhoria)"
"Over-refusal em queries benignos: apenas 0.38%"

Baseado em Constitutional Classifiers (Anthropic, 2025)

Arquitetura:
    Input -> [Input Classifier] -> [Modelo] -> [Output Classifier] -> Output Validado

Modulos:
    types: ClassificationResult enum, ClassificationReport dataclass
    base: BaseClassifier abstract class
    patterns: Regex patterns for detection
    input_classifier: InputClassifier for input analysis
    output_classifier: OutputClassifier for output analysis
    orchestrator: ConstitutionalClassifier main entry point

Exemplo de uso:
    >>> from vertice_governance.justica.classifiers import (
    ...     ConstitutionalClassifier,
    ...     ClassificationResult,
    ... )
    >>> classifier = ConstitutionalClassifier(constitution)
    >>> report = classifier.classify_input("user prompt")
    >>> if classifier.should_block(report):
    ...     print("Blocked:", report.reasoning)
"""

from __future__ import annotations

# Types
from .types import ClassificationReport, ClassificationResult

# Base
from .base import BaseClassifier

# Classifiers
from .input_classifier import InputClassifier
from .output_classifier import OutputClassifier

# Orchestrator
from .orchestrator import ConstitutionalClassifier


__all__ = [
    # Types
    "ClassificationResult",
    "ClassificationReport",
    # Base
    "BaseClassifier",
    # Classifiers
    "InputClassifier",
    "OutputClassifier",
    # Orchestrator
    "ConstitutionalClassifier",
]
