"""
Pytest fixtures for parity test suite.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pytest

# -----------------------------------------------------------------------------
# Data Classes for Testing
# -----------------------------------------------------------------------------


@dataclass
class MockTask:
    """Mock task for testing."""

    id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    estimated_tokens: int = 1000
    status: str = "pending"


@dataclass
class MockResponse:
    """Mock LLM response."""

    content: str
    model: str = "test-model"
    tokens_used: int = 100
    success: bool = True
    provider: str = "mock"


@dataclass
class MockToolResult:
    """Mock tool execution result."""

    tool_name: str
    success: bool
    output: Any
    duration_ms: int = 50


@dataclass
class IntentResult:
    """Intent classification result."""

    intent: str
    confidence: float
    reasoning: str
    secondary_intents: List[str] = field(default_factory=list)


# -----------------------------------------------------------------------------
# Mock Providers
# -----------------------------------------------------------------------------


class MockProvider:
    """Mock LLM provider for testing."""

    def __init__(self, name: str):
        self.name = name
        self.calls: List[Dict] = []
        self.fail_count = 0
        self.should_fail = False
        self.latency_ms = 50

    def fail_next(self, count: int):
        """Make the next N calls fail."""
        self.fail_count = count
        self.should_fail = True

    def recover(self):
        """Stop failing."""
        self.should_fail = False
        self.fail_count = 0

    async def generate(self, prompt: str, **kwargs) -> MockResponse:
        """Generate a mock response."""
        self.calls.append({"prompt": prompt, **kwargs})

        if self.should_fail and self.fail_count > 0:
            self.fail_count -= 1
            raise Exception(f"Mock provider {self.name} failure")

        await asyncio.sleep(self.latency_ms / 1000)

        return MockResponse(
            content=f"Mock response from {self.name}",
            model=f"{self.name}-model",
            provider=self.name,
        )


class MockProviderRegistry:
    """Registry of mock providers."""

    def __init__(self):
        self.providers = {
            "claude": MockProvider("claude"),
            "gemini": MockProvider("gemini"),
            "groq": MockProvider("groq"),
            "vertex-ai": MockProvider("vertex-ai"),
        }

    def __getitem__(self, key: str) -> MockProvider:
        return self.providers[key]

    def get(self, key: str) -> Optional[MockProvider]:
        return self.providers.get(key)


# -----------------------------------------------------------------------------
# Mock Agents
# -----------------------------------------------------------------------------


class MockAgent:
    """Mock agent for testing orchestration."""

    def __init__(self, name: str):
        self.name = name
        self.calls: List[Dict] = []
        self.was_called = False
        self.last_request: Optional[str] = None
        self.call_order = 0
        self.context: Dict = {}
        self.output: Optional[str] = None
        self._call_counter = 0

    async def process(self, request: str, context: Optional[Dict] = None) -> str:
        """Process a request."""
        self._call_counter += 1
        self.was_called = True
        self.last_request = request
        self.call_order = self._call_counter
        self.context = context or {}
        self.output = f"Output from {self.name}: processed '{request[:50]}...'"
        self.calls.append({"request": request, "context": context})
        return self.output

    def reset(self):
        """Reset call tracking."""
        self.calls = []
        self.was_called = False
        self.last_request = None
        self.call_order = 0
        self.context = {}
        self.output = None


# -----------------------------------------------------------------------------
# Mock Orchestrator
# -----------------------------------------------------------------------------


class MockOrchestrator:
    """Mock orchestrator for testing."""

    def __init__(self):
        self.agents: Dict[str, MockAgent] = {}
        self.task_decomposition_enabled = True
        self.plan_gating_enabled = True
        self.last_plan: List[MockTask] = []

    def register_agent(self, agent: MockAgent):
        """Register an agent."""
        self.agents[agent.name] = agent

    async def plan(self, request: str) -> List[MockTask]:
        """Generate a plan for the request."""
        if not self.task_decomposition_enabled:
            # Mimic broken behavior
            return [MockTask(id="task-1", description=request)]

        # Simulate proper decomposition
        tasks = []
        keywords = ["create", "implement", "add", "design", "test", "review"]

        for i, keyword in enumerate(keywords):
            if keyword in request.lower():
                tasks.append(
                    MockTask(
                        id=f"task-{i + 1}",
                        description=f"{keyword.capitalize()} component",
                        dependencies=[f"task-{i}"] if i > 0 else [],
                    )
                )

        if not tasks:
            tasks = [MockTask(id="task-1", description=request)]

        self.last_plan = tasks
        return tasks

    async def process(self, request: str) -> Dict:
        """Process a request through the orchestrator."""
        plan = await self.plan(request)

        # Route to appropriate agent
        agent = self._select_agent(request)
        if agent:
            await agent.process(request)

        return {
            "plan": plan,
            "agent_used": agent.name if agent else None,
            "success": True,
        }

    def _select_agent(self, request: str) -> Optional[MockAgent]:
        """Select agent based on request."""
        request_lower = request.lower()

        if any(word in request_lower for word in ["plan", "design", "architect"]):
            return self.agents.get("planner")
        elif any(word in request_lower for word in ["code", "implement", "create"]):
            return self.agents.get("coder")
        elif any(word in request_lower for word in ["review", "analyze"]):
            return self.agents.get("reviewer")
        elif any(word in request_lower for word in ["refactor", "improve"]):
            return self.agents.get("refactorer")

        return self.agents.get("coder")  # Default


# -----------------------------------------------------------------------------
# Mock Tool Executor
# -----------------------------------------------------------------------------


class MockToolExecutor:
    """Mock tool executor for testing."""

    def __init__(self):
        self.tools: Dict[str, callable] = {}
        self.execution_log: List[Dict] = []

    def register_tool(self, name: str, func: callable):
        """Register a tool."""
        self.tools[name] = func

    async def execute(self, tool_name: str, args: Dict) -> MockToolResult:
        """Execute a single tool."""
        start = asyncio.get_event_loop().time()

        if tool_name not in self.tools:
            return MockToolResult(
                tool_name=tool_name,
                success=False,
                output=f"Tool '{tool_name}' not found",
            )

        try:
            result = await self.tools[tool_name](**args)
            duration = int((asyncio.get_event_loop().time() - start) * 1000)

            self.execution_log.append({"tool": tool_name, "args": args, "success": True})

            return MockToolResult(
                tool_name=tool_name, success=True, output=result, duration_ms=duration
            )
        except Exception as e:
            return MockToolResult(tool_name=tool_name, success=False, output=str(e))

    async def execute_chain(self, chain: List[Dict]) -> List[MockToolResult]:
        """Execute a chain of dependent tools."""
        results = []
        prev_result = None

        for item in chain:
            args = item["args"].copy()

            # Replace $PREV_RESULT placeholder
            for key, value in args.items():
                if value == "$PREV_RESULT" and prev_result:
                    args[key] = prev_result.output

            result = await self.execute(item["tool"], args)
            results.append(result)
            prev_result = result

            if not result.success:
                break

        return results

    async def execute_parallel(self, tools: List[Dict]) -> List[MockToolResult]:
        """Execute independent tools in parallel."""
        tasks = [self.execute(t["tool"], t["args"]) for t in tools]
        return await asyncio.gather(*tasks)


# -----------------------------------------------------------------------------
# Mock User Input
# -----------------------------------------------------------------------------


class MockUserInput:
    """Mock user input for interactive testing."""

    def __init__(self):
        self.responses: List[str] = []
        self.response_index = 0

    def set_response(self, response: str):
        """Set a single response."""
        self.responses = [response]
        self.response_index = 0

    def set_responses(self, responses: List[str]):
        """Set multiple responses."""
        self.responses = responses
        self.response_index = 0

    async def get_input(self, prompt: str = "") -> str:
        """Get the next response."""
        if self.response_index >= len(self.responses):
            return ""

        response = self.responses[self.response_index]
        self.response_index += 1
        return response


# -----------------------------------------------------------------------------
# Mock Router with Circuit Breaker
# -----------------------------------------------------------------------------


class MockCircuitBreaker:
    """Mock circuit breaker."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.state = "CLOSED"
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    def record_failure(self):
        """Record a failure."""
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"

    def record_success(self):
        """Record a success."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
        self.failures = max(0, self.failures - 1)

    def attempt_reset(self):
        """Attempt to reset the circuit breaker."""
        if self.state == "OPEN":
            self.state = "HALF_OPEN"


class MockRouter:
    """Mock router with circuit breaker support."""

    def __init__(self, providers: MockProviderRegistry):
        self.providers = providers
        self.circuit_breakers: Dict[str, MockCircuitBreaker] = {
            name: MockCircuitBreaker() for name in providers.providers.keys()
        }
        self.routing_order = ["claude", "gemini", "groq", "vertex-ai"]

    async def generate(self, prompt: str, provider: Optional[str] = None) -> MockResponse:
        """Generate using router with failover."""
        providers_to_try = [provider] if provider else self.routing_order

        for prov_name in providers_to_try:
            cb = self.circuit_breakers.get(prov_name)
            if cb and cb.state == "OPEN":
                continue

            try:
                prov = self.providers.get(prov_name)
                if prov:
                    result = await prov.generate(prompt)
                    if cb:
                        cb.record_success()
                    return result
            except Exception:
                if cb:
                    cb.record_failure()
                continue

        raise Exception("All providers failed")


# -----------------------------------------------------------------------------
# Mock Vertice Client
# -----------------------------------------------------------------------------


class MockVerticeClient:
    """Mock Vertice client for E2E testing."""

    def __init__(self):
        self.orchestrator = MockOrchestrator()
        self.providers = MockProviderRegistry()
        self.router = MockRouter(self.providers)
        self.user_input = MockUserInput()

        # Setup default agents
        for name in ["planner", "coder", "reviewer", "refactorer", "tester"]:
            agent = MockAgent(name)
            self.orchestrator.register_agent(agent)

    async def process(self, message: str, mode: str = "execute") -> Dict:
        """Process a message."""
        result = {
            "tasks": [],
            "plan_displayed": False,
            "user_approved": False,
            "execution_started": False,
            "execution_started_after_approval": False,
            "output": "",
        }

        # Generate plan
        plan = await self.orchestrator.plan(message)
        result["tasks"] = plan

        if mode == "plan_only":
            return result

        # Show plan (plan gating)
        if self.orchestrator.plan_gating_enabled:
            result["plan_displayed"] = True

            # Get user approval
            approval = await self.user_input.get_input()
            result["user_approved"] = approval.upper() == "Y"

            if not result["user_approved"]:
                return result

            result["execution_started_after_approval"] = True

        # Execute
        result["execution_started"] = True
        exec_result = await self.orchestrator.process(message)
        result["output"] = exec_result

        return result


# -----------------------------------------------------------------------------
# Pytest Fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def mock_providers():
    """Provide mock providers."""
    return MockProviderRegistry()


@pytest.fixture
def mock_agent():
    """Provide a single mock agent."""
    return MockAgent("test_agent")


@pytest.fixture
def planner():
    """Provide planner agent."""
    return MockAgent("planner")


@pytest.fixture
def coder():
    """Provide coder agent."""
    return MockAgent("coder")


@pytest.fixture
def reviewer():
    """Provide reviewer agent."""
    return MockAgent("reviewer")


@pytest.fixture
def refactorer():
    """Provide refactorer agent."""
    return MockAgent("refactorer")


@pytest.fixture
def orchestrator(planner, coder, reviewer, refactorer):
    """Provide configured orchestrator."""
    orch = MockOrchestrator()
    orch.register_agent(planner)
    orch.register_agent(coder)
    orch.register_agent(reviewer)
    orch.register_agent(refactorer)
    return orch


@pytest.fixture
def tool_executor():
    """Provide tool executor with basic tools."""
    executor = MockToolExecutor()

    # Register basic tools
    async def read_file(path: str) -> str:
        return f"Contents of {path}"

    async def parse_json(content: str) -> Dict:
        return {"parsed": content}

    async def validate_schema(data: Dict) -> Dict:
        return {"valid": True}

    executor.register_tool("read_file", read_file)
    executor.register_tool("parse_json", parse_json)
    executor.register_tool("validate_schema", validate_schema)

    return executor


@pytest.fixture
def router(mock_providers):
    """Provide router with circuit breakers."""
    return MockRouter(mock_providers)


@pytest.fixture
def mock_user_input():
    """Provide mock user input."""
    return MockUserInput()


@pytest.fixture
def vertice_coreent():
    """Provide full mock Vertice client."""
    return MockVerticeClient()
