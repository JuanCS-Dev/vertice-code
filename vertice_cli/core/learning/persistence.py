"""
Learning Persistence - Save and load learned behaviors.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional

from .types import FeedbackType, LearningCategory, LearningRecord

logger = logging.getLogger(__name__)

DEFAULT_PERSISTENCE_PATH = ".vertice/context_learnings.json"


class LearningPersistence:
    """
    Persistence layer for context learnings.

    Saves and loads learnings to/from JSON file.
    """

    def __init__(self, path: Optional[str] = None) -> None:
        """
        Initialize persistence layer.

        Args:
            path: Path to persistence file (default: .vertice/context_learnings.json)
        """
        self.path = Path(path or DEFAULT_PERSISTENCE_PATH)

    def load(self) -> Dict[str, LearningRecord]:
        """
        Load learnings from persistence file.

        Returns:
            Dictionary of learning records keyed by category:key
        """
        if not self.path.exists():
            return {}

        try:
            with open(self.path, "r") as f:
                data = json.load(f)

            learnings: Dict[str, LearningRecord] = {}
            for key, record_data in data.items():
                learnings[key] = LearningRecord(
                    category=LearningCategory(record_data["category"]),
                    key=record_data["key"],
                    value=record_data["value"],
                    confidence=record_data["confidence"],
                    feedback_type=FeedbackType(record_data["feedback_type"]),
                    timestamp=record_data.get("timestamp", time.time()),
                    examples=record_data.get("examples", []),
                    decay_factor=record_data.get("decay_factor", 1.0),
                )

            logger.info(f"[LearningPersistence] Loaded {len(learnings)} learnings")
            return learnings

        except Exception as e:
            logger.warning(f"[LearningPersistence] Failed to load: {e}")
            return {}

    def save(self, learnings: Dict[str, LearningRecord]) -> bool:
        """
        Save learnings to persistence file.

        Args:
            learnings: Dictionary of learning records

        Returns:
            True if save succeeded
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)

        try:
            data = {}
            for key, record in learnings.items():
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

            with open(self.path, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"[LearningPersistence] Saved {len(learnings)} learnings")
            return True

        except Exception as e:
            logger.warning(f"[LearningPersistence] Failed to save: {e}")
            return False

    def clear(self) -> bool:
        """
        Clear persistence file.

        Returns:
            True if clear succeeded
        """
        try:
            if self.path.exists():
                self.path.unlink()
            return True
        except Exception as e:
            logger.warning(f"[LearningPersistence] Failed to clear: {e}")
            return False
