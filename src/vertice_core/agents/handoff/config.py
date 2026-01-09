"""Default configurations for handoffs."""

from typing import Dict, List
from ..router import AgentType
from .types import AgentCapability, EscalationChain

DEFAULT_CAPABILITIES: Dict[AgentType, AgentCapability] = {
    AgentType.PLANNER: AgentCapability(
        agent_type=AgentType.PLANNER,
        capabilities={"planning", "decomposition", "strategy"},
        can_plan=True,
        can_execute=False,
        priority=5,
        description="Creates execution plans and strategies",
    ),
    AgentType.EXECUTOR: AgentCapability(
        agent_type=AgentType.EXECUTOR,
        capabilities={"execution", "coding", "file_ops"},
        can_plan=False,
        can_execute=True,
        priority=3,
        description="Executes code changes and file operations",
    ),
    AgentType.REVIEWER: AgentCapability(
        agent_type=AgentType.REVIEWER,
        capabilities={"review", "quality", "best_practices"},
        can_plan=False,
        can_execute=False,
        can_review=True,
        priority=4,
        description="Reviews code for quality and issues",
    ),
    AgentType.ARCHITECT: AgentCapability(
        agent_type=AgentType.ARCHITECT,
        capabilities={"architecture", "design", "system", "planning"},
        can_plan=True,
        can_execute=False,
        priority=6,
        description="Designs system architecture",
    ),
    AgentType.EXPLORER: AgentCapability(
        agent_type=AgentType.EXPLORER,
        capabilities={"exploration", "search", "understanding"},
        can_plan=False,
        can_execute=False,
        priority=2,
        description="Explores and understands codebase",
    ),
    AgentType.SECURITY: AgentCapability(
        agent_type=AgentType.SECURITY,
        capabilities={"security", "vulnerability", "audit", "review"},
        can_plan=False,
        can_execute=False,
        can_review=True,
        priority=5,
        description="Security analysis and audit",
    ),
    AgentType.TESTING: AgentCapability(
        agent_type=AgentType.TESTING,
        capabilities={"testing", "test_writing", "coverage"},
        can_plan=False,
        can_execute=True,
        priority=3,
        description="Writes and runs tests",
    ),
    AgentType.CHAT: AgentCapability(
        agent_type=AgentType.CHAT,
        capabilities={"conversation", "explanation"},
        can_plan=False,
        can_execute=False,
        priority=1,
        description="General conversation",
    ),
}

DEFAULT_ESCALATION_CHAINS: List[EscalationChain] = [
    EscalationChain(
        name="execution",
        chain=[AgentType.EXECUTOR, AgentType.PLANNER, AgentType.ARCHITECT],
        description="Escalate execution failures to planning",
    ),
    EscalationChain(
        name="review",
        chain=[AgentType.REVIEWER, AgentType.SECURITY, AgentType.ARCHITECT],
        description="Escalate review to security to architect",
    ),
    EscalationChain(
        name="exploration",
        chain=[AgentType.EXPLORER, AgentType.ARCHITECT],
        description="Escalate exploration to architecture",
    ),
]
