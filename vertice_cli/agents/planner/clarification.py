"""
Planner Clarification - Clarifying Questions Module (v6.0).

This module provides the clarifying questions workflow inspired by Cursor 2.1:
- Generate targeted questions before planning
- Process user responses
- Enrich task context with clarifications

Philosophy:
    "Ask the right questions before making assumptions."
"""

from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

from .types import ClarifyingQuestion, ClarificationResponse
from .prompts import build_clarifying_questions_prompt
from .utils import robust_json_parse

if TYPE_CHECKING:
    from ..base import AgentTask, AgentResponse
    from .agent import PlannerAgent


async def generate_clarifying_questions(
    agent: "PlannerAgent", task: "AgentTask"
) -> List[ClarifyingQuestion]:
    """
    Generate 2-3 targeted clarifying questions based on the task.

    Inspired by Cursor 2.1's approach of asking questions before planning.

    Args:
        agent: The PlannerAgent instance
        task: The task to analyze

    Returns:
        List of clarifying questions
    """
    prompt = build_clarifying_questions_prompt(task.request, task.context or {})

    try:
        response = await agent._call_llm(prompt)
        data = robust_json_parse(response)

        if data and "questions" in data:
            questions = []
            for q in data["questions"][:3]:  # Max 3 questions
                questions.append(
                    ClarifyingQuestion(
                        question=q.get("question", ""),
                        category=q.get("category", "general"),
                        options=q.get("options", []),
                        required=q.get("required", False),
                    )
                )
            return questions
    except Exception as e:
        agent.logger.warning(f"Failed to generate clarifying questions: {e}")

    # Fallback: Default questions
    return get_default_questions()


def get_default_questions() -> List[ClarifyingQuestion]:
    """Get default clarifying questions when generation fails."""
    return [
        ClarifyingQuestion(
            question="What is the scope of this task? (e.g., single file, module, entire project)",
            category="scope",
            options=["Single file", "Module/directory", "Entire project"],
            required=False,
        ),
        ClarifyingQuestion(
            question="Do you want tests written for the changes?",
            category="preferences",
            options=["Yes, with high coverage", "Basic tests only", "No tests needed"],
            required=False,
        ),
    ]


async def execute_with_clarification(
    agent: "PlannerAgent",
    task: "AgentTask",
    responses: Optional[List[ClarificationResponse]] = None,
) -> "AgentResponse":
    """
    Execute planning with optional clarifying questions.

    This is the v6.0 enhanced entry point that:
    1. Generates clarifying questions (if enabled)
    2. Waits for user responses (via callback)
    3. Incorporates responses into planning
    4. Generates plan with confidence ratings
    5. Creates plan.md artifact

    Args:
        agent: The PlannerAgent instance
        task: The task to plan
        responses: Pre-provided responses (optional)

    Returns:
        AgentResponse with the plan
    """
    from ..base import AgentTask
    from .formatting import generate_confidence_summary

    clarifying_questions: List[ClarifyingQuestion] = []
    clarification_responses: List[ClarificationResponse] = responses or []

    # Step 1: Generate and ask clarifying questions
    if agent.ask_clarifying_questions and not responses:
        clarifying_questions = await generate_clarifying_questions(agent, task)

        if clarifying_questions and agent._question_callback:
            try:
                clarification_responses = agent._question_callback(clarifying_questions)
            except Exception as e:
                agent.logger.warning(f"Question callback failed: {e}")

    # Step 2: Enrich task context with clarification responses
    enriched_context = task.context.copy() if task.context else {}
    enriched_context["clarifications"] = {
        r.question_id: r.answer for r in clarification_responses if not r.skipped
    }

    enriched_task = AgentTask(
        task_id=task.task_id,
        request=task.request,
        context=enriched_context,
        session_id=task.session_id,
        metadata=task.metadata,
    )

    # Step 3: Execute standard planning
    response = await agent.execute(enriched_task)

    # Step 4: Enhance response with v6.0 features
    if response.success and "plan" in response.data:
        plan_data = response.data["plan"]

        if isinstance(plan_data, dict):
            # Add clarifying questions to plan
            plan_data["clarifying_questions"] = [q.model_dump() for q in clarifying_questions]
            plan_data["clarification_responses"] = [r.model_dump() for r in clarification_responses]

            # Calculate overall confidence
            sops = plan_data.get("sops", [])
            if sops:
                confidence_scores = [s.get("confidence_score", 0.7) for s in sops]
                plan_data["overall_confidence"] = sum(confidence_scores) / len(confidence_scores)
                plan_data["confidence_summary"] = generate_confidence_summary(
                    plan_data["overall_confidence"]
                )

            # Generate plan.md artifact
            from .artifact import generate_plan_artifact

            artifact_path = await generate_plan_artifact(agent, plan_data, task)
            if artifact_path:
                plan_data["plan_artifact_path"] = artifact_path

    return response


__all__ = [
    "generate_clarifying_questions",
    "get_default_questions",
    "execute_with_clarification",
]
