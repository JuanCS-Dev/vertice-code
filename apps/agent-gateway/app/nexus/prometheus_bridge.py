"""
NEXUS ↔ PROMETHEUS Bridge

Enables collaboration between the two meta-agents:
- NEXUS: Metacognition, Self-Healing, Evolutionary Optimization (Gemini 3 Pro)
- PROMETHEUS: World Model, 6-Type Memory, Reflection, Tool Factory

Together they form a more powerful autonomous system:
- NEXUS provides high-level metacognitive oversight and healing
- PROMETHEUS provides simulation, memory, and tool generation
- They share insights, learnings, and coordinate evolution

Synergy:
┌─────────────────────────────────────────────────────────────────┐
│                  META-AGENT COLLABORATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐                      ┌─────────────────┐     │
│   │   NEXUS     │ ◄───────────────────►│   PROMETHEUS    │     │
│   │             │   Insight Sharing     │                 │     │
│   │ • Metacog   │   Memory Sync        │ • World Model   │     │
│   │ • Healing   │   Evolution Coord    │ • 6-Type Memory │     │
│   │ • Evolution │   Task Delegation    │ • Reflection    │     │
│   │             │                      │ • Tool Factory  │     │
│   │ Gemini 3 Pro│                      │ • AutoTools     │     │
│   └─────────────┘                      └─────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from nexus.config import NexusConfig
from nexus.types import MetacognitiveInsight, EvolutionaryCandidate

logger = logging.getLogger(__name__)

# Try to import Prometheus components
PROMETHEUS_AVAILABLE = False
PrometheusProvider = None
PrometheusConfig = None

try:
    # Add vertice-core to path
    _core_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    _packages_path = os.path.join(_core_path, "packages", "vertice-core", "src")
    if _packages_path not in sys.path:
        sys.path.insert(0, _packages_path)

    from vertice_core.providers.prometheus_provider import (
        PrometheusProvider,
        PrometheusConfig,
    )

    PROMETHEUS_AVAILABLE = True
    logger.info("Prometheus provider available for NEXUS bridge")
except ImportError as e:
    logger.warning(f"Prometheus provider not available: {e}")


class PrometheusBridge:
    """
    Bridge for NEXUS ↔ PROMETHEUS collaboration.

    Enables the two meta-agents to work together:
    - Share insights and learnings bidirectionally
    - Coordinate evolution cycles
    - Delegate tasks based on capabilities
    - Sync memory systems
    """

    def __init__(self, nexus_config: NexusConfig):
        self.nexus_config = nexus_config
        self._prometheus: Optional[Any] = None
        self._connected = False
        self._sync_count = 0

    async def connect(self) -> bool:
        """Initialize connection to Prometheus."""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus not available, bridge inactive")
            return False

        try:
            config = PrometheusConfig(
                enable_world_model=True,
                enable_memory=True,
                enable_reflection=True,
                enable_evolution=False,  # NEXUS handles evolution
            )
            self._prometheus = PrometheusProvider(config)
            await self._prometheus._ensure_initialized()
            self._connected = True
            logger.info("✅ NEXUS ↔ PROMETHEUS bridge connected")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Prometheus: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from Prometheus."""
        self._prometheus = None
        self._connected = False
        logger.info("NEXUS ↔ PROMETHEUS bridge disconnected")

    @property
    def is_connected(self) -> bool:
        return self._connected and self._prometheus is not None

    # =========================================================================
    # WORLD MODEL INTEGRATION
    # =========================================================================

    async def simulate_action(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Use Prometheus World Model to simulate an action before execution.

        NEXUS uses this for:
        - Pre-healing simulation (predict if fix will work)
        - Evolution candidate testing (simulate code changes)
        - Risk assessment before autonomous actions
        """
        if not self.is_connected:
            return {"error": "Prometheus not connected", "simulated": False}

        try:
            orchestrator = self._prometheus._orchestrator
            if orchestrator and hasattr(orchestrator, "world_model"):
                result = await orchestrator.world_model.simulate(action, context or {})
                return {
                    "simulated": True,
                    "predicted_outcome": result.get("predicted_outcome", "Unknown"),
                    "risks": result.get("risks", []),
                    "confidence": result.get("confidence", 0.5),
                    "alternatives": result.get("alternatives", []),
                }
            else:
                # Fallback: use generate with simulation prompt
                prompt = f"""Simulate the following action and predict outcomes:

ACTION: {action}
CONTEXT: {context or 'No additional context'}

Analyze:
1. What will happen if this action is executed?
2. What are the potential risks or side effects?
3. What is the confidence level (0-1)?
4. Are there safer alternatives?

Respond in structured format."""

                response = await self._prometheus.generate(prompt)
                return {
                    "simulated": True,
                    "raw_response": response,
                    "confidence": 0.7,
                }

        except Exception as e:
            logger.warning(f"World model simulation failed: {e}")
            return {"error": str(e), "simulated": False}

    # =========================================================================
    # MEMORY SYSTEM INTEGRATION
    # =========================================================================

    async def query_prometheus_memory(
        self,
        query: str,
        memory_type: str = "all",
    ) -> Dict[str, Any]:
        """
        Query Prometheus 6-type memory system (MIRIX).

        NEXUS uses this for:
        - Finding past solutions to similar problems
        - Retrieving procedural knowledge for healing
        - Accessing episodic memories for pattern analysis
        """
        if not self.is_connected:
            return {"error": "Prometheus not connected"}

        try:
            context = self._prometheus.get_memory_context(query)
            return {
                "query": query,
                "memory_type": memory_type,
                "results": context,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as e:
            logger.warning(f"Memory query failed: {e}")
            return {"error": str(e)}

    async def sync_memories(
        self,
        nexus_insights: List[MetacognitiveInsight],
    ) -> Dict[str, Any]:
        """
        Sync NEXUS insights to Prometheus memory.

        Converts NEXUS metacognitive insights into Prometheus episodic/semantic memories.
        """
        if not self.is_connected:
            return {"synced": 0, "error": "Not connected"}

        synced = 0
        try:
            orchestrator = self._prometheus._orchestrator
            if orchestrator and hasattr(orchestrator, "memory"):
                for insight in nexus_insights:
                    # Store as episodic memory
                    episode = {
                        "source": "nexus_metacognitive",
                        "observation": insight.observation,
                        "analysis": insight.causal_analysis,
                        "learning": insight.learning,
                        "action": insight.action,
                        "confidence": insight.confidence,
                        "category": insight.category.value,
                        "timestamp": insight.timestamp.isoformat(),
                    }
                    orchestrator.memory.store_episode(episode)

                    # Also store as semantic knowledge if high confidence
                    if insight.confidence >= 0.8:
                        orchestrator.memory.learn_fact(
                            topic=f"nexus_insight_{insight.category.value}",
                            content=f"{insight.learning} → {insight.action}",
                        )

                    synced += 1

            self._sync_count += synced
            logger.info(f"Synced {synced} insights to Prometheus memory")

        except Exception as e:
            logger.warning(f"Memory sync failed: {e}")
            return {"synced": synced, "error": str(e)}

        return {"synced": synced, "total_syncs": self._sync_count}

    # =========================================================================
    # REFLECTION INTEGRATION
    # =========================================================================

    async def request_reflection(
        self,
        task: str,
        outcome: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Request Prometheus reflection on a task outcome.

        NEXUS combines this with its own metacognitive analysis for
        deeper insights.
        """
        if not self.is_connected:
            return {"error": "Prometheus not connected"}

        try:
            orchestrator = self._prometheus._orchestrator
            if orchestrator and hasattr(orchestrator, "reflection"):
                result = await orchestrator.reflection.reflect(task, outcome, context or {})
                return {
                    "quality_score": result.get("quality_score", 0),
                    "improvements": result.get("improvements", []),
                    "lessons_learned": result.get("lessons_learned", []),
                    "source": "prometheus_reflection",
                }
            else:
                # Fallback
                prompt = f"""Reflect on this task execution:

TASK: {task}
OUTCOME: {outcome}

Analyze:
1. What worked well?
2. What could be improved?
3. What lessons should be learned?
4. Quality score (0-10)?"""

                response = await self._prometheus.generate(prompt)
                return {
                    "raw_reflection": response,
                    "source": "prometheus_generate",
                }

        except Exception as e:
            logger.warning(f"Reflection request failed: {e}")
            return {"error": str(e)}

    # =========================================================================
    # TOOL FACTORY INTEGRATION
    # =========================================================================

    async def request_tool_creation(
        self,
        description: str,
        requirements: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Request Prometheus to create a new tool dynamically.

        NEXUS uses this when:
        - Healing requires a custom tool
        - Evolution identifies a missing capability
        - Optimization needs specialized functionality
        """
        if not self.is_connected:
            return {"error": "Prometheus not connected", "created": False}

        try:
            orchestrator = self._prometheus._orchestrator
            if orchestrator and hasattr(orchestrator, "tool_factory"):
                tool = await orchestrator.tool_factory.create_tool(
                    description=description,
                    requirements=requirements or [],
                )
                return {
                    "created": True,
                    "tool_name": tool.name if hasattr(tool, "name") else "dynamic_tool",
                    "description": description,
                }
            else:
                # Fallback: generate tool code
                prompt = f"""Create a Python tool for the following purpose:

DESCRIPTION: {description}
REQUIREMENTS: {requirements or 'None specified'}

Generate:
1. Function name and signature
2. Implementation
3. Docstring
4. Example usage

Output as valid Python code."""

                code = await self._prometheus.generate(prompt)
                return {
                    "created": True,
                    "tool_code": code,
                    "description": description,
                }

        except Exception as e:
            logger.warning(f"Tool creation failed: {e}")
            return {"error": str(e), "created": False}

    # =========================================================================
    # COORDINATED EVOLUTION
    # =========================================================================

    async def coordinate_evolution(
        self,
        nexus_candidate: EvolutionaryCandidate,
    ) -> Dict[str, Any]:
        """
        Coordinate evolution between NEXUS and Prometheus.

        NEXUS handles genetic algorithm evolution.
        Prometheus validates via world model simulation.
        """
        if not self.is_connected:
            return {"validated": False, "error": "Not connected"}

        try:
            # Simulate the evolved code using Prometheus world model
            simulation = await self.simulate_action(
                action=f"Execute evolved code:\n{nexus_candidate.code[:1000]}",
                context={
                    "fitness": nexus_candidate.fitness_scores,
                    "generation": nexus_candidate.generation,
                },
            )

            # Request reflection on the evolution
            reflection = await self.request_reflection(
                task="Evaluate evolved code candidate",
                outcome={
                    "code_preview": nexus_candidate.code[:500],
                    "fitness": nexus_candidate.aggregate_fitness,
                    "simulation": simulation,
                },
            )

            return {
                "validated": simulation.get("confidence", 0) > 0.6,
                "simulation": simulation,
                "reflection": reflection,
                "recommendation": (
                    "Deploy"
                    if simulation.get("confidence", 0) > 0.8
                    else "Test further"
                    if simulation.get("confidence", 0) > 0.5
                    else "Reject"
                ),
            }

        except Exception as e:
            logger.warning(f"Evolution coordination failed: {e}")
            return {"validated": False, "error": str(e)}

    # =========================================================================
    # TASK DELEGATION
    # =========================================================================

    async def delegate_to_prometheus(
        self,
        task: str,
        use_world_model: bool = True,
        use_memory: bool = True,
    ) -> Dict[str, Any]:
        """
        Delegate a task to Prometheus for execution.

        Used when NEXUS determines a task is better suited for
        Prometheus capabilities (world model simulation, tool creation, etc.)
        """
        if not self.is_connected:
            return {"error": "Prometheus not connected", "executed": False}

        try:
            # Configure Prometheus for the task
            self._prometheus.config.enable_world_model = use_world_model
            self._prometheus.config.enable_memory = use_memory

            # Execute via Prometheus
            result = await self._prometheus.generate(task)

            return {
                "executed": True,
                "result": result,
                "executor": "prometheus",
                "world_model_used": use_world_model,
                "memory_used": use_memory,
            }

        except Exception as e:
            logger.warning(f"Prometheus delegation failed: {e}")
            return {"executed": False, "error": str(e)}

    # =========================================================================
    # STATUS & STATS
    # =========================================================================

    async def get_prometheus_status(self) -> Dict[str, Any]:
        """Get Prometheus system status."""
        if not self.is_connected:
            return {
                "connected": False,
                "available": PROMETHEUS_AVAILABLE,
            }

        try:
            orchestrator = self._prometheus._orchestrator

            status = {
                "connected": True,
                "available": PROMETHEUS_AVAILABLE,
                "sync_count": self._sync_count,
            }

            # Get subsystem status if available
            if orchestrator:
                if hasattr(orchestrator, "memory"):
                    status["memory_active"] = True
                if hasattr(orchestrator, "world_model"):
                    status["world_model_active"] = True
                if hasattr(orchestrator, "reflection"):
                    status["reflection_active"] = True
                if hasattr(orchestrator, "evolution"):
                    status["evolution_active"] = True
                if hasattr(orchestrator, "tool_factory"):
                    status["tool_factory_active"] = True

            return status

        except Exception as e:
            return {"connected": False, "error": str(e)}

    def get_stats(self) -> Dict[str, Any]:
        """Get bridge statistics."""
        return {
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "connected": self._connected,
            "sync_count": self._sync_count,
        }
