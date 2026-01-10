"""
Compaction Strategy Base - Abstract base class for compaction strategies.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_core.agents.compaction.types import CompactionConfig, CompactionResult
    from vertice_core.agents.context import UnifiedContext


class CompactionStrategy_ABC(ABC):
    """Base class for compaction strategies."""

    @abstractmethod
    def compact(
        self,
        context: "UnifiedContext",
        config: "CompactionConfig",
    ) -> "CompactionResult":
        """Compact the context."""
        pass
