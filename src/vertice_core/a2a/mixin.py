"""
A2A Protocol Mixin

Mixin providing A2A protocol capabilities to agents.

Reference:
- A2A Specification: https://a2a-protocol.org/latest/specification/
"""

from __future__ import annotations

import uuid
import logging
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from .types import (
    MessageRole,
    TaskStatus,
    AgentSkill,
    AgentCapabilities,
)
from .task import A2ATask
from .agent_card import AgentCard

if TYPE_CHECKING:
    from .mixin import A2AProtocolMixin as A2AProtocolMixinType

logger = logging.getLogger(__name__)


class A2AProtocolMixin:
    """
    Mixin providing A2A protocol capabilities.

    Add to any agent class to enable:
    - Agent Card generation
    - Task lifecycle management
    - JSON-RPC message handling
    - Inter-agent communication

    Reference: https://a2a-protocol.org/latest/specification/
    """

    # Subclasses should define these
    name: str
    description: str

    def _init_a2a(
        self,
        agent_id: Optional[str] = None,
        version: str = "1.0.0",
        provider: str = "vertice",
        base_url: str = "http://localhost:8000",
    ) -> None:
        """Initialize A2A protocol support."""
        self._a2a_agent_id = agent_id or f"vertice-{getattr(self, 'name', 'agent')}"
        self._a2a_version = version
        self._a2a_provider = provider
        self._a2a_base_url = base_url
        self._a2a_tasks: Dict[str, A2ATask] = {}
        self._a2a_skills: List[AgentSkill] = []
        self._a2a_capabilities = AgentCapabilities()

        logger.info(f"[A2A] Initialized {self._a2a_agent_id}")

    def register_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        handler: Optional[Callable[..., Any]] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> AgentSkill:
        """
        Register a skill that this agent can perform.

        Skills are discoverable via the Agent Card.
        """
        if not hasattr(self, "_a2a_skills"):
            self._a2a_skills = []

        skill = AgentSkill(
            id=skill_id,
            name=name,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            tags=tags or [],
        )
        self._a2a_skills.append(skill)

        if handler:
            setattr(self, f"_skill_{skill_id}", handler)

        logger.info(f"[A2A] Registered skill: {skill_id}")
        return skill

    def get_agent_card(self) -> AgentCard:
        """Generate this agent's card for A2A discovery."""
        if not hasattr(self, "_a2a_agent_id"):
            self._init_a2a()

        return AgentCard(
            agent_id=self._a2a_agent_id,
            name=getattr(self, "name", "Agent"),
            description=getattr(self, "description", ""),
            version=self._a2a_version,
            provider=self._a2a_provider,
            url=f"{self._a2a_base_url}/agents/{self._a2a_agent_id}",
            capabilities=self._a2a_capabilities,
            skills=self._a2a_skills,
        )

    def create_task(
        self,
        initial_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> A2ATask:
        """Create a new A2A task."""
        if not hasattr(self, "_a2a_tasks"):
            self._a2a_tasks = {}

        task = A2ATask(
            id=str(uuid.uuid4()),
            status=TaskStatus.SUBMITTED,
            metadata=metadata or {},
        )

        if initial_message:
            task.add_message(MessageRole.USER, initial_message)

        self._a2a_tasks[task.id] = task
        logger.info(f"[A2A] Created task: {task.id}")

        return task

    def get_task(self, task_id: str) -> Optional[A2ATask]:
        """Get a task by ID."""
        if not hasattr(self, "_a2a_tasks"):
            return None
        return self._a2a_tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
    ) -> List[A2ATask]:
        """List tasks, optionally filtered by status."""
        if not hasattr(self, "_a2a_tasks"):
            return []

        tasks = list(self._a2a_tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by updated_at descending
        tasks.sort(key=lambda t: t.updated_at, reverse=True)

        return tasks[:limit]

    async def process_task(self, task: A2ATask) -> A2ATask:
        """
        Process a task through to completion.

        Subclasses should override for custom processing.
        """
        task.transition_to(TaskStatus.WORKING)

        try:
            # Default: echo the last user message
            user_messages = [m for m in task.messages if m.role == MessageRole.USER]
            if user_messages:
                response = f"Processed: {user_messages[-1].content}"
                task.add_message(MessageRole.AGENT, response)

            task.transition_to(TaskStatus.COMPLETED)

        except Exception as e:
            task.add_message(MessageRole.SYSTEM, f"Error: {str(e)}")
            task.transition_to(TaskStatus.FAILED)
            logger.error(f"[A2A] Task {task.id} failed: {e}")

        return task

    async def send_message(
        self,
        target_agent: "A2AProtocolMixinType",
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> A2ATask:
        """
        Send a message to another A2A-compatible agent.

        Creates a task on the target agent and waits for response.
        """
        # Create task on target agent
        task = target_agent.create_task(
            initial_message=message,
            metadata={
                **(metadata or {}),
                "sender_agent_id": getattr(self, "_a2a_agent_id", "unknown"),
            },
        )

        # Process the task
        await target_agent.process_task(task)

        return task

    def get_a2a_status(self) -> Dict[str, Any]:
        """Get A2A protocol status."""
        if not hasattr(self, "_a2a_agent_id"):
            return {"initialized": False}

        return {
            "initialized": True,
            "agent_id": self._a2a_agent_id,
            "version": self._a2a_version,
            "provider": self._a2a_provider,
            "skills_count": len(self._a2a_skills),
            "active_tasks": len([t for t in self._a2a_tasks.values() if not t.is_terminal()]),
            "total_tasks": len(self._a2a_tasks),
        }
