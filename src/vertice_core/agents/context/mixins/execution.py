"""
Execution Results Mixin - Manages step execution results.
"""

from typing import Dict, List, Optional

from ..types import ExecutionResult


class ExecutionResultsMixin:
    """Mixin for managing execution results."""

    def __init__(self) -> None:
        self._execution_results: Dict[str, ExecutionResult] = {}

    def add_step_result(self, result: ExecutionResult) -> None:
        """Add execution result for a step."""
        self._execution_results[result.step_id] = result

    def get_step_result(self, step_id: str) -> Optional[ExecutionResult]:
        """Get execution result for a specific step."""
        return self._execution_results.get(step_id)

    def has_failures(self) -> bool:
        """Check if any steps have failed."""
        return any(not result.success for result in self._execution_results.values())

    def get_execution_results(self) -> List[ExecutionResult]:
        """Get all execution results."""
        return list(self._execution_results.values())
