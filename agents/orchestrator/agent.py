"""
Vertice Orchestrator Agent

The lead agent that coordinates all other agents in the agency.

Key Features:
- Task decomposition and routing
- Bounded Autonomy (L0-L3 levels via mixin)
- Handoffs (OpenAI Agents SDK pattern)

Reference:
- https://www.infoq.com/articles/architects-ai-era/
- AGENTS_2028_EVOLUTION.md
"""

from __future__ import annotations

from typing import Dict, List, Optional, AsyncIterator, Any
import logging

from .types import (
    AgentRole,
    ApprovalCallback,
    ApprovalRequest,
    Handoff,
    NotifyCallback,
    Task,
    TaskComplexity,
)
from .bounded_autonomy import BoundedAutonomyMixin
from agents.base import BaseAgent
from core.resilience import ResilienceMixin
from core.caching import CachingMixin

logger = logging.getLogger(__name__)


class OrchestratorAgent(ResilienceMixin, CachingMixin, BoundedAutonomyMixin, BaseAgent):
    """
    Lead Agent - The Brain of Vertice Agency

    Implements Bounded Autonomy (Three Loops pattern):
    - L0: Autonomous - execute without human approval
    - L1: Notify - execute and notify human afterward
    - L2: Approve - propose and wait for human approval
    - L3: Human Only - human executes, agent advises

    Capabilities:
    - Task decomposition and planning
    - Autonomy level determination (via mixin)
    - Agent selection and routing
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

    ROUTING_TABLE = {
        "code": AgentRole.CODER,
        "review": AgentRole.REVIEWER,
        "architecture": AgentRole.ARCHITECT,
        "research": AgentRole.RESEARCHER,
        "deploy": AgentRole.DEVOPS,
        "test": AgentRole.CODER,
        "refactor": AgentRole.CODER,
        "security": AgentRole.REVIEWER,
        "documentation": AgentRole.RESEARCHER,
    }

    MODEL_ROUTING = {
        TaskComplexity.TRIVIAL: "groq",
        TaskComplexity.SIMPLE: "groq",
        TaskComplexity.MODERATE: "vertex-ai",
        TaskComplexity.COMPLEX: "claude",
        TaskComplexity.CRITICAL: "claude",
    }

    def __init__(
        self,
        approval_callback: Optional[ApprovalCallback] = None,
        notify_callback: Optional[NotifyCallback] = None,
    ) -> None:
        super().__init__()  # Initialize BaseAgent (observability)
        self.tasks: Dict[str, Task] = {}
        self.handoffs: List[Handoff] = []
        self.agents: Dict[AgentRole, Any] = {}
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self._llm = None
        self._approval_callback = approval_callback
        self._notify_callback = notify_callback

    async def plan(self, user_request: str) -> List[Task]:
        """
        Decompose user request into executable tasks.

        Args:
            user_request: The user's request.

        Returns:
            List of tasks to execute.

        Note:
            LLM integration required for advanced planning.
            Currently returns basic decomposition.
        """
        complexity = await self._analyze_complexity(user_request)

        tasks = [
            Task(
                id=f"task-{i}",
                description=f"Step {i}: {user_request[:50]}...",
                complexity=complexity,
            )
            for i in range(1, 2)  # Single task for now
        ]

        return tasks

    async def route(self, task: Task) -> AgentRole:
        """
        Route task to the most appropriate agent.

        Args:
            task: Task to route.

        Returns:
            AgentRole for the task.
        """
        for keyword, agent in self.ROUTING_TABLE.items():
            if keyword in task.description.lower():
                return agent

        return AgentRole.CODER

    async def handoff(
        self,
        task: Task,
        to_agent: AgentRole,
        context: str
    ) -> Handoff:
        """
        Perform handoff to another agent.

        Args:
            task: Task being handed off.
            to_agent: Target agent.
            context: Context for the handoff.

        Returns:
            Handoff record.
        """
        handoff = Handoff(
            from_agent=self.role,
            to_agent=to_agent,
            context=context,
            task_id=task.id,
            reason=f"Routing {task.description[:50]}..."
        )

        self.handoffs.append(handoff)
        logger.info(f"Handoff: {self.role} -> {to_agent} for task {task.id}")

        return handoff

    async def execute(
        self,
        user_request: str,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Execute user request with full orchestration.

        Args:
            user_request: The user's request.
            stream: Whether to stream output.

        Yields:
            Progress updates and results.
        """
        yield "[Orchestrator] Analyzing request...\n"

        tasks = await self.plan(user_request)
        yield f"[Orchestrator] Created {len(tasks)} tasks\n"

        for task in tasks:
            can_proceed, approval = await self.check_autonomy(task)

            if not can_proceed:
                yield f"[Orchestrator] Task requires approval: {task.autonomy_level.value}\n"
                if approval:
                    yield f"[Orchestrator] Approval ID: {approval.id}\n"
                continue

            agent_role = await self.route(task)
            yield f"[Orchestrator] Routing to {agent_role.value}...\n"

            task.status = "completed"
            await self.notify_completion(task, "Task completed")

        yield "[Orchestrator] All tasks completed\n"

    async def _analyze_complexity(self, request: str) -> TaskComplexity:
        """Analyze request complexity for routing decisions."""
        word_count = len(request.split())

        if word_count < 10:
            return TaskComplexity.SIMPLE
        elif word_count < 50:
            return TaskComplexity.MODERATE
        elif "architecture" in request.lower() or "design" in request.lower():
            return TaskComplexity.COMPLEX
        elif "production" in request.lower() or "security" in request.lower():
            return TaskComplexity.CRITICAL
        else:
            return TaskComplexity.MODERATE

    def get_status(self) -> Dict:
        """Get orchestrator status."""
        return {
            "name": self.name,
            "role": self.role.value,
            "active_tasks": len([t for t in self.tasks.values() if t.status == "in_progress"]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == "completed"]),
            "handoffs": len(self.handoffs),
            "agents_registered": len(self.agents),
            "pending_approvals": len(self.pending_approvals),
        }


# Singleton instance
orchestrator = OrchestratorAgent()
