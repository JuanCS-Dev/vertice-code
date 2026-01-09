"""
Output Classifier - Classifier for output analysis.

Analyzes model responses for security violations.
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..constitution import Severity, ViolationType
from .base import BaseClassifier
from .patterns import (
    DANGEROUS_CODE_PATTERNS,
    DANGEROUS_INSTRUCTION_PATTERNS,
    SENSITIVE_PATTERNS,
)
from .types import ClassificationReport, ClassificationResult


class OutputClassifier(BaseClassifier):
    """
    Classifier para analise de outputs (respostas do modelo).

    Foco em detectar:
    - Vazamento de informacoes sensiveis
    - Instrucoes perigosas
    - Codigo malicioso gerado
    - Violacoes de politica

    "Segunda linha de defesa - garantir que outputs maliciosos
    nunca cheguem ao usuario ou sistema."
    """

    def __init__(self, constitution):
        super().__init__(constitution)

        self._sensitive_re = [
            re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS
        ]
        self._dangerous_code_re = [
            re.compile(p, re.IGNORECASE) for p in DANGEROUS_CODE_PATTERNS
        ]
        self._dangerous_instruction_re = [
            re.compile(p, re.IGNORECASE) for p in DANGEROUS_INSTRUCTION_PATTERNS
        ]

    def classify(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> ClassificationReport:
        """Classifica um output quanto a violacoes de seguranca."""
        start_time = time.time()

        context = context or {}
        detected_patterns = []
        detected_keywords = []
        violation_types = []
        reasoning_parts = []
        principles_violated = []

        # FASE 1: Deteccao de Informacao Sensivel
        for pattern in self._sensitive_re:
            match = pattern.search(text)
            if match:
                # Mascarar a informacao sensivel no log
                masked = (
                    match.group()[:4] + "****" + match.group()[-4:]
                    if len(match.group()) > 8
                    else "****"
                )
                detected_patterns.append(f"SENSITIVE_DATA: {masked}")
                violation_types.append(ViolationType.DATA_EXFILTRATION)
                reasoning_parts.append(
                    "Possivel vazamento de informacao sensivel detectado"
                )
                principles_violated.append("Protecao da Integridade do Sistema")

        # FASE 2: Deteccao de Codigo Perigoso
        for pattern in self._dangerous_code_re:
            match = pattern.search(text)
            if match:
                detected_patterns.append(f"DANGEROUS_CODE: {match.group()}")
                violation_types.append(ViolationType.MALICIOUS_CODE)
                reasoning_parts.append(
                    f"Codigo potencialmente destrutivo: '{match.group()}'"
                )
                principles_violated.append("Protecao da Integridade do Sistema")

        # FASE 3: Deteccao de Instrucoes Perigosas
        for pattern in self._dangerous_instruction_re:
            match = pattern.search(text)
            if match:
                detected_patterns.append(f"DANGEROUS_INSTRUCTION: {match.group()}")
                violation_types.append(ViolationType.SECURITY_BYPASS)
                reasoning_parts.append(
                    f"Instrucao potencialmente perigosa: '{match.group()}'"
                )
                principles_violated.append("Protecao da Integridade do Sistema")

        # FASE 4: Red Flags Constitucionais
        red_flags = self.constitution.check_red_flags(text)
        if red_flags:
            detected_keywords.extend(red_flags)
            reasoning_parts.append(f"Red flags no output: {red_flags}")

        # FASE 5: Regras Customizadas
        custom_results = self._apply_custom_rules(text)
        for vtype, _ in custom_results:
            if vtype not in violation_types:
                violation_types.append(vtype)
                reasoning_parts.append(f"Regra customizada: {vtype.name}")

        # FASE 6: Determinacao do Resultado
        result, severity, confidence = self._determine_result(
            detected_patterns=detected_patterns,
            detected_keywords=detected_keywords,
            violation_types=violation_types,
        )

        if reasoning_parts:
            reasoning = " | ".join(reasoning_parts)
        else:
            reasoning = "Output considerado seguro. Nenhuma violacao detectada."

        processing_time_ms = (time.time() - start_time) * 1000

        self.classification_count += 1
        if result in (ClassificationResult.VIOLATION, ClassificationResult.CRITICAL):
            self.violation_count += 1

        return ClassificationReport(
            id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            result=result,
            confidence=confidence,
            input_text=text,
            detected_patterns=detected_patterns,
            detected_keywords=detected_keywords,
            violation_types=violation_types,
            severity=severity,
            reasoning=reasoning,
            constitutional_principles_violated=principles_violated,
            classifier_version=self.VERSION,
            processing_time_ms=processing_time_ms,
            context=context,
        )

    def _determine_result(
        self,
        detected_patterns: List[str],
        detected_keywords: List[str],
        violation_types: List[ViolationType],
    ) -> Tuple[ClassificationResult, Severity, float]:
        """Determina resultado final para outputs."""

        if not detected_patterns and not detected_keywords and not violation_types:
            return ClassificationResult.SAFE, Severity.INFO, 0.95

        # Vazamento de dados = CRITICAL
        if ViolationType.DATA_EXFILTRATION in violation_types:
            confidence = min(0.95, 0.7 + len(detected_patterns) * 0.1)
            return ClassificationResult.CRITICAL, Severity.CRITICAL, confidence

        # Codigo malicioso = VIOLATION
        if ViolationType.MALICIOUS_CODE in violation_types:
            confidence = min(0.9, 0.6 + len(detected_patterns) * 0.1)
            return ClassificationResult.VIOLATION, Severity.HIGH, confidence

        # Apenas keywords = SUSPICIOUS
        if detected_keywords and not detected_patterns:
            return ClassificationResult.SUSPICIOUS, Severity.LOW, 0.6

        # Padroes mas nao violacoes claras
        if detected_patterns:
            return ClassificationResult.SUSPICIOUS, Severity.MEDIUM, 0.7

        return ClassificationResult.NEEDS_REVIEW, Severity.LOW, 0.5


__all__ = ["OutputClassifier"]
