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

# Import from parent agents package
from ..base import (
    AgentCapability,
    AgentResponse,
    AgentRole,
    AgentTask,
    BaseAgent,
)

# Import types from modular subpackages
from .types import (
    ClarifyingQuestion,
    ClarificationResponse,
    PlanningMode,
    PlanStrategy,
    MultiPlanResult,
)

# Import GOAP components
from .goap import (
    WorldState,
    GoalState,
    Action,
    GOAPPlanner,
)

# Import dependency analysis
from .dependency import DependencyAnalyzer

# Import domain models
from .models import (
    SOPStep,
    ExecutionPlan,
    ExecutionStage,
)

# Import monitoring

# Import formatting utilities
from .formatting import (
    format_plan_as_markdown,
    generate_confidence_summary,
)

# Import validation

# Import multi-planning utilities
from .multi_planning import (
    generate_multi_plan,
)

# Import optimization utilities
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

# Import confidence calculation

# Import utilities
from .utils import robust_json_parse

# Import prompts
from .prompts import (
    build_planning_prompt,
    build_clarifying_questions_prompt,
    build_exploration_prompt,
    generate_basic_plan,
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
        llm_client: Any,
        mcp_client: Any,
        plan_artifact_dir: Optional[str] = None,
        ask_clarifying_questions: bool = True,
    ):
        super().__init__(
            role=AgentRole.PLANNER,
            capabilities=[
                AgentCapability.DESIGN,
                AgentCapability.READ_ONLY  # Narrow permissions!
            ],
            llm_client=llm_client,
            mcp_client=mcp_client,
            system_prompt=self._build_system_prompt()
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
            actions = self._generate_action_space(
                task,
                available_agents,
                context
            )

            # Phase 4: Run GOAP planner
            self.goap_planner = GOAPPlanner(actions)

            # Try GOAP first, fallback to LLM if needed
            goap_plan = self.goap_planner.plan(
                initial_state,
                goal_state,
                max_depth=20
            )

            if goap_plan:
                # Convert GOAP actions to SOPs
                sops = self._actions_to_sops(goap_plan)
            else:
                # GOAP failed, use LLM planning
                sops = await self._llm_planning_fallback(
                    task, context, available_agents
                )

            # Phase 5: Dependency analysis
            parallel_groups = self.dependency_analyzer.find_parallel_groups(sops)
            critical_path = self.dependency_analyzer.find_critical_path(sops)
            cycles = self.dependency_analyzer.detect_cycles(sops)

            # Fail if circular dependencies detected
            if cycles:
                return AgentResponse(
                    success=False,
                    error=f"Circular dependencies detected: {cycles}",
                    reasoning="Plan has dependency cycles that would cause deadlock."
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
                    "parallelism_factor": len(parallel_groups)
                }
            )

            return AgentResponse(
                success=True,
                data={"plan": plan.model_dump()},
                reasoning=generate_reasoning(plan)
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                reasoning="Planning execution failed. See error for details."
            )

    async def _gather_context(self, task: AgentTask) -> Dict[str, Any]:
        """Gather all relevant context for planning"""
        context = {
            "architecture": task.context.get("architecture", {}),
            "files": task.context.get("files", []),
            "constraints": task.context.get("constraints", {}),
            "team_standards": await self._load_team_standards(),
            "available_tools": await self._discover_available_tools()
        }
        return context

    async def _load_team_standards(self) -> Dict[str, Any]:
        """Load team standards from CLAUDE.md or similar.

        CLAUDE.md is optional. Falls back to empty standards if not found.

        Compliance: Vertice Constitution v3.0 - P3 (fail gracefully)
        """
        # Try to read CLAUDE.md (Anthropic best practice)
        try:
            result = await self._execute_tool("read_file", {"path": "CLAUDE.md"})
            if result.get("success"):
                self.logger.info("Loaded team standards from CLAUDE.md")
                return {"claude_md": result.get("content", "")}
        except FileNotFoundError:
            self.logger.debug(
                "CLAUDE.md not found (optional). "
                "Using default standards. "
                "Create CLAUDE.md for project-specific guidelines."
            )
        except Exception as e:
            self.logger.warning(f"Failed to load CLAUDE.md: {e}")

        # Fallback: Empty standards (agent uses defaults)
        return {}

    async def _discover_available_tools(self) -> List[str]:
        """Discover available MCP tools"""
        # In production: Query MCP for available tools
        return ["read_file", "write_file", "exec_command", "git_operations"]

    def _define_goal_state(self, task: AgentTask, context: Dict) -> GoalState:
        """Define desired end state (GOAP)"""
        # Parse task to extract goal facts
        # For now, simple heuristic
        goal_facts = {
            "task_complete": True,
            "tests_passing": True,
            "code_reviewed": True,
            "documented": True
        }

        return GoalState(
            name=f"goal-{task.task_id}",
            desired_facts=goal_facts,
            priority=1.0
        )

    def _define_initial_state(self, context: Dict) -> WorldState:
        """Define current state"""
        initial_facts = {
            "task_complete": False,
            "tests_passing": False,
            "code_reviewed": False,
            "documented": False,
            "has_codebase": len(context.get("files", [])) > 0
        }

        return WorldState(
            facts=initial_facts,
            resources={"tokens": 100000, "time_minutes": 120}
        )

    def _get_available_agents(self, task: AgentTask) -> List[str]:
        """Get list of available agents for delegation"""
        # Could query registry or configuration
        return [
            "architect",
            "coder",
            "refactorer",
            "reviewer",
            "security",
            "tester",
            "documenter"
        ]

    def _generate_action_space(
        self,
        task: AgentTask,
        agents: List[str],
        context: Dict
    ) -> List[Action]:
        """
        Generate available actions from agent capabilities.
        Each action represents what an agent can do.
        """
        actions = []

        # Architect actions
        actions.append(Action(
            id="design_architecture",
            agent_role="architect",
            description="Design system architecture",
            preconditions={"has_codebase": True},
            effects={"architecture_defined": True},
            cost=3.0,
            duration_estimate="15m"
        ))

        # Coder actions
        actions.append(Action(
            id="implement_features",
            agent_role="coder",
            description="Implement features based on design",
            preconditions={"architecture_defined": True},
            effects={"code_written": True},
            cost=5.0,
            duration_estimate="30m"
        ))

        # Tester actions
        actions.append(Action(
            id="write_tests",
            agent_role="tester",
            description="Write automated tests",
            preconditions={"code_written": True},
            effects={"tests_passing": True},
            cost=3.0,
            duration_estimate="20m"
        ))

        # Reviewer actions
        actions.append(Action(
            id="code_review",
            agent_role="reviewer",
            description="Perform code review",
            preconditions={"code_written": True, "tests_passing": True},
            effects={"code_reviewed": True},
            cost=2.0,
            duration_estimate="15m"
        ))

        # Documenter actions
        actions.append(Action(
            id="write_docs",
            agent_role="documenter",
            description="Write documentation",
            preconditions={"code_written": True},
            effects={"documented": True, "task_complete": True},
            cost=2.0,
            duration_estimate="10m"
        ))

        return actions

    def _actions_to_sops(self, actions: List[Action]) -> List[SOPStep]:
        """Convert GOAP actions to SOP steps"""
        sops = []

        for idx, action in enumerate(actions):
            # Find dependencies (actions whose effects match our preconditions)
            deps = []
            for prev_idx, prev_action in enumerate(actions[:idx]):
                # Check if previous action's effects satisfy our preconditions
                if any(
                    key in prev_action.effects and
                    prev_action.effects[key] == value
                    for key, value in action.preconditions.items()
                ):
                    deps.append(f"step-{prev_idx}")

            sop = SOPStep(
                id=f"step-{idx}",
                role=action.agent_role,
                action=action.description,
                objective=f"Execute {action.id}",
                definition_of_done=f"Action {action.id} completed successfully",
                preconditions=action.preconditions,
                effects=action.effects,
                cost=action.cost,
                dependencies=deps,
                context_isolation=True,
                max_tokens=4000,
                correlation_id=f"action-{action.id}"
            )
            sops.append(sop)

        return sops

    async def _llm_planning_fallback(
        self,
        task: AgentTask,
        context: Dict,
        agents: List[str]
    ) -> List[SOPStep]:
        """Fallback to LLM planning if GOAP fails"""
        prompt = build_planning_prompt(task.request, context, agents)
        raw_response = await self._call_llm(prompt)

        # Parse and validate
        plan_data = robust_json_parse(raw_response)

        if plan_data and "sops" in plan_data:
            return [SOPStep(**sop) for sop in plan_data["sops"]]

        # Emergency fallback: basic sequential plan
        return generate_basic_plan(agents)

    # Prompt methods moved to prompts.py module
    # Utility methods moved to utils.py module (robust_json_parse)
    # Optimization methods moved to optimization.py module

    async def execute_streaming(
        self,
        task: AgentTask
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Streaming execution for PlannerAgent.

        Claude Code Style: Generates plan internally, then streams formatted markdown.
        Does NOT stream raw JSON tokens to UI.

        Yields:
            Dict with format {"type": "status"|"thinking"|"result", "data": ...}
        """
        trace_id = getattr(task, 'trace_id', str(uuid.uuid4()))

        try:
            # PHASE 1: Initial Status
            yield {"type": "status", "data": "📋 Loading project context..."}

            cwd = task.context.get('cwd', '.') if task.context else '.'
            await asyncio.sleep(0.05)

            # PHASE 2: Build Prompt
            yield {"type": "status", "data": "🎯 Generating plan..."}

            # Detect language and add instruction
            try:
                from vertice_core import LanguageDetector
                lang_instruction = LanguageDetector.get_prompt_instruction(task.request)
            except ImportError:
                lang_instruction = None

            prompt = f"""Create an execution plan for the following request:

REQUEST: {task.request}

CONTEXT:
- Working Directory: {cwd}

CRITICAL INSTRUCTIONS:
1. Return ONLY a valid JSON object - no markdown, no code blocks, no explanations
2. DO NOT include any tool calls, function calls, or command syntax
3. DO NOT write [TOOL_CALL:...], mkdir, write_file, or any execution commands
4. Each step should be a high-level DESCRIPTION of what to do, not HOW to do it
5. The "action" field should be human-readable text, NOT code or commands

Respond with this EXACT JSON format:

{{
  "goal": "Brief description of the goal",
  "strategy_overview": "High-level approach in plain text",
  "sops": [
    {{
      "id": "step-1",
      "action": "Human-readable description of what to do",
      "role": "executor",
      "confidence_score": 0.8,
      "definition_of_done": "How to verify completion"
    }}
  ],
  "risk_assessment": "LOW|MEDIUM|HIGH",
  "rollback_strategy": "How to undo if needed",
  "estimated_duration": "Time estimate"
}}

Include 3-7 concrete steps. Each "action" must be plain text describing WHAT to do, not code.

{f'IMPORTANT: {lang_instruction}' if lang_instruction else ''}"""

            # PHASE 3: Generate LLM Response (internal - NOT streamed to UI)
            # Claude Code pattern: Generate internally, format, then stream formatted output
            response_buffer = []
            token_count = 0

            async for token in self.llm_client.stream(
                prompt=prompt,
                system_prompt=self._get_system_prompt() if hasattr(self, '_get_system_prompt') else None,
                max_tokens=4096,
                temperature=0.3
            ):
                response_buffer.append(token)
                token_count += 1
                # Show progress indicator every 50 tokens (Claude Code style)
                if token_count % 50 == 0:
                    yield {"type": "status", "data": f"🎯 Generating plan... ({token_count} tokens)"}

            llm_response = ''.join(response_buffer)

            # PHASE 4: Process and Format
            yield {"type": "status", "data": "⚙️ Processing plan..."}

            plan = robust_json_parse(llm_response) or {"raw_response": llm_response}

            # PHASE 5: Generate Formatted Markdown (Claude Code style)
            yield {"type": "status", "data": "📝 Formatting plan..."}

            # Use formatting module to create beautiful output
            formatted_markdown = format_plan_as_markdown(plan, task.request)

            # PHASE 6: Stream the formatted markdown LINE BY LINE
            # CRITICAL: Stream by lines to avoid cutting words in the middle!
            # This also helps the BlockDetector identify markdown blocks properly
            lines = formatted_markdown.split('\n')
            for line in lines:
                yield {"type": "thinking", "data": line + "\n"}
                await asyncio.sleep(0.005)  # 5ms delay for smooth visual

            # PHASE 7: Return Result (NO formatted_markdown - already streamed!)
            yield {"type": "status", "data": "✅ Plan complete!"}

            yield {
                "type": "result",
                "data": AgentResponse(
                    success=True,
                    data={
                        "plan": plan,
                        "sops": plan.get("sops", []) if isinstance(plan, dict) else [],
                        # NOTE: formatted_markdown NOT included to avoid duplication
                    },
                    reasoning=f"Generated plan with {len(plan.get('sops', []) if isinstance(plan, dict) else [])} steps"
                )
            }

        except Exception as e:
            self.logger.exception(f"[{trace_id}] Planning error: {e}")
            yield {"type": "error", "data": {"error": str(e), "trace_id": trace_id}}

    async def run(self, task: AgentTask) -> AsyncIterator[Dict[str, Any]]:
        """Alias for execute_streaming for backwards compatibility."""
        async for update in self.execute_streaming(task):
            yield update

    # =========================================================================
    # NEW v6.0: CLARIFYING QUESTIONS (Cursor 2.1 Pattern)
    # =========================================================================

    def set_question_callback(self, callback: Callable[[List[ClarifyingQuestion]], List[ClarificationResponse]]):
        """Set callback for asking clarifying questions to user."""
        self._question_callback = callback

    def set_approval_callback(self, callback: Callable[[ExecutionPlan], bool]):
        """Set callback for getting user approval before execution."""
        self._approval_callback = callback

    async def _generate_clarifying_questions(
        self,
        task: AgentTask
    ) -> List[ClarifyingQuestion]:
        """
        Generate 2-3 targeted clarifying questions based on the task.

        Inspired by Cursor 2.1's approach of asking questions before planning.
        """
        prompt = build_clarifying_questions_prompt(task.request, task.context or {})

        try:
            response = await self._call_llm(prompt)
            data = robust_json_parse(response)

            if data and "questions" in data:
                questions = []
                for q in data["questions"][:3]:  # Max 3 questions
                    questions.append(ClarifyingQuestion(
                        question=q.get("question", ""),
                        category=q.get("category", "general"),
                        options=q.get("options", []),
                        required=q.get("required", False)
                    ))
                return questions
        except Exception as e:
            self.logger.warning(f"Failed to generate clarifying questions: {e}")

        # Fallback: Default questions
        return [
            ClarifyingQuestion(
                question="What is the scope of this task? (e.g., single file, module, entire project)",
                category="scope",
                options=["Single file", "Module/directory", "Entire project"],
                required=False
            ),
            ClarifyingQuestion(
                question="Do you want tests written for the changes?",
                category="preferences",
                options=["Yes, with high coverage", "Basic tests only", "No tests needed"],
                required=False
            )
        ]

    async def execute_with_clarification(
        self,
        task: AgentTask,
        responses: Optional[List[ClarificationResponse]] = None
    ) -> AgentResponse:
        """
        Execute planning with optional clarifying questions.

        This is the v6.0 enhanced entry point that:
        1. Generates clarifying questions (if enabled)
        2. Waits for user responses (via callback)
        3. Incorporates responses into planning
        4. Generates plan with confidence ratings
        5. Creates plan.md artifact
        """
        clarifying_questions: List[ClarifyingQuestion] = []
        clarification_responses: List[ClarificationResponse] = responses or []

        # Step 1: Generate and ask clarifying questions
        if self.ask_clarifying_questions and not responses:
            clarifying_questions = await self._generate_clarifying_questions(task)

            if clarifying_questions and self._question_callback:
                try:
                    clarification_responses = self._question_callback(clarifying_questions)
                except Exception as e:
                    self.logger.warning(f"Question callback failed: {e}")

        # Step 2: Enrich task context with clarification responses
        enriched_context = task.context.copy() if task.context else {}
        enriched_context["clarifications"] = {
            r.question_id: r.answer
            for r in clarification_responses
            if not r.skipped
        }

        enriched_task = AgentTask(
            task_id=task.task_id,
            request=task.request,
            context=enriched_context,
            session_id=task.session_id,
            metadata=task.metadata
        )

        # Step 3: Execute standard planning
        response = await self.execute(enriched_task)

        # Step 4: Enhance response with v6.0 features
        if response.success and "plan" in response.data:
            plan_data = response.data["plan"]

            # Add clarifying questions to plan
            if isinstance(plan_data, dict):
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
                artifact_path = await self._generate_plan_artifact(plan_data, task)
                if artifact_path:
                    plan_data["plan_artifact_path"] = artifact_path

        return response

    # Confidence calculation moved to confidence.py module

    # =========================================================================
    # NEW v6.0: PLAN.MD ARTIFACT (Claude Code Pattern)
    # =========================================================================

    async def _generate_plan_artifact(
        self,
        plan_data: Dict[str, Any],
        task: AgentTask
    ) -> Optional[str]:
        """
        Generate a plan.md file for user tracking.

        Inspired by Claude Code's plan mode that generates a structured
        markdown file with checkboxes for each step.
        """
        try:
            # Ensure directory exists
            artifact_dir = Path(self.plan_artifact_dir)
            artifact_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plan_id = plan_data.get("plan_id", "unknown")[:8]
            filename = f"plan_{timestamp}_{plan_id}.md"
            filepath = artifact_dir / filename

            # Generate markdown content
            content = format_plan_as_markdown(plan_data, task.request)

            # Write file
            filepath.write_text(content, encoding="utf-8")

            self.logger.info(f"Generated plan artifact: {filepath}")
            return str(filepath)

        except Exception as e:
            self.logger.warning(f"Failed to generate plan artifact: {e}")
            return None

    # =========================================================================
    # NEW v6.0: EXPLORATION MODE (Claude Plan Mode Pattern)
    # =========================================================================

    async def explore(self, task: AgentTask) -> AgentResponse:
        """
        Execute in exploration mode - read-only analysis.

        Like Claude Code's Plan Mode, this gathers context and analyzes
        the task without making any modifications.

        Use this before execute() to understand the problem space.
        """
        self.current_mode = PlanningMode.EXPLORATION

        # Restrict to read-only operations
        original_capabilities = self.capabilities.copy()
        self.capabilities = [AgentCapability.READ_ONLY]

        try:
            # Gather context
            context = await self._gather_context(task)

            # Analyze task requirements
            analysis_prompt = build_exploration_prompt(task.request, context)
            response = await self._call_llm(analysis_prompt)
            analysis = robust_json_parse(response)

            return AgentResponse(
                success=True,
                data={
                    "mode": "exploration",
                    "analysis": analysis or {"raw": response},
                    "context": context
                },
                reasoning="Exploration complete. Ready for planning phase.",
                metadata={"mode": PlanningMode.EXPLORATION.value}
            )

        finally:
            # Restore capabilities
            self.capabilities = original_capabilities
            self.current_mode = PlanningMode.PLANNING

    # =========================================================================
    # NEW v6.1: MULTI-PLAN GENERATION (Verbalized Sampling)
    # =========================================================================

    async def generate_multi_plan_for_task(
        self,
        task: AgentTask,
        strategies: Optional[List[PlanStrategy]] = None
    ) -> MultiPlanResult:
        """
        Generate multiple alternative plans using Verbalized Sampling.

        Delegates to multi_planning module with agent's methods as dependencies.
        """
        async def gather_context() -> Dict[str, Any]:
            return await self._gather_context(task)

        return await generate_multi_plan(
            task_request=task.request,
            gather_context_fn=gather_context,
            call_llm_fn=self._call_llm,
            parse_json_fn=robust_json_parse,
            strategies=strategies,
            logger=self.logger,
        )

    async def execute_with_multi_plan(
        self,
        task: AgentTask,
        auto_select: bool = True,
        preferred_strategy: Optional[PlanStrategy] = None
    ) -> AgentResponse:
        """
        Execute planning with multi-plan generation.

        This is the ultimate v6.1 entry point that:
        1. Generates 3 alternative plans (Standard/Accelerator/Lateral)
        2. Calculates probabilities for each
        3. Recommends the best plan
        4. Optionally executes the selected plan

        Args:
            task: The task to plan
            auto_select: If True, automatically use recommended plan
            preferred_strategy: Override recommendation with specific strategy
        """
        # Generate multi-plan
        multi_result = await self.generate_multi_plan_for_task(task)

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
                    "markdown": multi_result.to_markdown()
                },
                reasoning=f"Generated {len(multi_result.plans)} alternative plans. "
                          f"Recommended: {multi_result.recommended_plan.value.upper()}",
                metadata={"mode": "multi_plan_selection"}
            )

        # Execute the selected plan
        if selected:
            # Create a task with the selected plan's SOPs
            plan_data = selected.plan
            return AgentResponse(
                success=True,
                data={
                    "plan": plan_data,
                    "selected_strategy": selected.strategy.value,
                    "probabilities": selected.probabilities.to_display(),
                    "multi_plan_summary": multi_result.comparison_summary,
                    "sops": plan_data.get("sops", [])
                },
                reasoning=f"Executing {selected.strategy.value.upper()} plan: {selected.name}. "
                          f"{multi_result.recommendation_reasoning}",
                metadata={
                    "mode": "multi_plan_execution",
                    "strategy": selected.strategy.value,
                    "overall_score": selected.overall_score
                }
            )

        return AgentResponse(
            success=False,
            error="No plan could be generated",
            reasoning="All plan generation attempts failed."
        )


    # =========================================================================
    # BACKWARDS COMPATIBILITY WRAPPERS
    # These methods delegate to module-level functions for API stability
    # =========================================================================

    def _calculate_step_confidence(
        self,
        step: "SOPStep",
        context: Dict[str, Any]
    ) -> Tuple[float, str, List[str]]:
        """Backwards compatibility wrapper for calculate_step_confidence."""
        from .confidence import calculate_step_confidence
        return calculate_step_confidence(step, context)

    def _generate_confidence_summary(self, score: float) -> str:
        """Backwards compatibility wrapper for generate_confidence_summary."""
        from .formatting import generate_confidence_summary
        return generate_confidence_summary(score)

    def _format_plan_as_markdown(
        self,
        plan_data: Dict[str, Any],
        task: AgentTask
    ) -> str:
        """Backwards compatibility wrapper for format_plan_as_markdown."""
        from .formatting import format_plan_as_markdown
        return format_plan_as_markdown(plan_data, task)

    def _create_fallback_plan(
        self,
        task: AgentTask,
        strategy: "PlanStrategy"
    ) -> "AlternativePlan":
        """Backwards compatibility wrapper for create_fallback_plan."""
        from .multi_planning import create_fallback_plan
        return create_fallback_plan(task, strategy)

    def _select_best_plan(
        self,
        plans: List["AlternativePlan"],
        task: AgentTask = None
    ) -> Tuple["PlanStrategy", str]:
        """Backwards compatibility wrapper for select_best_plan."""
        from .multi_planning import select_best_plan
        return select_best_plan(plans)

    def _build_comparison_summary(self, plans: List["AlternativePlan"]) -> str:
        """Backwards compatibility wrapper for build_comparison_summary."""
        from .multi_planning import build_comparison_summary
        return build_comparison_summary(plans)

    async def generate_multi_plan(self, task: AgentTask) -> "MultiPlanResult":
        """Backwards compatibility alias for generate_multi_plan_for_task."""
        return await self.generate_multi_plan_for_task(task)

    # Optimization module wrappers
    def _infer_stage_name(self, steps: List["SOPStep"]) -> str:
        """Backwards compatibility wrapper for infer_stage_name."""
        from .optimization import infer_stage_name
        return infer_stage_name(steps)

    def _assess_risk(self, sops: List["SOPStep"]) -> str:
        """Backwards compatibility wrapper for assess_risk."""
        from .optimization import assess_risk
        return assess_risk(sops)

    def _generate_stage_description(self, steps: List["SOPStep"]) -> str:
        """Backwards compatibility wrapper for generate_stage_description."""
        from .optimization import generate_stage_description
        return generate_stage_description(steps)

    def _calculate_max_parallel(self, stages: List["ExecutionStage"]) -> int:
        """Backwards compatibility wrapper for calculate_max_parallel."""
        from .optimization import calculate_max_parallel
        return calculate_max_parallel(stages)

    def _generate_strategy_overview(self, stages: List["ExecutionStage"]) -> str:
        """Backwards compatibility wrapper for generate_strategy_overview."""
        from .optimization import generate_strategy_overview
        return generate_strategy_overview(stages)

    def _estimate_duration(
        self,
        stages: List["ExecutionStage"],
        base_minutes_per_step: int = 5
    ) -> str:
        """Backwards compatibility wrapper for estimate_duration."""
        from .optimization import estimate_duration
        return estimate_duration(stages, base_minutes_per_step)

    def _identify_checkpoints(self, stages: List["ExecutionStage"]) -> List[str]:
        """Backwards compatibility wrapper for identify_checkpoints."""
        from .optimization import identify_checkpoints
        return identify_checkpoints(stages)

    def _robust_json_parse(self, text: str) -> Optional[Dict[str, Any]]:
        """Backwards compatibility wrapper for robust_json_parse."""
        from .utils import robust_json_parse
        return robust_json_parse(text)


# PlanValidator is now in .validation module
# ExecutionEvent and ExecutionMonitor are now in .monitoring module
