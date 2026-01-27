"""
NEXUS Meta-Agent - Main Orchestrator

The apex of the Vertice agent ecosystem - a self-evolving intelligence
powered by Gemini 3 Pro that manages all other agents.

Core Capabilities:
- Intrinsic Metacognition (thinking about thinking)
- Self-Healing Infrastructure
- Evolutionary Code Optimization
- Hierarchical Memory (1M tokens)

Model: gemini-3-pro-preview
SDK: google-genai >= 1.51.0
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from nexus.config import NexusConfig
from nexus.types import (
    EvolutionaryCandidate,
    MemoryLevel,
    MetacognitiveInsight,
    NexusStatus,
    SystemState,
)
from nexus.memory import HierarchicalMemory
from nexus.metacognitive import MetacognitiveEngine
from nexus.healing import SelfHealingOrchestrator
from nexus.evolution import EvolutionaryCodeOptimizer
from nexus.mcp_integration import NexusMCPIntegration
from nexus.prometheus_bridge import PrometheusBridge
from nexus.alloydb import AlloyDBStore
from nexus.nervous_system import DigitalNervousSystem

logger = logging.getLogger(__name__)


class NexusMetaAgent:
    """
    NEXUS: Neural Evolutionary eXtended Understanding System

    The self-evolving meta-agent that orchestrates the entire
    Vertice agent ecosystem. Powered by Gemini 3 Pro.
    """

    def __init__(self, config: Optional[NexusConfig] = None):
        self.config = config or NexusConfig.from_env()
        self._start_time: Optional[float] = None
        self._active = False

        # Core components
        self.memory = HierarchicalMemory(self.config)
        self.metacognitive = MetacognitiveEngine(self.config)
        self.healing = SelfHealingOrchestrator(self.config)
        self.evolution = EvolutionaryCodeOptimizer(self.config)

        # MCP Integration (connects to Vertice collective)
        self.mcp = NexusMCPIntegration(self.config)

        # Prometheus Bridge (collaboration with Prometheus meta-agent)
        self.prometheus = PrometheusBridge(self.config)

        # AlloyDB Persistent Store (GCloud infrastructure)
        self.alloydb = AlloyDBStore(self.config)

        # Digital Nervous System (Eventarc homeostatic infrastructure)
        self.nervous_system = DigitalNervousSystem(self.config)

        # System state
        self.state = SystemState()

        # Background task handles
        self._tasks: List[asyncio.Task] = []

        logger.info(
            f"🧬 NEXUS Meta-Agent initialized\n"
            f"   Model: {self.config.model}\n"
            f"   Thinking Level: {self.config.default_thinking_level}\n"
            f"   Context Window: {self.config.context_window:,} tokens\n"
            f"   MCP Integration: Enabled\n"
            f"   Prometheus Bridge: Available\n"
            f"   AlloyDB Store: {self.config.project_id}/{os.getenv('ALLOYDB_CLUSTER', 'vertice-memory-cluster')}\n"
            f"   Nervous System: Bio-inspired homeostasis"
        )

    async def start(self) -> None:
        """Start NEXUS autonomous operation."""
        if self._active:
            logger.warning("NEXUS already active")
            return

        self._active = True
        self._start_time = time.time()

        logger.info("=" * 60)
        logger.info("🧬 NEXUS Meta-Agent Starting")
        logger.info("=" * 60)

        # Connect to MCP collective
        mcp_connected = await self.mcp.connect()
        if mcp_connected:
            # Register NEXUS skill with the collective
            await self.mcp.register_nexus_skill()
            logger.info("📡 Connected to Vertice MCP collective")
        else:
            logger.warning("⚠️ Running in standalone mode (MCP not available)")

        # Connect to Prometheus meta-agent
        prometheus_connected = await self.prometheus.connect()
        if prometheus_connected:
            logger.info("🔥 Connected to Prometheus meta-agent")
        else:
            logger.warning("⚠️ Prometheus bridge inactive")

        # Initialize AlloyDB persistent store
        alloydb_initialized = await self.alloydb.initialize()
        if alloydb_initialized:
            # Load state from AlloyDB
            saved_state = await self.alloydb.load_latest_state()
            if saved_state:
                self.state = saved_state
                logger.info("🗄️ Restored state from AlloyDB")
            logger.info("🐘 AlloyDB persistent store active")
        else:
            logger.warning("⚠️ AlloyDB not available, using in-memory storage")

        # Load persistent memory from Firestore (fallback)
        await self.memory.load_from_firestore()

        # Connect Nervous System to NEXUS components
        self.nervous_system.set_nexus_components(
            metacognitive=self.metacognitive,
            prometheus_bridge=self.prometheus,
            alloydb_store=self.alloydb,
        )
        logger.info("🧠 Nervous System connected to NEXUS brain")

        # Start background loops
        self._tasks = [
            asyncio.create_task(self._reflection_loop()),
            asyncio.create_task(self._evolution_loop()),
            asyncio.create_task(self._mcp_sync_loop()),
        ]

        # Start healing monitoring
        asyncio.create_task(self.healing.start_monitoring())

        logger.info("✅ NEXUS operational")

    async def stop(self) -> None:
        """Stop NEXUS gracefully."""
        logger.info("🛑 NEXUS shutting down...")
        self._active = False

        # Disconnect from MCP
        await self.mcp.disconnect()

        # Disconnect from Prometheus
        await self.prometheus.disconnect()

        # Save state and close AlloyDB
        if self.alloydb._initialized:
            await self.alloydb.save_state(self.state)
            await self.alloydb.close()
            logger.info("AlloyDB state saved and connections closed")

        # Stop healing
        await self.healing.stop_monitoring()

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._tasks.clear()
        logger.info("NEXUS shutdown complete")

    async def _reflection_loop(self) -> None:
        """Continuous metacognitive reflection loop."""
        logger.info("🧠 Metacognitive engine active")

        while self._active:
            try:
                await asyncio.sleep(self.config.reflection_interval_seconds)

                if not self._active:
                    break

                logger.info("💭 Running reflection cycle...")

                # Identify improvement opportunities
                opportunities = await self.metacognitive.identify_improvement_opportunities()

                if opportunities:
                    logger.info(f"📈 Found {len(opportunities)} improvement opportunities")

                    # Store insights in memory
                    for opp in opportunities[:3]:
                        await self.memory.store(
                            content=f"Improvement opportunity: {opp}",
                            level=MemoryLevel.L3_SEMANTIC,
                            importance=opp.get("priority", 0.5),
                        )

                self.state.last_reflection = datetime.now(timezone.utc)
                self.state.total_insights = len(self.metacognitive._local_insights)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Reflection error: {e}")

    async def _evolution_loop(self) -> None:
        """Periodic evolutionary optimization loop."""
        logger.info("🧬 Evolutionary optimizer standby")

        # Evolution runs less frequently
        evolution_interval = self.config.reflection_interval_seconds * 24  # Daily

        while self._active:
            try:
                await asyncio.sleep(evolution_interval)

                if not self._active:
                    break

                # Check if evolution is warranted based on insights
                opportunities = await self.metacognitive.identify_improvement_opportunities()
                optimization_candidates = [
                    o
                    for o in opportunities
                    if o.get("category") in {"optimization", "performance", "capability_gap"}
                ]

                if optimization_candidates:
                    logger.info(
                        f"🔬 Starting evolution cycle for {len(optimization_candidates)} candidates"
                    )

                    for candidate in optimization_candidates[:1]:  # One at a time
                        goals = candidate.get("learnings", ["performance", "quality"])

                        best = await self.evolution.evolve(
                            target=f"optimization_{candidate.get('category', 'general')}",
                            goals=goals if isinstance(goals, list) else [str(goals)],
                            generations=30,
                        )

                        self.state.evolutionary_generation += 1
                        self.state.total_optimizations += 1

                        # Store result in memory
                        await self.memory.store_procedure(
                            procedure_name=f"evolved_{best.candidate_id}",
                            steps=["Evolution complete", f"Fitness: {best.aggregate_fitness}"],
                            success_rate=best.aggregate_fitness,
                        )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Evolution error: {e}")

    async def _mcp_sync_loop(self) -> None:
        """Sync with MCP collective periodically."""
        if not self.mcp.is_connected:
            logger.info("📡 MCP sync loop inactive (not connected)")
            return

        logger.info("📡 MCP sync loop active")
        sync_interval = 300  # 5 minutes

        while self._active:
            try:
                await asyncio.sleep(sync_interval)

                if not self._active:
                    break

                # Monitor agent health from collective
                agent_health = await self.mcp.monitor_agent_health()
                if agent_health:
                    self.state.agent_health.update(agent_health)

                # Share high-confidence insights with collective
                recent_insights = await self.metacognitive.get_recent_insights(
                    limit=5, min_confidence=0.85
                )
                for insight in recent_insights:
                    if not insight.applied:
                        await self.mcp.share_insight(insight)
                        insight.applied = True

                # Share successful healings
                healing_history = await self.healing.get_healing_history(limit=10)
                for record in healing_history:
                    if record.success:
                        await self.mcp.share_healing_procedure(record)

                logger.debug(f"MCP sync complete: {len(agent_health)} agents monitored")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"MCP sync error: {e}")

    async def reflect(
        self,
        task: Dict[str, Any],
        outcome: Dict[str, Any],
    ) -> MetacognitiveInsight:
        """
        Trigger metacognitive reflection on a task outcome.

        This is the main entry point for external systems to
        provide feedback to NEXUS.
        """
        # Store task context in working memory
        await self.memory.store(
            content=f"Task: {task}\nOutcome: {outcome}",
            level=MemoryLevel.L1_WORKING,
            importance=0.8 if outcome.get("success") else 0.9,
        )

        # Reflect
        insight = await self.metacognitive.reflect_on_task_outcome(
            task=task,
            outcome=outcome,
            system_state=self.state,
        )

        self.state.total_insights += 1

        # Store high-confidence insights in semantic memory
        if insight.confidence >= self.config.insight_confidence_threshold:
            await self.memory.store(
                content=f"INSIGHT: {insight.learning}\nACTION: {insight.action}",
                level=MemoryLevel.L3_SEMANTIC,
                importance=insight.confidence,
            )

        return insight

    async def evolve_code(
        self,
        target: str,
        goals: List[str],
        seed_code: Optional[str] = None,
        generations: int = 30,
    ) -> EvolutionaryCandidate:
        """
        Trigger evolutionary code optimization.

        Args:
            target: What to optimize
            goals: Optimization objectives
            seed_code: Optional starting code
            generations: Number of generations

        Returns:
            Best evolved candidate
        """
        result = await self.evolution.evolve(
            target=target,
            goals=goals,
            seed_code=seed_code,
            generations=generations,
        )

        self.state.evolutionary_generation += 1
        self.state.total_optimizations += 1

        return result

    async def get_status(self) -> NexusStatus:
        """Get current NEXUS status."""
        memory_stats = await self.memory.get_stats()

        return NexusStatus(
            active=self._active,
            model=self.config.model,
            thinking_level=self.config.default_thinking_level,
            system_state=self.state,
            total_insights=self.state.total_insights,
            total_healings=self.state.total_healings,
            total_evolutions=self.state.total_optimizations,
            memory_usage={
                level: stats.get("tokens", 0)
                for level, stats in memory_stats.get("by_level", {}).items()
            },
            last_reflection=(
                self.state.last_reflection.isoformat() if self.state.last_reflection else None
            ),
            uptime_seconds=(time.time() - self._start_time if self._start_time else 0.0),
        )

    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all components."""
        return {
            "nexus": {
                "active": self._active,
                "uptime_seconds": time.time() - self._start_time if self._start_time else 0,
                "model": self.config.model,
                "thinking_level": self.config.default_thinking_level,
            },
            "system_state": self.state.to_dict(),
            "memory": await self.memory.get_stats(),
            "metacognitive": self.metacognitive.get_stats(),
            "healing": self.healing.get_stats(),
            "evolution": self.evolution.get_stats(),
        }

    async def store_memory(
        self,
        content: str,
        level: str,
        importance: float = 0.5,
    ) -> Dict[str, Any]:
        """Store content in hierarchical memory."""
        level_enum = MemoryLevel(level)
        block = await self.memory.store(
            content=content,
            level=level_enum,
            importance=importance,
        )
        return block.to_dict()

    async def retrieve_memories(
        self,
        level: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Retrieve memories from a specific level."""
        level_enum = MemoryLevel(level)
        blocks = await self.memory.retrieve(level_enum, limit=limit)
        return [b.to_dict() for b in blocks]

    async def build_context(
        self,
        query: Optional[str] = None,
        max_tokens: int = 100_000,
    ) -> str:
        """Build context prompt from hierarchical memory."""
        memories = await self.memory.retrieve_all_levels(query=query)
        return self.memory.build_context_prompt(memories, max_tokens=max_tokens)


# Singleton instance for the gateway
_nexus_instance: Optional[NexusMetaAgent] = None


def get_nexus() -> NexusMetaAgent:
    """Get or create the NEXUS singleton instance."""
    global _nexus_instance
    if _nexus_instance is None:
        _nexus_instance = NexusMetaAgent()
    return _nexus_instance


async def initialize_nexus() -> NexusMetaAgent:
    """Initialize and start NEXUS."""
    nexus = get_nexus()
    if not nexus._active:
        await nexus.start()
    return nexus
