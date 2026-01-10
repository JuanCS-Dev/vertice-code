"""
Router Stats Mixin - Statistics tracking for routing performance.
"""

from typing import Dict, Any


class RouterStatsMixin:
    """Mixin for tracking routing statistics."""

    def __init__(self) -> None:
        self._stats: Dict[str, Any] = {
            "total_routes": 0,
            "fast_path": 0,
            "llm_fallback": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_confidence": 0.0,
            "avg_processing_time_ms": 0.0,
            "errors": 0,
        }
        self._route_counts: Dict[str, int] = {}

    def record_route(
        self,
        route_name: str,
        confidence: float,
        processing_time_ms: float,
        fallback_used: bool = False,
        cache_hit: bool = False,
    ) -> None:
        """
        Record a routing operation.

        Args:
            route_name: Name of the route selected
            confidence: Confidence score
            processing_time_ms: Processing time
            fallback_used: Whether LLM fallback was used
            cache_hit: Whether result came from cache
        """
        self._stats["total_routes"] += 1

        if cache_hit:
            self._stats["cache_hits"] += 1
        else:
            self._stats["cache_misses"] += 1

        if fallback_used:
            self._stats["llm_fallback"] += 1
        else:
            self._stats["fast_path"] += 1

        # Update route counts
        self._route_counts[route_name] = self._route_counts.get(route_name, 0) + 1

        # Update averages
        self._update_averages(confidence, processing_time_ms)

    def record_error(self) -> None:
        """Record a routing error."""
        self._stats["errors"] += 1

    def _update_averages(self, confidence: float, processing_time_ms: float) -> None:
        """Update running averages."""
        total = self._stats["total_routes"]

        # Update confidence average
        current_avg_conf = self._stats["avg_confidence"]
        self._stats["avg_confidence"] = (current_avg_conf * (total - 1) + confidence) / total

        # Update processing time average
        current_avg_time = self._stats["avg_processing_time_ms"]
        self._stats["avg_processing_time_ms"] = (
            current_avg_time * (total - 1) + processing_time_ms
        ) / total

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive routing statistics."""
        stats = dict(self._stats)

        # Add route distribution
        stats["route_distribution"] = self._route_counts.copy()

        # Calculate percentages
        total = stats["total_routes"]
        if total > 0:
            stats["fast_path_percent"] = (stats["fast_path"] / total) * 100
            stats["llm_fallback_percent"] = (stats["llm_fallback"] / total) * 100
            stats["cache_hit_rate"] = (stats["cache_hits"] / total) * 100
            stats["error_rate"] = (stats["errors"] / total) * 100

        return stats

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self._stats = {
            "total_routes": 0,
            "fast_path": 0,
            "llm_fallback": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_confidence": 0.0,
            "avg_processing_time_ms": 0.0,
            "errors": 0,
        }
        self._route_counts.clear()
