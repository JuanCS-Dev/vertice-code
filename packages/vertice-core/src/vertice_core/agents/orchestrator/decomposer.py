"""
Task Decomposer - LLM + heuristic task decomposition engine.

Breaks down user requests into atomic, actionable tasks.
Uses LLM when available, falls back to pattern-based heuristics.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, List, Optional, Tuple

from .types import Task, TaskComplexity

logger = logging.getLogger(__name__)


class TaskDecomposer:
    """
    Task decomposition engine.

    Analyzes user requests and breaks them into atomic tasks
    using LLM-based semantic decomposition or pattern-based heuristics.
    """

    # Phase keywords for multi-phase detection
    PHASE_KEYWORDS = [
        ("plan", "Planning"),
        ("design", "Design"),
        ("architect", "Architecture"),
        ("implement", "Implementation"),
        ("create", "Creation"),
        ("build", "Building"),
        ("code", "Coding"),
        ("test", "Testing"),
        ("review", "Review"),
        ("refactor", "Refactoring"),
        ("deploy", "Deployment"),
        ("document", "Documentation"),
    ]

    # Indicators of complex multi-phase tasks
    COMPLEX_INDICATORS = [
        "complete system",
        "full implementation",
        "entire application",
        "from scratch",
        "end to end",
        "comprehensive",
        "production ready",
    ]

    def __init__(self, llm_client: Optional[Any] = None) -> None:
        self._llm = llm_client

    async def decompose(self, user_request: str) -> List[Task]:
        """
        Decompose user request into executable tasks.

        Args:
            user_request: The user's request.

        Returns:
            List of tasks to execute in order.
        """
        complexity = await self.analyze_complexity(user_request)

        # Try LLM-based decomposition first
        if self._llm is not None:
            tasks = await self._decompose_with_llm(user_request, complexity)
            if tasks:
                return tasks

        # Fallback: Intelligent heuristic decomposition
        return await self._decompose_heuristic(user_request, complexity)

    async def analyze_complexity(self, request: str) -> TaskComplexity:
        """Analyze request complexity for routing decisions."""
        word_count = len(request.split())

        if word_count < 10:
            return TaskComplexity.SIMPLE
        elif word_count < 50:
            return TaskComplexity.MODERATE
        elif "architecture" in request.lower() or "design" in request.lower():
            return TaskComplexity.COMPLEX
        elif "production" in request.lower() or "security" in request.lower():
            return TaskComplexity.CRITICAL
        else:
            return TaskComplexity.MODERATE

    async def _decompose_with_llm(
        self,
        user_request: str,
        complexity: TaskComplexity,
    ) -> List[Task]:
        """
        Use LLM to decompose request into atomic tasks.

        Returns empty list if LLM unavailable or fails.
        """
        try:
            prompt = f"""Decompose this request into atomic, actionable tasks.

Request: {user_request}

Return a JSON array of tasks. Each task should be:
- Atomic (can be done in one step)
- Actionable (clear what to do)
- Independent or with clear dependencies

Format:
[
  {{"id": "1", "description": "First task", "depends_on": []}},
  {{"id": "2", "description": "Second task", "depends_on": ["1"]}}
]

Only return the JSON array, nothing else."""

            response = await self._llm.generate(prompt)
            return self._parse_task_list(response, complexity)

        except Exception as e:
            logger.warning(f"LLM decomposition failed: {e}")
            return []

    async def _decompose_heuristic(
        self,
        user_request: str,
        complexity: TaskComplexity,
    ) -> List[Task]:
        """
        Heuristic-based task decomposition.

        Uses patterns and keywords to identify multiple components
        in the request and creates separate tasks for each.
        """
        request_lower = user_request.lower()
        tasks: List[Task] = []

        # Pattern 1: Check for multi-phase keywords FIRST
        phases = self._extract_phases(request_lower)
        if len(phases) > 1:
            return self._create_phase_tasks(user_request, phases, complexity)

        # Pattern 2: Explicit list with "with", ",", "and" for features
        components = self._extract_components(user_request)

        if len(components) > 1:
            for i, component in enumerate(components):
                task = Task(
                    id=f"task-{i+1}",
                    description=component.strip(),
                    complexity=self._component_complexity(component, complexity),
                    parent_task=None if i == 0 else "task-1",
                )
                tasks.append(task)
            return tasks

        # Pattern 3: Complex request indicators
        if self._is_complex_request(request_lower):
            standard_phases = [
                ("Design", f"Design the architecture for: {user_request}"),
                ("Implement", f"Implement the core functionality: {user_request}"),
                ("Test", f"Create tests for: {user_request}"),
            ]
            for i, (phase, desc) in enumerate(standard_phases):
                task = Task(
                    id=f"task-{i+1}",
                    description=desc,
                    complexity=complexity,
                )
                tasks.append(task)
            return tasks

        # Default: Single task (simple request)
        return [
            Task(
                id="task-1",
                description=user_request,
                complexity=complexity,
            )
        ]

    def _create_phase_tasks(
        self,
        user_request: str,
        phases: List[Tuple[str, str]],
        complexity: TaskComplexity,
    ) -> List[Task]:
        """
        Create tasks from detected phases.

        Extracts the target object and creates one task per phase.
        """
        request_lower = user_request.lower()

        # Extract the object being worked on
        phase_keywords = "|".join([p[0] for p in phases])

        # Remove "and", "then", commas, and phase keywords
        cleaned = re.sub(
            rf"\b({phase_keywords})\b|\band\b|\bthen\b|,",
            "",
            request_lower,
        ).strip()

        # Clean up extra spaces
        target_object = " ".join(cleaned.split())

        # If nothing left, use original request
        if not target_object or len(target_object) < 3:
            target_object = user_request

        tasks = []
        for i, (phase, phase_desc) in enumerate(phases):
            task_desc = f"{phase_desc} {target_object}"
            task = Task(
                id=f"task-{i+1}",
                description=task_desc.strip(),
                complexity=complexity,
                subtasks=[f"task-{i+2}"] if i < len(phases) - 1 else [],
            )
            tasks.append(task)

        return tasks

    def _extract_components(self, request: str) -> List[str]:
        """
        Extract distinct components from request.

        Keeps the base context and extracts individual features.
        """
        # Try to find the base action and object
        with_match = re.match(
            r"^(.+?)\s+(?:with|including|featuring|that has|having)\s+(.+)$",
            request,
            re.IGNORECASE,
        )

        if with_match:
            base_action = with_match.group(1).strip()
            features_part = with_match.group(2).strip()

            # Split the features
            features = re.split(r",\s*(?:and\s+)?|\s+and\s+", features_part)
            features = [f.strip() for f in features if len(f.strip()) > 2]

            if len(features) > 1:
                components = []
                for feature in features:
                    component_desc = f"Implement {feature} for {base_action}"
                    components.append(component_desc)
                return components

        # Fallback: simple split by "and" for lists
        parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", request)
        components = [p.strip() for p in parts if len(p.strip()) > 5]

        return components if len(components) > 1 else [request]

    def _extract_phases(self, request_lower: str) -> List[Tuple[str, str]]:
        """Extract sequential phases from request."""
        found_phases = []
        for keyword, phase_name in self.PHASE_KEYWORDS:
            if keyword in request_lower:
                found_phases.append((keyword, phase_name))

        return found_phases

    def _is_complex_request(self, request_lower: str) -> bool:
        """Check if request indicates a complex multi-phase task."""
        return any(ind in request_lower for ind in self.COMPLEX_INDICATORS)

    def _component_complexity(
        self,
        component: str,
        base_complexity: TaskComplexity,
    ) -> TaskComplexity:
        """Determine complexity of a component."""
        component_lower = component.lower()

        if any(w in component_lower for w in ["security", "authentication", "production"]):
            return TaskComplexity.CRITICAL
        elif any(w in component_lower for w in ["architecture", "design", "system"]):
            return TaskComplexity.COMPLEX
        elif any(w in component_lower for w in ["simple", "basic", "add"]):
            return TaskComplexity.SIMPLE

        return base_complexity

    def _parse_task_list(
        self,
        response: str,
        complexity: TaskComplexity,
    ) -> List[Task]:
        """Parse LLM response into Task list."""
        try:
            # Extract JSON from response
            start = response.find("[")
            end = response.rfind("]") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)

                tasks = []
                for item in data:
                    task = Task(
                        id=f"task-{item.get('id', len(tasks)+1)}",
                        description=item.get("description", ""),
                        complexity=complexity,
                    )
                    tasks.append(task)

                return tasks if tasks else []

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse task list: {e}")

        return []
