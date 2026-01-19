"""
Scientific E2E Tests: Agent Pipeline Flow

Flow: Request → Planning → Execution → Response

Tests cover:
- Request parsing and validation
- Agent selection/routing
- Planning phase correctness
- Execution with tools
- Response formatting
- Context preservation
- Handoff integrity
"""

import pytest
import asyncio
import time
from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum, auto


# =============================================================================
# AGENT PIPELINE MODELS FOR TESTING
# =============================================================================


class RequestType(Enum):
    """Types of user requests."""

    CODE_GENERATION = auto()
    CODE_REVIEW = auto()
    BUG_FIX = auto()
    REFACTOR = auto()
    DOCUMENTATION = auto()
    QUESTION = auto()
    COMMAND = auto()


@dataclass
class UserRequest:
    """Parsed user request."""

    raw_input: str
    request_type: RequestType
    intent: str
    entities: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentPlan:
    """Plan created by agent."""

    steps: List[str]
    tools_needed: List[str]
    estimated_complexity: str  # low, medium, high
    requires_approval: bool = False


@dataclass
class ExecutionResult:
    """Result of execution."""

    success: bool
    output: str
    artifacts: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0


class RequestParser:
    """Parses user input into structured requests."""

    KEYWORDS = {
        RequestType.CODE_GENERATION: ["create", "write", "implement", "add", "generate"],
        RequestType.CODE_REVIEW: ["review", "check", "analyze", "audit"],
        RequestType.BUG_FIX: ["fix", "bug", "error", "issue", "broken"],
        RequestType.REFACTOR: ["refactor", "improve", "optimize", "clean"],
        RequestType.DOCUMENTATION: ["document", "docs", "readme", "explain"],
        RequestType.QUESTION: ["what", "how", "why", "where", "?"],
        RequestType.COMMAND: ["/", "run", "execute"],
    }

    def parse(self, raw_input: str) -> UserRequest:
        """Parse raw input into structured request."""
        if not raw_input or not raw_input.strip():
            raise ValueError("Empty input")

        raw_lower = raw_input.lower()
        request_type = RequestType.QUESTION  # default

        for rtype, keywords in self.KEYWORDS.items():
            if any(kw in raw_lower for kw in keywords):
                request_type = rtype
                break

        return UserRequest(
            raw_input=raw_input,
            request_type=request_type,
            intent=self._extract_intent(raw_input, request_type),
            entities=self._extract_entities(raw_input),
            context={},
        )

    def _extract_intent(self, raw: str, rtype: RequestType) -> str:
        """Extract intent from input."""
        # Simplified intent extraction
        return f"{rtype.name.lower()}: {raw[:50]}..."

    def _extract_entities(self, raw: str) -> Dict[str, Any]:
        """Extract entities from input."""
        entities = {}
        # Extract file paths
        import re

        paths = re.findall(r"[\w/]+\.\w+", raw)
        if paths:
            entities["files"] = paths
        return entities


class AgentRouter:
    """Routes requests to appropriate agents."""

    AGENT_MAPPING = {
        RequestType.CODE_GENERATION: "coder",
        RequestType.CODE_REVIEW: "reviewer",
        RequestType.BUG_FIX: "coder",
        RequestType.REFACTOR: "refactorer",
        RequestType.DOCUMENTATION: "documenter",
        RequestType.QUESTION: "researcher",
        RequestType.COMMAND: "executor",
    }

    def route(self, request: UserRequest) -> str:
        """Route request to agent."""
        return self.AGENT_MAPPING.get(request.request_type, "orchestrator")


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, name: str):
        self.name = name
        self.plans_created: List[AgentPlan] = []
        self.executions: List[ExecutionResult] = []

    def plan(self, request: UserRequest) -> AgentPlan:
        """Create execution plan."""
        plan = AgentPlan(
            steps=[f"Step 1 for {request.intent}", "Step 2: Execute", "Step 3: Verify"],
            tools_needed=["read_file", "write_file"],
            estimated_complexity="medium",
        )
        self.plans_created.append(plan)
        return plan

    async def execute(self, plan: AgentPlan) -> ExecutionResult:
        """Execute the plan."""
        await asyncio.sleep(0.01)  # Simulate work
        result = ExecutionResult(
            success=True,
            output=f"Executed {len(plan.steps)} steps",
            artifacts=[f"artifact_{i}" for i in range(len(plan.steps))],
            duration_ms=10,
        )
        self.executions.append(result)
        return result


class AgentPipeline:
    """Full agent pipeline."""

    def __init__(self):
        self.parser = RequestParser()
        self.router = AgentRouter()
        self.agents: Dict[str, MockAgent] = {}
        self.history: List[Dict[str, Any]] = []

    def get_agent(self, name: str) -> MockAgent:
        """Get or create agent."""
        if name not in self.agents:
            self.agents[name] = MockAgent(name)
        return self.agents[name]

    async def process(self, raw_input: str) -> ExecutionResult:
        """Process user input through pipeline."""
        # Parse
        request = self.parser.parse(raw_input)

        # Route
        agent_name = self.router.route(request)
        agent = self.get_agent(agent_name)

        # Plan
        plan = agent.plan(request)

        # Execute
        result = await agent.execute(plan)

        # Record history
        self.history.append(
            {"request": request, "agent": agent_name, "plan": plan, "result": result}
        )

        return result


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def parser():
    """Create request parser."""
    return RequestParser()


@pytest.fixture
def router():
    """Create agent router."""
    return AgentRouter()


@pytest.fixture
def pipeline():
    """Create agent pipeline."""
    return AgentPipeline()


@pytest.fixture
def mock_agent():
    """Create mock agent."""
    return MockAgent("test_agent")


# =============================================================================
# 1. REQUEST PARSING TESTS
# =============================================================================


class TestRequestParsing:
    """Test request parsing and validation."""

    def test_parse_simple_request(self, parser):
        """Simple request is parsed correctly."""
        request = parser.parse("create a hello world function")
        assert request.raw_input == "create a hello world function"
        assert request.request_type == RequestType.CODE_GENERATION

    def test_parse_empty_input_rejected(self, parser):
        """Empty input is rejected."""
        with pytest.raises(ValueError, match="Empty"):
            parser.parse("")

    def test_parse_whitespace_only_rejected(self, parser):
        """Whitespace-only input is rejected."""
        with pytest.raises(ValueError, match="Empty"):
            parser.parse("   \t\n  ")

    def test_parse_code_review_request(self, parser):
        """Code review request is identified."""
        request = parser.parse("review this code for security issues")
        assert request.request_type == RequestType.CODE_REVIEW

    def test_parse_bug_fix_request(self, parser):
        """Bug fix request is identified."""
        request = parser.parse("fix the error in authentication")
        assert request.request_type == RequestType.BUG_FIX

    def test_parse_refactor_request(self, parser):
        """Refactor request is identified."""
        request = parser.parse("refactor this function for better performance")
        assert request.request_type == RequestType.REFACTOR

    def test_parse_documentation_request(self, parser):
        """Documentation request is identified."""
        request = parser.parse("document the API endpoints")
        assert request.request_type == RequestType.DOCUMENTATION

    def test_parse_question(self, parser):
        """Question is identified."""
        request = parser.parse("what does this function do?")
        assert request.request_type == RequestType.QUESTION

    def test_parse_command(self, parser):
        """Command is identified."""
        request = parser.parse("/commit -m 'message'")
        assert request.request_type == RequestType.COMMAND

    def test_parse_extracts_file_paths(self, parser):
        """File paths are extracted as entities."""
        request = parser.parse("read the file src/main.py")
        assert "files" in request.entities
        assert "src/main.py" in request.entities["files"]

    def test_parse_multiple_file_paths(self, parser):
        """Multiple file paths are extracted."""
        request = parser.parse("compare test.py and main.py")
        assert "files" in request.entities
        assert len(request.entities["files"]) == 2

    def test_parse_preserves_raw_input(self, parser):
        """Raw input is preserved exactly."""
        original = "Create a function with CAPS and 123 numbers"
        request = parser.parse(original)
        assert request.raw_input == original

    def test_parse_unicode_input(self, parser):
        """Unicode input is handled."""
        request = parser.parse("create function with émoji 🚀")
        assert "émoji" in request.raw_input

    def test_parse_long_input(self, parser):
        """Long input is handled."""
        long_input = "create " + "a " * 1000 + "function"
        request = parser.parse(long_input)
        assert request.request_type == RequestType.CODE_GENERATION


# =============================================================================
# 2. AGENT ROUTING TESTS
# =============================================================================


class TestAgentRouting:
    """Test agent selection/routing."""

    def test_route_code_generation(self, router):
        """Code generation routes to coder."""
        request = UserRequest(
            raw_input="create function", request_type=RequestType.CODE_GENERATION, intent="create"
        )
        assert router.route(request) == "coder"

    def test_route_code_review(self, router):
        """Code review routes to reviewer."""
        request = UserRequest(
            raw_input="review code", request_type=RequestType.CODE_REVIEW, intent="review"
        )
        assert router.route(request) == "reviewer"

    def test_route_bug_fix(self, router):
        """Bug fix routes to coder."""
        request = UserRequest(raw_input="fix bug", request_type=RequestType.BUG_FIX, intent="fix")
        assert router.route(request) == "coder"

    def test_route_refactor(self, router):
        """Refactor routes to refactorer."""
        request = UserRequest(
            raw_input="refactor", request_type=RequestType.REFACTOR, intent="refactor"
        )
        assert router.route(request) == "refactorer"

    def test_route_documentation(self, router):
        """Documentation routes to documenter."""
        request = UserRequest(
            raw_input="document", request_type=RequestType.DOCUMENTATION, intent="document"
        )
        assert router.route(request) == "documenter"

    def test_route_question(self, router):
        """Question routes to researcher."""
        request = UserRequest(
            raw_input="what is this?", request_type=RequestType.QUESTION, intent="question"
        )
        assert router.route(request) == "researcher"

    def test_route_command(self, router):
        """Command routes to executor."""
        request = UserRequest(
            raw_input="/run tests", request_type=RequestType.COMMAND, intent="command"
        )
        assert router.route(request) == "executor"


# =============================================================================
# 3. PLANNING PHASE TESTS
# =============================================================================


class TestPlanningPhase:
    """Test planning phase correctness."""

    def test_plan_has_steps(self, mock_agent):
        """Plan includes steps."""
        request = UserRequest(
            raw_input="create function", request_type=RequestType.CODE_GENERATION, intent="create"
        )
        plan = mock_agent.plan(request)
        assert len(plan.steps) > 0

    def test_plan_identifies_tools(self, mock_agent):
        """Plan identifies needed tools."""
        request = UserRequest(
            raw_input="edit file", request_type=RequestType.CODE_GENERATION, intent="edit"
        )
        plan = mock_agent.plan(request)
        assert len(plan.tools_needed) > 0

    def test_plan_estimates_complexity(self, mock_agent):
        """Plan estimates complexity."""
        request = UserRequest(
            raw_input="create function", request_type=RequestType.CODE_GENERATION, intent="create"
        )
        plan = mock_agent.plan(request)
        assert plan.estimated_complexity in ["low", "medium", "high"]

    def test_plan_is_recorded(self, mock_agent):
        """Plans are recorded for history."""
        request = UserRequest(
            raw_input="create", request_type=RequestType.CODE_GENERATION, intent="create"
        )
        mock_agent.plan(request)
        assert len(mock_agent.plans_created) == 1

    def test_multiple_plans_independent(self, mock_agent):
        """Multiple plans are independent."""
        for i in range(3):
            request = UserRequest(
                raw_input=f"task {i}", request_type=RequestType.CODE_GENERATION, intent=f"task {i}"
            )
            mock_agent.plan(request)
        assert len(mock_agent.plans_created) == 3


# =============================================================================
# 4. EXECUTION TESTS
# =============================================================================


class TestExecution:
    """Test execution with tools."""

    @pytest.mark.asyncio
    async def test_execution_returns_result(self, mock_agent):
        """Execution returns result."""
        plan = AgentPlan(steps=["step1"], tools_needed=["tool1"], estimated_complexity="low")
        result = await mock_agent.execute(plan)
        assert isinstance(result, ExecutionResult)

    @pytest.mark.asyncio
    async def test_execution_success_flag(self, mock_agent):
        """Execution sets success flag."""
        plan = AgentPlan(steps=["step1"], tools_needed=["tool1"], estimated_complexity="low")
        result = await mock_agent.execute(plan)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_execution_produces_output(self, mock_agent):
        """Execution produces output."""
        plan = AgentPlan(
            steps=["step1", "step2"], tools_needed=["tool1"], estimated_complexity="low"
        )
        result = await mock_agent.execute(plan)
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_execution_creates_artifacts(self, mock_agent):
        """Execution creates artifacts."""
        plan = AgentPlan(
            steps=["step1", "step2", "step3"], tools_needed=["tool1"], estimated_complexity="low"
        )
        result = await mock_agent.execute(plan)
        assert len(result.artifacts) == 3

    @pytest.mark.asyncio
    async def test_execution_tracks_duration(self, mock_agent):
        """Execution tracks duration."""
        plan = AgentPlan(steps=["step1"], tools_needed=["tool1"], estimated_complexity="low")
        result = await mock_agent.execute(plan)
        assert result.duration_ms > 0

    @pytest.mark.asyncio
    async def test_execution_is_recorded(self, mock_agent):
        """Executions are recorded."""
        plan = AgentPlan(steps=["step1"], tools_needed=["tool1"], estimated_complexity="low")
        await mock_agent.execute(plan)
        assert len(mock_agent.executions) == 1

    @pytest.mark.asyncio
    async def test_parallel_executions(self, mock_agent):
        """Parallel executions work."""
        plans = [
            AgentPlan(steps=[f"step{i}"], tools_needed=[], estimated_complexity="low")
            for i in range(5)
        ]
        results = await asyncio.gather(*[mock_agent.execute(p) for p in plans])
        assert len(results) == 5
        assert all(r.success for r in results)


# =============================================================================
# 5. FULL PIPELINE TESTS
# =============================================================================


class TestFullPipeline:
    """Test full pipeline from request to response."""

    @pytest.mark.asyncio
    async def test_pipeline_simple_request(self, pipeline):
        """Simple request flows through pipeline."""
        result = await pipeline.process("create a hello world function")
        assert result.success

    @pytest.mark.asyncio
    async def test_pipeline_records_history(self, pipeline):
        """Pipeline records history."""
        await pipeline.process("create function")
        assert len(pipeline.history) == 1

    @pytest.mark.asyncio
    async def test_pipeline_history_complete(self, pipeline):
        """Pipeline history is complete."""
        await pipeline.process("create function")
        entry = pipeline.history[0]
        assert "request" in entry
        assert "agent" in entry
        assert "plan" in entry
        assert "result" in entry

    @pytest.mark.asyncio
    async def test_pipeline_multiple_requests(self, pipeline):
        """Multiple requests are processed."""
        for i in range(3):
            await pipeline.process(f"task {i}")
        assert len(pipeline.history) == 3

    @pytest.mark.asyncio
    async def test_pipeline_different_agents(self, pipeline):
        """Different requests route to different agents."""
        await pipeline.process("create function")
        await pipeline.process("review code")
        await pipeline.process("fix bug")

        agents_used = {h["agent"] for h in pipeline.history}
        assert "coder" in agents_used
        assert "reviewer" in agents_used

    @pytest.mark.asyncio
    async def test_pipeline_reuses_agents(self, pipeline):
        """Pipeline reuses agents."""
        await pipeline.process("create function 1")
        await pipeline.process("create function 2")

        assert len(pipeline.agents) == 1
        assert len(pipeline.agents["coder"].plans_created) == 2


# =============================================================================
# 6. CONTEXT PRESERVATION TESTS
# =============================================================================


class TestContextPreservation:
    """Test context preservation across pipeline."""

    @pytest.mark.asyncio
    async def test_request_context_preserved(self, pipeline):
        """Request context is preserved in history."""
        await pipeline.process("create function in test.py")
        entry = pipeline.history[0]
        assert entry["request"].raw_input == "create function in test.py"

    @pytest.mark.asyncio
    async def test_entities_preserved(self, pipeline):
        """Entities are preserved in history."""
        await pipeline.process("edit file.py")
        entry = pipeline.history[0]
        assert "files" in entry["request"].entities

    @pytest.mark.asyncio
    async def test_plan_preserved(self, pipeline):
        """Plan is preserved in history."""
        await pipeline.process("create function")
        entry = pipeline.history[0]
        assert len(entry["plan"].steps) > 0

    @pytest.mark.asyncio
    async def test_result_preserved(self, pipeline):
        """Result is preserved in history."""
        await pipeline.process("create function")
        entry = pipeline.history[0]
        assert entry["result"].success


# =============================================================================
# 7. HANDOFF INTEGRITY TESTS
# =============================================================================


class TestHandoffIntegrity:
    """Test handoff integrity between components."""

    def test_parser_to_router_handoff(self, parser, router):
        """Parser output is valid for router."""
        request = parser.parse("create function")
        agent = router.route(request)
        assert isinstance(agent, str)
        assert len(agent) > 0

    @pytest.mark.asyncio
    async def test_router_to_agent_handoff(self, pipeline):
        """Router correctly hands off to agent."""
        await pipeline.process("review this code")
        assert "reviewer" in pipeline.agents

    @pytest.mark.asyncio
    async def test_plan_to_execution_handoff(self, mock_agent):
        """Plan is correctly handed to execution."""
        request = UserRequest(
            raw_input="create", request_type=RequestType.CODE_GENERATION, intent="create"
        )
        plan = mock_agent.plan(request)
        result = await mock_agent.execute(plan)

        # Artifacts should match steps
        assert len(result.artifacts) == len(plan.steps)


# =============================================================================
# 8. ERROR HANDLING IN PIPELINE TESTS
# =============================================================================


class TestPipelineErrorHandling:
    """Test error handling in pipeline."""

    @pytest.mark.asyncio
    async def test_empty_input_error(self, pipeline):
        """Empty input raises error."""
        with pytest.raises(ValueError):
            await pipeline.process("")

    @pytest.mark.asyncio
    async def test_whitespace_input_error(self, pipeline):
        """Whitespace input raises error."""
        with pytest.raises(ValueError):
            await pipeline.process("   ")

    @pytest.mark.asyncio
    async def test_pipeline_continues_after_success(self, pipeline):
        """Pipeline continues after successful request."""
        await pipeline.process("create function")
        await pipeline.process("review code")
        assert len(pipeline.history) == 2


# =============================================================================
# 9. RESPONSE FORMATTING TESTS
# =============================================================================


class TestResponseFormatting:
    """Test response formatting."""

    @pytest.mark.asyncio
    async def test_result_has_output(self, pipeline):
        """Result has output text."""
        result = await pipeline.process("create function")
        assert result.output is not None
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_result_has_artifacts_list(self, pipeline):
        """Result has artifacts list."""
        result = await pipeline.process("create function")
        assert isinstance(result.artifacts, list)

    @pytest.mark.asyncio
    async def test_result_has_errors_list(self, pipeline):
        """Result has errors list (empty on success)."""
        result = await pipeline.process("create function")
        assert isinstance(result.errors, list)

    @pytest.mark.asyncio
    async def test_successful_result_no_errors(self, pipeline):
        """Successful result has no errors."""
        result = await pipeline.process("create function")
        assert result.success
        assert len(result.errors) == 0


# =============================================================================
# 10. CONCURRENT PIPELINE TESTS
# =============================================================================


class TestConcurrentPipeline:
    """Test concurrent pipeline operations."""

    @pytest.mark.asyncio
    async def test_parallel_requests(self, pipeline):
        """Parallel requests are handled."""
        requests = [f"create function {i}" for i in range(5)]
        results = await asyncio.gather(*[pipeline.process(r) for r in requests])
        assert len(results) == 5
        assert all(r.success for r in results)

    @pytest.mark.asyncio
    async def test_parallel_different_types(self, pipeline):
        """Parallel requests of different types."""
        requests = ["create function", "review code", "fix bug", "document api", "what is this?"]
        results = await asyncio.gather(*[pipeline.process(r) for r in requests])
        assert len(results) == 5

    @pytest.mark.asyncio
    async def test_history_order_preserved(self, pipeline):
        """History order is preserved."""
        # Sequential to ensure order
        for i in range(5):
            await pipeline.process(f"task {i}")

        for i, entry in enumerate(pipeline.history):
            assert f"task {i}" in entry["request"].raw_input


# =============================================================================
# 11. PERFORMANCE TESTS
# =============================================================================


class TestPipelinePerformance:
    """Test pipeline performance characteristics."""

    @pytest.mark.asyncio
    async def test_simple_request_fast(self, pipeline):
        """Simple request completes quickly."""
        start = time.time()
        await pipeline.process("create function")
        elapsed = time.time() - start
        assert elapsed < 1.0  # Should be < 1s

    @pytest.mark.asyncio
    async def test_batch_throughput(self, pipeline):
        """Batch of requests has good throughput."""
        start = time.time()
        for i in range(10):
            await pipeline.process(f"task {i}")
        elapsed = time.time() - start
        assert elapsed < 5.0  # 10 requests in < 5s

    @pytest.mark.asyncio
    async def test_parallel_throughput(self, pipeline):
        """Parallel requests have good throughput."""
        requests = [f"task {i}" for i in range(10)]
        start = time.time()
        await asyncio.gather(*[pipeline.process(r) for r in requests])
        elapsed = time.time() - start
        assert elapsed < 2.0  # Parallel should be faster
