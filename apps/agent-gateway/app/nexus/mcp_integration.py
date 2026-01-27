"""
NEXUS MCP Integration

Integrates NEXUS Meta-Agent with the Vertice MCP (Multi-Agent Collective Platform).

Capabilities:
- Register NEXUS as a skill in the collective
- Monitor and receive tasks from other agents
- Share learned insights and procedures
- Coordinate with other agents for healing/optimization
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from nexus.config import NexusConfig
from nexus.types import MetacognitiveInsight, HealingRecord, EvolutionaryCandidate

logger = logging.getLogger(__name__)

# Import MCP SDK types
try:
    import sys
    from pathlib import Path

    # Add SDK to path if needed
    _sdk_path = Path(__file__).resolve().parents[4] / "sdk" / "python"
    if str(_sdk_path) not in sys.path:
        sys.path.insert(0, str(_sdk_path))

    from vertice_mcp.client import AsyncMCPClient
    from vertice_mcp.types import MCPClientConfig, AgentTask, Skill

    MCP_SDK_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MCP SDK not available: {e}")
    MCP_SDK_AVAILABLE = False

    # Stub classes for when SDK not available
    class MCPClientConfig:
        def __init__(self, endpoint: str = "", api_key: str = "", timeout: float = 30.0):
            self.endpoint = endpoint
            self.api_key = api_key
            self.timeout = timeout

    class AsyncMCPClient:
        def __init__(self, config):
            self.config = config

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

    class AgentTask:
        def __init__(self, id: str = "", description: str = "", agent_role: str = ""):
            self.id = id
            self.description = description
            self.agent_role = agent_role

    class Skill:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


class NexusMCPIntegration:
    """
    MCP Integration layer for NEXUS Meta-Agent.

    Connects NEXUS to the Vertice collective for:
    - Task coordination
    - Skill sharing
    - Agent monitoring
    - Ecosystem-wide optimization
    """

    def __init__(
        self,
        nexus_config: NexusConfig,
        mcp_endpoint: Optional[str] = None,
        mcp_api_key: Optional[str] = None,
    ):
        self.nexus_config = nexus_config
        self._mcp_client: Optional[AsyncMCPClient] = None
        self._connected = False
        self._task_handlers: Dict[str, Any] = {}

        # MCP Configuration
        self.mcp_config = MCPClientConfig(
            endpoint=mcp_endpoint or os.getenv("MCP_ENDPOINT", "https://mcp.vertice.ai"),
            api_key=mcp_api_key or os.getenv("MCP_API_KEY"),
            timeout=30.0,
        )

        logger.info(f"NEXUS MCP Integration initialized (endpoint: {self.mcp_config.endpoint})")

    async def connect(self) -> bool:
        """Connect to the MCP collective."""
        if not MCP_SDK_AVAILABLE:
            logger.warning("MCP SDK not available, running in standalone mode")
            return False

        try:
            self._mcp_client = AsyncMCPClient(self.mcp_config)
            await self._mcp_client.__aenter__()
            self._connected = True
            logger.info("✅ Connected to MCP collective")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MCP: {e}")
            self._connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from MCP collective."""
        if self._mcp_client:
            try:
                await self._mcp_client.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error disconnecting from MCP: {e}")
            self._mcp_client = None
        self._connected = False
        logger.info("Disconnected from MCP collective")

    async def register_nexus_skill(self) -> bool:
        """Register NEXUS as a skill in the MCP collective."""
        if not self._connected or not self._mcp_client:
            logger.warning("Not connected to MCP, skipping registration")
            return False

        nexus_skill = Skill(
            name="nexus_meta_agent",
            description="Self-evolving meta-cognitive agent powered by Gemini 3 Pro for ecosystem optimization",
            procedure_steps=[
                "Monitor all agents and tasks in the collective",
                "Perform metacognitive reflection on system performance",
                "Identify improvement opportunities using causal analysis",
                "Autonomously heal system issues and anomalies",
                "Evolve agent code via LLM-guided genetic algorithms",
                "Deploy optimizations to production",
                "Learn and adapt continuously from outcomes",
            ],
            category="meta-cognitive",
            success_rate=0.95,
            usage_count=0,
            metadata={
                "capabilities": [
                    "intrinsic_metacognition",
                    "self_healing",
                    "evolutionary_optimization",
                    "hierarchical_memory_1M",
                    "autonomous_learning",
                ],
                "powered_by": "gemini-3-pro-preview",
                "thinking_level": self.nexus_config.default_thinking_level,
                "context_window": self.nexus_config.context_window,
                "autonomous": True,
                "self_improving": True,
                "version": "2026.1.0",
            },
        )

        try:
            success = await self._mcp_client.share_skill(nexus_skill)
            if success:
                logger.info("✅ NEXUS registered with MCP collective")
            else:
                logger.warning("NEXUS registration returned false")
            return success
        except Exception as e:
            logger.error(f"Failed to register NEXUS skill: {e}")
            return False

    async def share_insight(self, insight: MetacognitiveInsight) -> bool:
        """Share a metacognitive insight with the collective."""
        if not self._connected or not self._mcp_client:
            return False

        try:
            # Convert insight to skill for sharing
            insight_skill = Skill(
                name=f"nexus_insight_{insight.insight_id}",
                description=insight.learning,
                procedure_steps=[
                    f"Observation: {insight.observation}",
                    f"Analysis: {insight.causal_analysis}",
                    f"Action: {insight.action}",
                ],
                category=f"nexus_insight_{insight.category.value}",
                success_rate=insight.confidence,
                metadata={
                    "insight_id": insight.insight_id,
                    "timestamp": insight.timestamp.isoformat(),
                    "category": insight.category.value,
                    "applied": insight.applied,
                },
            )

            return await self._mcp_client.share_skill(insight_skill)
        except Exception as e:
            logger.warning(f"Failed to share insight: {e}")
            return False

    async def share_evolved_solution(self, candidate: EvolutionaryCandidate) -> bool:
        """Share an evolved solution with the collective."""
        if not self._connected or not self._mcp_client:
            return False

        try:
            evolution_skill = Skill(
                name=f"nexus_evolved_{candidate.candidate_id}",
                description=f"Evolved solution with fitness {candidate.aggregate_fitness:.3f}",
                procedure_steps=[
                    f"Generation: {candidate.generation}",
                    f"Island: {candidate.island_id}",
                    f"Code preview: {candidate.code[:200]}...",
                ],
                category="nexus_evolution",
                success_rate=candidate.aggregate_fitness,
                metadata={
                    "candidate_id": candidate.candidate_id,
                    "generation": candidate.generation,
                    "fitness_scores": candidate.fitness_scores,
                    "ancestry": candidate.ancestry,
                },
            )

            return await self._mcp_client.share_skill(evolution_skill)
        except Exception as e:
            logger.warning(f"Failed to share evolved solution: {e}")
            return False

    async def share_healing_procedure(self, record: HealingRecord) -> bool:
        """Share a successful healing procedure with the collective."""
        if not self._connected or not self._mcp_client:
            return False

        if not record.success:
            return False  # Only share successful healings

        try:
            healing_skill = Skill(
                name=f"nexus_healing_{record.record_id}",
                description=f"Healing procedure for {record.anomaly_type}",
                procedure_steps=[
                    f"Anomaly detected: {record.anomaly_type}",
                    f"Severity: {record.anomaly_severity:.2f}",
                    f"Diagnosis: {record.diagnosis}",
                    f"Action taken: {record.action.value}",
                    "Result: Success",
                ],
                category="nexus_healing",
                success_rate=1.0,
                metadata={
                    "record_id": record.record_id,
                    "timestamp": record.timestamp.isoformat(),
                    "action": record.action.value,
                    "anomaly_type": record.anomaly_type,
                },
            )

            return await self._mcp_client.share_skill(healing_skill)
        except Exception as e:
            logger.warning(f"Failed to share healing procedure: {e}")
            return False

    async def get_collective_status(self) -> Dict[str, Any]:
        """Get status of the MCP collective."""
        if not self._connected or not self._mcp_client:
            return {"connected": False, "error": "Not connected to MCP"}

        try:
            status = await self._mcp_client.get_status()
            status["connected"] = True
            return status
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def get_collective_skills(self) -> List[Dict[str, Any]]:
        """Get all skills from the collective."""
        if not self._connected or not self._mcp_client:
            return []

        try:
            skills = await self._mcp_client.get_skills()
            return [s.to_dict() if hasattr(s, "to_dict") else vars(s) for s in skills]
        except Exception as e:
            logger.warning(f"Failed to get collective skills: {e}")
            return []

    async def submit_optimization_task(
        self,
        target: str,
        goals: List[str],
    ) -> Optional[str]:
        """Submit an optimization task to the collective."""
        if not self._connected or not self._mcp_client:
            return None

        try:
            task = AgentTask(
                id=f"nexus_optimize_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                description=f"Optimize {target} for: {', '.join(goals)}",
                agent_role="nexus",
            )

            response = await self._mcp_client.submit_task(task)
            return response.task_id if hasattr(response, "task_id") else None
        except Exception as e:
            logger.warning(f"Failed to submit optimization task: {e}")
            return None

    async def monitor_agent_health(self) -> Dict[str, float]:
        """Monitor health of all agents in the collective."""
        if not self._connected or not self._mcp_client:
            return {}

        try:
            status = await self._mcp_client.get_status()
            agents = status.get("agents", {})

            health_scores = {}
            for agent_id, agent_info in agents.items():
                if isinstance(agent_info, dict):
                    health_scores[agent_id] = agent_info.get("health", 1.0)

            return health_scores
        except Exception as e:
            logger.warning(f"Failed to monitor agent health: {e}")
            return {}

    @property
    def is_connected(self) -> bool:
        """Check if connected to MCP."""
        return self._connected

    def get_stats(self) -> Dict[str, Any]:
        """Get MCP integration statistics."""
        return {
            "mcp_sdk_available": MCP_SDK_AVAILABLE,
            "connected": self._connected,
            "endpoint": self.mcp_config.endpoint,
            "has_api_key": bool(self.mcp_config.api_key),
        }
