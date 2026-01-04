"""
planner/multi_planning.py: Multi-Plan Generation (v6.1).

Implements Verbalized Sampling (Zhang et al. 2025) for generating
multiple alternative execution plans with probability estimates.

Features:
- STANDARD: Conventional, low-risk path
- ACCELERATOR: High-speed, higher-risk approach
- LATERAL: Creative/unconventional solution

Each plan includes verbalized probabilities:
- P(Success): Probability of achieving the goal
- P(Friction): Probability of encountering blockers
- P(Quality): Probability of high-quality output

Following CODE_CONSTITUTION.md:
- <500 lines
- 100% type hints
- Zero placeholders
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple

from .types import (
    AlternativePlan,
    MultiPlanResult,
    PlanStrategy,
)


async def generate_multi_plan(
    task_request: str,
    gather_context_fn: Callable[[], Coroutine[Any, Any, Dict[str, Any]]],
    call_llm_fn: Callable[[str], Coroutine[Any, Any, str]],
    parse_json_fn: Callable[[str], Dict[str, Any]],
    strategies: Optional[List[PlanStrategy]] = None,
    logger: Optional[Any] = None,
) -> MultiPlanResult:
    """
    Generate multiple alternative plans using Verbalized Sampling.

    Based on Zhang et al. (2025) - instead of generating one "average" plan,
    we explore the latent space of possibilities with distinct approaches.

    Args:
        task_request: The task description
        gather_context_fn: Async function to gather context
        call_llm_fn: Async function to call LLM
        parse_json_fn: Function to parse JSON from LLM response
        strategies: List of strategies to generate (default: all three)
        logger: Optional logger

    Returns:
        MultiPlanResult with all plans and recommendation
    """
    start_time = time.time()

    strategies = strategies or [
        PlanStrategy.STANDARD,
        PlanStrategy.ACCELERATOR,
        PlanStrategy.LATERAL,
    ]

    # Gather context once
    context = await gather_context_fn()

    # Generate each plan type
    plans: List[AlternativePlan] = []

    for strategy in strategies:
        try:
            plan = await _generate_plan_variant(
                task_request, context, strategy, call_llm_fn, parse_json_fn
            )
            if plan:
                plans.append(plan)
        except Exception as e:
            if logger:
                logger.warning(f"Failed to generate {strategy.value} plan: {e}")

    # If no plans generated, create a basic standard plan
    if not plans:
        basic_plan = create_fallback_plan(task_request, PlanStrategy.STANDARD)
        plans.append(basic_plan)

    # Select best plan
    recommended, reasoning = select_best_plan(plans)

    # Build comparison summary
    comparison = build_comparison_summary(plans)

    generation_time = int((time.time() - start_time) * 1000)

    return MultiPlanResult(
        task_summary=task_request[:200],
        plans=plans,
        recommended_plan=recommended,
        recommendation_reasoning=reasoning,
        comparison_summary=comparison,
        generation_time_ms=generation_time,
    )


async def _generate_plan_variant(
    task_request: str,
    context: Dict[str, Any],
    strategy: PlanStrategy,
    call_llm_fn: Callable[[str], Coroutine[Any, Any, str]],
    parse_json_fn: Callable[[str], Dict[str, Any]],
) -> Optional[AlternativePlan]:
    """Generate a single plan variant for a specific strategy."""

    strategy_prompts = {
        PlanStrategy.STANDARD: """
Generate a STANDARD plan - the conventional, low-risk approach.
Focus on:
- Proven patterns and best practices
- Step-by-step sequential execution
- Comprehensive validation at each step
- Prefer stability over speed
""",
        PlanStrategy.ACCELERATOR: """
Generate an ACCELERATOR plan - high-speed, parallel execution approach.
Focus on:
- Maximum parallelization of independent tasks
- Aggressive timelines
- Minimal validation (fail-fast approach)
- Accept higher risk for faster delivery
""",
        PlanStrategy.LATERAL: """
Generate a LATERAL plan - creative, unconventional approach.
Focus on:
- Alternative solutions that others might not consider
- Novel use of tools or patterns
- Potential shortcuts or innovations
- "What if we approached this completely differently?"
""",
    }

    prompt = f"""You are generating a {strategy.value.upper()} execution plan.

TASK: {task_request}

CONTEXT:
{json.dumps(context, indent=2)}

{strategy_prompts.get(strategy, "")}

Generate a plan with VERBALIZED PROBABILITIES. Think explicitly about:
- P(Success): How likely is this approach to succeed? (0.0-1.0)
- P(Friction): How likely are we to hit blockers? (0.0-1.0)
- P(TimeOverrun): How likely to take longer than estimated? (0.0-1.0)
- P(Quality): How likely to produce high-quality output? (0.0-1.0)

OUTPUT JSON FORMAT:
{{
  "name": "Short descriptive name for this plan variant",
  "description": "Brief description of the approach",
  "p_success": 0.XX,
  "p_friction": 0.XX,
  "p_time_overrun": 0.XX,
  "p_quality": 0.XX,
  "pros": ["advantage 1", "advantage 2"],
  "cons": ["disadvantage 1", "disadvantage 2"],
  "best_for": "When this plan is the best choice",
  "sops": [
    {{
      "id": "step-1",
      "role": "agent_role",
      "action": "What to do",
      "objective": "Why",
      "definition_of_done": "Success criteria",
      "dependencies": [],
      "cost": 1.0,
      "confidence_score": 0.XX
    }}
  ]
}}

RESPOND WITH PURE JSON ONLY."""

    response = await call_llm_fn(prompt)
    data = parse_json_fn(response)

    if not data:
        return None

    return AlternativePlan(
        strategy=strategy,
        name=data.get("name", f"{strategy.value.title()} Plan"),
        description=data.get("description", ""),
        plan=data,
        p_success=float(data.get("p_success", 0.7)),
        p_friction=float(data.get("p_friction", 0.3)),
        p_time_overrun=float(data.get("p_time_overrun", 0.3)),
        p_quality=float(data.get("p_quality", 0.7)),
        pros=data.get("pros", []),
        cons=data.get("cons", []),
        best_for=data.get("best_for", ""),
    )


def create_fallback_plan(task_request: str, strategy: PlanStrategy) -> AlternativePlan:
    """Create a basic fallback plan when LLM generation fails."""
    return AlternativePlan(
        strategy=strategy,
        name="Basic Sequential Plan",
        description="Fallback plan with standard sequential execution",
        plan={
            "sops": [
                {
                    "id": "step-1",
                    "role": "architect",
                    "action": "Analyze and plan",
                    "objective": "Understand requirements",
                    "definition_of_done": "Plan documented",
                    "cost": 2.0,
                },
                {
                    "id": "step-2",
                    "role": "coder",
                    "action": "Implement solution",
                    "objective": "Write code",
                    "definition_of_done": "Code compiles",
                    "dependencies": ["step-1"],
                    "cost": 5.0,
                },
                {
                    "id": "step-3",
                    "role": "tester",
                    "action": "Test implementation",
                    "objective": "Verify correctness",
                    "definition_of_done": "Tests pass",
                    "dependencies": ["step-2"],
                    "cost": 3.0,
                },
            ]
        },
        p_success=0.7,
        p_friction=0.3,
        p_time_overrun=0.4,
        p_quality=0.6,
        pros=["Simple and predictable", "Easy to follow"],
        cons=["May not be optimal", "No parallelization"],
        best_for="When other approaches fail or for simple tasks",
    )


def select_best_plan(
    plans: List[AlternativePlan],
) -> Tuple[PlanStrategy, str]:
    """
    Select the best plan based on overall score.

    Uses a weighted scoring system that considers:
    - Success probability (most important)
    - Friction probability (risk factor)
    - Quality probability
    - Time overrun probability
    """
    if not plans:
        return PlanStrategy.STANDARD, "No plans available, defaulting to standard"

    # Sort by overall score
    sorted_plans = sorted(plans, key=lambda p: p.overall_score, reverse=True)
    best = sorted_plans[0]

    # Build reasoning
    reasoning_parts = [
        f"Selected {best.strategy.value.upper()} with score {best.overall_score:.2f}.",
    ]

    if best.p_success >= 0.8:
        reasoning_parts.append(f"High success probability ({best.p_success:.0%}).")
    if best.p_friction <= 0.3:
        reasoning_parts.append(f"Low friction risk ({best.p_friction:.0%}).")

    # Compare to alternatives
    if len(sorted_plans) > 1:
        runner_up = sorted_plans[1]
        score_diff = best.overall_score - runner_up.overall_score
        if score_diff < 0.1:
            reasoning_parts.append(
                f"Close call with {runner_up.strategy.value.upper()} "
                f"(score diff: {score_diff:.2f})."
            )

    return best.strategy, " ".join(reasoning_parts)


def build_comparison_summary(plans: List[AlternativePlan]) -> str:
    """Build a comparison summary of all plans."""
    if not plans:
        return "No plans to compare."

    lines = ["Plan Comparison:"]
    for plan in sorted(plans, key=lambda p: p.overall_score, reverse=True):
        lines.append(
            f"  {plan.strategy.value.upper()}: "
            f"Score={plan.overall_score:.2f} | "
            f"Success={plan.p_success:.0%} | "
            f"Friction={plan.p_friction:.0%}"
        )

    return "\n".join(lines)


async def execute_with_multi_plan(
    agent: Any,
    task: Any,
    auto_select: bool = True,
    preferred_strategy: Optional[PlanStrategy] = None,
) -> Any:
    """
    Execute planning with multi-plan generation.

    This is the ultimate v6.1 entry point that:
    1. Generates 3 alternative plans (Standard/Accelerator/Lateral)
    2. Calculates probabilities for each
    3. Recommends the best plan
    4. Optionally executes the selected plan

    Args:
        agent: The PlannerAgent instance
        task: The task to plan
        auto_select: If True, automatically use recommended plan
        preferred_strategy: Override recommendation with specific strategy

    Returns:
        AgentResponse with the plan
    """
    from ..base import AgentResponse

    # Generate multi-plan
    multi_result = await generate_multi_plan_for_task(agent, task)

    # Select plan
    if preferred_strategy:
        selected = multi_result.get_plan(preferred_strategy)
        if not selected:
            selected = multi_result.get_recommended()
    elif auto_select:
        selected = multi_result.get_recommended()
    else:
        # Return multi-plan result for user selection
        return AgentResponse(
            success=True,
            data={
                "multi_plan": multi_result.model_dump(),
                "requires_selection": True,
                "markdown": multi_result.to_markdown(),
            },
            reasoning=f"Generated {len(multi_result.plans)} alternative plans. "
            f"Recommended: {multi_result.recommended_plan.value.upper()}",
            metadata={"mode": "multi_plan_selection"},
        )

    # Execute the selected plan
    if selected:
        plan_data = selected.plan
        return AgentResponse(
            success=True,
            data={
                "plan": plan_data,
                "selected_strategy": selected.strategy.value,
                "probabilities": selected.probabilities.to_display(),
                "multi_plan_summary": multi_result.comparison_summary,
                "sops": plan_data.get("sops", []),
            },
            reasoning=f"Executing {selected.strategy.value.upper()} plan: {selected.name}. "
            f"{multi_result.recommendation_reasoning}",
            metadata={
                "mode": "multi_plan_execution",
                "strategy": selected.strategy.value,
                "overall_score": selected.overall_score,
            },
        )

    return AgentResponse(
        success=False,
        error="No plan could be generated",
        reasoning="All plan generation attempts failed.",
    )


async def generate_multi_plan_for_task(
    agent: Any, task: Any, strategies: Optional[List[PlanStrategy]] = None
) -> MultiPlanResult:
    """
    Generate multiple alternative plans using Verbalized Sampling.

    Delegates to generate_multi_plan with agent's methods as dependencies.

    Args:
        agent: The PlannerAgent instance
        task: The task to plan
        strategies: Optional list of strategies to use

    Returns:
        MultiPlanResult with all plans and recommendation
    """

    async def gather_context() -> Dict[str, Any]:
        return await agent._gather_context(task)

    return await generate_multi_plan(
        task_request=task.request,
        gather_context_fn=gather_context,
        call_llm_fn=agent._call_llm,
        parse_json_fn=lambda x: _parse_json_safe(x),
        strategies=strategies,
        logger=agent.logger,
    )


def _parse_json_safe(text: str) -> Dict[str, Any]:
    """Safely parse JSON from text."""
    try:
        # Try to find JSON object in text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return {}


__all__ = [
    "generate_multi_plan",
    "create_fallback_plan",
    "select_best_plan",
    "build_comparison_summary",
    "execute_with_multi_plan",
    "generate_multi_plan_for_task",
]
