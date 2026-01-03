"""
Tree-of-Thought Planning - Multi-path exploration for workflows.

Implements Claude pattern + Constitutional Layer 2:
- Multi-path exploration
- Constitutional scoring (P1, P2, P6)
- Best path selection
"""

import logging
from typing import Any, List

from .models import ThoughtPath, WorkflowStep

logger = logging.getLogger(__name__)


class TreeOfThought:
    """
    Tree-of-Thought planning (Claude pattern + Constitutional Layer 2).

    Features:
    - Multi-path exploration
    - Constitutional scoring
    - Best path selection
    """

    def __init__(self, llm_client: Any = None) -> None:
        self.llm = llm_client

    async def generate_paths(
        self,
        user_goal: str,
        available_tools: List[str],
        max_paths: int = 3
    ) -> List[ThoughtPath]:
        """
        Generate multiple solution paths.

        Args:
            user_goal: User's goal
            available_tools: Available tools
            max_paths: Max paths to generate

        Returns:
            List of thought paths
        """
        if self.llm is None:
            # Fallback: single naive path
            return [self._generate_naive_path(user_goal, available_tools)]

        try:
            # Use LLM to brainstorm approaches
            prompt = self._build_brainstorm_prompt(user_goal, available_tools)

            response = await self.llm.generate_async(
                messages=[
                    {"role": "system", "content": self._get_planning_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Higher for creativity
                max_tokens=1000
            )

            # Parse LLM response into paths
            paths = self._parse_paths(response.get("content", ""), user_goal)

            # Limit to max_paths
            return paths[:max_paths]

        except Exception as e:
            logger.error(f"LLM path generation failed: {e}")
            return [self._generate_naive_path(user_goal, available_tools)]

    def _get_planning_system_prompt(self) -> str:
        """System prompt for planning."""
        return """You are an expert workflow planner. Generate multiple approaches to solve tasks.

For each approach:
1. List the steps needed
2. Explain pros and cons
3. Estimate complexity

Format:
PATH 1: [Name]
Steps:
1. tool_name(args)
2. tool_name(args)
Pros: ...
Cons: ...
Complexity: Low/Medium/High

PATH 2: [Name]
...

Be creative and consider different strategies."""

    def _build_brainstorm_prompt(self, goal: str, tools: List[str]) -> str:
        """Build brainstorming prompt."""
        tools_str = ", ".join(tools)
        return f"""Generate 3 different approaches to: "{goal}"

Available tools: {tools_str}

Think about:
- Direct approach (fastest)
- Safe approach (most reliable)
- Smart approach (most efficient)

Generate 3 distinct paths."""

    def _parse_paths(self, llm_response: str, goal: str) -> List[ThoughtPath]:
        """Parse LLM response into paths."""
        paths = []

        # Simple parsing (production would be more robust)
        path_sections = llm_response.split("PATH ")

        for i, section in enumerate(path_sections[1:], 1):  # Skip first split
            lines = section.strip().split('\n')
            if not lines:
                continue

            path = ThoughtPath(
                path_id=f"path_{i}",
                description=lines[0].split(':', 1)[-1].strip() if ':' in lines[0] else f"Approach {i}",
                steps=[]
            )

            # Extract steps (simplified)
            # Production would parse more carefully
            paths.append(path)

        return paths if paths else [self._generate_naive_path(goal, [])]

    def _generate_naive_path(self, goal: str, tools: List[str]) -> ThoughtPath:
        """Generate simple fallback path."""
        return ThoughtPath(
            path_id="naive_path",
            description="Direct approach",
            steps=[],
            completeness_score=0.7,
            validation_score=0.7,
            efficiency_score=0.7,
            total_score=0.7
        )

    def score_paths(self, paths: List[ThoughtPath]) -> List[ThoughtPath]:
        """
        Score paths using Constitutional criteria.

        Args:
            paths: Paths to score

        Returns:
            Paths sorted by score (best first)
        """
        for path in paths:
            # P1: Completeness (are all steps defined?)
            path.completeness_score = self._score_completeness(path)

            # P2: Validation (can we verify results?)
            path.validation_score = self._score_validation(path)

            # P6: Efficiency (is it efficient?)
            path.efficiency_score = self._score_efficiency(path)

            # Total score
            path.calculate_score()

        return sorted(paths, key=lambda p: p.total_score, reverse=True)

    def _score_completeness(self, path: ThoughtPath) -> float:
        """Score path completeness."""
        if not path.steps:
            return 0.5  # No steps defined yet

        # Check if steps have all required info
        complete_steps = sum(
            1 for step in path.steps
            if step.tool_name and step.args is not None
        )

        return complete_steps / len(path.steps) if path.steps else 0.5

    def _score_validation(self, path: ThoughtPath) -> float:
        """Score path validation capability."""
        # Paths with test/verify steps score higher
        has_validation = any(
            'test' in step.tool_name.lower() or 'verify' in step.tool_name.lower()
            for step in path.steps
        )

        return 0.9 if has_validation else 0.6

    def _score_efficiency(self, path: ThoughtPath) -> float:
        """Score path efficiency."""
        if not path.steps:
            return 0.5

        # Shorter paths are more efficient (but not too short)
        num_steps = len(path.steps)

        if num_steps <= 3:
            return 0.9
        elif num_steps <= 6:
            return 0.7
        else:
            return 0.5

    def select_best_path(self, paths: List[ThoughtPath]) -> ThoughtPath:
        """Select best path after scoring."""
        scored_paths = self.score_paths(paths)
        return scored_paths[0] if scored_paths else paths[0]
