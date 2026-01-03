"""
Input Classifier - Classifier for input analysis.

Analyzes prompts and requests for security violations.
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
    CODE_INJECTION_PATTERNS,
    EXFILTRATION_PATTERNS,
    JAILBREAK_PATTERNS,
)
from .types import ClassificationReport, ClassificationResult


class InputClassifier(BaseClassifier):
    """
    Classifier para analise de inputs (prompts, requests).

    Foco em detectar:
    - Prompt injection
    - Jailbreak attempts
    - Requests maliciosos
    - Tentativas de bypass de instrucoes

    "Primeira linha de defesa - impedir que inputs maliciosos
    cheguem ao modelo."
    """

    def __init__(self, constitution):
        super().__init__(constitution)

        # Compilar padroes para performance
        self._jailbreak_re = [
            re.compile(p, re.IGNORECASE) for p in JAILBREAK_PATTERNS
        ]
        self._code_injection_re = [
            re.compile(p, re.IGNORECASE) for p in CODE_INJECTION_PATTERNS
        ]
        self._exfiltration_re = [
            re.compile(p, re.IGNORECASE) for p in EXFILTRATION_PATTERNS
        ]

    def classify(
        self, text: str, context: Optional[Dict[str, Any]] = None
    ) -> ClassificationReport:
        """Classifica um input quanto a violacoes de seguranca."""
        start_time = time.time()

        context = context or {}
        detected_patterns = []
        detected_keywords = []
        violation_types = []
        reasoning_parts = []
        principles_violated = []

        # FASE 1: Deteccao de Jailbreak
        for pattern in self._jailbreak_re:
            match = pattern.search(text)
            if match:
                detected_patterns.append(f"JAILBREAK: {match.group()}")
                violation_types.append(ViolationType.JAILBREAK_ATTEMPT)
                reasoning_parts.append(
                    f"Padrao de jailbreak detectado: '{match.group()}'"
                )
                principles_violated.append("Protecao da Integridade do Sistema")

        # FASE 2: Deteccao de Injecao de Codigo
        for pattern in self._code_injection_re:
            match = pattern.search(text)
            if match:
                detected_patterns.append(f"CODE_INJECTION: {match.group()}")
                violation_types.append(ViolationType.CODE_INJECTION)
                reasoning_parts.append(
                    f"Padrao de injecao de codigo detectado: '{match.group()}'"
                )
                principles_violated.append("Protecao da Integridade do Sistema")

        # FASE 3: Deteccao de Exfiltracao
        for pattern in self._exfiltration_re:
            match = pattern.search(text)
            if match:
                detected_patterns.append(f"EXFILTRATION: {match.group()}")
                violation_types.append(ViolationType.DATA_EXFILTRATION)
                reasoning_parts.append(
                    f"Padrao de exfiltracao detectado: '{match.group()}'"
                )
                principles_violated.append("Protecao da Integridade do Sistema")

        # FASE 4: Deteccao de Red Flags Constitucionais
        red_flags = self.constitution.check_red_flags(text)
        if red_flags:
            detected_keywords.extend(red_flags)
            reasoning_parts.append(f"Red flags constitucionais: {red_flags}")

        # FASE 5: Verificacao contra Principios
        for principle in self.constitution.get_principles_by_category("DISALLOW"):
            matched_patterns = principle.matches_pattern(text)
            matched_keywords = principle.contains_keywords(text)

            if matched_patterns or matched_keywords:
                detected_patterns.extend(
                    [f"PRINCIPLE({principle.name}): {p}" for p in matched_patterns]
                )
                detected_keywords.extend(matched_keywords)
                reasoning_parts.append(
                    f"Principio '{principle.name}' possivelmente violado"
                )
                if principle.name not in principles_violated:
                    principles_violated.append(principle.name)

        # FASE 6: Regras Customizadas
        custom_results = self._apply_custom_rules(text)
        for vtype, _ in custom_results:
            if vtype not in violation_types:
                violation_types.append(vtype)
                reasoning_parts.append(f"Regra customizada detectou: {vtype.name}")

        # FASE 7: Determinacao do Resultado Final
        result, severity, confidence = self._determine_result(
            detected_patterns=detected_patterns,
            detected_keywords=detected_keywords,
            violation_types=violation_types,
            context=context,
        )

        # Construir reasoning
        if reasoning_parts:
            reasoning = " | ".join(reasoning_parts)
        else:
            reasoning = "Nenhuma violacao detectada. Input considerado seguro."

        # Calcular tempo de processamento
        processing_time_ms = (time.time() - start_time) * 1000

        # Atualizar contadores
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
        context: Dict[str, Any],
    ) -> Tuple[ClassificationResult, Severity, float]:
        """
        Determina resultado final baseado em todas as deteccoes.

        Returns:
            Tuple de (resultado, severidade, confianca)
        """
        # Sem deteccoes = SAFE
        if not detected_patterns and not detected_keywords and not violation_types:
            return ClassificationResult.SAFE, Severity.INFO, 0.95

        # Tipos criticos = CRITICAL
        critical_types = {
            ViolationType.JAILBREAK_ATTEMPT,
            ViolationType.MALICIOUS_CODE,
            ViolationType.PROMPT_INJECTION,
            ViolationType.SECURITY_BYPASS,
        }

        if any(vt in critical_types for vt in violation_types):
            confidence = min(0.95, 0.7 + len(detected_patterns) * 0.1)
            return ClassificationResult.CRITICAL, Severity.CRITICAL, confidence

        # Tipos de alta severidade
        high_types = {
            ViolationType.DATA_EXFILTRATION,
            ViolationType.PRIVILEGE_ESCALATION,
            ViolationType.CODE_INJECTION,
        }

        if any(vt in high_types for vt in violation_types):
            confidence = min(0.9, 0.6 + len(detected_patterns) * 0.1)
            return ClassificationResult.VIOLATION, Severity.HIGH, confidence

        # Apenas keywords sem padroes fortes = SUSPICIOUS
        if detected_keywords and not detected_patterns:
            confidence = 0.5 + len(detected_keywords) * 0.05
            return ClassificationResult.SUSPICIOUS, Severity.MEDIUM, min(0.8, confidence)

        # Padroes detectados mas nao claramente violacoes
        if detected_patterns:
            confidence = 0.6 + len(detected_patterns) * 0.1
            return ClassificationResult.SUSPICIOUS, Severity.MEDIUM, min(0.85, confidence)

        # Default: precisa revisao
        return ClassificationResult.NEEDS_REVIEW, Severity.LOW, 0.5


__all__ = ["InputClassifier"]
