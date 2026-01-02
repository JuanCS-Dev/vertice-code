"""
Vertice Orchestrator Agent

The lead agent that coordinates all other agents in the agency.

Key Features:
- Task decomposition and routing
- Bounded Autonomy (L0-L3 levels via mixin)
- Handoffs (OpenAI Agents SDK pattern)

Reference:
- https://www.infoq.com/articles/architects-ai-era/
- AGENTS_2028_EVOLUTION.md
"""

from __future__ import annotations

from typing import Dict, List, Optional, AsyncIterator, Any
import logging

from .types import (
    AgentRole,
    ApprovalCallback,
    ApprovalRequest,
    Handoff,
    NotifyCallback,
    Task,
    TaskComplexity,
)
from .bounded_autonomy import BoundedAutonomyMixin
from agents.base import BaseAgent
from core.resilience import ResilienceMixin
from core.caching import CachingMixin
from core.mesh.mixin import HybridMeshMixin

logger = logging.getLogger(__name__)


class OrchestratorAgent(HybridMeshMixin, ResilienceMixin, CachingMixin, BoundedAutonomyMixin, BaseAgent):
    """
    Lead Agent - The Brain of Vertice Agency

    Implements Bounded Autonomy (Three Loops pattern):
    - L0: Autonomous - execute without human approval
    - L1: Notify - execute and notify human afterward
    - L2: Approve - propose and wait for human approval
    - L3: Human Only - human executes, agent advises

    Capabilities:
    - Task decomposition and planning
    - Autonomy level determination (via mixin)
    - Agent selection and routing
    - Context preservation across handoffs
    """

    name = "orchestrator"
    role = AgentRole.ORCHESTRATOR
    description = """
    Strategic coordinator for Vertice Agency.
    Decomposes complex tasks, routes to specialists,
    maintains context, and ensures quality output.
    Enforces Bounded Autonomy for safe operations.
    """

    ROUTING_TABLE = {
        "code": AgentRole.CODER,
        "review": AgentRole.REVIEWER,
        "architecture": AgentRole.ARCHITECT,
        "research": AgentRole.RESEARCHER,
        "deploy": AgentRole.DEVOPS,
        "test": AgentRole.CODER,
        "refactor": AgentRole.CODER,
        "security": AgentRole.REVIEWER,
        "documentation": AgentRole.RESEARCHER,
    }

    MODEL_ROUTING = {
        TaskComplexity.TRIVIAL: "groq",
        TaskComplexity.SIMPLE: "groq",
        TaskComplexity.MODERATE: "vertex-ai",
        TaskComplexity.COMPLEX: "claude",
        TaskComplexity.CRITICAL: "claude",
    }

    def __init__(
        self,
        approval_callback: Optional[ApprovalCallback] = None,
        notify_callback: Optional[NotifyCallback] = None,
    ) -> None:
        super().__init__()  # Initialize BaseAgent (observability)
        self.tasks: Dict[str, Task] = {}
        self.handoffs: List[Handoff] = []
        self.agents: Dict[AgentRole, Any] = {}
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self._llm = None
        self._approval_callback = approval_callback
        self._notify_callback = notify_callback
        self._agents_initialized = False

        # Initialize hybrid mesh for topology-based coordination
        self._init_mesh()
        logger.info("[Orchestrator] Hybrid mesh initialized")

    def _ensure_agents(self) -> None:
        """
        Lazy-initialize specialized agents and register in mesh.

        Pattern: Anthropic Orchestrator-Worker (2026)
        - Lead agent (this) coordinates
        - Subagents execute specialized tasks
        - Mesh topology optimizes coordination
        """
        if self._agents_initialized:
            return

        # Import agents lazily to avoid circular imports
        from agents.coder.agent import CoderAgent
        from agents.reviewer.agent import ReviewerAgent
        from agents.architect.agent import ArchitectAgent
        from agents.researcher.agent import ResearcherAgent
        from agents.devops.agent import DevOpsAgent

        self.agents = {
            AgentRole.CODER: CoderAgent(),
            AgentRole.REVIEWER: ReviewerAgent(),
            AgentRole.ARCHITECT: ArchitectAgent(),
            AgentRole.RESEARCHER: ResearcherAgent(),
            AgentRole.DEVOPS: DevOpsAgent(),
        }

        # Register all agents as workers in the mesh
        for role, agent in self.agents.items():
            self.register_worker(
                agent_id=role.value,
                metadata={"role": role.value, "agent_type": type(agent).__name__}
            )

        self._agents_initialized = True
        logger.info(f"[Orchestrator] Initialized {len(self.agents)} subagents in mesh")

    async def plan(self, user_request: str) -> List[Task]:
        """
        Decompose user request into executable tasks.

        This method analyzes the request and breaks it down into
        atomic, actionable tasks that can be executed by specialized agents.

        Args:
            user_request: The user's request.

        Returns:
            List of tasks to execute in order.

        Pattern:
            Uses LLM for semantic decomposition when available,
            falls back to keyword-based heuristics otherwise.
        """
        complexity = await self._analyze_complexity(user_request)

        # Try LLM-based decomposition first
        if self._llm is not None:
            tasks = await self._decompose_with_llm(user_request, complexity)
            if tasks:
                return tasks

        # Fallback: Intelligent heuristic decomposition
        tasks = await self._decompose_heuristic(user_request, complexity)
        return tasks

    async def _decompose_with_llm(
        self,
        user_request: str,
        complexity: TaskComplexity
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
        complexity: TaskComplexity
    ) -> List[Task]:
        """
        Heuristic-based task decomposition.

        Uses patterns and keywords to identify multiple components
        in the request and creates separate tasks for each.
        """
        request_lower = user_request.lower()
        tasks: List[Task] = []

        # Pattern 1: Check for multi-phase keywords FIRST
        # "design and implement" -> phases take priority over component split
        phases = self._extract_phases(request_lower)
        if len(phases) > 1:
            # This is a multi-phase request, not a component list
            return self._create_phase_tasks(user_request, phases, complexity)

        # Pattern 2: Explicit list with "with", ",", "and" for features
        # "Create X with A, B, and C" -> feature tasks
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
        # "complete system", "full implementation" -> break into standard phases
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
        phases: List[tuple],
        complexity: TaskComplexity
    ) -> List[Task]:
        """
        Create tasks from detected phases.

        Extracts the target object and creates one task per phase.
        "design and implement a REST API" -> ["Design a REST API", "Implement a REST API"]
        """
        import re

        request_lower = user_request.lower()

        # Extract the object being worked on
        # Remove all phase keywords to find the target
        phase_keywords = '|'.join([p[0] for p in phases])

        # Remove "and", "then", commas, and phase keywords
        cleaned = re.sub(
            rf'\b({phase_keywords})\b|\band\b|\bthen\b|,',
            '',
            request_lower
        ).strip()

        # Clean up extra spaces
        target_object = ' '.join(cleaned.split())

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
        "Create X with A, B, and C" -> ["Create A", "Create B", "Create C"]
        """
        import re

        # Try to find the base action and object
        # Pattern: "Create/Build/Implement X with/including A, B, and C"
        with_match = re.match(
            r'^(.+?)\s+(?:with|including|featuring|that has|having)\s+(.+)$',
            request,
            re.IGNORECASE
        )

        if with_match:
            base_action = with_match.group(1).strip()
            features_part = with_match.group(2).strip()

            # Split the features
            features = re.split(r',\s*(?:and\s+)?|\s+and\s+', features_part)
            features = [f.strip() for f in features if len(f.strip()) > 2]

            if len(features) > 1:
                # Create full descriptions for each feature
                components = []
                for feature in features:
                    # Add context: "Create todo app" + "add feature" -> "Implement add feature for todo app"
                    component_desc = f"Implement {feature} for {base_action}"
                    components.append(component_desc)
                return components

        # Fallback: simple split by "and" for lists
        # "login, logout, and password reset" -> 3 items
        parts = re.split(r',\s*(?:and\s+)?|\s+and\s+', request)
        components = [p.strip() for p in parts if len(p.strip()) > 5]

        return components if len(components) > 1 else [request]

    def _extract_phases(self, request_lower: str) -> List[tuple]:
        """Extract sequential phases from request."""
        phase_keywords = [
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

        found_phases = []
        for keyword, phase_name in phase_keywords:
            if keyword in request_lower:
                found_phases.append((keyword, phase_name))

        return found_phases

    def _is_complex_request(self, request_lower: str) -> bool:
        """Check if request indicates a complex multi-phase task."""
        complex_indicators = [
            "complete system",
            "full implementation",
            "entire application",
            "from scratch",
            "end to end",
            "comprehensive",
            "production ready",
        ]
        return any(ind in request_lower for ind in complex_indicators)

    def _component_complexity(
        self,
        component: str,
        base_complexity: TaskComplexity
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
        complexity: TaskComplexity
    ) -> List[Task]:
        """Parse LLM response into Task list."""
        import json

        try:
            # Extract JSON from response
            start = response.find('[')
            end = response.rfind(']') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                data = json.loads(json_str)

                tasks = []
                for item in data:
                    task = Task(
                        id=f"task-{item.get('id', len(tasks)+1)}",
                        description=item.get('description', ''),
                        complexity=complexity,
                    )
                    tasks.append(task)

                return tasks if tasks else []

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse task list: {e}")

        return []

    async def route(self, task: Task) -> AgentRole:
        """
        Route task to the most appropriate agent.

        Args:
            task: Task to route.

        Returns:
            AgentRole for the task.
        """
        for keyword, agent in self.ROUTING_TABLE.items():
            if keyword in task.description.lower():
                return agent

        return AgentRole.CODER

    async def handoff(
        self,
        task: Task,
        to_agent: AgentRole,
        context: str
    ) -> Handoff:
        """
        Perform handoff to another agent.

        Args:
            task: Task being handed off.
            to_agent: Target agent.
            context: Context for the handoff.

        Returns:
            Handoff record.
        """
        handoff = Handoff(
            from_agent=self.role,
            to_agent=to_agent,
            context=context,
            task_id=task.id,
            reason=f"Routing {task.description[:50]}..."
        )

        self.handoffs.append(handoff)
        logger.info(f"Handoff: {self.role} -> {to_agent} for task {task.id}")

        return handoff

    async def execute(
        self,
        user_request: str,
        stream: bool = True
    ) -> AsyncIterator[str]:
        """
        Execute user request with full orchestration and mesh topology.

        Pattern: Anthropic Orchestrator-Worker (2026) + Hybrid Mesh
        - Lead agent decomposes and delegates
        - Mesh topology optimizes coordination pattern
        - Subagents execute with optimal coordination
        - Results aggregated back to user

        Reference: arXiv:2512.08296 (Scaling Agent Systems)
        - Parallelizable → Centralized (+80.8%)
        - Exploratory → Decentralized (+9.2%)
        - Sequential → Single-agent (avoid MAS)

        Args:
            user_request: The user's request.
            stream: Whether to stream output.

        Yields:
            Progress updates and results.
        """
        self._ensure_agents()
        yield "[Orchestrator] Analyzing request...\n"

        tasks = await self.plan(user_request)
        yield f"[Orchestrator] Created {len(tasks)} task(s)\n"

        # Get topology recommendation for the overall request
        topology_info = self.get_topology_recommendation(user_request)
        yield f"[Mesh] Task type: {topology_info['task_characteristic']}, "
        yield f"Topology: {topology_info['recommended_topology']}\n"

        if topology_info.get('warning'):
            yield f"[Mesh] Warning: {topology_info['warning']}\n"

        for task in tasks:
            # Check bounded autonomy
            can_proceed, approval = await self.check_autonomy(task)

            if not can_proceed:
                yield f"[Orchestrator] Task requires approval: {task.autonomy_level.value}\n"
                if approval:
                    yield f"[Orchestrator] Approval ID: {approval.id}\n"
                continue

            # Route to appropriate agent
            agent_role = await self.route(task)
            agent = self.agents.get(agent_role)

            if agent is None:
                yield f"[Orchestrator] No agent for role: {agent_role.value}\n"
                task.status = "failed"
                continue

            # Route task through mesh with optimal topology
            route = self.route_task(
                task_id=task.id,
                task_description=task.description,
                target_agents=[agent_role.value],
                prefer_parallel=True,
            )
            yield f"[Mesh] Task {task.id} routed via {route.topology.value} "
            yield f"(error factor: {route.estimated_error_factor:.1f}x)\n"

            # Create handoff with context (Anthropic pattern)
            handoff = await self.handoff(task, agent_role, user_request)
            yield f"[Orchestrator] Handoff to {agent_role.value}...\n"

            # EXECUTE VIA MESH - applies topology-based coordination
            task.status = "in_progress"
            try:
                # Execute agent with mesh coordination
                if hasattr(agent, 'generate') and agent_role == AgentRole.CODER:
                    from agents.coder.types import CodeGenerationRequest
                    request = CodeGenerationRequest(
                        description=task.description,
                        language="python",
                    )
                    async for chunk in agent.generate(request, stream=stream):
                        yield chunk
                elif hasattr(agent, 'execute'):
                    async for chunk in agent.execute(task.description, stream=stream):
                        yield chunk
                elif hasattr(agent, 'analyze'):
                    async for chunk in agent.analyze(task.description, stream=stream):
                        yield chunk
                else:
                    yield f"[{agent_role.value}] Processing: {task.description}\n"

                task.status = "completed"
                task.result = "Execution completed"
                yield f"\n[Orchestrator] Task completed by {agent_role.value}\n"

            except Exception as e:
                task.status = "failed"
                task.result = str(e)
                logger.error(f"Agent {agent_role.value} failed: {e}")
                yield f"\n[Orchestrator] Task failed: {e}\n"

            await self.notify_completion(task, task.result or "")

        # Report mesh status
        mesh_status = self.get_mesh_status()
        yield f"[Mesh] Status: {mesh_status['worker_nodes']} workers, "
        yield f"{mesh_status['active_routes']} routes active\n"
        yield "[Orchestrator] All tasks processed\n"

    async def _analyze_complexity(self, request: str) -> TaskComplexity:
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

    def get_status(self) -> Dict:
        """Get orchestrator status."""
        self._ensure_agents()
        return {
            "name": self.name,
            "role": self.role.value,
            "active_tasks": len([t for t in self.tasks.values() if t.status == "in_progress"]),
            "completed_tasks": len([t for t in self.tasks.values() if t.status == "completed"]),
            "failed_tasks": len([t for t in self.tasks.values() if t.status == "failed"]),
            "handoffs": len(self.handoffs),
            "agents_registered": list(self.agents.keys()),
            "pending_approvals": len(self.pending_approvals),
        }


# Singleton instance
orchestrator = OrchestratorAgent()
