import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from vertice_cli.core.recovery import (
    ErrorRecoveryEngine,
    RecoveryContext,
    ErrorCategory,
)


@pytest.fixture
def mock_llm():
    """Mock LLM client."""
    llm = Mock()
    llm.generate_async = AsyncMock(return_value={
        "content": """DIAGNOSIS: Test error analysis
CORRECTION: Use corrected parameters
TOOL_CALL: {"tool": "test_tool", "args": {"corrected": true}}"""
    })
    return llm


@pytest.fixture
def recovery_context():
    """Create recovery context."""
    return RecoveryContext(
        attempt_number=1,
        max_attempts=2,
        error="Test error",
        error_category=ErrorCategory.SYNTAX,
        failed_tool="test_tool",
        failed_args={"arg": "value"},
        previous_result=None,
        user_intent="Test intent",
        previous_commands=[]
    )


@pytest.mark.skip(reason="QUARANTINED: Timing-based test is flaky - functionality verified in other tests")
@pytest.mark.asyncio
async def test_recovery_with_backoff_applies_delay(mock_llm, recovery_context):
    """Test that backoff delay is applied on retry."""
    engine = ErrorRecoveryEngine(
        llm_client=mock_llm,
        enable_retry_policy=True,
        enable_circuit_breaker=False
    )

    # Second attempt should have delay
    recovery_context.attempt_number = 2

    import time
    start = time.time()

    await engine.attempt_recovery_with_backoff(
        recovery_context,
        Exception("Transient error: timeout")
    )

    elapsed = time.time() - start

    # Should have waited at least 0.9 seconds (base delay ~1s minus jitter variance)
    # We allow some margin due to system timing and async overhead
    assert elapsed >= 0.8, f"Expected >= 0.8s, got {elapsed}s"


@pytest.mark.skip(reason="QUARANTINED: Timing-based test is flaky - functionality verified in other tests")
@pytest.mark.asyncio
async def test_multiple_recovery_attempts_with_backoff(mock_llm):
    """Test multiple recovery attempts with exponential backoff."""
    engine = ErrorRecoveryEngine(
        llm_client=mock_llm,
        max_attempts=4,
        enable_retry_policy=True,
        enable_circuit_breaker=False
    )

    delays = []

    for attempt in range(1, 5):
        context = RecoveryContext(
            attempt_number=attempt,
            max_attempts=4,
            error="Test error",
            error_category=ErrorCategory.NETWORK,
            failed_tool="test_tool",
            failed_args={},
            previous_result=None,
            user_intent="Test",
            previous_commands=[]
        )

        import time
        start = time.time()

        await engine.attempt_recovery_with_backoff(
            context,
            Exception("Network timeout")
        )

        elapsed = time.time() - start
        delays.append(elapsed)

    # First attempt: no delay (first attempt doesn't need backoff)
    assert delays[0] < 0.5

    # Subsequent attempts should have increasing delays
    # Second attempt: ~1s delay
    assert delays[1] >= 0.8, f"Attempt 2: expected >= 0.8s, got {delays[1]}s"

    # Third attempt: ~2s delay
    assert delays[2] >= 1.8, f"Attempt 3: expected >= 1.8s, got {delays[2]}s"

    # Fourth attempt: ~4s delay
    assert delays[3] >= 3.5, f"Attempt 4: expected >= 3.5s, got {delays[3]}s"

    # Verify exponential growth pattern
    assert delays[2] > delays[1], "Delays should grow exponentially"
    assert delays[3] > delays[2], "Delays should grow exponentially"
