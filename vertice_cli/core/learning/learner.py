"""
Context Learner - Behavioral adaptation from user interactions.

Implements Claude Code-style behavioral learning:
- Learn from user corrections and preferences
- Adapt responses based on patterns
- Track implicit and explicit feedback

Reference: HEROIC_IMPLEMENTATION_PLAN.md Sprint P2-MEDIUM
Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional

from .types import (
    CONFIDENCE_DELTAS,
    FeedbackType,
    LearningCategory,
    LearningRecord,
    UserPreferences,
)
from .persistence import LearningPersistence

logger = logging.getLogger(__name__)


class ContextLearner:
    """
    Learn and adapt from user interactions.

    Key principles:
    - Learn from both explicit and implicit feedback
    - Decay old learnings over time
    - Maintain confidence scores for each learning
    - Persist learnings across sessions
    """

    CONFIDENCE_THRESHOLD = 0.5
    DECAY_RATE = 0.1
    MAX_EXAMPLES = 5

    def __init__(
        self,
        persist: bool = True,
        persist_path: Optional[str] = None,
    ) -> None:
        """
        Initialize context learner.

        Args:
            persist: Whether to persist learnings to disk
            persist_path: Custom path for persistence file
        """
        self.learnings: Dict[str, LearningRecord] = {}
        self.persist = persist
        self._persistence = LearningPersistence(persist_path) if persist else None

        if self._persistence:
            self.learnings = self._persistence.load()

    def record_feedback(
        self,
        category: LearningCategory,
        key: str,
        value: Any,
        feedback_type: FeedbackType,
        example: Optional[str] = None,
    ) -> None:
        """
        Record user feedback for learning.

        Args:
            category: Learning category
            key: Specific aspect (e.g., "indentation")
            value: Learned value
            feedback_type: Type of feedback
            example: Optional example for context
        """
        learning_key = f"{category.value}:{key}"
        confidence_delta = CONFIDENCE_DELTAS.get(feedback_type, 0.1)

        if learning_key in self.learnings:
            record = self.learnings[learning_key]
            self._update_existing(record, value, confidence_delta, feedback_type, example)
        else:
            self.learnings[learning_key] = LearningRecord(
                category=category,
                key=key,
                value=value,
                confidence=abs(confidence_delta),
                feedback_type=feedback_type,
                examples=[example] if example else [],
            )

        logger.debug(
            f"[Learning] {learning_key} = {value} "
            f"(confidence: {self.learnings[learning_key].confidence:.2f})"
        )

        if self._persistence:
            self._persistence.save(self.learnings)

    def _update_existing(
        self,
        record: LearningRecord,
        value: Any,
        confidence_delta: float,
        feedback_type: FeedbackType,
        example: Optional[str],
    ) -> None:
        """Update existing learning record."""
        if record.value == value:
            record.confidence = min(1.0, record.confidence + confidence_delta)
            record.decay_factor = 1.0
        else:
            record.confidence -= abs(confidence_delta) * 0.5
            if record.confidence <= 0:
                record.value = value
                record.confidence = abs(confidence_delta)
                record.examples = []

        record.timestamp = time.time()
        record.feedback_type = feedback_type

        if example and len(record.examples) < self.MAX_EXAMPLES:
            record.examples.append(example)

    def record_correction(
        self,
        category: LearningCategory,
        original: str,
        corrected: str,
    ) -> None:
        """
        Record a user correction (most valuable feedback).

        Args:
            category: Learning category
            original: Original AI output
            corrected: User's corrected version
        """
        diff_analysis = self._analyze_diff(original, corrected)

        for key, value in diff_analysis.items():
            self.record_feedback(
                category=category,
                key=key,
                value=value,
                feedback_type=FeedbackType.CORRECTION,
                example=f"Original: {original[:50]}... -> Corrected: {corrected[:50]}...",
            )

    def _analyze_diff(self, original: str, corrected: str) -> Dict[str, Any]:
        """Analyze difference to extract learnings."""
        learnings = {}

        # Indentation
        orig_indent = self._detect_indent(original)
        corr_indent = self._detect_indent(corrected)
        if orig_indent != corr_indent:
            learnings["indentation"] = corr_indent

        # Quotes
        if original.count('"') != corrected.count('"'):
            learnings["quotes"] = "double" if '"' in corrected else "single"

        # Verbosity
        if len(corrected) < len(original) * 0.7:
            learnings["verbosity"] = "concise"
        elif len(corrected) > len(original) * 1.5:
            learnings["verbosity"] = "detailed"

        return learnings

    def _detect_indent(self, code: str) -> str:
        """Detect indentation style."""
        for line in code.split("\n"):
            if line and line[0] == " ":
                spaces = len(line) - len(line.lstrip())
                if spaces == 2:
                    return "2 spaces"
                elif spaces == 4:
                    return "4 spaces"
            elif line and line[0] == "\t":
                return "tabs"
        return "4 spaces"

    def record_tool_usage(self, tool_name: str, success: bool) -> None:
        """Record tool usage for preference learning."""
        feedback_type = FeedbackType.IMPLICIT_ACCEPT if success else FeedbackType.IMPLICIT_REJECT
        self.record_feedback(
            category=LearningCategory.TOOL_PREFERENCE,
            key=tool_name,
            value=success,
            feedback_type=feedback_type,
        )

    def record_agent_routing(
        self,
        agent_name: str,
        task_type: str,
        was_correct: bool,
    ) -> None:
        """Record agent routing decision."""
        feedback_type = (
            FeedbackType.IMPLICIT_ACCEPT if was_correct else FeedbackType.IMPLICIT_REJECT
        )
        self.record_feedback(
            category=LearningCategory.AGENT_ROUTING,
            key=task_type,
            value=agent_name if was_correct else f"not_{agent_name}",
            feedback_type=feedback_type,
        )

    def get_preferences(self) -> UserPreferences:
        """Get aggregated user preferences."""
        self._apply_decay()

        prefs = UserPreferences()

        for key, record in self.learnings.items():
            if record.confidence < self.CONFIDENCE_THRESHOLD:
                continue

            category, aspect = key.split(":", 1)

            if category == LearningCategory.CODE_STYLE.value:
                prefs.code_style[aspect] = record.value
            elif category == LearningCategory.TOOL_PREFERENCE.value:
                prefs.tool_preferences[aspect] = record.confidence
            elif category == LearningCategory.RESPONSE_FORMAT.value:
                prefs.response_format[aspect] = record.value
            elif category == LearningCategory.VERBOSITY.value:
                prefs.verbosity = record.value
            elif category == LearningCategory.LANGUAGE.value:
                prefs.language = record.value
            else:
                prefs.custom[key] = record.value

        return prefs

    def apply_learnings(self, base_prompt: str) -> str:
        """Apply learned preferences to a base prompt."""
        prefs = self.get_preferences()
        additions = []

        if prefs.code_style:
            style_str = ", ".join(f"{k}: {v}" for k, v in prefs.code_style.items())
            additions.append(f"User's code style preferences: {style_str}")

        if prefs.verbosity != "normal":
            if prefs.verbosity == "concise":
                additions.append("The user prefers concise, to-the-point responses.")
            elif prefs.verbosity == "detailed":
                additions.append("The user prefers detailed, comprehensive explanations.")

        if not additions:
            return base_prompt

        learnings_section = "\n## Learned User Preferences\n" + "\n".join(
            f"- {a}" for a in additions
        )

        return base_prompt + "\n" + learnings_section

    def _apply_decay(self) -> None:
        """Apply decay to old learnings."""
        now = time.time()
        day_seconds = 86400

        for record in self.learnings.values():
            days_old = (now - record.timestamp) / day_seconds
            if days_old > 1:
                decay = self.DECAY_RATE * days_old
                record.decay_factor = max(0.1, 1.0 - decay)
                record.confidence *= record.decay_factor

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        self._apply_decay()

        by_category: Dict[str, int] = {}
        high_confidence = 0

        for record in self.learnings.values():
            cat = record.category.value
            by_category[cat] = by_category.get(cat, 0) + 1
            if record.confidence >= self.CONFIDENCE_THRESHOLD:
                high_confidence += 1

        return {
            "total_learnings": len(self.learnings),
            "high_confidence": high_confidence,
            "by_category": by_category,
        }

    def reset(self) -> None:
        """Reset all learnings."""
        self.learnings.clear()
        if self._persistence:
            self._persistence.clear()
        logger.info("[ContextLearner] Reset all learnings")


# Singleton instance
_learner: Optional[ContextLearner] = None


def get_context_learner() -> ContextLearner:
    """Get or create the global context learner."""
    global _learner
    if _learner is None:
        _learner = ContextLearner()
    return _learner


def record_user_feedback(
    category: str,
    key: str,
    value: Any,
    feedback: str = "implicit_accept",
) -> None:
    """Convenience function to record feedback."""
    try:
        cat = LearningCategory(category)
        fb = FeedbackType(feedback)
    except ValueError:
        cat = LearningCategory.CODE_STYLE
        fb = FeedbackType.IMPLICIT_ACCEPT

    get_context_learner().record_feedback(cat, key, value, fb)


def apply_learned_preferences(prompt: str) -> str:
    """Convenience function to apply learnings to prompt."""
    return get_context_learner().apply_learnings(prompt)
