"""
Planner Context - Context Gathering and State Management.

This module provides context gathering and GOAP state management:
- Gather project context
- Load team standards from CLAUDE.md
- Discover available tools
- Define initial and goal states
- Generate action space from available agents

Philosophy:
    "Good context leads to good plans."
"""

from typing import Any, Dict, List, TYPE_CHECKING

from .goap import WorldState, GoalState, Action

if TYPE_CHECKING:
    from ..base import AgentTask
    from .agent import PlannerAgent


async def gather_context(agent: "PlannerAgent", task: "AgentTask") -> Dict[str, Any]:
    """Gather all relevant context for planning.

    Args:
        agent: The PlannerAgent instance
        task: The task to gather context for

    Returns:
        Dictionary with context information
    """
    return {
        "architecture": task.context.get("architecture", {}),
        "files": task.context.get("files", []),
        "constraints": task.context.get("constraints", {}),
        "team_standards": await load_team_standards(agent),
        "available_tools": await discover_available_tools(agent),
    }


async def load_team_standards(agent: "PlannerAgent") -> Dict[str, Any]:
    """Load team standards from CLAUDE.md or similar.

    CLAUDE.md is optional. Falls back to empty standards if not found.

    Args:
        agent: The PlannerAgent instance

    Returns:
        Dictionary with team standards
    """
    try:
        result = await agent._execute_tool("read_file", {"path": "CLAUDE.md"})
        if result.get("success"):
            agent.logger.info("Loaded team standards from CLAUDE.md")
            return {"claude_md": result.get("content", "")}
    except FileNotFoundError:
        agent.logger.debug(
            "CLAUDE.md not found (optional). "
            "Using default standards. "
            "Create CLAUDE.md for project-specific guidelines."
        )
    except Exception as e:
        agent.logger.warning(f"Failed to load CLAUDE.md: {e}")

    return {}


async def discover_available_tools(agent: "PlannerAgent") -> List[str]:
    """Discover available MCP tools.

    Args:
        agent: The PlannerAgent instance

    Returns:
        List of available tool names
    """
    # In production: Query MCP for available tools
    return ["read_file", "write_file", "exec_command", "git_operations"]


def define_goal_state(task: "AgentTask", context: Dict[str, Any]) -> GoalState:
    """Define desired end state (GOAP).

    Args:
        task: The task defining the goal
        context: Current context

    Returns:
        GoalState with desired facts
    """
    goal_facts = {
        "task_complete": True,
        "tests_passing": True,
        "code_reviewed": True,
        "documented": True,
    }

    return GoalState(name=f"goal-{task.task_id}", desired_facts=goal_facts, priority=1.0)


def define_initial_state(context: Dict[str, Any]) -> WorldState:
    """Define current state.

    Args:
        context: Current context

    Returns:
        WorldState with current facts
    """
    initial_facts = {
        "task_complete": False,
        "tests_passing": False,
        "code_reviewed": False,
        "documented": False,
        "has_codebase": len(context.get("files", [])) > 0,
    }

    return WorldState(facts=initial_facts, resources={"tokens": 100000, "time_minutes": 120})


def get_available_agents(task: "AgentTask") -> List[str]:
    """Get list of available agents for delegation.

    Args:
        task: The current task

    Returns:
        List of available agent names
    """
    return ["architect", "coder", "refactorer", "reviewer", "security", "tester", "documenter"]


def generate_action_space(
    task: "AgentTask", agents: List[str], context: Dict[str, Any]
) -> List[Action]:
    """Generate available actions from agent capabilities.

    Each action represents what an agent can do.

    Args:
        task: The current task
        agents: Available agents
        context: Current context

    Returns:
        List of possible actions
    """
    actions = []

    # Architect actions
    actions.append(
        Action(
            id="design_architecture",
            agent_role="architect",
            description="Design system architecture",
            preconditions={"has_codebase": True},
            effects={"architecture_defined": True},
            cost=3.0,
            duration_estimate="15m",
        )
    )

    # Coder actions
    actions.append(
        Action(
            id="implement_features",
            agent_role="coder",
            description="Implement features based on design",
            preconditions={"architecture_defined": True},
            effects={"code_written": True},
            cost=5.0,
            duration_estimate="30m",
        )
    )

    # Tester actions
    actions.append(
        Action(
            id="write_tests",
            agent_role="tester",
            description="Write automated tests",
            preconditions={"code_written": True},
            effects={"tests_passing": True},
            cost=3.0,
            duration_estimate="20m",
        )
    )

    # Reviewer actions
    actions.append(
        Action(
            id="code_review",
            agent_role="reviewer",
            description="Perform code review",
            preconditions={"code_written": True, "tests_passing": True},
            effects={"code_reviewed": True},
            cost=2.0,
            duration_estimate="15m",
        )
    )

    # Documenter actions
    actions.append(
        Action(
            id="write_docs",
            agent_role="documenter",
            description="Write documentation",
            preconditions={"code_written": True},
            effects={"documented": True, "task_complete": True},
            cost=2.0,
            duration_estimate="10m",
        )
    )

    return actions


__all__ = [
    "gather_context",
    "load_team_standards",
    "discover_available_tools",
    "define_goal_state",
    "define_initial_state",
    "get_available_agents",
    "generate_action_space",
]
