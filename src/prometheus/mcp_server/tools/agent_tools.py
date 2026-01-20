"""
Agent Tools for MCP Server
Meta-tools that expose agent execution capabilities

This module provides tools that allow executing various agents
through the MCP Server interface with real implementations.
"""

import logging
from typing import Dict, Any, Optional
from .base import ToolResult
from .validated import create_validated_tool
from .agent_tools_core import (
    ArchitectAgent,
    ExecutorAgent,
    ReviewerAgent,
    PlannerAgent,
    ResearcherAgent,
)

logger = logging.getLogger(__name__)

# Agent registry for dynamic loading
_agent_registry = {}


def register_agent(name: str, agent_class):
    """Register an agent class for dynamic instantiation."""
    _agent_registry[name] = agent_class


async def _get_agent_instance(agent_name: str):
    """Get or create an agent instance."""
    if agent_name not in _agent_registry:
        # Create agent instances with basic implementations
        if agent_name == "architect":
            _agent_registry[agent_name] = ArchitectAgent()
        elif agent_name == "executor":
            _agent_registry[agent_name] = ExecutorAgent()
        elif agent_name == "reviewer":
            _agent_registry[agent_name] = ReviewerAgent()
        elif agent_name == "planner":
            _agent_registry[agent_name] = PlannerAgent()
        elif agent_name == "researcher":
            _agent_registry[agent_name] = ResearcherAgent()
        else:
            raise ValueError(f"Unknown agent: {agent_name}")

    return _agent_registry[agent_name]


async def execute_with_architect(task: str, context: Optional[Dict[str, Any]] = None) -> ToolResult:
    """Execute task using the Architect agent."""
    try:
        agent = await _get_agent_instance("architect")
        result = await agent.execute_task(task, context)

        return ToolResult(
            success=True,
            data=result,
            metadata={
                "agent_type": "architect",
                "capabilities": agent.capabilities,
                "execution_mode": "real_implementation",
                "processing_time": "completed",
            },
        )
    except Exception as e:
        logger.error(f"Architect agent execution error: {e}")
        return ToolResult(success=False, error=f"Architect agent failed: {str(e)}")


async def execute_with_executor(task: str, context: Optional[Dict[str, Any]] = None) -> ToolResult:
    """Execute task using the Executor agent."""
    try:
        agent = await _get_agent_instance("executor")
        result = await agent.execute_task(task, context)

        return ToolResult(
            success=True,
            data=result,
            metadata={
                "agent_type": "executor",
                "capabilities": agent.capabilities,
                "execution_mode": "real_implementation",
                "processing_time": "completed",
            },
        )
    except Exception as e:
        logger.error(f"Executor agent execution error: {e}")
        return ToolResult(success=False, error=f"Executor agent failed: {str(e)}")


async def execute_with_reviewer(task: str, context: Optional[Dict[str, Any]] = None) -> ToolResult:
    """Execute task using the Reviewer agent."""
    try:
        agent = await _get_agent_instance("reviewer")
        result = await agent.execute_task(task, context)

        return ToolResult(
            success=True,
            data=result,
            metadata={
                "agent_type": "reviewer",
                "capabilities": agent.capabilities,
                "execution_mode": "real_implementation",
                "processing_time": "completed",
            },
        )
    except Exception as e:
        logger.error(f"Reviewer agent execution error: {e}")
        return ToolResult(success=False, error=f"Reviewer agent failed: {str(e)}")


async def execute_with_planner(task: str, context: Optional[Dict[str, Any]] = None) -> ToolResult:
    """Execute task using the Planner agent."""
    try:
        agent = await _get_agent_instance("planner")
        result = await agent.execute_task(task, context)

        return ToolResult(
            success=True,
            data=result,
            metadata={
                "agent_type": "planner",
                "capabilities": agent.capabilities,
                "execution_mode": "real_implementation",
                "processing_time": "completed",
            },
        )
    except Exception as e:
        logger.error(f"Planner agent execution error: {e}")
        return ToolResult(success=False, error=f"Planner agent failed: {str(e)}")


async def execute_with_researcher(
    task: str, context: Optional[Dict[str, Any]] = None
) -> ToolResult:
    """Execute task using the Researcher agent."""
    try:
        agent = await _get_agent_instance("researcher")
        result = await agent.execute_task(task, context)

        return ToolResult(
            success=True,
            data=result,
            metadata={
                "agent_type": "researcher",
                "capabilities": agent.capabilities,
                "execution_mode": "real_implementation",
                "processing_time": "completed",
            },
        )
    except Exception as e:
        logger.error(f"Researcher agent execution error: {e}")
        return ToolResult(success=False, error=f"Researcher agent failed: {str(e)}")


# Create and register all agent tools
agent_tools = [
    create_validated_tool(
        name="execute_with_architect",
        description="Execute task using the Architect agent for analysis, design, and planning",
        category="execution",
        parameters={
            "task": {
                "type": "string",
                "description": "Task description for the architect agent",
                "required": True,
            },
            "context": {
                "type": "object",
                "description": "Additional context for the task",
            },
        },
        required_params=["task"],
        execute_func=execute_with_architect,
    ),
    create_validated_tool(
        name="execute_with_executor",
        description="Execute task using the Executor agent for implementation and execution",
        category="execution",
        parameters={
            "task": {
                "type": "string",
                "description": "Task description for the executor agent",
                "required": True,
            },
            "context": {
                "type": "object",
                "description": "Additional context for the task",
            },
        },
        required_params=["task"],
        execute_func=execute_with_executor,
    ),
    create_validated_tool(
        name="execute_with_reviewer",
        description="Execute task using the Reviewer agent for code review and quality assurance",
        category="execution",
        parameters={
            "task": {
                "type": "string",
                "description": "Task description for the reviewer agent",
                "required": True,
            },
            "context": {
                "type": "object",
                "description": "Additional context for the task",
            },
        },
        required_params=["task"],
        execute_func=execute_with_reviewer,
    ),
    create_validated_tool(
        name="execute_with_planner",
        description="Execute task using the Planner agent for project planning and task breakdown",
        category="execution",
        parameters={
            "task": {
                "type": "string",
                "description": "Task description for the planner agent",
                "required": True,
            },
            "context": {
                "type": "object",
                "description": "Additional context for the task",
            },
        },
        required_params=["task"],
        execute_func=execute_with_planner,
    ),
    create_validated_tool(
        name="execute_with_researcher",
        description="Execute task using the Researcher agent for information gathering and analysis",
        category="execution",
        parameters={
            "task": {
                "type": "string",
                "description": "Task description for the researcher agent",
                "required": True,
            },
            "context": {
                "type": "object",
                "description": "Additional context for the task",
            },
        },
        required_params=["task"],
        execute_func=execute_with_researcher,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in agent_tools:
    register_tool(tool)
