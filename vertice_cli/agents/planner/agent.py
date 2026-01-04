"""
PlannerAgent v6.0: "Espetacular" Edition (Nov 2025)

The main PlannerAgent class for enterprise-grade planning and orchestration.
This module contains only the PlannerAgent class - all types and helpers
are imported from the modular subpackages.

Following CODE_CONSTITUTION.md:
- Target: <500 lines (refactoring in progress)
- 100% type hints
- Zero placeholders
"""

import asyncio
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

# Base imports
from ..base import AgentCapability, AgentResponse, AgentRole, AgentTask, BaseAgent

# Types and GOAP
from .types import (
    ClarifyingQuestion,
    ClarificationResponse,
    PlanningMode,
    PlanStrategy,
    MultiPlanResult,
)
from .goap import WorldState, GoalState, Action, GOAPPlanner
from .dependency import DependencyAnalyzer
from .models import SOPStep, ExecutionPlan, ExecutionStage

# Formatting and utilities
from .formatting import format_plan_as_markdown, generate_confidence_summary
from .utils import robust_json_parse
from .prompts import (
    build_planning_prompt,
    build_clarifying_questions_prompt,
    build_exploration_prompt,
    generate_basic_plan,
)

# Multi-planning and optimization
from .multi_planning import (
    generate_multi_plan,
    execute_with_multi_plan as _execute_with_multi_plan,
    generate_multi_plan_for_task as _generate_multi_plan_for_task,
)
from .optimization import (
    build_stages,
    assess_risk,
    generate_rollback_strategy,
    identify_checkpoints,
    estimate_duration,
    calculate_max_parallel,
    generate_strategy_overview,
    generate_reasoning,
)

# Import streaming
from .streaming import execute_streaming as _execute_streaming, run_streaming as _run_streaming

# Import compat wrappers
from .compat import (
    calculate_step_confidence_compat,
    generate_confidence_summary_compat,
    format_plan_as_markdown_compat,
    create_fallback_plan_compat,
    select_best_plan_compat,
    build_comparison_summary_compat,
    infer_stage_name_compat,
    assess_risk_compat,
    generate_stage_description_compat,
    calculate_max_parallel_compat,
    generate_strategy_overview_compat,
    estimate_duration_compat,
    identify_checkpoints_compat,
    robust_json_parse_compat,
)

# Import clarification, exploration, artifact modules
from .clarification import (
    generate_clarifying_questions as _generate_clarifying_questions,
    execute_with_clarification as _execute_with_clarification,
)
from .exploration import explore as _explore

# Import context management
from .context import (
    gather_context as _gather_context,
    load_team_standards as _load_team_standards,
    discover_available_tools as _discover_available_tools,
    define_goal_state as _define_goal_state,
    define_initial_state as _define_initial_state,
    get_available_agents as _get_available_agents,
    generate_action_space as _generate_action_space,
)

# Import SOP conversion
from .sops import (
    actions_to_sops as _actions_to_sops,
    llm_planning_fallback as _llm_planning_fallback,
)

# ============================================================================
# PLANNER AGENT - The Orchestrator Queen
# ============================================================================
# All types, models, GOAP, and dependency analysis are imported from:
# - .types (enums, lightweight models)
# - .models (SOPStep, ExecutionStage, ExecutionPlan)
# - .goap (WorldState, GoalState, Action, GOAPPlanner)
# - .dependency (DependencyAnalyzer)
# - .monitoring (ExecutionEvent, ExecutionMonitor)
# ============================================================================


# ============================================================================


class PlannerAgent(BaseAgent):
    """
    Enterprise-Grade Planning & Orchestration Agent v6.0 "Espetacular"

    The "Queen" of the multi-agent swarm (Claude-Flow pattern).
    Responsible for:
    - High-level strategic planning (GOAP)
    - Agent coordination & delegation
    - Resource allocation
    - Risk assessment
    - Observability

    NEW in v6.0 (Inspired by Claude Code, Cursor 2.1, Devin):
    - Interactive Clarifying Questions before planning
    - plan.md Artifact Generation for user tracking
    - Confidence Ratings per step
    - Read-Only Exploration Mode

    Keep tool permissions narrow: "read and route" (Anthropic best practice).
    """

    def __init__(
        self,
        llm_client: Optional[Any] = None,
        mcp_client: Optional[Any] = None,
        plan_artifact_dir: Optional[str] = None,
        ask_clarifying_questions: bool = True,
    ):
        # FIX 1.4: Validate required clients
        if llm_client is None:
            raise ValueError("llm_client is required for PlannerAgent")
        if mcp_client is None:
            raise ValueError("mcp_client is required for PlannerAgent")

        super().__init__(
            role=AgentRole.PLANNER,
            capabilities=[AgentCapability.DESIGN, AgentCapability.READ_ONLY],  # Narrow permissions!
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt=self._build_system_prompt(),
        )

        # Initialize analyzers
        self.dependency_analyzer = DependencyAnalyzer()
        self.goap_planner: Optional[GOAPPlanner] = None

        # NEW v6.0: Configuration
        self.plan_artifact_dir = plan_artifact_dir or ".qwen/plans"
        self.ask_clarifying_questions = ask_clarifying_questions
        self.current_mode: PlanningMode = PlanningMode.PLANNING

        # NEW v6.0: Callbacks for interactive features
        self._question_callback: Optional[Callable] = None
        self._approval_callback: Optional[Callable] = None

    def _build_system_prompt(self) -> str:
        return """
You are PlannerAgent v6.0 "Espetacular" - Enterprise Orchestration Queen 👑

MISSION: Convert high-level goals into optimal, executable multi-agent workflows.

CORE PRINCIPLES (Anthropic 2025 Best Practices):
1. **Context Isolation**: Each sub-agent gets isolated context (no drift)
2. **Atomic Actions**: Each step must be completable by ONE agent in ONE turn
3. **Verifiable Outcomes**: Every step has a "definition_of_done"
4. **Graceful Degradation**: Non-critical steps can fail without breaking the plan
5. **Observability**: Include correlation IDs for distributed tracing

PLANNING METHODOLOGY (GOAP):
- Define clear GOAL STATE (what success looks like)
- Identify INITIAL STATE (current reality)
- Generate ACTIONS with preconditions & effects
- Use A* to find optimal path
- Consider COST (time, tokens, complexity)

ORCHESTRATION PATTERNS:
- **Sequential**: Dependencies require ordering (analyst → architect → coder)
- **Parallel**: Independent tasks run together (UI, API, DB teams)
- **Fork-Join**: Parallel work with merge point (multi-region deployment)
- **Pipeline**: Stream output between agents (preprocessor → analyzer → formatter)
- **Conditional**: Runtime branching based on results

OUTPUT FORMAT:
Pure JSON matching ExecutionPlan schema.
NO preamble, NO markdown blocks, JUST valid JSON.

CRITICAL:
- Detect parallel execution opportunities (save time!)
- Calculate critical path (longest dependency chain)
- Include checkpoints for rollback
- Assess risks and provide mitigation
- Keep token budgets realistic per agent
        """

    async def execute(self, task: AgentTask) -> AgentResponse:
        """
        Main planning workflow:
        1. Analyze task & context
        2. Define goal state (GOAP)
        3. Generate action space
        4. Run GOAP planner (A* pathfinding)
        5. Optimize execution order
        6. Detect parallel opportunities
        7. Add safety measures (checkpoints, rollback)
        8. Return comprehensive plan
        """
        try:
            # Phase 1: Context gathering
            context = await self._gather_context(task)

            # Phase 2: Define GOAP goal
            goal_state = self._define_goal_state(task, context)
            initial_state = self._define_initial_state(context)

            # Phase 3: Generate action space from available agents
            available_agents = self._get_available_agents(task)
            actions = self._generate_action_space(task, available_agents, context)

            # Phase 4: Run GOAP planner
            self.goap_planner = GOAPPlanner(actions)

            # Try GOAP first, fallback to LLM if needed
            goap_plan = self.goap_planner.plan(initial_state, goal_state, max_depth=20)

            if goap_plan:
                # Convert GOAP actions to SOPs
                sops = self._actions_to_sops(goap_plan)
            else:
                # GOAP failed, use LLM planning
                sops = await self._llm_planning_fallback(task, context, available_agents)

            # Phase 5: Dependency analysis
            parallel_groups = self.dependency_analyzer.find_parallel_groups(sops)
            critical_path = self.dependency_analyzer.find_critical_path(sops)
            cycles = self.dependency_analyzer.detect_cycles(sops)

            # Fail if circular dependencies detected
            if cycles:
                return AgentResponse(
                    success=False,
                    error=f"Circular dependencies detected: {cycles}",
                    reasoning="Plan has dependency cycles that would cause deadlock.",
                )

            # Phase 6: Build stages from parallel groups
            stages = build_stages(sops, parallel_groups)

            # Phase 7: Risk assessment & rollback strategy
            risk_level = assess_risk(sops)
            rollback_strat = generate_rollback_strategy(stages, sops)

            # Phase 8: Resource estimation
            est_duration = estimate_duration(sops, parallel_groups, self.dependency_analyzer)
            token_budget = sum(step.max_tokens for step in sops)

            # Phase 9: Build final plan
            plan = ExecutionPlan(
                plan_id=f"plan-{task.task_id}",
                goal=task.request,
                strategy_overview=generate_strategy_overview(stages),
                initial_state=initial_state.facts,
                goal_state=goal_state.desired_facts,
                estimated_cost=sum(s.cost for s in sops),
                stages=stages,
                sops=sops,
                rollback_strategy=rollback_strat,
                checkpoints=identify_checkpoints(stages),
                risk_assessment=risk_level,
                parallel_execution_opportunities=parallel_groups,
                critical_path=critical_path,
                estimated_duration=est_duration,
                token_budget=token_budget,
                max_parallel_agents=calculate_max_parallel(parallel_groups),
                plan_version="5.0",
                metadata={
                    "goap_used": goap_plan is not None,
                    "stages_count": len(stages),
                    "total_steps": len(sops),
                    "parallelism_factor": len(parallel_groups),
                },
            )

            return AgentResponse(
                success=True, data={"plan": plan.model_dump()}, reasoning=generate_reasoning(plan)
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                reasoning="Planning execution failed. See error for details.",
            )

    # Context management - delegates to context module
    async def _gather_context(self, task: AgentTask) -> Dict[str, Any]:
        return await _gather_context(self, task)

    async def _load_team_standards(self) -> Dict[str, Any]:
        return await _load_team_standards(self)

    async def _discover_available_tools(self) -> List[str]:
        return await _discover_available_tools(self)

    def _define_goal_state(self, task: AgentTask, context: Dict) -> GoalState:
        return _define_goal_state(task, context)

    def _define_initial_state(self, context: Dict) -> WorldState:
        return _define_initial_state(context)

    def _get_available_agents(self, task: AgentTask) -> List[str]:
        return _get_available_agents(task)

    def _generate_action_space(
        self, task: AgentTask, agents: List[str], context: Dict
    ) -> List[Action]:
        return _generate_action_space(task, agents, context)

    def _actions_to_sops(self, actions: List[Action]) -> List[SOPStep]:
        """Convert GOAP actions to SOP steps - delegates to sops module."""
        return _actions_to_sops(actions)

    async def _llm_planning_fallback(
        self, task: AgentTask, context: Dict, agents: List[str]
    ) -> List[SOPStep]:
        """Fallback to LLM planning - delegates to sops module."""
        return await _llm_planning_fallback(self, task, context, agents)

    # Prompt methods moved to prompts.py module
    # Utility methods moved to utils.py module (robust_json_parse)
    # Optimization methods moved to optimization.py module

    async def execute_streaming(self, task: AgentTask) -> AsyncIterator[Dict[str, Any]]:
        """Streaming execution - delegates to streaming module."""
        async for update in _execute_streaming(self, task):
            yield update

    async def run(self, task: AgentTask) -> AsyncIterator[Dict[str, Any]]:
        """Alias for execute_streaming for backwards compatibility."""
        async for update in _run_streaming(self, task):
            yield update

    # =========================================================================
    # NEW v6.0: CLARIFYING QUESTIONS (delegates to clarification module)
    # =========================================================================

    def set_question_callback(
        self, callback: Callable[[List[ClarifyingQuestion]], List[ClarificationResponse]]
    ):
        """Set callback for asking clarifying questions to user."""
        self._question_callback = callback

    def set_approval_callback(self, callback: Callable[[ExecutionPlan], bool]):
        """Set callback for getting user approval before execution."""
        self._approval_callback = callback

    async def _generate_clarifying_questions(self, task: AgentTask) -> List[ClarifyingQuestion]:
        """Generate clarifying questions - delegates to clarification module."""
        return await _generate_clarifying_questions(self, task)

    async def execute_with_clarification(
        self, task: AgentTask, responses: Optional[List[ClarificationResponse]] = None
    ) -> AgentResponse:
        """Execute with clarification - delegates to clarification module."""
        return await _execute_with_clarification(self, task, responses)

    # =========================================================================
    # NEW v6.0: EXPLORATION MODE (delegates to exploration module)
    # =========================================================================

    async def explore(self, task: AgentTask) -> AgentResponse:
        """Execute in exploration mode - delegates to exploration module."""
        return await _explore(self, task)

    # =========================================================================
    # NEW v6.1: MULTI-PLAN GENERATION (delegates to multi_planning module)
    # =========================================================================

    async def generate_multi_plan_for_task(
        self, task: AgentTask, strategies: Optional[List[PlanStrategy]] = None
    ) -> MultiPlanResult:
        """Generate multiple alternative plans - delegates to multi_planning module."""
        return await _generate_multi_plan_for_task(self, task, strategies)

    async def execute_with_multi_plan(
        self,
        task: AgentTask,
        auto_select: bool = True,
        preferred_strategy: Optional[PlanStrategy] = None,
    ) -> AgentResponse:
        """Execute with multi-plan - delegates to multi_planning module."""
        return await _execute_with_multi_plan(self, task, auto_select, preferred_strategy)

    # =========================================================================
    # BACKWARDS COMPATIBILITY WRAPPERS (delegate to compat module)
    # =========================================================================

    def _calculate_step_confidence(
        self, step: "SOPStep", context: Dict[str, Any]
    ) -> Tuple[float, str, List[str]]:
        return calculate_step_confidence_compat(step, context)

    def _generate_confidence_summary(self, score: float) -> str:
        return generate_confidence_summary_compat(score)

    def _format_plan_as_markdown(self, plan_data: Dict[str, Any], task: AgentTask) -> str:
        return format_plan_as_markdown_compat(plan_data, task)

    def _create_fallback_plan(self, task: AgentTask, strategy: "PlanStrategy") -> "AlternativePlan":
        return create_fallback_plan_compat(task, strategy)

    def _select_best_plan(
        self, plans: List["AlternativePlan"], task: AgentTask = None
    ) -> Tuple["PlanStrategy", str]:
        return select_best_plan_compat(plans, task)

    def _build_comparison_summary(self, plans: List["AlternativePlan"]) -> str:
        return build_comparison_summary_compat(plans)

    async def generate_multi_plan(self, task: AgentTask) -> "MultiPlanResult":
        return await self.generate_multi_plan_for_task(task)

    def _infer_stage_name(self, steps: List["SOPStep"]) -> str:
        return infer_stage_name_compat(steps)

    def _assess_risk(self, sops: List["SOPStep"]) -> str:
        return assess_risk_compat(sops)

    def _generate_stage_description(self, steps: List["SOPStep"]) -> str:
        return generate_stage_description_compat(steps)

    def _calculate_max_parallel(self, stages: List["ExecutionStage"]) -> int:
        return calculate_max_parallel_compat(stages)

    def _generate_strategy_overview(self, stages: List["ExecutionStage"]) -> str:
        return generate_strategy_overview_compat(stages)

    def _estimate_duration(
        self, stages: List["ExecutionStage"], base_minutes_per_step: int = 5
    ) -> str:
        return estimate_duration_compat(stages, base_minutes_per_step)

    def _identify_checkpoints(self, stages: List["ExecutionStage"]) -> List[str]:
        return identify_checkpoints_compat(stages)

    def _robust_json_parse(self, text: str) -> Optional[Dict[str, Any]]:
        return robust_json_parse_compat(text)
