"""
Vertice Orchestrator Agent

The lead agent that coordinates all other agents in the agency.

Key Features:
- Task decomposition and routing (via composed components)
- Bounded Autonomy (L0-L3 levels via mixin)
- Handoffs (OpenAI Agents SDK pattern)

Reference:
- https://www.infoq.com/articles/architects-ai-era/
- AGENTS_2028_EVOLUTION.md
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from agents.base import BaseAgent
from core.caching import CachingMixin
from core.mesh.mixin import HybridMeshMixin
from core.resilience import ResilienceMixin

from .bounded_autonomy import BoundedAutonomyMixin
from .decomposer import TaskDecomposer
from .router import TaskRouter
from .types import (
    AgentRole,
    ApprovalCallback,
    ApprovalRequest,
    Handoff,
    NotifyCallback,
    Task,
)

logger = logging.getLogger(__name__)


class OrchestratorAgent(
    HybridMeshMixin, ResilienceMixin, CachingMixin, BoundedAutonomyMixin, BaseAgent
):
    """
    Lead Agent - The Brain of Vertice Agency

    Implements Bounded Autonomy (Three Loops pattern):
    - L0: Autonomous - execute without human approval
    - L1: Notify - execute and notify human afterward
    - L2: Approve - propose and wait for human approval
    - L3: Human Only - human executes, agent advises

    Capabilities:
    - Task decomposition (via TaskDecomposer)
    - Agent routing (via TaskRouter)
    - Context preservation across handoffs
    """

    name = "orchestrator"
    role = AgentRole.ORCHESTRATOR
    description = """
    Strategic coordinator for Vertice Agency.
    Decomposes complex tasks, routes to specialists,
    maintains context, and ensures quality output.
    Enforces Bounded Autonomy for safe operations.
    """

    def __init__(
        self,
        approval_callback: Optional[ApprovalCallback] = None,
        notify_callback: Optional[NotifyCallback] = None,
        llm_client: Optional[Any] = None,
    ) -> None:
        super().__init__()

        # Composed components
        self.decomposer = TaskDecomposer(llm_client)
        self.router = TaskRouter()

        # State
        self.tasks: Dict[str, Task] = {}
        self.handoffs: List[Handoff] = []
        self.agents: Dict[AgentRole, Any] = {}
        self.pending_approvals: Dict[str, ApprovalRequest] = {}

        # Callbacks
        self._approval_callback = approval_callback
        self._notify_callback = notify_callback
        self._agents_initialized = False

        # Initialize hybrid mesh for topology-based coordination
        self._init_mesh()
        logger.info("[Orchestrator] Hybrid mesh initialized")

    def _ensure_agents(self) -> None:
        """
        Lazy-initialize specialized agents and register in mesh.

        Pattern: Anthropic Orchestrator-Worker (2026)
        """
        if self._agents_initialized:
            return

        # Import agents lazily to avoid circular imports
        from agents.architect.agent import ArchitectAgent
        from agents.coder.agent import CoderAgent
        from agents.devops.agent import DevOpsAgent
        from agents.researcher.agent import ResearcherAgent
        from agents.reviewer.agent import ReviewerAgent

        self.agents = {
            AgentRole.CODER: CoderAgent(),
            AgentRole.REVIEWER: ReviewerAgent(),
            AgentRole.ARCHITECT: ArchitectAgent(),
            AgentRole.RESEARCHER: ResearcherAgent(),
            AgentRole.DEVOPS: DevOpsAgent(),
        }

        # Lazy load Prometheus Meta-Agent (L4 Autonomy)
        try:
            from vertice_agents.registry import get_agent
            prometheus = get_agent("prometheus")
            if prometheus:
                self.agents[AgentRole.PROMETHEUS] = prometheus
        except ImportError:
            logger.warning("Could not load Prometheus agent")

        # Register all agents as workers in the mesh
        for role, agent in self.agents.items():
            self.register_worker(
                agent_id=role.value,
                metadata={"role": role.value, "agent_type": type(agent).__name__},
            )

        self._agents_initialized = True
        logger.info(f"[Orchestrator] Initialized {len(self.agents)} subagents in mesh")

    async def plan(self, user_request: str) -> List[Task]:
        """Decompose user request into executable tasks."""
        return await self.decomposer.decompose(user_request)

    async def route(self, task: Task) -> AgentRole:
        """Route task to the most appropriate agent."""
        return self.router.route(task)

    async def handoff(
        self,
        task: Task,
        to_agent: AgentRole,
        context: str,
    ) -> Handoff:
        """Perform handoff to another agent."""
        handoff = self.router.create_handoff(
            task=task,
            from_agent=self.role,
            to_agent=to_agent,
            context=context,
        )

        self.handoffs.append(handoff)
        logger.info(f"Handoff: {self.role} -> {to_agent} for task {task.id}")

        return handoff

    async def execute(
        self,
        user_request: str,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        """
        Execute user request with full orchestration and mesh topology.

        Pattern: Anthropic Orchestrator-Worker (2026) + Hybrid Mesh
        - Lead agent decomposes and delegates
        - Mesh topology optimizes coordination pattern
        - Subagents execute with optimal coordination
        - Results aggregated back to user

        Reference: arXiv:2512.08296 (Scaling Agent Systems)
        """
        self._ensure_agents()
        yield "[Orchestrator] Analyzing request...\n"

        tasks = await self.plan(user_request)
        yield f"[Orchestrator] Created {len(tasks)} task(s)\n"

        # Get topology recommendation for the overall request
        topology_info = self.get_topology_recommendation(user_request)
        yield f"[Mesh] Task type: {topology_info['task_characteristic']}, "
        yield f"Topology: {topology_info['recommended_topology']}\n"

        if topology_info.get("warning"):
            yield f"[Mesh] Warning: {topology_info['warning']}\n"

        for task in tasks:
            async for chunk in self._execute_task(task, user_request, stream):
                yield chunk

        # Report mesh status
        mesh_status = self.get_mesh_status()
        yield f"[Mesh] Status: {mesh_status['worker_nodes']} workers, "
        yield f"{mesh_status['active_routes']} routes active\n"
        yield "[Orchestrator] All tasks processed\n"

    async def _execute_task(
        self,
        task: Task,
        user_request: str,
        stream: bool,
    ) -> AsyncIterator[str]:
        """Execute a single task with autonomy check and agent delegation."""
        # Check bounded autonomy
        can_proceed, approval = await self.check_autonomy(task)

        if not can_proceed:
            yield f"[Orchestrator] Task requires approval: {task.autonomy_level.value}\n"
            if approval:
                yield f"[Orchestrator] Approval ID: {approval.id}\n"
            return

        # Route to appropriate agent
        agent_role = await self.route(task)
        agent = self.agents.get(agent_role)

        if agent is None:
            yield f"[Orchestrator] No agent for role: {agent_role.value}\n"
            task.status = "failed"
            return

        # Route task through mesh with optimal topology
        route = self.route_task(
            task_id=task.id,
            task_description=task.description,
            target_agents=[agent_role.value],
            prefer_parallel=True,
        )
        yield f"[Mesh] Task {task.id} routed via {route.topology.value} "
        yield f"(error factor: {route.estimated_error_factor:.1f}x)\n"

        # Create handoff with context (Anthropic pattern)
        handoff = await self.handoff(task, agent_role, user_request)
        yield f"[Orchestrator] Handoff to {agent_role.value}...\n"

        # Execute via agent
        task.status = "in_progress"
        try:
            async for chunk in self._delegate_to_agent(agent, agent_role, task, stream):
                yield chunk

            task.status = "completed"
            task.result = "Execution completed"
            yield f"\n[Orchestrator] Task completed by {agent_role.value}\n"

        except Exception as e:
            task.status = "failed"
            task.result = str(e)
            logger.error(f"Agent {agent_role.value} failed: {e}")
            yield f"\n[Orchestrator] Task failed: {e}\n"

        await self.notify_completion(task, task.result or "")

    async def _delegate_to_agent(
        self,
        agent: Any,
        agent_role: AgentRole,
        task: Task,
        stream: bool,
    ) -> AsyncIterator[str]:
        """Delegate task execution to specialized agent."""
        if agent_role == AgentRole.PROMETHEUS:
            # Adapt Core Task -> CLI AgentTask
            # This bridges the gap between Core and CLI agent protocols
            from vertice_cli.agents.base import AgentTask
            
            agent_task = AgentTask(
                task_id=task.id,
                request=task.description,
                metadata={
                    "complexity": task.complexity.value,
                    "fast_mode": True  # Default to fast mode for integration
                }
            )
            response = await agent.execute(agent_task)
            
            # Extract result from AgentResponse (response.data["result"])
            task_result = response.data.get("result")
            if task_result and hasattr(task_result, "output"):
                output_data = task_result.output
                # Output might be a dict (TaskResult definition) or string (if coerced)
                if isinstance(output_data, dict):
                    yield output_data.get("output") or str(output_data)
                else:
                    yield str(output_data)
            else:
                yield "Prometheus task executed (no output available)"

        elif hasattr(agent, "generate") and agent_role == AgentRole.CODER:
            from agents.coder.types import CodeGenerationRequest

            request = CodeGenerationRequest(
                description=task.description,
                language="python",
            )
            async for chunk in agent.generate(request, stream=stream):
                yield chunk
        elif hasattr(agent, "execute"):
            async for chunk in agent.execute(task.description, stream=stream):
                yield chunk
        elif hasattr(agent, "analyze"):
            async for chunk in agent.analyze(task.description, stream=stream):
                yield chunk
        else:
            yield f"[{agent_role.value}] Processing: {task.description}\n"

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        self._ensure_agents()
        return {
            "name": self.name,
            "role": self.role.value,
            "active_tasks": len(
                [t for t in self.tasks.values() if t.status == "in_progress"]
            ),
            "completed_tasks": len(
                [t for t in self.tasks.values() if t.status == "completed"]
            ),
            "failed_tasks": len(
                [t for t in self.tasks.values() if t.status == "failed"]
            ),
            "handoffs": len(self.handoffs),
            "agents_registered": list(self.agents.keys()),
            "pending_approvals": len(self.pending_approvals),
        }


# Singleton instance
orchestrator = OrchestratorAgent()
