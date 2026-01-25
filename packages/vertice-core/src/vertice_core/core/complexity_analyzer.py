"""
Complexity Analyzer - Determines when to auto-invoke think tool.

Phase 9 Quality Fix: Implements Anthropic's 2025 recommendation
for agentic workflows - automatically invoke extended thinking
for complex tasks.

Source: NLU_OPTIMIZATION_PLAN.md Phase 9
"""

import re
from dataclasses import dataclass
from typing import List, Optional

from vertice_core.core.intent_classifier import Intent


@dataclass
class ComplexityAnalysis:
    """Result of complexity analysis."""

    score: float  # 0.0 to 1.0
    needs_thinking: bool
    reasons: List[str]
    suggested_think_prompt: Optional[str] = None


class ComplexityAnalyzer:
    """
    Analyzes request complexity to determine if extended thinking is needed.

    Based on Anthropic's 2025 "think" tool research:
    - Complex tasks benefit from step-by-step reasoning before action
    - Auto-invoking think increases tool call success by 2x

    Complexity indicators:
    - Multi-step operations (3+ tools expected)
    - Ambiguous requests requiring interpretation
    - Tasks with potential side effects (file deletion, git push)
    - Low intent confidence
    - Multiple files or components mentioned
    """

    # Patterns indicating multi-step complexity
    MULTI_STEP_PATTERNS = [
        # English
        (r"\b(then|after|next|also|and then)\b", 0.2),
        (r"\b(all|every|each|multiple)\b", 0.15),
        (r"\b(create|setup|implement|build)\s+\w+\s+(with|and|including)\b", 0.25),
        (r"\b(refactor|redesign|restructure)\b", 0.3),
        # Portuguese
        (r"\b(depois|apos|entao|tambem|e depois)\b", 0.2),
        (r"\b(todos|todas|cada|multiplos|varios)\b", 0.15),
        (r"\b(criar|configurar|implementar|construir)\s+\w+\s+(com|e|incluindo)\b", 0.25),
        (r"\b(refatorar|redesenhar|reestruturar)\b", 0.3),
    ]

    # Patterns indicating side effects (destructive operations)
    SIDE_EFFECT_PATTERNS = [
        # Destructive file operations - English and Portuguese
        (r"\b(delete|remove|drop|truncate|deleta|apaga|exclui)\b", 0.4),
        (r"\b(deletar|remover|apagar|excluir)\b", 0.4),
        # Git operations with push
        (r"\b(push|force|reset|rebase)\b", 0.35),
        (r"\b(pusha|forca|reseta)\b", 0.35),
        # Database operations
        (r"\b(migrate|rollback|drop\s+table)\b", 0.4),
        # Deploy operations
        (r"\b(deploy|publish|release)\b", 0.3),
        (r"\b(deployar|publicar|lancar)\b", 0.3),
    ]

    # Patterns indicating ambiguity
    AMBIGUITY_PATTERNS = [
        (r"^.{1,20}$", 0.2),  # Very short request
        (r"\b(maybe|perhaps|possibly|somehow)\b", 0.15),
        (r"\b(talvez|possivelmente|de alguma forma)\b", 0.15),
        (r"\b(best|better|good|right)\s+(way|approach|method)\b", 0.2),
        (r"\b(melhor|boa)\s+(forma|maneira|abordagem)\b", 0.2),
        (r"\?.*\?", 0.2),  # Multiple questions
    ]

    # Patterns indicating multiple targets
    MULTI_TARGET_PATTERNS = [
        (r"\.(py|js|ts|go|rs|java)\b.*\.(py|js|ts|go|rs|java)\b", 0.25),  # Multiple file extensions
        (r"\b(files|arquivos|modulos|modules)\b", 0.15),
        (r",\s*\w+\s*,", 0.1),  # Comma-separated list
        (r"\band\b.*\band\b", 0.15),  # Multiple "and"s
        (r"\be\b.*\be\b", 0.15),  # Multiple "e"s (PT)
    ]

    # Complexity thresholds
    THINK_THRESHOLD = 0.5  # Score above this triggers thinking
    HIGH_COMPLEXITY_THRESHOLD = 0.7

    def __init__(self):
        """Initialize complexity analyzer."""
        pass

    def analyze(
        self, request: str, intent: Optional[Intent] = None, confidence: float = 1.0
    ) -> ComplexityAnalysis:
        """
        Analyze request complexity.

        Args:
            request: User's natural language request
            intent: Detected intent (optional)
            confidence: Intent classification confidence

        Returns:
            ComplexityAnalysis with score and recommendations
        """
        score = 0.0
        reasons = []
        lower_request = request.lower()

        # Factor 1: Low confidence adds complexity
        if confidence < 0.7:
            conf_penalty = (0.7 - confidence) * 0.5
            score += conf_penalty
            reasons.append(f"baixa confianca / low confidence ({confidence:.0%})")

        # Factor 2: Multi-step patterns
        for pattern, weight in self.MULTI_STEP_PATTERNS:
            if re.search(pattern, lower_request, re.IGNORECASE):
                score += weight
                reasons.append(f"multi-step: '{pattern}'")
                break  # Only count once per category

        # Factor 3: Side effect patterns
        for pattern, weight in self.SIDE_EFFECT_PATTERNS:
            if re.search(pattern, lower_request, re.IGNORECASE):
                score += weight
                reasons.append(f"efeito colateral / side effect: '{pattern}'")
                break

        # Factor 4: Ambiguity patterns
        for pattern, weight in self.AMBIGUITY_PATTERNS:
            if re.search(pattern, lower_request, re.IGNORECASE):
                score += weight
                reasons.append(f"ambiguidade / ambiguity: '{pattern}'")
                break

        # Factor 5: Multiple targets
        for pattern, weight in self.MULTI_TARGET_PATTERNS:
            if re.search(pattern, lower_request, re.IGNORECASE):
                score += weight
                reasons.append("multiplos alvos / multiple targets")
                break

        # Factor 6: Intent-based complexity
        if intent:
            intent_complexity = self._get_intent_complexity(intent)
            score += intent_complexity
            if intent_complexity > 0.1:
                reasons.append(f"intent complexo / complex intent: {intent.value}")

        # Normalize score to 0-1
        score = min(1.0, score)

        # Determine if thinking is needed
        needs_thinking = score >= self.THINK_THRESHOLD

        # Generate suggested think prompt if needed
        think_prompt = None
        if needs_thinking:
            think_prompt = self._generate_think_prompt(request, reasons, intent)

        return ComplexityAnalysis(
            score=score,
            needs_thinking=needs_thinking,
            reasons=reasons,
            suggested_think_prompt=think_prompt,
        )

    def _get_intent_complexity(self, intent: Intent) -> float:
        """Get base complexity for an intent."""
        complexity_map = {
            Intent.ARCHITECTURE: 0.25,
            Intent.REFACTOR: 0.2,
            Intent.PLANNING: 0.2,
            Intent.SECURITY: 0.2,
            Intent.PERFORMANCE: 0.15,
            Intent.DEBUG: 0.15,
            Intent.CODING: 0.1,
            Intent.TEST: 0.1,
            Intent.DOCS: 0.05,
            Intent.REVIEW: 0.05,
            Intent.EXPLORE: 0.0,
            Intent.GENERAL: 0.0,
        }
        return complexity_map.get(intent, 0.0)

    def _generate_think_prompt(
        self, request: str, reasons: List[str], intent: Optional[Intent]
    ) -> str:
        """Generate a structured think prompt for the LLM."""
        intent_str = intent.value if intent else "unknown"
        reasons_str = ", ".join(reasons[:3])

        return f"""Analisando tarefa complexa / Analyzing complex task:

Requisicao / Request: "{request[:100]}..."
Intent: {intent_str}
Complexidade / Complexity: {reasons_str}

Passo a passo / Step by step:
1. Qual o objetivo final? / What's the end goal?
2. Quais ferramentas preciso? / What tools do I need?
3. Qual a ordem de execucao? / What's the execution order?
4. Quais os riscos? / What are the risks?
5. Preciso confirmar algo com o usuario? / Need to confirm anything with user?
"""


def analyze_complexity(
    request: str, intent: Optional[Intent] = None, confidence: float = 1.0
) -> ComplexityAnalysis:
    """Convenience function for complexity analysis."""
    analyzer = ComplexityAnalyzer()
    return analyzer.analyze(request, intent, confidence)
