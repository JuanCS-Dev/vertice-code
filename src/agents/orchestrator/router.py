"""
Task Router - Agent selection and handoff management.

Routes tasks to appropriate specialized agents based on
keywords, complexity, and capability matching.
"""

from __future__ import annotations

from typing import Dict, List

from .types import AgentRole, Handoff, Task, TaskComplexity


class TaskRouter:
    """
    Agent selection and task routing.

    Routes tasks to specialized agents based on keywords
    and manages handoff creation with context preservation.
    """

    # Keyword -> AgentRole mapping
    ROUTING_TABLE: Dict[str, AgentRole] = {
        "code": AgentRole.CODER,
        "review": AgentRole.REVIEWER,
        "architecture": AgentRole.ARCHITECT,
        "research": AgentRole.RESEARCHER,
        "deploy": AgentRole.DEVOPS,
        "test": AgentRole.CODER,
        "refactor": AgentRole.CODER,
        "security": AgentRole.REVIEWER,
        "documentation": AgentRole.RESEARCHER,
        "plan": AgentRole.PROMETHEUS,
        "complex": AgentRole.PROMETHEUS,
        "evolve": AgentRole.PROMETHEUS,
        "simulate": AgentRole.PROMETHEUS,
    }

    # Complexity -> recommended model mapping
    MODEL_ROUTING: Dict[TaskComplexity, str] = {
        TaskComplexity.TRIVIAL: "groq",
        TaskComplexity.SIMPLE: "groq",
        TaskComplexity.MODERATE: "vertex-ai",
        TaskComplexity.COMPLEX: "claude",
        TaskComplexity.CRITICAL: "claude",
    }

    def route(self, task: Task) -> AgentRole:
        """
        Route task to the most appropriate agent.

        Args:
            task: Task to route.

        Returns:
            AgentRole for the task.
        """
        # Complexity-based routing (L4 Autonomy elevation)
        if task.complexity in (TaskComplexity.COMPLEX, TaskComplexity.CRITICAL):
            return AgentRole.PROMETHEUS

        description_lower = task.description.lower()

        for keyword, agent in self.ROUTING_TABLE.items():
            if keyword in description_lower:
                return agent

        return AgentRole.CODER

    def route_multiple(self, tasks: List[Task]) -> Dict[str, AgentRole]:
        """
        Route multiple tasks at once.

        Args:
            tasks: List of tasks to route.

        Returns:
            Dictionary mapping task_id -> AgentRole.
        """
        return {task.id: self.route(task) for task in tasks}

    def get_model_for_complexity(self, complexity: TaskComplexity) -> str:
        """
        Get recommended model for task complexity.

        Args:
            complexity: Task complexity level.

        Returns:
            Model identifier string.
        """
        return self.MODEL_ROUTING.get(complexity, "vertex-ai")

    def create_handoff(
        self,
        task: Task,
        from_agent: AgentRole,
        to_agent: AgentRole,
        context: str,
    ) -> Handoff:
        """
        Create a handoff record for agent-to-agent transfer.

        Args:
            task: Task being handed off.
            from_agent: Source agent.
            to_agent: Target agent.
            context: Context for the handoff.

        Returns:
            Handoff record.
        """
        return Handoff(
            from_agent=from_agent,
            to_agent=to_agent,
            context=context,
            task_id=task.id,
            reason=f"Routing {task.description[:50]}...",
        )

    def get_agents_for_tasks(self, tasks: List[Task]) -> List[AgentRole]:
        """
        Get unique set of agents needed for a task list.

        Args:
            tasks: List of tasks.

        Returns:
            List of unique AgentRoles needed.
        """
        agents = set()
        for task in tasks:
            agents.add(self.route(task))
        return list(agents)
