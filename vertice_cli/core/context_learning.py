"""
Context Learning - Behavioral adaptation from user interactions.

Implements Claude Code-style behavioral learning:
- Learn from user corrections and preferences
- Adapt responses based on patterns
- Track implicit and explicit feedback
- Persist learned behaviors across sessions

Reference: HEROIC_IMPLEMENTATION_PLAN.md Sprint P2-MEDIUM
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of user feedback."""
    EXPLICIT_POSITIVE = "explicit_positive"     # User explicitly approves
    EXPLICIT_NEGATIVE = "explicit_negative"     # User explicitly rejects
    IMPLICIT_ACCEPT = "implicit_accept"         # User proceeds without change
    IMPLICIT_REJECT = "implicit_reject"         # User modifies before proceeding
    CORRECTION = "correction"                   # User corrects AI output
    PREFERENCE = "preference"                   # User states a preference


class LearningCategory(str, Enum):
    """Categories of learned behaviors."""
    CODE_STYLE = "code_style"
    TOOL_PREFERENCE = "tool_preference"
    RESPONSE_FORMAT = "response_format"
    LANGUAGE = "language"
    VERBOSITY = "verbosity"
    AGENT_ROUTING = "agent_routing"
    ERROR_HANDLING = "error_handling"


@dataclass
class LearningRecord:
    """Record of a learned behavior."""
    category: LearningCategory
    key: str
    value: Any
    confidence: float
    feedback_type: FeedbackType
    timestamp: float = field(default_factory=time.time)
    examples: List[str] = field(default_factory=list)
    decay_factor: float = 1.0


@dataclass
class UserPreferences:
    """Aggregated user preferences."""
    code_style: Dict[str, Any] = field(default_factory=dict)
    tool_preferences: Dict[str, float] = field(default_factory=dict)
    response_format: Dict[str, Any] = field(default_factory=dict)
    language: str = "en"
    verbosity: str = "normal"  # minimal, normal, verbose
    custom: Dict[str, Any] = field(default_factory=dict)


class ContextLearner:
    """
    Learn and adapt from user interactions.

    Key principles:
    - Learn from both explicit and implicit feedback
    - Decay old learnings over time
    - Maintain confidence scores for each learning
    - Persist learnings across sessions

    Usage:
        learner = ContextLearner()

        # Record user feedback
        learner.record_feedback(
            category=LearningCategory.CODE_STYLE,
            key="indentation",
            value="4 spaces",
            feedback_type=FeedbackType.CORRECTION
        )

        # Get learned preferences
        prefs = learner.get_preferences()
        print(prefs.code_style)  # {"indentation": "4 spaces"}

        # Apply to prompt
        enhanced_prompt = learner.apply_learnings(base_prompt)
    """

    # Configuration
    CONFIDENCE_THRESHOLD = 0.5      # Minimum confidence to apply learning
    DECAY_RATE = 0.1               # Decay per day of inactivity
    MAX_EXAMPLES = 5                # Max examples per learning
    PERSISTENCE_FILE = ".vertice/context_learnings.json"

    def __init__(self, persist: bool = True, persist_path: Optional[str] = None):
        """
        Initialize context learner.

        Args:
            persist: Whether to persist learnings to disk
            persist_path: Custom path for persistence file
        """
        self.learnings: Dict[str, LearningRecord] = {}
        self.persist = persist
        self.persist_path = persist_path or self.PERSISTENCE_FILE
        self._load_learnings()

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
            key: Specific aspect (e.g., "indentation", "verbosity")
            value: Learned value
            feedback_type: Type of feedback
            example: Optional example for context
        """
        learning_key = f"{category.value}:{key}"

        # Calculate confidence based on feedback type
        confidence_delta = self._get_confidence_delta(feedback_type)

        if learning_key in self.learnings:
            # Update existing learning
            record = self.learnings[learning_key]

            if record.value == value:
                # Same value - reinforce
                record.confidence = min(1.0, record.confidence + confidence_delta)
                record.decay_factor = 1.0  # Reset decay
            else:
                # Different value - reduce confidence or replace
                record.confidence -= abs(confidence_delta) * 0.5
                if record.confidence <= 0:
                    # Replace with new learning
                    record.value = value
                    record.confidence = abs(confidence_delta)
                    record.examples = []

            record.timestamp = time.time()
            record.feedback_type = feedback_type

            if example and len(record.examples) < self.MAX_EXAMPLES:
                record.examples.append(example)

        else:
            # New learning
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

        if self.persist:
            self._save_learnings()

    def _get_confidence_delta(self, feedback_type: FeedbackType) -> float:
        """Get confidence change based on feedback type."""
        deltas = {
            FeedbackType.EXPLICIT_POSITIVE: 0.3,
            FeedbackType.EXPLICIT_NEGATIVE: -0.3,
            FeedbackType.IMPLICIT_ACCEPT: 0.1,
            FeedbackType.IMPLICIT_REJECT: -0.1,
            FeedbackType.CORRECTION: 0.4,
            FeedbackType.PREFERENCE: 0.5,
        }
        return deltas.get(feedback_type, 0.1)

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
        # Analyze the difference
        diff_analysis = self._analyze_diff(original, corrected)

        for key, value in diff_analysis.items():
            self.record_feedback(
                category=category,
                key=key,
                value=value,
                feedback_type=FeedbackType.CORRECTION,
                example=f"Original: {original[:50]}... -> Corrected: {corrected[:50]}..."
            )

    def _analyze_diff(self, original: str, corrected: str) -> Dict[str, Any]:
        """Analyze difference between original and corrected to extract learnings."""
        learnings = {}

        # Check indentation preference
        orig_indent = self._detect_indent(original)
        corr_indent = self._detect_indent(corrected)
        if orig_indent != corr_indent:
            learnings["indentation"] = corr_indent

        # Check quote preference
        orig_quotes = "double" if '"' in original else "single"
        corr_quotes = "double" if '"' in corrected else "single"
        if orig_quotes != corr_quotes and corrected.count("'") != corrected.count('"'):
            learnings["quotes"] = corr_quotes

        # Check line length preference
        orig_max_line = max(len(line) for line in original.split("\n")) if original else 0
        corr_max_line = max(len(line) for line in corrected.split("\n")) if corrected else 0
        if abs(orig_max_line - corr_max_line) > 20:
            learnings["max_line_length"] = corr_max_line

        # Check verbosity
        if len(corrected) < len(original) * 0.7:
            learnings["verbosity"] = "concise"
        elif len(corrected) > len(original) * 1.5:
            learnings["verbosity"] = "detailed"

        return learnings

    def _detect_indent(self, code: str) -> str:
        """Detect indentation style from code."""
        lines = code.split("\n")
        for line in lines:
            if line and line[0] == " ":
                # Count leading spaces
                spaces = len(line) - len(line.lstrip())
                if spaces == 2:
                    return "2 spaces"
                elif spaces == 4:
                    return "4 spaces"
            elif line and line[0] == "\t":
                return "tabs"
        return "4 spaces"  # Default

    def record_tool_usage(self, tool_name: str, success: bool) -> None:
        """
        Record tool usage for preference learning.

        Args:
            tool_name: Name of the tool used
            success: Whether the tool execution was successful
        """
        feedback_type = (
            FeedbackType.IMPLICIT_ACCEPT if success
            else FeedbackType.IMPLICIT_REJECT
        )

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
        """
        Record agent routing decision for learning.

        Args:
            agent_name: Agent that was selected
            task_type: Type of task
            was_correct: Whether the routing was correct
        """
        feedback_type = (
            FeedbackType.IMPLICIT_ACCEPT if was_correct
            else FeedbackType.IMPLICIT_REJECT
        )

        self.record_feedback(
            category=LearningCategory.AGENT_ROUTING,
            key=task_type,
            value=agent_name if was_correct else f"not_{agent_name}",
            feedback_type=feedback_type,
        )

    def get_preferences(self) -> UserPreferences:
        """
        Get aggregated user preferences from learnings.

        Returns:
            UserPreferences with learned behaviors
        """
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
        """
        Apply learned preferences to a base prompt.

        Args:
            base_prompt: Original system prompt

        Returns:
            Enhanced prompt with learned preferences
        """
        prefs = self.get_preferences()

        additions = []

        # Code style preferences
        if prefs.code_style:
            style_str = ", ".join(f"{k}: {v}" for k, v in prefs.code_style.items())
            additions.append(f"User's code style preferences: {style_str}")

        # Verbosity preference
        if prefs.verbosity != "normal":
            if prefs.verbosity == "concise":
                additions.append("The user prefers concise, to-the-point responses.")
            elif prefs.verbosity == "detailed":
                additions.append("The user prefers detailed, comprehensive explanations.")

        # Response format
        if prefs.response_format:
            format_str = ", ".join(f"{k}: {v}" for k, v in prefs.response_format.items())
            additions.append(f"Response format preferences: {format_str}")

        if not additions:
            return base_prompt

        learnings_section = "\n## Learned User Preferences\n" + "\n".join(f"- {a}" for a in additions)

        return base_prompt + "\n" + learnings_section

    def get_tool_recommendation(self, task_description: str) -> Optional[str]:
        """
        Get recommended tool based on learned preferences.

        Args:
            task_description: Description of the task

        Returns:
            Recommended tool name or None
        """
        prefs = self.get_preferences()

        if not prefs.tool_preferences:
            return None

        # Return highest confidence tool
        sorted_tools = sorted(
            prefs.tool_preferences.items(),
            key=lambda x: x[1],
            reverse=True
        )

        if sorted_tools and sorted_tools[0][1] >= self.CONFIDENCE_THRESHOLD:
            return sorted_tools[0][0]

        return None

    def get_routing_suggestion(self, task_type: str) -> Optional[str]:
        """
        Get agent routing suggestion based on learned preferences.

        Args:
            task_type: Type of task

        Returns:
            Suggested agent name or None
        """
        key = f"{LearningCategory.AGENT_ROUTING.value}:{task_type}"

        if key in self.learnings:
            record = self.learnings[key]
            if record.confidence >= self.CONFIDENCE_THRESHOLD:
                value = record.value
                if not value.startswith("not_"):
                    return value

        return None

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

    def _load_learnings(self) -> None:
        """Load learnings from persistence file."""
        if not self.persist:
            return

        path = Path(self.persist_path)
        if not path.exists():
            return

        try:
            with open(path, "r") as f:
                data = json.load(f)

            for key, record_data in data.items():
                self.learnings[key] = LearningRecord(
                    category=LearningCategory(record_data["category"]),
                    key=record_data["key"],
                    value=record_data["value"],
                    confidence=record_data["confidence"],
                    feedback_type=FeedbackType(record_data["feedback_type"]),
                    timestamp=record_data.get("timestamp", time.time()),
                    examples=record_data.get("examples", []),
                    decay_factor=record_data.get("decay_factor", 1.0),
                )

            logger.info(f"[ContextLearner] Loaded {len(self.learnings)} learnings")

        except Exception as e:
            logger.warning(f"[ContextLearner] Failed to load learnings: {e}")

    def _save_learnings(self) -> None:
        """Save learnings to persistence file."""
        if not self.persist:
            return

        path = Path(self.persist_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = {}
            for key, record in self.learnings.items():
                data[key] = {
                    "category": record.category.value,
                    "key": record.key,
                    "value": record.value,
                    "confidence": record.confidence,
                    "feedback_type": record.feedback_type.value,
                    "timestamp": record.timestamp,
                    "examples": record.examples,
                    "decay_factor": record.decay_factor,
                }

            with open(path, "w") as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.warning(f"[ContextLearner] Failed to save learnings: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics."""
        self._apply_decay()

        by_category: Dict[str, int] = {}
        high_confidence = 0
        low_confidence = 0

        for record in self.learnings.values():
            cat = record.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            if record.confidence >= self.CONFIDENCE_THRESHOLD:
                high_confidence += 1
            else:
                low_confidence += 1

        return {
            "total_learnings": len(self.learnings),
            "high_confidence": high_confidence,
            "low_confidence": low_confidence,
            "by_category": by_category,
        }

    def get_report(self) -> str:
        """Generate a learning report."""
        stats = self.get_stats()
        prefs = self.get_preferences()

        lines = [
            "=" * 50,
            "CONTEXT LEARNING REPORT",
            "=" * 50,
            "",
            f"Total Learnings: {stats['total_learnings']}",
            f"High Confidence: {stats['high_confidence']}",
            f"Low Confidence: {stats['low_confidence']}",
            "",
            "By Category:",
        ]

        for cat, count in stats["by_category"].items():
            lines.append(f"  {cat}: {count}")

        if prefs.code_style:
            lines.append("")
            lines.append("Learned Code Style:")
            for k, v in prefs.code_style.items():
                lines.append(f"  {k}: {v}")

        if prefs.verbosity != "normal":
            lines.append("")
            lines.append(f"Verbosity Preference: {prefs.verbosity}")

        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all learnings."""
        self.learnings.clear()
        if self.persist:
            path = Path(self.persist_path)
            if path.exists():
                path.unlink()
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
