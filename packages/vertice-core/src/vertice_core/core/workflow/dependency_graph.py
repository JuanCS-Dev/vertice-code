"""
Dependency Graph - DAG-based workflow ordering.

Implements Cursor AI pattern for workflow orchestration:
- Topological sort for execution order
- Cycle detection
- Parallel execution identification
"""

from typing import Dict, List, Tuple

from .models import WorkflowStep


class DependencyGraph:
    """
    Dependency graph for workflow steps (Cursor AI pattern).

    Features:
    - Topological sort for execution order
    - Cycle detection
    - Parallel execution identification
    """

    def __init__(self) -> None:
        self.nodes: Dict[str, WorkflowStep] = {}
        self.edges: List[Tuple[str, str]] = []  # (from, to)

    def add_step(self, step: WorkflowStep) -> None:
        """Add step to graph."""
        self.nodes[step.step_id] = step

        # Add edges for dependencies
        for dep_id in step.dependencies:
            self.edges.append((dep_id, step.step_id))

    def topological_sort(self) -> List[WorkflowStep]:
        """
        Sort steps respecting dependencies.

        Returns:
            Ordered list of steps

        Raises:
            ValueError: If cycle detected
        """
        # Calculate in-degrees
        in_degree = {node_id: 0 for node_id in self.nodes}

        for from_id, to_id in self.edges:
            in_degree[to_id] += 1

        # Queue nodes with no dependencies
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Pick node with no dependencies
            node_id = queue.pop(0)
            result.append(self.nodes[node_id])

            # Remove edges from this node
            for from_id, to_id in self.edges:
                if from_id == node_id:
                    in_degree[to_id] -= 1
                    if in_degree[to_id] == 0:
                        queue.append(to_id)

        # Check for cycles
        if len(result) != len(self.nodes):
            raise ValueError("Dependency cycle detected in workflow")

        return result

    def find_parallel_groups(self) -> List[List[WorkflowStep]]:
        """
        Find steps that can execute in parallel.

        Returns:
            List of groups, where each group can run in parallel
        """
        sorted_steps = self.topological_sort()
        groups: List[List[WorkflowStep]] = []

        processed = set()

        for step in sorted_steps:
            # Check if all dependencies are processed
            deps_ready = all(dep in processed for dep in step.dependencies)

            if deps_ready:
                # Find which group this belongs to
                found_group = False
                for group in groups:
                    # Can add to group if no dependencies within group
                    if not any(dep_step.step_id in step.dependencies for dep_step in group):
                        group.append(step)
                        found_group = True
                        break

                if not found_group:
                    groups.append([step])

                processed.add(step.step_id)

        return groups
