"""
Context Scoring - File relevance scoring algorithms.

Multi-factor analysis for context optimization.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from .types import ContextItem, FileRelevance


class RelevanceScorer:
    """Calculate relevance scores for files and items."""

    # Scoring weights (research-optimized)
    WEIGHTS = {
        "recent_access": 0.3,
        "frequency": 0.2,
        "dependencies": 0.25,
        "semantic": 0.15,
        "user_pinned": 0.1,
    }

    def __init__(self):
        """Initialize scorer."""
        self.access_history: Dict[str, List[datetime]] = {}
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.semantic_cache: Dict[str, Set[str]] = {}
        self.user_pinned: Set[str] = set()

    def score_file_relevance(
        self,
        file_path: str,
        current_task: Optional[str] = None,
        recent_files: Optional[List[str]] = None,
    ) -> FileRelevance:
        """Score file relevance using multi-factor analysis.

        Factors (research-based):
        1. Recent access (recency bias - Cursor inspiration)
        2. Access frequency (popularity)
        3. Dependency connections (import/require analysis)
        4. Semantic similarity (keyword matching)
        5. User pinning (explicit importance)

        Args:
            file_path: Path to score.
            current_task: Current user task description.
            recent_files: Recently accessed files.

        Returns:
            FileRelevance score object.
        """
        scores = {}
        reasons = []

        # Factor 1: Recent Access (exponential decay)
        recent_score = self._score_recent_access(file_path)
        scores["recent_access"] = recent_score
        if recent_score > 0.5:
            reasons.append("Recently accessed")

        # Factor 2: Access Frequency
        freq_score = self._score_frequency(file_path)
        scores["frequency"] = freq_score
        if freq_score > 0.7:
            reasons.append("Frequently accessed")

        # Factor 3: Dependencies
        dep_score = self._score_dependencies(file_path, recent_files or [])
        scores["dependencies"] = dep_score
        if dep_score > 0.5:
            reasons.append("Connected to active files")

        # Factor 4: Semantic Similarity
        if current_task:
            semantic_score = self._score_semantic(file_path, current_task)
            scores["semantic"] = semantic_score
            if semantic_score > 0.6:
                reasons.append("Matches current task")
        else:
            scores["semantic"] = 0.0

        # Factor 5: User Pinned
        if file_path in self.user_pinned:
            scores["user_pinned"] = 1.0
            reasons.append("User pinned")
        else:
            scores["user_pinned"] = 0.0

        # Weighted sum
        final_score = sum(scores[factor] * self.WEIGHTS[factor] for factor in scores)

        return FileRelevance(
            path=file_path,
            score=final_score,
            reasons=reasons,
            last_accessed=(
                self.access_history[file_path][-1]
                if file_path in self.access_history and self.access_history[file_path]
                else None
            ),
            dependencies=self.dependency_graph.get(file_path, set()),
        )

    def calculate_item_relevance(self, item: ContextItem) -> float:
        """Calculate relevance for LRU.

        Args:
            item: Context item to score.

        Returns:
            Relevance score (0.0 to 1.0).
        """
        if item.pinned:
            return 1.0

        import time

        age = time.time() - item.last_accessed
        recency = 1.0 / (1.0 + age / 300)
        frequency = min(1.0, (item.access_count + 1) / 10)
        return 0.7 * recency + 0.3 * frequency

    def _score_recent_access(self, file_path: str) -> float:
        """Score based on recent access (exponential decay)."""
        if file_path not in self.access_history:
            return 0.0

        if not self.access_history[file_path]:
            return 0.0

        last_access = self.access_history[file_path][-1]
        time_since = (datetime.now() - last_access).total_seconds()

        # Exponential decay: e^(-t/3600) (half-life = 1 hour)
        return math.exp(-time_since / 3600)

    def _score_frequency(self, file_path: str) -> float:
        """Score based on access frequency."""
        if file_path not in self.access_history:
            return 0.0

        # Count accesses in last 24h
        cutoff = datetime.now() - timedelta(hours=24)
        recent_accesses = [t for t in self.access_history[file_path] if t > cutoff]

        # Normalize (assume max 20 accesses = 1.0)
        return min(1.0, len(recent_accesses) / 20.0)

    def _score_dependencies(self, file_path: str, recent_files: List[str]) -> float:
        """Score based on dependency connections."""
        if file_path not in self.dependency_graph:
            return 0.0

        deps = self.dependency_graph[file_path]

        # Count how many recent files are connected
        connected = sum(1 for f in recent_files if f in deps)

        return min(1.0, connected / max(1, len(recent_files)))

    def _score_semantic(self, file_path: str, task: str) -> float:
        """Score based on semantic similarity to task."""
        if file_path not in self.semantic_cache:
            return 0.0

        file_keywords = self.semantic_cache[file_path]
        task_keywords = set(re.findall(r"\w+", task.lower()))

        # Jaccard similarity
        intersection = len(file_keywords & task_keywords)
        union = len(file_keywords | task_keywords)

        return intersection / union if union > 0 else 0.0

    def record_access(self, file_path: str) -> None:
        """Record file access for scoring."""
        if file_path not in self.access_history:
            self.access_history[file_path] = []
        self.access_history[file_path].append(datetime.now())

    def set_dependencies(self, file_path: str, deps: Set[str]) -> None:
        """Set file dependencies."""
        self.dependency_graph[file_path] = deps

    def set_keywords(self, file_path: str, keywords: Set[str]) -> None:
        """Set file semantic keywords."""
        self.semantic_cache[file_path] = keywords

    def pin_file(self, file_path: str) -> None:
        """Mark file as user-pinned."""
        self.user_pinned.add(file_path)

    def unpin_file(self, file_path: str) -> None:
        """Remove user-pinned mark."""
        self.user_pinned.discard(file_path)


__all__ = ["RelevanceScorer"]
