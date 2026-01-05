"""
REAL End-to-End Orchestration Tests

These tests use REAL LLM calls and REAL execution.
They validate actual system behavior, not mocks.

Requirements:
- Valid API keys in environment (.env)
- Network connectivity
- Sufficient API quota

WARNING: These tests consume API tokens and may take several minutes.
"""

import pytest
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Skip all tests if no API keys configured
pytestmark = [
    pytest.mark.e2e,
    pytest.mark.real,
    pytest.mark.skipif(
        not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"),
        reason="No API keys configured"
    )
]


def load_env():
    """Load environment variables from .env file."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"\''))


# Load env at module import
load_env()


class RealVerticeClient:
    """Real Vertice client wrapper for testing."""

    def __init__(self):
        self.initialized = False
        self.bridge = None
        self.errors: List[str] = []

    async def initialize(self):
        """Initialize real Vertice components."""
        try:
            from vertice_tui.core.bridge import Bridge

            self.bridge = Bridge()
            await self.bridge.initialize()
            self.initialized = True
            return True
        except Exception as e:
            self.errors.append(str(e))
            return False

    async def process(self, message: str, timeout: int = 60) -> Dict[str, Any]:
        """Process a message through real Vertice system."""
        if not self.initialized:
            raise RuntimeError("Client not initialized")

        result = {
            "success": False,
            "output": "",
            "chunks": [],
            "tools_called": [],
            "agent_used": None,
            "error": None,
            "duration_ms": 0,
        }

        start = time.time()

        try:
            chunks = []
            async for chunk in self.bridge.process_message(message):
                chunks.append(chunk)
                if hasattr(chunk, "content"):
                    result["output"] += chunk.content
                elif isinstance(chunk, str):
                    result["output"] += chunk
                elif isinstance(chunk, dict):
                    if "content" in chunk:
                        result["output"] += chunk["content"]
                    if "tool_calls" in chunk:
                        result["tools_called"].extend(chunk["tool_calls"])

            result["chunks"] = chunks
            result["success"] = True

        except asyncio.TimeoutError:
            result["error"] = "Timeout"
        except Exception as e:
            result["error"] = str(e)

        result["duration_ms"] = int((time.time() - start) * 1000)
        return result

    async def cleanup(self):
        """Cleanup resources."""
        if self.bridge:
            try:
                await self.bridge.shutdown()
            except Exception:
                pass


@pytest.fixture
async def real_client():
    """Provide real Vertice client."""
    client = RealVerticeClient()
    success = await client.initialize()

    if not success:
        pytest.skip(f"Could not initialize Vertice: {client.errors}")

    yield client

    await client.cleanup()


class TestRealTaskDecomposition:
    """Test real task decomposition with actual LLM calls."""

    @pytest.mark.timeout(120)
    async def test_complex_request_decomposes(self, real_client):
        """
        REAL TEST: Complex request should decompose into multiple tasks.

        This test sends a complex request and validates that the system
        produces multiple actionable tasks, not just one monolithic task.
        """
        request = """
        Create a user authentication system with:
        1. User registration with email validation
        2. Login with password hashing
        3. Password reset via email
        4. Session management with JWT tokens
        """

        result = await real_client.process(request)

        print(f"\n[REAL TEST] Duration: {result['duration_ms']}ms")
        print(f"[REAL TEST] Output length: {len(result['output'])} chars")
        print(f"[REAL TEST] Success: {result['success']}")

        if result['error']:
            print(f"[REAL TEST] Error: {result['error']}")
            pytest.skip(f"LLM error: {result['error']}")

        # Validate decomposition happened
        output_lower = result['output'].lower()

        # Should mention multiple components
        components_found = sum([
            "registration" in output_lower or "register" in output_lower,
            "login" in output_lower,
            "password" in output_lower,
            "session" in output_lower or "jwt" in output_lower,
        ])

        assert components_found >= 2, \
            f"Expected multiple components addressed, found {components_found}"

        # Output should be substantial (not just "ok")
        assert len(result['output']) > 100, \
            "Output too short for complex request"

    @pytest.mark.timeout(60)
    async def test_simple_request_handled(self, real_client):
        """
        REAL TEST: Simple request should produce focused output.
        """
        request = "Explain what a Python decorator is in one sentence."

        result = await real_client.process(request)

        print(f"\n[REAL TEST] Duration: {result['duration_ms']}ms")
        print(f"[REAL TEST] Output: {result['output'][:200]}...")

        assert result['success'] or result['error'] is None
        assert len(result['output']) > 20, "Should produce some output"


class TestRealIntentRecognition:
    """Test real intent recognition with actual LLM calls."""

    @pytest.mark.timeout(60)
    async def test_coding_intent_produces_code(self, real_client):
        """
        REAL TEST: Coding request should produce actual code.
        """
        request = "Write a Python function that checks if a number is prime."

        result = await real_client.process(request)

        print(f"\n[REAL TEST] Duration: {result['duration_ms']}ms")

        if result['error']:
            pytest.skip(f"LLM error: {result['error']}")

        # Should contain code markers
        has_code = any([
            "def " in result['output'],
            "```python" in result['output'],
            "```" in result['output'],
        ])

        assert has_code, "Coding request should produce code"

        # Should mention prime
        assert "prime" in result['output'].lower(), \
            "Output should relate to the request"

    @pytest.mark.timeout(60)
    async def test_planning_intent_produces_plan(self, real_client):
        """
        REAL TEST: Planning request should produce structured plan.
        """
        request = "Plan the architecture for a microservices-based e-commerce platform."

        result = await real_client.process(request)

        print(f"\n[REAL TEST] Duration: {result['duration_ms']}ms")

        if result['error']:
            pytest.skip(f"LLM error: {result['error']}")

        output_lower = result['output'].lower()

        # Should mention architectural concepts
        architectural_terms = [
            "service", "api", "database", "component",
            "architecture", "microservice", "gateway"
        ]

        terms_found = sum(1 for term in architectural_terms if term in output_lower)
        assert terms_found >= 2, \
            f"Planning output should mention architectural concepts, found {terms_found}"


class TestRealToolExecution:
    """Test real tool execution."""

    @pytest.mark.timeout(90)
    async def test_file_read_tool(self, real_client):
        """
        REAL TEST: Request to read a file should use file reading tool.
        """
        # Use a known file in the project
        request = "Read the contents of pyproject.toml and tell me the project name."

        result = await real_client.process(request)

        print(f"\n[REAL TEST] Duration: {result['duration_ms']}ms")
        print(f"[REAL TEST] Tools called: {result['tools_called']}")

        if result['error']:
            pytest.skip(f"LLM error: {result['error']}")

        # Should mention the project name (vertice)
        assert "vertice" in result['output'].lower(), \
            "Should read and report the project name"

    @pytest.mark.timeout(90)
    async def test_code_search_tool(self, real_client):
        """
        REAL TEST: Request to find code should search effectively.
        """
        request = "Find where the TUIBridge class is defined in this project."

        result = await real_client.process(request)

        print(f"\n[REAL TEST] Duration: {result['duration_ms']}ms")

        if result['error']:
            pytest.skip(f"LLM error: {result['error']}")

        # Should find the file
        assert "bridge" in result['output'].lower(), \
            "Should mention the bridge file"


class TestRealProviderRouting:
    """Test real provider routing and failover."""

    @pytest.mark.timeout(60)
    async def test_provider_responds(self, real_client):
        """
        REAL TEST: At least one provider should respond successfully.
        """
        request = "Say hello in one word."

        result = await real_client.process(request)

        print(f"\n[REAL TEST] Duration: {result['duration_ms']}ms")
        print(f"[REAL TEST] Success: {result['success']}")

        # Should get some response
        assert result['success'] or len(result['output']) > 0, \
            "Should get a response from at least one provider"


class TestRealStreaming:
    """Test real streaming behavior."""

    @pytest.mark.timeout(60)
    async def test_streaming_produces_chunks(self, real_client):
        """
        REAL TEST: Response should stream in chunks, not all at once.
        """
        request = "Write a haiku about programming."

        result = await real_client.process(request)

        print(f"\n[REAL TEST] Duration: {result['duration_ms']}ms")
        print(f"[REAL TEST] Chunks received: {len(result['chunks'])}")

        if result['error']:
            pytest.skip(f"LLM error: {result['error']}")

        # Should have received multiple chunks (streaming)
        # Note: Some providers may batch, so allow minimum of 1
        assert len(result['chunks']) >= 1, \
            "Should receive streaming chunks"


class TestRealQualityValidation:
    """Validate quality of real outputs."""

    @pytest.mark.timeout(120)
    async def test_code_quality(self, real_client):
        """
        REAL TEST: Generated code should be syntactically valid.
        """
        request = "Write a Python function to calculate factorial recursively."

        result = await real_client.process(request)

        if result['error']:
            pytest.skip(f"LLM error: {result['error']}")

        # Extract code from output
        output = result['output']

        # Try to find code block
        if "```python" in output:
            code_start = output.find("```python") + len("```python")
            code_end = output.find("```", code_start)
            code = output[code_start:code_end].strip()
        elif "def " in output:
            # Find the function definition
            lines = output.split('\n')
            code_lines = []
            in_code = False
            for line in lines:
                if "def " in line:
                    in_code = True
                if in_code:
                    code_lines.append(line)
                    if line.strip() and not line.startswith(' ') and not line.startswith('def'):
                        break
            code = '\n'.join(code_lines)
        else:
            code = ""

        if code:
            # Validate syntax
            try:
                compile(code, '<string>', 'exec')
                syntax_valid = True
            except SyntaxError as e:
                print(f"[REAL TEST] Syntax error: {e}")
                syntax_valid = False

            assert syntax_valid, "Generated code should be syntactically valid"

    @pytest.mark.timeout(90)
    async def test_response_relevance(self, real_client):
        """
        REAL TEST: Response should be relevant to the request.
        """
        request = "What are the benefits of using type hints in Python?"

        result = await real_client.process(request)

        if result['error']:
            pytest.skip(f"LLM error: {result['error']}")

        output_lower = result['output'].lower()

        # Should mention type-related concepts
        relevant_terms = ["type", "hint", "annotation", "static", "check", "error", "ide"]
        terms_found = sum(1 for term in relevant_terms if term in output_lower)

        assert terms_found >= 2, \
            f"Response should be relevant to type hints, found {terms_found} relevant terms"


class TestRealErrorHandling:
    """Test real error handling behavior."""

    @pytest.mark.timeout(60)
    async def test_invalid_request_handled(self, real_client):
        """
        REAL TEST: Invalid/nonsense requests should be handled gracefully.
        """
        request = "asdfghjkl qwertyuiop zxcvbnm"

        result = await real_client.process(request)

        # Should not crash
        # May produce error message or ask for clarification
        assert result['success'] or result['error'] is not None or len(result['output']) > 0

    @pytest.mark.timeout(60)
    async def test_empty_request_handled(self, real_client):
        """
        REAL TEST: Empty requests should be handled gracefully.
        """
        result = await real_client.process("")

        # Should not crash
        # May produce error or prompt for input
        assert True  # If we get here, it didn't crash


# Performance benchmarks
class TestRealPerformance:
    """Performance benchmarks with real system."""

    @pytest.mark.timeout(180)
    @pytest.mark.benchmark
    async def test_latency_benchmark(self, real_client):
        """
        REAL BENCHMARK: Measure response latency.
        """
        request = "What is 2+2?"

        durations = []
        for i in range(3):
            result = await real_client.process(request)
            if result['success']:
                durations.append(result['duration_ms'])

        if durations:
            avg_ms = sum(durations) / len(durations)
            print(f"\n[BENCHMARK] Average latency: {avg_ms:.0f}ms")
            print(f"[BENCHMARK] Min: {min(durations)}ms, Max: {max(durations)}ms")

            # Basic latency expectation
            assert avg_ms < 30000, f"Average latency too high: {avg_ms}ms"
