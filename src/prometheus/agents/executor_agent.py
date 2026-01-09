"""
Executor Agent - Learns to solve tasks.

Reference: Agent0 (arXiv:2511.16043)
- Co-evolution with Curriculum Agent
- Learns from both successes and failures
- Develops skills progressively

The Executor Agent is responsible for:
1. Attempting to solve generated tasks
2. Learning from successes and failures
3. Developing and improving skills
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple
from datetime import datetime
import logging

from prometheus.agents.curriculum_agent import EvolutionTask, TaskDifficulty, TaskDomain
from prometheus.agents.skills import SkillDetector, SkillProfile
from prometheus.agents.utils.parsers import JSONResponseParser
from prometheus.agents.testing import TestRunner
from prometheus.agents.prompts import ExecutorPrompts

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a task."""

    task: EvolutionTask
    solution: str
    success: bool
    score: float  # 0-1
    time_taken: float  # seconds
    skills_demonstrated: List[str]
    errors_made: List[str]
    reflection: str = ""
    improvement_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "task_id": self.task.id,
            "success": self.success,
            "score": self.score,
            "time_taken": self.time_taken,
            "skills": self.skills_demonstrated,
            "errors": self.errors_made,
        }


class ExecutorAgent:
    """
    Learns to solve tasks through practice.

    Develops skills progressively through the co-evolution loop.
    """

    def __init__(
        self,
        llm_client,
        tool_factory,
        memory_system,
        reflection_engine,
        sandbox_executor,
    ):
        self.llm = llm_client
        self.tools = tool_factory
        self.memory = memory_system
        self.reflection = reflection_engine
        self.sandbox = sandbox_executor

        # Initialize helper modules
        self.skill_detector = SkillDetector()
        self.test_runner = TestRunner(sandbox_executor)
        self.json_parser = JSONResponseParser()
        self.prompts = ExecutorPrompts()

        # State
        self.skills: Dict[str, SkillProfile] = {}
        self.execution_history: List[ExecutionResult] = []

        # Performance tracking
        self._total_attempts = 0
        self._total_successes = 0

    async def attempt_task(
        self,
        task: EvolutionTask,
        use_hints: bool = False,
        max_retries: int = 2,
    ) -> ExecutionResult:
        """
        Attempt to solve a task.

        Process:
        1. Plan approach
        2. Execute with available tools
        3. Evaluate result
        4. Learn from experience
        """
        start_time = datetime.now()

        # Get relevant context from memory
        context = self.memory.get_context_for_task(task.description)

        # Format hints if requested and available
        hints_section = ""
        if use_hints and task.hints:
            hints_section = self.prompts.format_hints(task.hints)

        # Plan and execute
        solution = await self._generate_solution(task, context, hints_section)

        # Evaluate the solution
        score, errors = await self._evaluate_solution(task, solution)

        # Retry if failed and retries available
        retry_count = 0
        while score < 0.7 and retry_count < max_retries:
            retry_count += 1
            # Get feedback and try again
            improved_solution = await self._improve_solution(task, solution, errors, context)
            solution = improved_solution
            score, errors = await self._evaluate_solution(task, solution)

        end_time = datetime.now()
        time_taken = (end_time - start_time).total_seconds()

        # Identify skills demonstrated
        skills_demonstrated = self.skill_detector.identify_skills(solution, task.expected_skills)

        # Create result
        result = ExecutionResult(
            task=task,
            solution=solution,
            success=score >= 0.7,
            score=score,
            time_taken=time_taken,
            skills_demonstrated=skills_demonstrated,
            errors_made=errors,
        )

        # Learn from the attempt
        await self._learn_from_result(result)

        # Store in history
        self.execution_history.append(result)
        self._total_attempts += 1
        if result.success:
            self._total_successes += 1

        return result

    async def _generate_solution(
        self,
        task: EvolutionTask,
        context: dict,
        hints_section: str = "",
    ) -> str:
        """Generate a solution for the task."""
        # Format context sections using prompts module
        experiences_section = self.prompts.format_experiences(
            context.get("relevant_experiences", [])
        )
        procedures_section = self.prompts.format_procedures(context.get("relevant_procedures", []))
        tools_section = self.prompts.format_tools(self.tools.list_tools())

        # Generate prompt
        prompt = self.prompts.solution_generation(
            task,
            experiences_section=experiences_section,
            procedures_section=procedures_section,
            tools_section=tools_section,
            hints_section=hints_section,
        )

        return await self.llm.generate(prompt)

    async def _evaluate_solution(
        self,
        task: EvolutionTask,
        solution: str,
    ) -> Tuple[float, List[str]]:
        """Evaluate a solution against task criteria."""
        errors = []

        # If there are test cases, run them
        if task.test_cases and task.domain == TaskDomain.CODE:
            test_score, test_errors = await self.test_runner.run_test_cases(task, solution)
            errors.extend(test_errors)
            if test_score is not None:
                return test_score, errors

        # LLM-based evaluation
        prompt = self.prompts.solution_evaluation(task, solution)
        response = await self.llm.generate(prompt)
        data = self.json_parser.parse(response)

        errors.extend(data.get("errors", []))
        errors.extend(data.get("what_failed", []))

        return data.get("overall_score", 0.5), errors

    async def _improve_solution(
        self,
        task: EvolutionTask,
        current_solution: str,
        errors: List[str],
        context: dict,
    ) -> str:
        """Improve a failed solution."""
        prompt = self.prompts.solution_improvement(task, current_solution, errors)
        return await self.llm.generate(prompt)

    async def _learn_from_result(self, result: ExecutionResult):
        """Learn from task execution result."""
        # Update skill profiles
        for skill in result.skills_demonstrated:
            if skill not in self.skills:
                self.skills[skill] = SkillProfile(name=skill, proficiency=0.5)
            self.skills[skill].update(result.success)

        # Store experience in memory
        outcome = "SUCCESS" if result.success else "FAILURE"
        self.memory.remember_experience(
            experience=f"Task: {result.task.description[:100]}",
            outcome=f"{outcome} (score: {result.score:.2f})",
            context={
                "errors": result.errors_made,
                "skills": result.skills_demonstrated,
                "difficulty": result.task.difficulty.name,
            },
            importance=result.score if result.success else 1 - result.score,
        )

        # If failed, do deeper reflection
        if not result.success and result.errors_made:
            reflection_result = await self.reflection.critique_action(
                action=f"Attempted task: {result.task.description[:100]}",
                result=f"Failed with score {result.score:.2f}. Errors: {result.errors_made}",
                context={"solution": result.solution[:500]},
            )
            result.reflection = reflection_result.critique
            result.improvement_notes = reflection_result.improvements

            # Learn procedure from reflection
            if reflection_result.lessons_learned:
                self.memory.learn_procedure(
                    skill_name=f"avoid_error_{result.task.domain.value}",
                    steps=reflection_result.lessons_learned,
                )

    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        if not self.execution_history:
            return {
                "total_attempts": 0,
                "success_rate": 0.0,
                "current_frontier": TaskDifficulty.EASY.name,
                "skills_mastered": [],
                "skills_to_improve": [],
            }

        # Calculate success rates by difficulty
        by_difficulty = {}
        for result in self.execution_history:
            diff = result.task.difficulty.name
            if diff not in by_difficulty:
                by_difficulty[diff] = {"attempts": 0, "successes": 0}
            by_difficulty[diff]["attempts"] += 1
            if result.success:
                by_difficulty[diff]["successes"] += 1

        # Determine current frontier (highest difficulty with >40% success)
        current_frontier = TaskDifficulty.EASY
        for d in TaskDifficulty:
            if d.name in by_difficulty:
                data = by_difficulty[d.name]
                rate = data["successes"] / data["attempts"]
                if rate > 0.4:
                    current_frontier = d

        # Categorize skills
        mastered = [s for s, p in self.skills.items() if p.proficiency > 0.8]
        to_improve = [s for s, p in self.skills.items() if 0.3 < p.proficiency < 0.7]

        return {
            "total_attempts": self._total_attempts,
            "total_successes": self._total_successes,
            "success_rate": self._total_successes / max(self._total_attempts, 1),
            "current_frontier": current_frontier.name,
            "current_level": current_frontier.name,
            "skills_mastered": mastered,
            "skills_to_improve": to_improve,
            "skill_count": len(self.skills),
            "by_difficulty": {
                d: {"rate": data["successes"] / data["attempts"], "attempts": data["attempts"]}
                for d, data in by_difficulty.items()
            },
        }

    def get_skill_report(self) -> Dict[str, Any]:
        """Get detailed skill report."""
        return {
            skill: {
                "proficiency": round(profile.proficiency, 3),
                "practice_count": profile.practice_count,
                "last_practiced": (
                    profile.last_practiced.isoformat() if profile.last_practiced else None
                ),
                "recent_success_rate": sum(profile.success_history[-10:])
                / max(len(profile.success_history[-10:]), 1),
            }
            for skill, profile in self.skills.items()
        }

    def export_state(self) -> dict:
        """Export executor state."""
        return {
            "stats": self.get_stats(),
            "skills": self.get_skill_report(),
            "history_size": len(self.execution_history),
        }

    def import_state(self, state: dict) -> None:
        """Import executor state (stats and skills are read-only, so this is a no-op)."""
        # Note: execution_history and stats are runtime-generated
        # and don't need restoration from persistence
        pass
