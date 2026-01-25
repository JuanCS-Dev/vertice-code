"""
Context Compactor - Main compaction engine.

Orchestrates different compaction strategies and manages compaction lifecycle.
"""

import logging
import time
from typing import Dict, List, Optional, TYPE_CHECKING

from .types import CompactionResult

from .strategies import (
    CompactionStrategy_ABC,
    HierarchicalStrategy,
    LLMSummaryStrategy,
    ObservationMaskingStrategy,
)
from .types import CompactionConfig, CompactionStrategy

if TYPE_CHECKING:
    from ..context import UnifiedContext

logger = logging.getLogger(__name__)


class ContextCompactor:
    """
    Main context compaction engine.

    Manages compaction strategies and applies them based on context state.
    """

    def __init__(self, context: "UnifiedContext", config: Optional[CompactionConfig] = None):
        """
        Initialize compactor.

        Args:
            context: Context to compact
            config: Compaction configuration
        """
        self.context = context
        self.config = config or CompactionConfig()
        self._strategies: Dict[CompactionStrategy, CompactionStrategy_ABC] = {
            CompactionStrategy.OBSERVATION_MASKING: ObservationMaskingStrategy(),
            CompactionStrategy.HIERARCHICAL: HierarchicalStrategy(),
            CompactionStrategy.LLM_SUMMARY: LLMSummaryStrategy(),
        }
        self._compaction_history: List[CompactionResult] = []

    def auto_compact(self) -> Optional[CompactionResult]:
        """
        Automatically compact if needed based on thresholds.

        Returns:
            Compaction result if compaction was performed, None otherwise
        """
        if not self._should_compact():
            return None

        # Try default strategy first
        result = self.compact(strategy=self.config.default_strategy)

        # If failed and we have fallback, try fallback
        if not result.success and self.config.fallback_strategy != self.config.default_strategy:
            logger.warning(
                f"Default strategy failed, trying fallback: {self.config.fallback_strategy}"
            )
            result = self.compact(strategy=self.config.fallback_strategy, force=True)

        if result.success:
            self._compaction_history.append(result)
            logger.info(f"Auto-compaction completed: {result.compression_ratio:.2f}x compression")

        return result

    def compact(self, strategy: CompactionStrategy, force: bool = False) -> CompactionResult:
        """
        Compact context using specified strategy.

        Args:
            strategy: Compaction strategy to use
            force: Force compaction even if below threshold

        Returns:
            Compaction result
        """
        if not force and not self._should_compact():
            return CompactionResult(
                success=False,
                strategy_used=strategy,
                tokens_before=self.context._token_usage,
                tokens_after=self.context._token_usage,
                compression_ratio=1.0,
                duration_ms=0.0,
                messages_removed=0,
                error="Threshold not met",
            )

        strategy_impl = self._strategies.get(strategy)
        if not strategy_impl:
            return CompactionResult(
                success=False,
                strategy_used=strategy,
                tokens_before=self.context._token_usage,
                tokens_after=self.context._token_usage,
                compression_ratio=1.0,
                duration_ms=0.0,
                messages_removed=0,
                error=f"Strategy {strategy} not implemented",
            )

        try:
            result = strategy_impl.compact(self.context, self.config)
            if result.success:
                logger.info(
                    f"Compaction successful: {strategy.value}, {result.compression_ratio:.2f}x"
                )
            else:
                logger.warning(f"Compaction failed: {strategy.value}, {result.error}")
            return result

        except Exception as e:
            logger.error(f"Compaction error in {strategy.value}: {e}")
            return CompactionResult(
                success=False,
                strategy_used=strategy,
                tokens_before=self.context._token_usage,
                tokens_after=self.context._token_usage,
                compression_ratio=1.0,
                duration_ms=time.time() * 1000,  # Rough estimate
                messages_removed=0,
                error=str(e),
            )

    def _should_compact(self) -> bool:
        """Check if context should be compacted based on thresholds."""
        usage_ratio = self.context._token_usage / self.context.max_tokens
        return usage_ratio >= self.config.trigger_threshold

    def get_stats(self) -> Dict:
        """Get compaction statistics."""
        total_compactions = len(self._compaction_history)
        if not total_compactions:
            return {"total_compactions": 0}

        avg_compression = (
            sum(r.compression_ratio for r in self._compaction_history) / total_compactions
        )
        total_tokens_saved = sum(r.tokens_saved for r in self._compaction_history)
        total_messages_removed = sum(r.messages_removed for r in self._compaction_history)

        return {
            "total_compactions": total_compactions,
            "average_compression_ratio": avg_compression,
            "total_tokens_saved": total_tokens_saved,
            "total_messages_removed": total_messages_removed,
            "recent_compactions": [
                {
                    "strategy": r.strategy_used.value,
                    "compression_ratio": r.compression_ratio,
                    "tokens_saved": r.tokens_saved,
                    "duration_ms": r.duration_ms,
                }
                for r in self._compaction_history[-5:]  # Last 5
            ],
        }


__all__ = ["ContextCompactor"]
