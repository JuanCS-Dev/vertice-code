"""
Prometheus Tools for MCP Server
Self-evolving meta-agent capabilities toolkit

This module provides 8 essential Prometheus tools with lazy initialization
and graceful degradation when provider is not available.
"""

import logging
from typing import Optional
from .base import ToolResult
from .validated import create_validated_tool

logger = logging.getLogger(__name__)

# Global provider reference (lazy initialized)
_prometheus_provider = None


def set_prometheus_provider(provider):
    """Set the global Prometheus provider for lazy initialization."""
    global _prometheus_provider
    _prometheus_provider = provider
    logger.info("Prometheus provider set for MCP tools")


async def _ensure_provider():
    """Ensure provider is available, raise error if not."""
    if _prometheus_provider is None:
        raise ValueError(
            "Prometheus provider not initialized. Use set_prometheus_provider() first."
        )
    return _prometheus_provider


async def prometheus_execute(
    task: str, use_world_model: bool = True, use_memory: bool = True
) -> ToolResult:
    """Execute task via PROMETHEUS self-evolving meta-agent."""
    try:
        provider = await _ensure_provider()

        # Configure provider
        provider.config.enable_world_model = use_world_model
        provider.config.enable_memory = use_memory

        result = await provider.generate(task)
        return ToolResult(
            success=True,
            data={
                "tool": "prometheus_execute",
                "result": result,
                "world_model_used": use_world_model,
                "memory_used": use_memory,
            },
            metadata={"task_length": len(task), "execution_type": "prometheus_generate"},
        )
    except Exception as e:
        logger.error(f"Prometheus execute error: {e}")
        return ToolResult(success=False, error=f"Prometheus execute failed: {str(e)}")


async def prometheus_memory_query(query: str, memory_type: str = "all") -> ToolResult:
    """Query PROMETHEUS 6-type persistent memory system (MIRIX)."""
    try:
        provider = await _ensure_provider()

        # Use get_memory_context for queries
        context = provider.get_memory_context(query)
        return ToolResult(
            success=True,
            data={
                "tool": "prometheus_memory_query",
                "query": query,
                "memory_type": memory_type,
                "result": context,
            },
            metadata={"query_length": len(query), "memory_type": memory_type},
        )
    except Exception as e:
        logger.error(f"Prometheus memory query error: {e}")
        return ToolResult(success=False, error=f"Prometheus memory query failed: {str(e)}")


async def prometheus_simulate(action_plan: str) -> ToolResult:
    """Simulate action via World Model (SimuRA) without executing it."""
    try:
        provider = await _ensure_provider()
        await provider._ensure_initialized()

        if (
            provider._orchestrator
            and hasattr(provider._orchestrator, "world_model")
            and hasattr(provider._orchestrator.world_model, "simulate")
        ):
            simulation = await provider._orchestrator.world_model.simulate(action_plan)
            return ToolResult(
                success=True,
                data={
                    "tool": "prometheus_simulate",
                    "action_plan": action_plan,
                    "simulation": simulation,
                },
                metadata={"simulation_available": True, "action_plan_length": len(action_plan)},
            )
        else:
            return ToolResult(
                success=False,
                error="World Model simulation not available",
                metadata={"simulation_available": False},
            )
    except Exception as e:
        logger.error(f"Prometheus simulate error: {e}")
        return ToolResult(success=False, error=f"Prometheus simulate failed: {str(e)}")


async def prometheus_evolve(iterations: int = 5) -> ToolResult:
    """Run self-evolution cycle (Agent0) to improve capabilities."""
    try:
        provider = await _ensure_provider()

        result = await provider.evolve(iterations)
        return ToolResult(
            success=True,
            data={
                "tool": "prometheus_evolve",
                "iterations": iterations,
                "result": result,
            },
            metadata={"iterations": iterations, "evolution_completed": True},
        )
    except Exception as e:
        logger.error(f"Prometheus evolve error: {e}")
        return ToolResult(success=False, error=f"Prometheus evolve failed: {str(e)}")


async def prometheus_reflect(outcome: str, task_id: Optional[str] = None) -> ToolResult:
    """Trigger self-reflection on a completed task or action."""
    try:
        provider = await _ensure_provider()
        await provider._ensure_initialized()

        if (
            provider._orchestrator
            and hasattr(provider._orchestrator, "reflection")
            and hasattr(provider._orchestrator.reflection, "reflect")
        ):
            reflection = await provider._orchestrator.reflection.reflect(outcome, task_id)
            return ToolResult(
                success=True,
                data={
                    "tool": "prometheus_reflect",
                    "outcome": outcome,
                    "task_id": task_id,
                    "reflection": reflection,
                },
                metadata={"reflection_available": True, "outcome_length": len(outcome)},
            )
        else:
            return ToolResult(
                success=False,
                error="Reflection module not available",
                metadata={"reflection_available": False},
            )
    except Exception as e:
        logger.error(f"Prometheus reflect error: {e}")
        return ToolResult(success=False, error=f"Prometheus reflect failed: {str(e)}")


async def prometheus_create_tool(tool_description: str, language: str = "python") -> ToolResult:
    """Generate a new tool dynamically (AutoTools) based on description."""
    try:
        provider = await _ensure_provider()
        await provider._ensure_initialized()

        if hasattr(provider._orchestrator, "tool_factory"):
            new_tool = await provider._orchestrator.tool_factory.create_tool(
                tool_description, language
            )
            return ToolResult(
                success=True,
                data={
                    "tool": "prometheus_create_tool",
                    "description": tool_description,
                    "language": language,
                    "new_tool": new_tool,
                },
                metadata={"tool_factory_available": True, "language": language},
            )
        else:
            return ToolResult(
                success=False,
                error="Tool Factory not available",
                metadata={"tool_factory_available": False},
            )
    except Exception as e:
        logger.error(f"Prometheus create tool error: {e}")
        return ToolResult(success=False, error=f"Prometheus create tool failed: {str(e)}")


async def prometheus_get_status() -> ToolResult:
    """Get full PROMETHEUS system status (memory, world model, evolution)."""
    try:
        provider = await _ensure_provider()

        status = provider.get_status()
        return ToolResult(
            success=True,
            data={"tool": "prometheus_get_status", "status": status},
            metadata={"status_retrieved": True},
        )
    except Exception as e:
        logger.error(f"Prometheus get status error: {e}")
        return ToolResult(success=False, error=f"Prometheus get status failed: {str(e)}")


async def prometheus_benchmark(suite: str = "all") -> ToolResult:
    """Run PROMETHEUS benchmark suite to measure capabilities."""
    try:
        provider = await _ensure_provider()
        await provider._ensure_initialized()

        if hasattr(provider._orchestrator, "run_benchmark"):
            results = await provider._orchestrator.run_benchmark(suite)
            return ToolResult(
                success=True,
                data={
                    "tool": "prometheus_benchmark",
                    "suite": suite,
                    "results": results,
                },
                metadata={"benchmark_available": True, "suite": suite},
            )
        else:
            return ToolResult(
                success=False,
                error="Benchmark capability not available",
                metadata={"benchmark_available": False},
            )
    except Exception as e:
        logger.error(f"Prometheus benchmark error: {e}")
        return ToolResult(success=False, error=f"Prometheus benchmark failed: {str(e)}")


# Create and register all prometheus tools
prometheus_tools = [
    create_validated_tool(
        name="prometheus_execute",
        description="Execute task via PROMETHEUS self-evolving meta-agent with configurable world model and memory usage",
        category="prometheus",
        parameters={
            "task": {
                "type": "string",
                "description": "Task to execute via Prometheus",
                "required": True,
            },
            "use_world_model": {
                "type": "boolean",
                "description": "Enable world model simulation",
                "default": True,
            },
            "use_memory": {
                "type": "boolean",
                "description": "Enable memory system",
                "default": True,
            },
        },
        required_params=["task"],
        execute_func=prometheus_execute,
    ),
    create_validated_tool(
        name="prometheus_memory_query",
        description="Query PROMETHEUS 6-type persistent memory system (MIRIX)",
        category="prometheus",
        parameters={
            "query": {
                "type": "string",
                "description": "Query string for memory search",
                "required": True,
            },
            "memory_type": {
                "type": "string",
                "description": "Type of memory to query (episodic, semantic, procedural, meta, reflective, all)",
                "default": "all",
                "enum": ["episodic", "semantic", "procedural", "meta", "reflective", "all"],
            },
        },
        required_params=["query"],
        execute_func=prometheus_memory_query,
    ),
    create_validated_tool(
        name="prometheus_simulate",
        description="Simulate action via World Model (SimuRA) without executing it",
        category="prometheus",
        parameters={
            "action_plan": {
                "type": "string",
                "description": "Action plan to simulate",
                "required": True,
            }
        },
        required_params=["action_plan"],
        execute_func=prometheus_simulate,
    ),
    create_validated_tool(
        name="prometheus_evolve",
        description="Run self-evolution cycle (Agent0) to improve capabilities",
        category="prometheus",
        parameters={
            "iterations": {
                "type": "integer",
                "description": "Number of evolution iterations",
                "default": 5,
                "minimum": 1,
                "maximum": 50,
            }
        },
        required_params=[],
        execute_func=prometheus_evolve,
    ),
    create_validated_tool(
        name="prometheus_reflect",
        description="Trigger self-reflection on a completed task or action",
        category="prometheus",
        parameters={
            "outcome": {
                "type": "string",
                "description": "Outcome description to reflect on",
                "required": True,
            },
            "task_id": {"type": "string", "description": "Optional task ID for tracking"},
        },
        required_params=["outcome"],
        execute_func=prometheus_reflect,
    ),
    create_validated_tool(
        name="prometheus_create_tool",
        description="Generate a new tool dynamically (AutoTools) based on description",
        category="prometheus",
        parameters={
            "tool_description": {
                "type": "string",
                "description": "Description of the tool to create",
                "required": True,
            },
            "language": {
                "type": "string",
                "description": "Programming language for the tool",
                "default": "python",
                "enum": ["python", "javascript", "typescript", "bash"],
            },
        },
        required_params=["tool_description"],
        execute_func=prometheus_create_tool,
    ),
    create_validated_tool(
        name="prometheus_get_status",
        description="Get full PROMETHEUS system status (memory, world model, evolution)",
        category="prometheus",
        parameters={},
        required_params=[],
        execute_func=prometheus_get_status,
    ),
    create_validated_tool(
        name="prometheus_benchmark",
        description="Run PROMETHEUS benchmark suite to measure capabilities",
        category="prometheus",
        parameters={
            "suite": {
                "type": "string",
                "description": "Benchmark suite to run",
                "default": "all",
                "enum": ["cognitive", "tool_creation", "evolution", "memory", "all"],
            }
        },
        required_params=[],
        execute_func=prometheus_benchmark,
    ),
]

# Register all tools with the global registry
from .registry import register_tool

for tool in prometheus_tools:
    register_tool(tool)
