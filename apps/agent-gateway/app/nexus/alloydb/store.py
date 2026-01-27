"""
AlloyDB Store - Combined Interface.

Aggregates all AlloyDB operations into a single class using mixins.
"""

from __future__ import annotations

from nexus.config import NexusConfig
from nexus.alloydb.base import AlloyDBBase
from nexus.alloydb.memories import MemoryOperations
from nexus.alloydb.insights import InsightOperations
from nexus.alloydb.evolution import EvolutionOperations
from nexus.alloydb.state import StateOperations


class AlloyDBStore(
    AlloyDBBase,
    MemoryOperations,
    InsightOperations,
    EvolutionOperations,
    StateOperations,
):
    """
    AlloyDB-backed persistent store for NEXUS Meta-Agent.

    Combines all operations through mixins:
    - MemoryOperations: Store and search memories
    - InsightOperations: Store and search insights
    - EvolutionOperations: Evolution candidates
    - StateOperations: System state and healing records
    """

    def __init__(self, config: NexusConfig):
        """Initialize AlloyDB store."""
        super().__init__(config)
