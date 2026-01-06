"""
Prometheus Event Definitions.

Defines the event schema for the Prometheus meta-agent ecosystem.
Inherits from Vertice's core Event system for compatibility.

Events:
- PrometheusTaskReceived: New task accepted
- PrometheusStepExecuted: Reasoning/Action step completed
- PrometheusTaskCompleted: Task finished successfully
- PrometheusTaskFailed: Task failed with error
- PrometheusReflection: Self-correction triggered
- PrometheusEvolution: Agent0 skill learned

Phase 2 of Prometheus Integration Roadmap v2.3.
Created with love by: JuanCS Dev & Claude Opus 4.5
Date: 2026-01-06
"""

from dataclasses import dataclass

from vertice_core.messaging.events import Event


@dataclass
class PrometheusEvent(Event):
    """Base class for all Prometheus events."""

    source: str = "prometheus"


@dataclass
class PrometheusTaskReceived(PrometheusEvent):
    """
    Emitted when a new task is accepted by the agent.

    Data:
        task_id (str): Unique task identifier
        request (str): Original user request
        complexity (str): complexity level (simple, complex, etc.)
    """

    pass


@dataclass
class PrometheusStepExecuted(PrometheusEvent):
    """
    Emitted when a reasoning or execution step completes.

    Data:
        task_id (str): Task identifier
        step_index (int): Current step number
        action (str): Action taken (e.g., "reasoning", "tool_use")
        output (str): Brief output or summary
        duration_ms (float): Execution time in milliseconds
    """

    pass


@dataclass
class PrometheusTaskCompleted(PrometheusEvent):
    """
    Emitted when a task finishes successfully.

    Data:
        task_id (str): Task identifier
        result (str): Final answer or output
        total_steps (int): Total steps executed
        total_duration_ms (float): Total time taken
    """

    pass


@dataclass
class PrometheusTaskFailed(PrometheusEvent):
    """
    Emitted when a task fails.

    Data:
        task_id (str): Task identifier
        error (str): Error message
        error_type (str): Exception class name
        failed_at_step (int): Step number where failure occurred
    """

    pass


@dataclass
class PrometheusReflection(PrometheusEvent):
    """
    Emitted when the Reflexion engine triggers a self-correction.

    Data:
        task_id (str): Task identifier
        critique (str): Self-critique content
        correction (str): Proposed plan adjustment
    """

    pass


@dataclass
class PrometheusEvolution(PrometheusEvent):
    """
    Emitted when Agent0 learns a new skill or evolves.

    Data:
        skill_name (str): Name of the learned skill
        success_rate (float): Performance metric
        evolution_generation (int): Current generation index
    """

    pass
