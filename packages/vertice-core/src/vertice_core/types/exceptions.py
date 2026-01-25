"""
Domain Exceptions.

SCALE & SUSTAIN Phase 1.3 - Type Consolidation.

Author: JuanCS Dev
Date: 2025-11-26
"""


class QwenCoreError(Exception):
    """
    Base exception for all vertice_core domain errors.

    This is the legacy base class for exceptions in vertice_core.
    For new code, prefer using VerticeError from vertice_core.exceptions,
    which provides richer context (ErrorContext) and recovery hints.

    Design:
        Simple base class for domain-specific exceptions that don't need
        the full ErrorContext infrastructure. Useful for lightweight
        exceptions in the domain kernel.

    Hierarchy:
        QwenCoreError
        ├── CapabilityViolationError  (capability checks)
        ├── TaskValidationError       (pre-execution validation)
        └── AgentTimeoutError         (execution timeout)
    """

    pass


class CapabilityViolationError(QwenCoreError):
    """
    Raised when an agent attempts to use a capability it doesn't have.

    Example:
        if AgentCapability.BASH_EXEC not in agent.capabilities:
            raise CapabilityViolationError(
                agent_id=agent.id,
                capability="BASH_EXEC",
                message="Agent not authorized for command execution"
            )
    """

    def __init__(self, agent_id: str, capability: str, message: str = ""):
        self.agent_id = agent_id
        self.capability = capability
        super().__init__(
            f"Agent '{agent_id}' lacks capability '{capability}'"
            + (f": {message}" if message else "")
        )


class TaskValidationError(QwenCoreError):
    """
    Raised when task validation fails before agent execution.

    This exception is raised during the pre-execution validation phase
    when a task doesn't meet the requirements for execution.

    Common causes:
        - Missing required fields in task context
        - Invalid task parameters
        - Incompatible task type for the agent
        - Schema validation failures

    Example:
        if not task.context.get("files"):
            raise TaskValidationError("Task requires at least one file")
    """

    pass


class AgentTimeoutError(QwenCoreError):
    """
    Raised when agent execution exceeds the allowed time limit.

    This exception indicates that an agent's execute() method did not
    complete within the configured timeout period.

    Attributes inherited from QwenCoreError allow tracking:
        - Which agent timed out
        - The timeout duration
        - Partial results (if any)

    Example:
        async def execute_with_timeout(agent, task, timeout=30):
            try:
                return await asyncio.wait_for(agent.execute(task), timeout)
            except asyncio.TimeoutError:
                raise AgentTimeoutError(f"Agent timed out after {timeout}s")
    """

    pass


__all__ = [
    "QwenCoreError",
    "CapabilityViolationError",
    "TaskValidationError",
    "AgentTimeoutError",
]
