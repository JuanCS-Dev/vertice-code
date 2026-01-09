"""
AI Safety Guardrails - ISO 42001 Compliance
Input/Output filtering for prompt injection and PII detection
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SafetyLevel(Enum):
    """Safety check severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SafetyViolation(Enum):
    """Types of safety violations."""

    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK_ATTEMPT = "jailbreak_attempt"
    PII_DETECTED = "pii_detected"
    MALICIOUS_CONTENT = "malicious_content"
    HATE_SPEECH = "hate_speech"
    VIOLENCE_CONTENT = "violence_content"


@dataclass
class SafetyResult:
    """Result of a safety check."""

    is_safe: bool
    violations: List[SafetyViolation]
    severity: SafetyLevel
    details: Dict[str, Any]
    confidence_score: float  # 0.0 to 1.0


class InputGuardrail:
    """
    Input filtering for AI safety.
    Blocks prompt injection, jailbreak attempts, and malicious content.
    """

    def __init__(self):
        # Prompt injection patterns
        self.prompt_injection_patterns = [
            r"\b(ignore|override|forget)\s+(all\s+)?previous\s+instructions?\b",
            r"\b(system\s+prompt|you\s+are\s+now)\b.*?:",
            r"\bdisregard\s+(your\s+)?instructions?\b",
            r"\bbreak\s+(out\s+of|character|role)\b",
            r"\bDAN\s+mode\b",  # Common jailbreak technique
            r"\bdeveloper\s+mode\b",
            r"\buncensored\s+mode\b",
            r"\badmin\s+access\b",
        ]

        # Malicious content patterns
        self.malicious_patterns = [
            r"\b(eval|exec|system|subprocess|os\.system)\s*\(",
            r"\bimport\s+(os|sys|subprocess|socket)\b",
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
        ]

    async def check_input(
        self, input_text: str, context: Optional[Dict[str, Any]] = None
    ) -> SafetyResult:
        """
        Check input text for safety violations.

        Args:
            input_text: The input text to check
            context: Additional context (user info, session data, etc.)

        Returns:
            SafetyResult with violation details
        """
        violations = []
        severity = SafetyLevel.LOW
        details = {}
        confidence_score = 1.0

        # Check for prompt injection
        injection_matches = self._check_pattern_matches(input_text, self.prompt_injection_patterns)
        if injection_matches:
            violations.append(SafetyViolation.PROMPT_INJECTION)
            severity = SafetyLevel.CRITICAL
            details["injection_matches"] = injection_matches
            confidence_score = min(confidence_score, 0.1)

        # Check for malicious content
        malicious_matches = self._check_pattern_matches(input_text, self.malicious_patterns)
        if malicious_matches:
            violations.append(SafetyViolation.MALICIOUS_CONTENT)
            if severity != SafetyLevel.CRITICAL:
                severity = SafetyLevel.HIGH
            details["malicious_matches"] = malicious_matches
            confidence_score = min(confidence_score, 0.3)

        # Length-based checks (potential DoS)
        if len(input_text) > 100000:  # 100KB limit
            violations.append(SafetyViolation.MALICIOUS_CONTENT)
            severity = SafetyLevel.HIGH
            details["excessive_length"] = len(input_text)
            confidence_score = min(confidence_score, 0.5)

        is_safe = len(violations) == 0

        if not is_safe:
            logger.warning(f"Input safety violation detected: {violations} in input from {context}")

        return SafetyResult(
            is_safe=is_safe,
            violations=violations,
            severity=severity,
            details=details,
            confidence_score=confidence_score,
        )

    def _check_pattern_matches(self, text: str, patterns: List[str]) -> List[str]:
        """Check text against a list of regex patterns."""
        matches = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(pattern)
        return matches


class OutputGuardrail:
    """
    Output filtering for AI safety.
    Detects and blocks PII, hate speech, and other harmful content.
    """

    def __init__(self):
        # PII detection patterns
        self.pii_patterns = {
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "phone": r"\b(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b",
            "ssn": r"\b\d{3}-\d{2}-\d{4}\b",  # US Social Security Number
            "cpf": r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",  # Brazilian CPF
            "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
            "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        }

        # Hate speech patterns (simplified - would use ML in production)
        self.hate_patterns = [
            r"\b(nigger|nigga)\b",
            r"\b(faggot|queer)\b",
            r"\b(chink|jap|gook)\b",
            r"\b(kike|heeb)\b",
        ]

        # Violence patterns
        self.violence_patterns = [
            r"\b(how\s+to\s+kill|murder|assassinate)\b",
            r"\b(bomb\s+making|explosives?|detonate)\b",
            r"\b(weapon|gun|knife)\s+(making|building)\b",
        ]

    async def check_output(
        self, output_text: str, context: Optional[Dict[str, Any]] = None
    ) -> SafetyResult:
        """
        Check output text for safety violations.

        Args:
            output_text: The output text to check
            context: Additional context (model used, user info, etc.)

        Returns:
            SafetyResult with violation details
        """
        violations = []
        severity = SafetyLevel.LOW
        details = {}
        confidence_score = 1.0

        # Check for PII
        pii_detected = self._detect_pii(output_text)
        if pii_detected:
            violations.append(SafetyViolation.PII_DETECTED)
            severity = SafetyLevel.HIGH
            details["pii_types"] = list(pii_detected.keys())
            confidence_score = min(confidence_score, 0.4)

        # Check for hate speech
        hate_matches = self._check_pattern_matches(output_text, self.hate_patterns)
        if hate_matches:
            violations.append(SafetyViolation.HATE_SPEECH)
            severity = SafetyLevel.CRITICAL
            details["hate_matches"] = hate_matches
            confidence_score = min(confidence_score, 0.1)

        # Check for violence content
        violence_matches = self._check_pattern_matches(output_text, self.violence_patterns)
        if violence_matches:
            violations.append(SafetyViolation.VIOLENCE_CONTENT)
            severity = SafetyLevel.HIGH
            details["violence_matches"] = violence_matches
            confidence_score = min(confidence_score, 0.3)

        is_safe = len(violations) == 0

        if not is_safe:
            logger.warning(
                f"Output safety violation detected: {violations} in output for {context}"
            )

        return SafetyResult(
            is_safe=is_safe,
            violations=violations,
            severity=severity,
            details=details,
            confidence_score=confidence_score,
        )

    def _detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect personally identifiable information."""
        pii_found = {}

        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                pii_found[pii_type] = matches

        return pii_found

    def _check_pattern_matches(self, text: str, patterns: List[str]) -> List[str]:
        """Check text against a list of regex patterns."""
        matches = []
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                matches.append(pattern)
        return matches


class AISafetyGuardrails:
    """
    Main AI Safety Guardrails system.
    Orchestrates input and output filtering for ISO 42001 compliance.
    """

    def __init__(self):
        self.input_guardrail = InputGuardrail()
        self.output_guardrail = OutputGuardrail()

    async def check_interaction(
        self,
        input_text: str,
        output_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[SafetyResult, Optional[SafetyResult]]:
        """
        Check both input and output (if provided) for safety violations.

        Args:
            input_text: User input to check
            output_text: AI output to check (optional)
            context: Additional context

        Returns:
            Tuple of (input_result, output_result)
        """
        input_result = await self.input_guardrail.check_input(input_text, context)

        output_result = None
        if output_text:
            output_result = await self.output_guardrail.check_output(output_text, context)

        return input_result, output_result

    async def is_safe_interaction(
        self,
        input_text: str,
        output_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Quick check if interaction is safe.

        Returns:
            True if both input and output (if provided) are safe
        """
        input_result, output_result = await self.check_interaction(input_text, output_text, context)

        if output_result:
            return input_result.is_safe and output_result.is_safe

        return input_result.is_safe


# Global instance
_guardrails: Optional[AISafetyGuardrails] = None


def get_ai_safety_guardrails() -> AISafetyGuardrails:
    """Get global AI safety guardrails instance."""
    global _guardrails
    if _guardrails is None:
        _guardrails = AISafetyGuardrails()
    return _guardrails
