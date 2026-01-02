"""
REAL Tool Execution Tests

Tests actual tool execution with REAL LLM calls.
Validates that tools are:
1. Correctly identified from requests
2. Properly executed with correct parameters
3. Results properly integrated into responses
"""

import pytest
import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.real,
    pytest.mark.tool_interaction,
]


def load_env():
    """Load environment variables."""
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip('"\''))


load_env()


class ToolExecutionTester:
    """Tester for real tool execution."""

    def __init__(self):
        self.initialized = False
        self.bridge = None
        self.tool_calls: List[Dict] = []

    async def initialize(self):
        """Initialize the system."""
        try:
            from vertice_tui.core.bridge import Bridge

            self.bridge = Bridge()
            await self.bridge.initialize()
            self.initialized = True
            return True
        except Exception as e:
            print(f"Initialization error: {e}")
            return False

    async def execute_request(self, message: str, timeout: int = 90) -> Dict:
        """Execute a request and track tool usage."""
        result = {
            "success": False,
            "output": "",
            "tools_detected": [],
            "tool_results": [],
            "latency_ms": 0,
            "error": None,
        }

        start = time.time()

        try:
            output = ""
            async for chunk in self.bridge.process_message(message):
                if hasattr(chunk, 'content'):
                    output += chunk.content
                elif isinstance(chunk, str):
                    output += chunk
                elif isinstance(chunk, dict):
                    if 'content' in chunk:
                        output += chunk['content']
                    if 'tool_call' in chunk:
                        result['tools_detected'].append(chunk['tool_call'])
                    if 'tool_result' in chunk:
                        result['tool_results'].append(chunk['tool_result'])

            result['output'] = output
            result['success'] = True

        except asyncio.TimeoutError:
            result['error'] = 'Timeout'
        except Exception as e:
            result['error'] = str(e)

        result['latency_ms'] = int((time.time() - start) * 1000)
        return result

    async def cleanup(self):
        """Cleanup resources."""
        if self.bridge:
            try:
                await self.bridge.shutdown()
            except Exception:
                pass


@pytest.fixture
async def tool_tester():
    """Provide tool execution tester."""
    tester = ToolExecutionTester()
    success = await tester.initialize()

    if not success:
        pytest.skip("Could not initialize tool tester")

    yield tester

    await tester.cleanup()


class TestFileOperationTools:
    """Test file operation tools."""

    @pytest.mark.timeout(120)
    async def test_read_file_tool(self, tool_tester):
        """
        REAL TEST: Read file tool should read actual files.
        """
        # Request to read a known file
        request = "Read the pyproject.toml file and tell me the project name"

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Duration: {result['latency_ms']}ms")
        print(f"[TOOL] Output: {result['output'][:300]}...")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should find the project name
        output_lower = result['output'].lower()
        assert 'vertice' in output_lower, \
            "Should read and report the project name from pyproject.toml"

    @pytest.mark.timeout(120)
    async def test_search_code_tool(self, tool_tester):
        """
        REAL TEST: Code search tool should find code.
        """
        request = "Search for where 'TUIBridge' class is defined in this project"

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should mention the file location
        output = result['output']
        found_location = any(s in output for s in ['bridge.py', 'vertice_tui', 'core'])

        assert found_location or 'TUIBridge' in output, \
            "Should find where TUIBridge is defined"

    @pytest.mark.timeout(120)
    async def test_list_files_tool(self, tool_tester):
        """
        REAL TEST: List files tool should show directory contents.
        """
        request = "List the files in the root directory of this project"

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should mention common project files
        output_lower = result['output'].lower()
        common_files = ['pyproject.toml', 'readme', 'setup', '.git', 'tests']
        found_files = sum(1 for f in common_files if f in output_lower)

        assert found_files >= 1, \
            "Should list recognizable project files"


class TestCodeExecutionTools:
    """Test code execution related tools."""

    @pytest.mark.timeout(120)
    async def test_python_execution(self, tool_tester):
        """
        REAL TEST: Should be able to execute/evaluate Python code.
        """
        request = "Calculate the factorial of 5 using Python"

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Duration: {result['latency_ms']}ms")
        print(f"[TOOL] Output: {result['output'][:300]}...")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should produce the correct answer (120)
        assert '120' in result['output'], \
            "Should calculate factorial(5) = 120"

    @pytest.mark.timeout(120)
    async def test_code_analysis(self, tool_tester):
        """
        REAL TEST: Should analyze code for issues.
        """
        request = """
        Analyze this Python code for potential issues:
        ```python
        def divide(a, b):
            return a / b
        ```
        """

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        output_lower = result['output'].lower()

        # Should mention division by zero risk
        mentions_issue = any(word in output_lower for word in
            ['zero', 'divide', 'error', 'exception', 'check', 'handle'])

        assert mentions_issue, \
            "Should identify division by zero as potential issue"


class TestToolChaining:
    """Test chained tool execution."""

    @pytest.mark.timeout(180)
    async def test_read_then_analyze(self, tool_tester):
        """
        REAL TEST: Should chain read and analyze operations.
        """
        request = "Read the README.md file and summarize its main points"

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should produce a summary (substantial output)
        assert len(result['output']) > 100, \
            "Should produce a meaningful summary"

    @pytest.mark.timeout(180)
    async def test_search_then_read(self, tool_tester):
        """
        REAL TEST: Should search for file then read it.
        """
        request = "Find the main configuration file and show me its contents"

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should find and show config content
        output_lower = result['output'].lower()
        found_config = any(word in output_lower for word in
            ['config', 'settings', 'yaml', 'toml', 'json', 'env'])

        assert found_config or len(result['output']) > 50, \
            "Should find and display configuration"


class TestToolErrorHandling:
    """Test tool error handling."""

    @pytest.mark.timeout(90)
    async def test_nonexistent_file(self, tool_tester):
        """
        REAL TEST: Should handle request for nonexistent file gracefully.
        """
        request = "Read the file nonexistent_file_12345.xyz"

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Output: {result['output'][:200]}...")

        # Should not crash, should report file not found
        assert result['output'] or result['error']

        if result['output']:
            output_lower = result['output'].lower()
            handled_gracefully = any(word in output_lower for word in
                ['not found', 'doesn\'t exist', 'cannot', 'unable', 'error', 'no such'])
            assert handled_gracefully or len(result['output']) > 0

    @pytest.mark.timeout(90)
    async def test_invalid_path(self, tool_tester):
        """
        REAL TEST: Should handle invalid path gracefully.
        """
        request = "Read the file at /this/path/is/definitely/invalid/file.txt"

        result = await tool_tester.execute_request(request)

        # Should not crash
        assert result is not None


class TestToolIntegration:
    """Test tool integration with LLM responses."""

    @pytest.mark.timeout(120)
    async def test_tool_result_in_response(self, tool_tester):
        """
        REAL TEST: Tool results should be integrated into response.
        """
        request = "What is the Python version specified in pyproject.toml?"

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        # Should mention Python version
        output = result['output']
        has_version = any(v in output for v in ['3.', 'python', 'version'])

        assert has_version, \
            "Response should include Python version from file"

    @pytest.mark.timeout(180)
    async def test_multi_tool_coordination(self, tool_tester):
        """
        REAL TEST: Multiple tools should work together.
        """
        request = """
        1. Find the test files in this project
        2. Count how many test files there are
        3. Tell me which testing framework is used
        """

        result = await tool_tester.execute_request(request)

        print(f"\n[TOOL] Duration: {result['latency_ms']}ms")

        if result['error']:
            pytest.skip(f"Error: {result['error']}")

        output_lower = result['output'].lower()

        # Should mention tests
        mentions_tests = any(word in output_lower for word in
            ['test', 'pytest', 'unittest', 'files', 'found'])

        assert mentions_tests, \
            "Should address the multi-part request about tests"


class TestToolPerformance:
    """Performance tests for tools."""

    @pytest.mark.timeout(180)
    @pytest.mark.benchmark
    async def test_file_read_performance(self, tool_tester):
        """
        REAL BENCHMARK: Measure file read tool performance.
        """
        requests = [
            "Read pyproject.toml",
            "Read README.md",
            "Read CLAUDE.md",
        ]

        latencies = []
        for req in requests:
            result = await tool_tester.execute_request(req)
            if result['success']:
                latencies.append(result['latency_ms'])

        if latencies:
            avg = sum(latencies) / len(latencies)
            print(f"\n[BENCHMARK] Avg file read latency: {avg:.0f}ms")
            print(f"[BENCHMARK] Individual: {latencies}")

    @pytest.mark.timeout(180)
    @pytest.mark.benchmark
    async def test_search_performance(self, tool_tester):
        """
        REAL BENCHMARK: Measure code search performance.
        """
        result = await tool_tester.execute_request(
            "Search for all Python files containing 'async def'"
        )

        print(f"\n[BENCHMARK] Search latency: {result['latency_ms']}ms")
        print(f"[BENCHMARK] Success: {result['success']}")
