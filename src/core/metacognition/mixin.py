"""
MetaCognitive Mixin

Mixin providing metacognitive reflection capabilities to agents.

Reference:
- Microsoft Metacognition Research (2025)
- Reflexion (Shinn et al., 2023)
- MetaAgent (arXiv:2508.00271v2)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    ReflectionOutcome,
    ReasoningStep,
    ReflectionResult,
    StrategyProfile,
)
from .engine import ReflectionEngine
from .memory import ExperienceMemory

logger = logging.getLogger(__name__)


class MetaCognitiveMixin:
    """
    Mixin providing metacognitive reflection capabilities.

    Add to any agent for:
    - Self-reflection during task execution
    - Learning from experience
    - Strategy adaptation
    - Confidence calibration

    Implements patterns from:
    - Reflexion (Shinn et al., 2023)
    - MetaAgent (2025)
    - Microsoft Metacognition Research
    """

    def _init_metacognition(self) -> None:
        """Initialize metacognitive systems."""
        self._reflection_engine = ReflectionEngine()
        self._experience_memory = ExperienceMemory()
        self._strategy_profiles: Dict[str, StrategyProfile] = {}
        self._current_strategy: Optional[str] = None
        self._metacognition_initialized = True

        logger.info("[MetaCognition] Initialized")

    def begin_reflection(self, task_description: str) -> None:
        """Begin a new reflection session for a task."""
        if not hasattr(self, "_reflection_engine"):
            self._init_metacognition()

        self._reflection_engine.clear_chain()
        self._current_task = task_description

        # Check for relevant lessons
        task_type = self._classify_task_type(task_description)
        lessons = self._experience_memory.get_relevant_lessons(task_type)

        if lessons:
            logger.info(f"[MetaCognition] Applying {len(lessons)} lessons from experience")
            self._active_lessons = lessons
        else:
            self._active_lessons = []

    def record_reasoning(
        self,
        step_description: str,
        confidence: float,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
    ) -> ReasoningStep:
        """Record a reasoning step."""
        if not hasattr(self, "_reflection_engine"):
            self._init_metacognition()

        return self._reflection_engine.add_reasoning_step(
            description=step_description,
            input_state=input_data or {},
            output_state=output_data or {},
            confidence=confidence,
        )

    def reflect(self) -> ReflectionResult:
        """Perform reflection on current reasoning."""
        if not hasattr(self, "_reflection_engine"):
            self._init_metacognition()

        return self._reflection_engine.reflect_on_chain()

    def should_continue(self, threshold: float = 0.4) -> Tuple[bool, str]:
        """
        Determine if execution should continue based on reflection.

        Returns:
            Tuple of (should_continue, reason)
        """
        result = self.reflect()

        if result.outcome == ReflectionOutcome.ABORT:
            return False, "Reflection suggests aborting: " + result.reasoning

        if result.confidence < threshold:
            return False, f"Confidence ({result.confidence:.2f}) below threshold ({threshold})"

        return True, "Proceeding with execution"

    def learn_from_outcome(
        self,
        success: bool,
        lessons: Optional[List[str]] = None,
    ) -> None:
        """Record outcome and learn from the experience."""
        if not hasattr(self, "_experience_memory"):
            self._init_metacognition()

        task_type = self._classify_task_type(getattr(self, "_current_task", "unknown"))

        # Get confidence before/after from reflection history
        history = self._reflection_engine._reflection_history
        conf_before = history[0].confidence if history else 0.5
        conf_after = history[-1].confidence if history else 0.5

        # Record the experience
        self._experience_memory.record_experience(
            task_type=task_type,
            strategy_used=self._current_strategy or "default",
            outcome="success" if success else "failure",
            confidence_before=conf_before,
            confidence_after=conf_after,
            lessons_learned=lessons or [],
        )

        # Update calibration
        self._reflection_engine._calibrator.record_outcome(conf_after, success)

    def get_strategy_suggestion(
        self,
        task_description: str,
    ) -> Optional[str]:
        """Get strategy suggestion for a task."""
        if not hasattr(self, "_experience_memory"):
            self._init_metacognition()

        task_type = self._classify_task_type(task_description)
        return self._experience_memory.suggest_strategy(task_type, {})

    def set_current_strategy(self, strategy: str) -> None:
        """Set the current strategy being used."""
        self._current_strategy = strategy

    def register_strategy(
        self,
        strategy_id: str,
        name: str,
        description: str,
        applicable_contexts: Optional[List[str]] = None,
        contraindications: Optional[List[str]] = None,
    ) -> StrategyProfile:
        """Register a strategy profile."""
        if not hasattr(self, "_strategy_profiles"):
            self._strategy_profiles = {}

        profile = StrategyProfile(
            id=strategy_id,
            name=name,
            description=description,
            success_rate=0.5,  # Initial neutral rate
            applicable_contexts=applicable_contexts or [],
            contraindications=contraindications or [],
            avg_confidence=0.5,
        )

        self._strategy_profiles[strategy_id] = profile
        return profile

    def _classify_task_type(self, description: str) -> str:
        """Classify a task into a type category."""
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in ["code", "implement", "fix", "bug"]):
            return "coding"
        if any(kw in desc_lower for kw in ["analyze", "review", "audit"]):
            return "analysis"
        if any(kw in desc_lower for kw in ["design", "architect", "plan"]):
            return "design"
        if any(kw in desc_lower for kw in ["test", "verify", "validate"]):
            return "testing"
        if any(kw in desc_lower for kw in ["refactor", "improve", "optimize"]):
            return "refactoring"

        return "general"

    def get_metacognition_status(self) -> Dict[str, Any]:
        """Get metacognition system status."""
        if not hasattr(self, "_reflection_engine"):
            return {"initialized": False}

        return {
            "initialized": True,
            "chain_summary": self._reflection_engine.get_chain_summary(),
            "calibration_stats": self._reflection_engine._calibrator.get_calibration_stats(),
            "memory_stats": self._experience_memory.get_memory_stats(),
            "registered_strategies": list(self._strategy_profiles.keys()),
            "current_strategy": self._current_strategy,
            "active_lessons": getattr(self, "_active_lessons", []),
        }
