"""
Prompt templates for Executor Agent.

Centralizes all LLM prompt construction for maintainability.
"""

from typing import Dict, List

from .curriculum_agent import EvolutionTask


class ExecutorPrompts:
    """Prompt templates for executor agent operations."""

    @staticmethod
    def solution_generation(
        task: EvolutionTask,
        experiences_section: str = "",
        procedures_section: str = "",
        tools_section: str = "",
        hints_section: str = "",
    ) -> str:
        """
        Generate prompt for solution generation.

        Args:
            task: The evolution task
            experiences_section: Formatted relevant experiences
            procedures_section: Formatted relevant procedures
            tools_section: Formatted available tools
            hints_section: Formatted hints (if any)

        Returns:
            Complete prompt string
        """
        return f"""Solve this task step by step.

TASK: {task.description}
DIFFICULTY: {task.difficulty.name}
DOMAIN: {task.domain.value}

SUCCESS CRITERIA:
{chr(10).join(f'- {c}' for c in task.success_criteria)}

{experiences_section}
{procedures_section}
{tools_section}
{hints_section}

Think through the problem carefully and provide a complete solution.
If this is a coding task, provide working code.
If this is a reasoning task, show your reasoning step by step.

SOLUTION:"""

    @staticmethod
    def solution_evaluation(task: EvolutionTask, solution: str) -> str:
        """
        Generate prompt for solution evaluation.

        Args:
            task: The evolution task
            solution: The solution to evaluate

        Returns:
            Evaluation prompt string
        """
        return f"""Evaluate this solution against the success criteria.

TASK: {task.description}

SUCCESS CRITERIA:
{chr(10).join(f'- {c}' for c in task.success_criteria)}

SOLUTION:
{solution}

Evaluate each criterion and provide scores in JSON:
{{
    "criterion_scores": {{"criterion": 0.8, ...}},
    "overall_score": 0.0-1.0,
    "errors": ["error 1", "error 2"],
    "what_worked": ["thing that worked"],
    "what_failed": ["thing that failed"]
}}"""

    @staticmethod
    def solution_improvement(
        task: EvolutionTask,
        current_solution: str,
        errors: List[str],
    ) -> str:
        """
        Generate prompt for solution improvement.

        Args:
            task: The evolution task
            current_solution: The current failed solution
            errors: List of errors from evaluation

        Returns:
            Improvement prompt string
        """
        return f"""Your previous solution had errors. Fix them.

TASK: {task.description}

PREVIOUS SOLUTION:
{current_solution}

ERRORS:
{chr(10).join(f'- {e}' for e in errors)}

Analyze what went wrong and provide a corrected solution.
Focus on fixing the specific errors mentioned.

IMPROVED SOLUTION:"""

    @staticmethod
    def format_experiences(relevant_experiences: List[Dict]) -> str:
        """
        Format relevant experiences for prompt.

        Args:
            relevant_experiences: List of experience dicts

        Returns:
            Formatted experiences section
        """
        if not relevant_experiences:
            return ""

        exp_list = [
            f"- {e.get('content', '')[:100]}" for e in relevant_experiences[:3]
        ]
        return "\nRELEVANT EXPERIENCES:\n" + "\n".join(exp_list)

    @staticmethod
    def format_procedures(relevant_procedures: List[Dict]) -> str:
        """
        Format relevant procedures for prompt.

        Args:
            relevant_procedures: List of procedure dicts

        Returns:
            Formatted procedures section
        """
        if not relevant_procedures:
            return ""

        proc_list = [
            f"- {p.get('skill', '')}: {p.get('steps', [])[:2]}"
            for p in relevant_procedures[:3]
        ]
        return "\nRELEVANT PROCEDURES:\n" + "\n".join(proc_list)

    @staticmethod
    def format_tools(tools_list: List[Dict]) -> str:
        """
        Format available tools for prompt.

        Args:
            tools_list: List of tool dicts

        Returns:
            Formatted tools section
        """
        if not tools_list:
            return ""

        formatted = [
            f"- {t['name']}: {t.get('description', 'No description')[:50]}"
            for t in tools_list[:10]
        ]
        return "\nAVAILABLE TOOLS:\n" + "\n".join(formatted)

    @staticmethod
    def format_hints(hints: List[str]) -> str:
        """
        Format hints for prompt.

        Args:
            hints: List of hint strings

        Returns:
            Formatted hints section
        """
        if not hints:
            return ""

        return "\nHINTS:\n" + "\n".join(f"- {h}" for h in hints)
