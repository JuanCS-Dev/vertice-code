"""Pytest configuration and fixtures for Textual async testing (2025 best practices)."""

import pytest
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root and src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# =============================================================================
# MOCK LLM CLIENT - Global fixture for all agent tests
# =============================================================================


class MockLLMClient:
    """
    Mock LLM client for testing without API calls.

    Used by all agent tests that require llm_client parameter.
    """

    def __init__(self, responses: Optional[Dict[str, str]] = None):
        self.responses = responses or {}
        self.call_history: List[Dict[str, Any]] = []
        self.default_response = '{"success": true, "result": "Mock response"}'

    async def generate(
        self,
        prompt: str,
        context: str = "",
        max_tokens: int = 500,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """Generate mock response."""
        self.call_history.append(
            {"method": "generate", "prompt": prompt, "context": context, "kwargs": kwargs}
        )

        # Check for specific responses
        for key, response in self.responses.items():
            if key.lower() in prompt.lower():
                return response

        return self.default_response

    async def stream_chat(self, prompt: str, context: str = "", **kwargs):
        """Stream mock response."""
        self.call_history.append({"method": "stream_chat", "prompt": prompt, "context": context})

        response = self.default_response
        for word in response.split():
            yield word + " "
            await asyncio.sleep(0.001)


# =============================================================================
# MOCK MCP CLIENT - Global fixture for all agent tests
# =============================================================================


class MockMCPClient:
    """
    Mock MCP client for testing tool execution.

    Used by all agent tests that require mcp_client parameter.
    """

    def __init__(self):
        self.call_history: List[Dict[str, Any]] = []
        self.mock_results: Dict[str, Dict[str, Any]] = {}

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a mock tool call."""
        self.call_history.append({"tool": tool_name, "arguments": arguments})

        # Return mock result if configured
        if tool_name in self.mock_results:
            return self.mock_results[tool_name]

        # Default mock responses
        default_results = {
            "read_file": {"content": "# Mock file content"},
            "write_file": {"success": True},
            "list_files": {"files": ["file1.py", "file2.py"]},
            "execute_command": {"stdout": "OK", "returncode": 0},
        }

        return default_results.get(tool_name, {"result": "OK"})

    def set_mock_result(self, tool_name: str, result: Dict[str, Any]) -> None:
        """Configure mock result for a specific tool."""
        self.mock_results[tool_name] = result


# =============================================================================
# GLOBAL FIXTURES FOR AGENT TESTS
# =============================================================================


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    return MockLLMClient()


@pytest.fixture
def mock_mcp_client():
    """Create a mock MCP client for testing."""
    return MockMCPClient()


@pytest.fixture
def mock_llm_with_responses():
    """Factory fixture to create mock LLM with custom responses."""

    def _create(responses: Dict[str, str]):
        return MockLLMClient(responses)

    return _create


# =============================================================================
# SESSION FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def event_loop():
    """Create session-scoped event loop for all async tests.

    Based on 2025 best practices for pytest-asyncio + Textual.
    Prevents 'Event loop is closed' errors.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def mock_config():
    """Mock configuration for testing."""
    from vertice_cli.core.config import Config

    config = Config()
    config.model_name = "test-model"
    config.api_key = "test-key"
    config.max_tokens = 1000
    return config


@pytest.fixture(scope="function")
def temp_workspace(tmp_path):
    """Create temporary workspace for file operations."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace


# =============================================================================
# AZURE EMBEDDINGS FIXTURES (Sprint 0: Test Hygiene)
# =============================================================================


@pytest.fixture
def mock_azure_env(monkeypatch):
    """
    Mock Azure environment to force local fallback.

    Use this fixture in tests that should NOT call real Azure API.
    """
    monkeypatch.delenv("AZURE_OPENAI_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_DEPLOYMENT", raising=False)


@pytest.fixture
def mock_embeddings():
    """
    Mock embedding generation for tests that don't need real embeddings.

    Returns a function that generates deterministic fake embeddings.
    """

    def _generate(text: str, dimensions: int = 64) -> List[float]:
        """Generate deterministic fake embedding from text hash."""
        import hashlib

        hash_bytes = hashlib.sha256(text.encode()).digest()
        embedding = []
        for i in range(dimensions):
            byte_val = hash_bytes[i % len(hash_bytes)]
            embedding.append((byte_val / 255.0) * 2 - 1)  # Normalize to [-1, 1]
        # Normalize to unit length
        import math

        norm = math.sqrt(sum(x * x for x in embedding))
        return [x / norm for x in embedding]

    return _generate


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "azure_integration: mark test as requiring real Azure API (skip when unavailable)",
    )
    config.addinivalue_line("markers", "slow: mark test as slow running")
