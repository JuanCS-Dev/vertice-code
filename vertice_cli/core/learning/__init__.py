"""
Learning Package - Context learning and behavioral adaptation.

Exports:
- ContextLearner: Main learning class
- Types: FeedbackType, LearningCategory, UserPreferences
- Helpers: get_context_learner, record_user_feedback

Reference: HEROIC_IMPLEMENTATION_PLAN.md
Follows CODE_CONSTITUTION: Modular, <500 lines per file
"""

from .types import (
    CONFIDENCE_DELTAS,
    FeedbackType,
    LearningCategory,
    LearningRecord,
    UserPreferences,
)

from .persistence import (
    LearningPersistence,
)

from .learner import (
    ContextLearner,
    apply_learned_preferences,
    get_context_learner,
    record_user_feedback,
)

__all__ = [
    # Types
    "FeedbackType",
    "LearningCategory",
    "LearningRecord",
    "UserPreferences",
    "CONFIDENCE_DELTAS",
    # Persistence
    "LearningPersistence",
    # Learner
    "ContextLearner",
    "get_context_learner",
    "record_user_feedback",
    "apply_learned_preferences",
]
