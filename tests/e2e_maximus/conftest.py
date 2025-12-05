"""
E2E Test Fixtures for MAXIMUS Integration.

Production-ready fixtures using respx for httpx mocking.

Based on 2025 best practices:
- respx for async httpx mocking
- Factory pattern for response builders
- Session-scoped fixtures for efficiency

Follows CODE_CONSTITUTION: <500 lines, 100% type hints, Google docstrings.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Generator, List

import pytest
import respx

from jdev_cli.core.providers.maximus_config import MaximusConfig
from jdev_cli.core.providers.maximus_provider import MaximusProvider
from jdev_cli.core.providers.resilience import CircuitBreakerConfig, RetryConfig

from .mock_builders import MaximusMockFactory


# =============================================================================
# RESPX FIXTURES
# =============================================================================


@pytest.fixture
def maximus_base_url() -> str:
    """Get MAXIMUS base URL for testing."""
    return "http://localhost:8100"


@pytest.fixture
def mock_factory() -> MaximusMockFactory:
    """Get mock factory instance."""
    return MaximusMockFactory()


@pytest.fixture
def mock_maximus_health(
    maximus_base_url: str,  # pylint: disable=redefined-outer-name
    mock_factory: MaximusMockFactory,  # pylint: disable=redefined-outer-name
) -> Generator[respx.MockRouter, None, None]:
    """Mock MAXIMUS health endpoint."""
    with respx.mock(assert_all_called=False) as router:
        router.get(f"{maximus_base_url}/health").respond(
            json=mock_factory.health_response()
        )
        yield router


@pytest.fixture
def mock_maximus_tribunal(
    maximus_base_url: str,  # pylint: disable=redefined-outer-name
    mock_factory: MaximusMockFactory,  # pylint: disable=redefined-outer-name
) -> Generator[respx.MockRouter, None, None]:
    """Mock MAXIMUS Tribunal endpoints."""
    with respx.mock(assert_all_called=False) as router:
        router.get(f"{maximus_base_url}/health").respond(
            json=mock_factory.health_response()
        )
        router.post(f"{maximus_base_url}/v1/tribunal/evaluate").respond(
            json=mock_factory.tribunal_evaluate()
        )
        router.get(f"{maximus_base_url}/v1/tribunal/health").respond(
            json=mock_factory.health_response()
        )
        router.get(f"{maximus_base_url}/v1/tribunal/stats").respond(
            json=mock_factory.tribunal_stats()
        )
        yield router


@pytest.fixture
def mock_maximus_memory(
    maximus_base_url: str,  # pylint: disable=redefined-outer-name
    mock_factory: MaximusMockFactory,  # pylint: disable=redefined-outer-name
) -> respx.MockRouter:
    """Mock MAXIMUS Memory endpoints."""
    with respx.mock(assert_all_called=False) as router:
        router.get(f"{maximus_base_url}/health").respond(
            json=mock_factory.health_response()
        )
        router.post(f"{maximus_base_url}/v1/memories").respond(
            json=mock_factory.memory_store()
        )
        router.get(f"{maximus_base_url}/v1/memories/search").respond(
            json=mock_factory.memory_search()
        )
        router.post(f"{maximus_base_url}/v1/memories/context").respond(
            json=mock_factory.memory_context()
        )
        router.post(f"{maximus_base_url}/v1/memories/consolidate").respond(
            json=mock_factory.memory_consolidate()
        )
        yield router


@pytest.fixture
def mock_maximus_factory(
    maximus_base_url: str,  # pylint: disable=redefined-outer-name
    mock_factory: MaximusMockFactory,  # pylint: disable=redefined-outer-name
) -> respx.MockRouter:
    """Mock MAXIMUS Factory endpoints."""
    with respx.mock(assert_all_called=False) as router:
        router.get(f"{maximus_base_url}/health").respond(
            json=mock_factory.health_response()
        )
        router.post(f"{maximus_base_url}/v1/tools/generate").respond(
            json=mock_factory.factory_generate()
        )
        router.get(f"{maximus_base_url}/v1/tools").respond(
            json=mock_factory.factory_list()
        )
        router.post(url__regex=r".*/v1/tools/.*/execute").respond(
            json=mock_factory.factory_execute("test_tool")
        )
        router.delete(url__regex=r".*/v1/tools/.*").respond(
            json={"success": True}
        )
        yield router


@pytest.fixture
def mock_maximus_all(
    maximus_base_url: str,  # pylint: disable=redefined-outer-name
    mock_factory: MaximusMockFactory,  # pylint: disable=redefined-outer-name
) -> respx.MockRouter:
    """Mock all MAXIMUS endpoints."""
    with respx.mock(assert_all_called=False) as router:
        # Health
        router.get(f"{maximus_base_url}/health").respond(
            json=mock_factory.health_response()
        )

        # Tribunal
        router.post(f"{maximus_base_url}/v1/tribunal/evaluate").respond(
            json=mock_factory.tribunal_evaluate()
        )
        router.get(f"{maximus_base_url}/v1/tribunal/health").respond(
            json=mock_factory.health_response()
        )
        router.get(f"{maximus_base_url}/v1/tribunal/stats").respond(
            json=mock_factory.tribunal_stats()
        )

        # Memory
        router.post(f"{maximus_base_url}/v1/memories").respond(
            json=mock_factory.memory_store()
        )
        router.get(f"{maximus_base_url}/v1/memories/search").respond(
            json=mock_factory.memory_search()
        )
        router.post(f"{maximus_base_url}/v1/memories/context").respond(
            json=mock_factory.memory_context()
        )
        router.post(f"{maximus_base_url}/v1/memories/consolidate").respond(
            json=mock_factory.memory_consolidate()
        )

        # Factory
        router.post(f"{maximus_base_url}/v1/tools/generate").respond(
            json=mock_factory.factory_generate()
        )
        router.get(f"{maximus_base_url}/v1/tools").respond(
            json=mock_factory.factory_list()
        )
        router.post(url__regex=r".*/v1/tools/.*/execute").respond(
            json=mock_factory.factory_execute("test_tool")
        )
        router.delete(url__regex=r".*/v1/tools/.*").respond(
            json={"success": True}
        )

        yield router


# =============================================================================
# PROVIDER FIXTURES
# =============================================================================


@pytest.fixture
def maximus_config() -> MaximusConfig:
    """Create test configuration."""
    return MaximusConfig(
        base_url="http://localhost:8100",
        timeout=5.0,
        retry=RetryConfig(max_attempts=2, initial_wait=0.1),
        circuit_breaker=CircuitBreakerConfig(failure_threshold=3),
    )


@pytest.fixture
async def maximus_provider(
    maximus_config: MaximusConfig,  # pylint: disable=redefined-outer-name
    mock_maximus_all: respx.MockRouter,  # pylint: disable=redefined-outer-name,unused-argument
) -> AsyncIterator[MaximusProvider]:
    """Create MaximusProvider with mocked backend."""
    provider = MaximusProvider(config=maximus_config)
    yield provider
    await provider.close()


# =============================================================================
# METRICS FIXTURES
# =============================================================================


@dataclass
class E2EMetrics:
    """Metrics collection for E2E tests."""

    test_name: str = ""
    duration_ms: float = 0.0
    success: bool = True
    api_calls: int = 0
    errors: List[str] = field(default_factory=list)


@pytest.fixture
def e2e_metrics() -> E2EMetrics:
    """Create metrics collector for a test."""
    return E2EMetrics()


@pytest.fixture
def timer() -> type:
    """Create a timer context manager."""

    class Timer:
        """Simple timer for performance measurement."""

        def __init__(self) -> None:
            """Initialize timer."""
            self.start_time: float = 0.0
            self.end_time: float = 0.0

        def __enter__(self) -> "Timer":
            """Start timer."""
            self.start_time = time.perf_counter()
            return self

        def __exit__(self, *args: Any) -> None:
            """Stop timer."""
            self.end_time = time.perf_counter()

        @property
        def elapsed_ms(self) -> float:
            """Get elapsed time in milliseconds."""
            return (self.end_time - self.start_time) * 1000

    return Timer
