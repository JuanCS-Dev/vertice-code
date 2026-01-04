"""
Context Awareness Engine - Intelligent context management.

Research-driven context optimization with smart suggestions.
"""

from __future__ import annotations

import re
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich.console import Console
from rich.panel import Panel

from .types import (
    ContentType,
    ContextItem,
    ContextWindow,
    FileRelevance,
    OptimizationMetrics,
)
from .scoring import RelevanceScorer
from .rendering import render_context_panel, render_token_usage_realtime


class ContextAwarenessEngine:
    """Intelligent context management system.

    Features (Research-Driven):
    - File relevance scoring (Cursor/Cody algorithms)
    - Auto-optimization (removes low-value context)
    - Dependency tracking (includes related files)
    - Smart suggestions (predicts needed files)
    - Token budget management

    Constitutional Alignment:
    - P6 (Efficiency): Minimizes token waste
    - P3 (Skepticism): Questions every context addition
    - P2 (Validation): Validates relevance before adding
    """

    def __init__(
        self,
        max_context_tokens: int = 100_000,
        console: Optional[Console] = None,
    ):
        """Initialize context awareness engine.

        Args:
            max_context_tokens: Maximum tokens for context window.
            console: Optional Rich console for output.
        """
        self.max_context_tokens = max_context_tokens
        self.console = console or Console()

        # Context tracking
        self.window = ContextWindow(total_tokens=0, max_tokens=max_context_tokens)

        # LRU tracking
        self.items: Dict[str, ContextItem] = {}
        self.optimizations_performed = 0
        self.total_tokens_freed = 0

        # Thresholds
        self.warning_threshold = 0.8
        self.critical_threshold = 0.9

        # Scoring
        self.scorer = RelevanceScorer()

        # Access tracking
        self.access_history: Dict[str, List[datetime]] = defaultdict(list)
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.semantic_cache: Dict[str, Set[str]] = {}

    def score_file_relevance(
        self,
        file_path: str,
        current_task: Optional[str] = None,
        recent_files: Optional[List[str]] = None,
    ) -> FileRelevance:
        """Score file relevance using multi-factor analysis.

        Args:
            file_path: Path to score.
            current_task: Current user task description.
            recent_files: Recently accessed files.

        Returns:
            FileRelevance score object.
        """
        # Sync state to scorer
        self.scorer.access_history = self.access_history
        self.scorer.dependency_graph = self.dependency_graph
        self.scorer.semantic_cache = self.semantic_cache
        self.scorer.user_pinned = self.window.user_pinned

        relevance = self.scorer.score_file_relevance(file_path, current_task, recent_files)
        relevance.token_count = self._estimate_tokens(file_path)
        return relevance

    def optimize_context(
        self,
        target_utilization: float = 0.8,
        preserve_pinned: bool = True,
    ) -> Dict[str, Any]:
        """Auto-optimize context window.

        Removes low-relevance files to stay within target utilization.

        Args:
            target_utilization: Target context utilization (0.0-1.0).
            preserve_pinned: Keep user-pinned files.

        Returns:
            Optimization report.
        """
        if self.window.utilization <= target_utilization:
            return {
                "action": "none",
                "reason": "Context utilization acceptable",
                "removed": [],
            }

        # Score all files
        scored_files = [(path, self.score_file_relevance(path)) for path in self.window.files]

        # Sort by score (ascending - remove lowest first)
        scored_files.sort(key=lambda x: x[1].score)

        removed = []
        target_tokens = int(self.max_context_tokens * target_utilization)

        for path, relevance in scored_files:
            # Stop if target reached
            if self.window.total_tokens <= target_tokens:
                break

            # Skip pinned files
            if preserve_pinned and path in self.window.user_pinned:
                continue

            # Remove file
            if path in self.window.files:
                del self.window.files[path]
                self.window.total_tokens -= relevance.token_count
                self.window.auto_added.discard(path)
                removed.append((path, relevance.score))

        return {
            "action": "optimized",
            "removed": removed,
            "tokens_freed": sum(r[1] for r in removed),
            "new_utilization": self.window.utilization,
        }

    def suggest_context(
        self,
        current_task: str,
        max_suggestions: int = 5,
    ) -> List[FileRelevance]:
        """Suggest relevant files for current task.

        Args:
            current_task: User's current task description.
            max_suggestions: Maximum suggestions to return.

        Returns:
            List of FileRelevance objects (sorted by score).
        """
        candidate_files = self._get_candidate_files()

        suggestions = []
        for file_path in candidate_files:
            if file_path not in self.window.files:
                relevance = self.score_file_relevance(
                    file_path,
                    current_task=current_task,
                    recent_files=list(self.window.files.keys()),
                )
                if relevance.is_relevant:
                    suggestions.append(relevance)

        suggestions.sort(key=lambda x: x.score, reverse=True)
        return suggestions[:max_suggestions]

    def add_file_to_context(
        self,
        file_path: str,
        pinned: bool = False,
        auto_include_deps: bool = True,
    ) -> bool:
        """Add file to context window.

        Args:
            file_path: File to add.
            pinned: Mark as user-pinned.
            auto_include_deps: Automatically include dependencies.

        Returns:
            Success status.
        """
        if not Path(file_path).exists():
            return False

        token_count = self._estimate_tokens(file_path)

        if token_count > self.window.available_tokens:
            self.optimize_context(target_utilization=0.7)
            if token_count > self.window.available_tokens:
                return False

        relevance = self.score_file_relevance(file_path)
        relevance.token_count = token_count

        self.window.files[file_path] = relevance
        self.window.total_tokens += token_count

        if pinned:
            self.window.user_pinned.add(file_path)
        else:
            self.window.auto_added.add(file_path)

        self.access_history[file_path].append(datetime.now())

        if auto_include_deps:
            deps = self._extract_dependencies(file_path)
            self.dependency_graph[file_path] = deps

            for dep in deps:
                if dep not in self.window.files and Path(dep).exists():
                    dep_tokens = self._estimate_tokens(dep)
                    if dep_tokens <= self.window.available_tokens:
                        self.add_file_to_context(dep, pinned=False, auto_include_deps=False)

        return True

    def render_context_panel(self) -> Panel:
        """Render context awareness panel.

        Returns:
            Rich Panel with context information.
        """
        return render_context_panel(self.window, self.max_context_tokens)

    def render_token_usage_realtime(self) -> Panel:
        """Render real-time token usage panel.

        Returns:
            Rich Panel with token usage.
        """
        return render_token_usage_realtime(self.window)

    def update_streaming_tokens(self, delta: int) -> None:
        """Update streaming token counter.

        Args:
            delta: Token count delta.
        """
        self.window.streaming_tokens = max(0, self.window.streaming_tokens + delta)

    def finalize_streaming_session(
        self,
        final_input_tokens: int,
        final_output_tokens: int,
        cost_estimate: float = 0.0,
    ) -> None:
        """Finalize streaming session and record snapshot.

        Args:
            final_input_tokens: Total input tokens.
            final_output_tokens: Total output tokens.
            cost_estimate: Estimated cost in USD.
        """
        self.window.streaming_tokens = 0
        self.window.add_token_snapshot(
            input_tokens=final_input_tokens,
            output_tokens=final_output_tokens,
            cost_estimate=cost_estimate,
        )

    def add_item(
        self,
        item_id: str,
        content: str,
        content_type: ContentType,
        token_count: int,
        pinned: bool = False,
    ) -> bool:
        """Add item with LRU tracking.

        Args:
            item_id: Unique item identifier.
            content: Item content.
            content_type: Type of content.
            token_count: Token count for item.
            pinned: Whether item is pinned.

        Returns:
            Success status.
        """
        if self.window.total_tokens + token_count > self.max_context_tokens:
            if not pinned:
                self.auto_optimize(tokens_needed=token_count)

        if self.window.total_tokens + token_count > self.max_context_tokens:
            return False

        if item_id in self.items:
            old_item = self.items[item_id]
            self.window.total_tokens -= old_item.token_count

        item = ContextItem(
            id=item_id,
            content=content,
            content_type=content_type,
            token_count=token_count,
            timestamp=time.time(),
            pinned=pinned,
        )
        self.items[item_id] = item
        self.window.total_tokens += token_count
        return True

    def auto_optimize(
        self,
        tokens_needed: int = 0,
        target_usage: float = 0.7,
    ) -> OptimizationMetrics:
        """Auto-optimize using LRU.

        Args:
            tokens_needed: Tokens needed for new content.
            target_usage: Target usage ratio.

        Returns:
            Optimization metrics.
        """
        start = time.time()
        items_before = len(self.items)
        tokens_before = self.window.total_tokens

        target_tokens = int(self.max_context_tokens * target_usage) - tokens_needed

        scored = [
            (self.scorer.calculate_item_relevance(item), item)
            for item in self.items.values()
            if not item.pinned
        ]
        scored.sort(key=lambda x: x[0])

        removed: List[str] = []
        freed = 0

        for _, item in scored:
            if self.window.total_tokens <= target_tokens:
                break
            removed.append(item.id)
            freed += item.token_count
            self.window.total_tokens -= item.token_count

        for rid in removed:
            self.items.pop(rid, None)

        self.optimizations_performed += 1
        self.total_tokens_freed += freed

        return OptimizationMetrics(
            items_before=items_before,
            items_after=len(self.items),
            tokens_before=tokens_before,
            tokens_after=self.window.total_tokens,
            items_removed=len(removed),
            tokens_freed=freed,
            duration_ms=(time.time() - start) * 1000,
        )

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get optimization statistics.

        Returns:
            Statistics dictionary.
        """
        return {
            "total_items": len(self.items),
            "total_tokens": self.window.total_tokens,
            "max_tokens": self.max_context_tokens,
            "usage_percent": self.window.utilization * 100,
            "pinned_items": sum(1 for i in self.items.values() if i.pinned),
            "optimizations_performed": self.optimizations_performed,
            "total_tokens_freed": self.total_tokens_freed,
        }

    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations.

        Returns:
            List of recommendation strings.
        """
        recs: List[str] = []
        usage = self.window.utilization * 100
        if usage >= 90:
            recs.append("CRITICAL: Context >90% full")
        elif usage >= 80:
            recs.append("WARNING: Context >80% full")
        return recs

    def _estimate_tokens(self, file_path: str) -> int:
        """Estimate token count for file."""
        try:
            with open(file_path, "r") as f:
                content = f.read()
                return len(content) // 4
        except (FileNotFoundError, PermissionError, IOError):
            return 0

    def _extract_dependencies(self, file_path: str) -> Set[str]:
        """Extract file dependencies (imports, requires)."""
        deps = set()
        try:
            with open(file_path, "r") as f:
                content = f.read()

                for match in re.finditer(r"from\s+(\S+)\s+import", content):
                    deps.add(match.group(1).replace(".", "/") + ".py")

                for match in re.finditer(r"import\s+(\S+)", content):
                    deps.add(match.group(1).replace(".", "/") + ".py")

        except (FileNotFoundError, PermissionError, IOError):
            pass

        return deps

    def _extract_keywords(self, file_path: str) -> Set[str]:
        """Extract semantic keywords from file."""
        keywords = set()
        try:
            with open(file_path, "r") as f:
                content = f.read()
                for match in re.finditer(r"(?:def|class)\s+(\w+)", content):
                    keywords.add(match.group(1).lower())
        except (FileNotFoundError, PermissionError, IOError):
            pass
        return keywords

    def _get_candidate_files(self) -> List[str]:
        """Get candidate files for suggestions."""
        return []


__all__ = ["ContextAwarenessEngine"]
