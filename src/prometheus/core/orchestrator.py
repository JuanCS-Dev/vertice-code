"""
Prometheus Orchestrator v2.0 - Fully Integrated
================================================
Core orchestration engine for the Prometheus Meta-Agent.
Connects ALL subsystems: Memory, WorldModel, Reflection, Evolution.

UPGRADE: Replaced MockMemory with real MemorySystem (MIRIX).
"""

from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import logging

from ..memory.system import MemorySystem
from .world_model import WorldModel, ActionType, WorldState
from .reflection import ReflectionEngine, CritiqueAspect

logger = logging.getLogger(__name__)


@dataclass
class PrometheusTask:
    """A task to be executed by Prometheus."""

    id: str
    description: str
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class PrometheusOrchestrator:
    """
    Unified Orchestrator for Prometheus Meta-Agent v2.0.

    NOW INTEGRATES:
    - MemorySystem (MIRIX): 6-type memory for context
    - WorldModel (SimuRA): Simulates actions before execution
    - ReflectionEngine: Self-critique and learning

    Execution Flow:
    1. Retrieve context from Memory
    2. Simulate plan via WorldModel
    3. Execute with LLM
    4. Reflect and learn from result
    """

    def __init__(
        self,
        llm_client: Any = None,
        agent_name: str = "Prometheus",
        event_bus: Any = None,
        mcp_client: Any = None,
        memory_system: Optional[MemorySystem] = None,
        world_model: Optional[WorldModel] = None,
        reflection_engine: Optional[ReflectionEngine] = None,
    ):
        """Initialize Prometheus Orchestrator with all subsystems.

        Args:
            llm_client: LLM provider (GeminiClient or VertexAI)
            agent_name: Name for memory identity
            event_bus: Optional event bus for observability
            mcp_client: MCP client for tools
            memory_system: Pre-configured MemorySystem (creates new if None)
            world_model: Pre-configured WorldModel (creates new if None)
            reflection_engine: Pre-configured ReflectionEngine (creates new if None)
        """
        self.llm_client = llm_client
        self.agent_name = agent_name
        self.event_bus = event_bus
        self.mcp_client = mcp_client

        # Internal state
        self._is_executing = False
        self.execution_history: List[Dict[str, Any]] = []

        # === REAL SUBSYSTEMS (v2.0) ===
        self.memory = memory_system or MemorySystem(agent_name=agent_name)
        self.world_model = world_model or (WorldModel(llm_client) if llm_client else None)
        self.reflection = reflection_engine or (
            ReflectionEngine(llm_client, self.memory) if llm_client else None
        )

        logger.info("PrometheusOrchestrator v2.0 initialized with real subsystems")

    async def execute(
        self, task: str, stream: bool = False, fast_mode: bool = False
    ) -> AsyncIterator[str]:
        """
        Execute a complex task with full cognitive pipeline.

        Pipeline:
        1. Memory Context: Retrieve relevant experiences
        2. World Model: Simulate approach (if not fast_mode)
        3. LLM Execution: Generate solution
        4. Reflection: Critique and learn (if not fast_mode)

        Args:
            task: Task description
            stream: Whether to stream output
            fast_mode: Skip memory/reflection for speed
        """
        self._is_executing = True
        start_time = datetime.now()

        try:
            # === PHASE 1: Memory Context ===
            if stream:
                yield "🧠 Retrieving context from memory...\n"

            context = {}
            if not fast_mode:
                context = self.memory.get_context_for_task(task)
                relevant_experiences = context.get("relevant_experiences", [])
                if relevant_experiences and stream:
                    yield f"📚 Found {len(relevant_experiences)} relevant experiences\n"

            # === PHASE 2: World Model Simulation ===
            simulation_result = None
            if self.world_model and not fast_mode:
                if stream:
                    yield "🌍 Simulating approach via World Model...\n"
                try:
                    # Create initial state
                    initial_state = WorldState()
                    # Simulate a thinking action
                    simulation_result = await self.world_model.simulate_action(
                        action=ActionType.THINK,
                        parameters={"task": task[:200]},
                        current_state=initial_state,
                    )
                    if stream and simulation_result:
                        yield f"✅ Simulation: {simulation_result.predicted_outcome[:100]}...\n"
                except Exception as e:
                    logger.warning(f"World Model simulation failed: {e}")
                    if stream:
                        yield f"⚠️ Simulation skipped: {e}\n"

            # === PHASE 3: LLM Execution ===
            if stream:
                yield "⚡ Executing task...\n"

            response = ""
            if self.llm_client:
                try:
                    # Build enhanced prompt with context
                    enhanced_prompt = self._build_enhanced_prompt(task, context)
                    response = await self.llm_client.generate(enhanced_prompt)
                    if stream:
                        yield response
                except Exception as e:
                    logger.warning(f"LLM execution failed: {e}")
                    response = f"Execution failed: {e}"
                    if stream:
                        yield response
            else:
                response = f"[No LLM] Would execute: {task}"
                if stream:
                    yield response

            # === PHASE 4: Reflection & Learning ===
            if self.reflection and not fast_mode and response:
                if stream:
                    yield "\n\n🔍 Reflecting on execution...\n"
                try:
                    reflection_result = await self.reflection.critique_action(
                        action=f"Executed task: {task[:100]}",
                        result=response[:500],
                        context={
                            "simulation": simulation_result.to_dict() if simulation_result else None
                        },
                        aspects=[CritiqueAspect.CORRECTNESS, CritiqueAspect.COMPLETENESS],
                    )
                    # Learn from the experience
                    self.memory.remember_experience(
                        experience=f"Task: {task[:100]}",
                        outcome=f"Score: {reflection_result.score:.2f}",
                        context={"lessons": reflection_result.lessons_learned},
                        importance=reflection_result.score,
                    )
                    if stream:
                        yield f"📝 Learned from execution (score: {reflection_result.score:.2f})\n"
                except Exception as e:
                    logger.warning(f"Reflection failed: {e}")

            # Record execution
            execution_time = (datetime.now() - start_time).total_seconds()
            self.execution_history.append(
                {
                    "task": task[:100],
                    "time": execution_time,
                    "fast_mode": fast_mode,
                    "timestamp": start_time.isoformat(),
                }
            )

        finally:
            self._is_executing = False

    def _build_enhanced_prompt(self, task: str, context: Dict[str, Any]) -> str:
        """Build prompt enhanced with memory context."""
        prompt_parts = [task]

        # Add relevant experiences
        experiences = context.get("relevant_experiences", [])
        if experiences:
            prompt_parts.append("\n\nRelevant past experiences:")
            for exp in experiences[:3]:
                prompt_parts.append(f"- {exp.get('experience', '')[:100]}")

        # Add relevant procedures
        procedures = context.get("relevant_procedures", [])
        if procedures:
            prompt_parts.append("\n\nKnown procedures:")
            for proc in procedures[:2]:
                prompt_parts.append(f"- {proc.get('name', '')}: {len(proc.get('steps', []))} steps")

        return "\n".join(prompt_parts)

    async def evolve_capabilities(
        self, iterations: int = 1, domain: str = "general"
    ) -> Dict[str, Any]:
        """
        Run self-evolution loop.

        NOTE: For full evolution, use CoEvolutionLoop directly.
        This method provides a simplified interface.
        """
        logger.info(f"Running evolution: {iterations} iterations in {domain}")

        # Import here to avoid circular imports
        from .evolution import CoEvolutionLoop, TaskDomain
        from ..tools.tool_factory import ToolFactory
        from ..sandbox.executor import SandboxExecutor

        if not self.llm_client:
            return {"status": "error", "message": "No LLM client available"}

        try:
            sandbox = SandboxExecutor()
            tool_factory = ToolFactory(self.llm_client, sandbox)

            evolution = CoEvolutionLoop(
                llm_client=self.llm_client,
                tool_factory=tool_factory,
                memory_system=self.memory,
                reflection_engine=self.reflection,
                sandbox_executor=sandbox,
            )

            # Map domain string to enum
            domain_map = {
                "general": TaskDomain.GENERAL,
                "code": TaskDomain.CODE,
                "math": TaskDomain.MATH,
                "reasoning": TaskDomain.REASONING,
            }
            task_domain = domain_map.get(domain, TaskDomain.GENERAL)

            stats = await evolution.evolve(num_iterations=iterations, domain=task_domain)
            return stats.to_dict()

        except Exception as e:
            logger.error(f"Evolution failed: {e}")
            return {"status": "error", "message": str(e)}

    async def benchmark_capabilities(self) -> Dict[str, Any]:
        """Run capability benchmarks using real subsystems."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "memory_stats": self.memory.get_stats(),
            "execution_history_size": len(self.execution_history),
        }

        if self.world_model:
            results["world_model_stats"] = self.world_model.get_stats()

        if self.reflection:
            results["reflection_summary"] = self.reflection.get_learning_summary()

        return results

    async def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status including subsystem health."""
        return {
            "status": "operational",
            "version": "2.0",
            "agent": self.agent_name,
            "active": self._is_executing,
            "subsystems": {
                "memory": self.memory is not None,
                "world_model": self.world_model is not None,
                "reflection": self.reflection is not None,
            },
            "executions": len(self.execution_history),
        }
