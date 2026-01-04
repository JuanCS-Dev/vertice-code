"""Tests for Day 7 recovery engine integration.

Tests the integration of RetryPolicy and CircuitBreaker with ErrorRecoveryEngine.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from vertice_cli.core.recovery import (
    ErrorRecoveryEngine,
    RecoveryContext,
    ErrorCategory
)


class TestRecoveryEngineIntegration:
    """Test recovery engine with retry policy and circuit breaker."""

    @pytest.fixture
    def mock_llm(self):
        """Mock LLM client."""
        llm = Mock()
        llm.generate_async = AsyncMock(return_value={
            "content": """DIAGNOSIS: Test error analysis
CORRECTION: Use corrected parameters
TOOL_CALL: {"tool": "test_tool", "args": {"corrected": true}}"""
        })
        return llm

    @pytest.fixture
    def recovery_context(self):
        """Create recovery context."""
        return RecoveryContext(
            attempt_number=1,
            max_attempts=3,
            error="Test error",
            error_category=ErrorCategory.NETWORK,
            failed_tool="test_tool",
            failed_args={"arg": "value"},
            previous_result=None,
            user_intent="Test intent",
            previous_commands=[]
        )

    def test_initialization_with_enhancements(self, mock_llm):
        """Test engine initialization with retry policy and circuit breaker."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_retry_policy=True,
            enable_circuit_breaker=True
        )

        assert engine.retry_policy is not None
        assert engine.circuit_breaker is not None

    def test_initialization_without_enhancements(self, mock_llm):
        """Test engine initialization without enhancements."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_retry_policy=False,
            enable_circuit_breaker=False
        )

        assert engine.retry_policy is None
        assert engine.circuit_breaker is None

    @pytest.mark.asyncio
    async def test_recovery_with_backoff_success(self, mock_llm, recovery_context):
        """Test successful recovery with backoff."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_retry_policy=True,
            enable_circuit_breaker=True
        )

        result = await engine.attempt_recovery_with_backoff(
            recovery_context,
            Exception("Test error")
        )

        assert result is not None
        # Circuit breaker should record success
        assert engine.circuit_breaker.state == "CLOSED"

    @patch('asyncio.sleep', new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_recovery_with_backoff_applies_delay(self, mock_sleep, mock_llm, recovery_context):
        """Test that backoff delay is applied on retry."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_retry_policy=True,
            enable_circuit_breaker=False
        )
        recovery_context.attempt_number = 2

        await engine.attempt_recovery_with_backoff(
            recovery_context,
            Exception("Transient error: timeout")
        )

        mock_sleep.assert_awaited_once()
        delay_duration = mock_sleep.call_args[0][0]
        assert 1.8 <= delay_duration <= 3.2

    @pytest.mark.asyncio
    async def test_circuit_breaker_prevents_recovery(self, mock_llm, recovery_context):
        """Test circuit breaker prevents recovery when open."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_retry_policy=False,
            enable_circuit_breaker=True
        )

        # Open the circuit by recording failures
        for _ in range(5):
            engine.circuit_breaker.record_failure()

        assert engine.circuit_breaker.state == "OPEN"

        # Attempt recovery should be prevented
        result = await engine.attempt_recovery_with_backoff(
            recovery_context,
            Exception("Test error")
        )

        assert result.success is False
        assert "Circuit breaker" in result.escalation_reason

    @pytest.mark.asyncio
    async def test_circuit_breaker_allows_after_timeout(self, mock_llm, recovery_context):
        """Test circuit breaker allows recovery after timeout."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_retry_policy=False,
            enable_circuit_breaker=True
        )

        # Configure short timeout
        engine.circuit_breaker.timeout = 0.1

        # Open the circuit
        for _ in range(5):
            engine.circuit_breaker.record_failure()

        assert engine.circuit_breaker.state == "OPEN"

        # Wait for timeout
        await asyncio.sleep(0.15)

        # Check if circuit allows recovery (should transition to HALF_OPEN)
        allowed, reason = engine.circuit_breaker.should_allow_recovery()

        assert allowed is True
        assert engine.circuit_breaker.state == "HALF_OPEN"

    @pytest.mark.asyncio
    async def test_retry_policy_rejects_permanent_errors(self, mock_llm, recovery_context):
        """Test retry policy rejects permanent errors."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_retry_policy=True,
            enable_circuit_breaker=False
        )

        recovery_context.attempt_number = 2

        # Permanent error
        permanent_error = Exception("File not found 404")

        result = await engine.attempt_recovery_with_backoff(
            recovery_context,
            permanent_error
        )

        assert result.success is False
        assert "Retry policy rejected" in result.escalation_reason

    @pytest.mark.asyncio
    async def test_retry_policy_accepts_transient_errors(self, mock_llm, recovery_context):
        """Test retry policy accepts transient errors."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_retry_policy=True,
            enable_circuit_breaker=False
        )

        recovery_context.attempt_number = 2

        # Transient error
        transient_error = Exception("Connection timeout")

        result = await engine.attempt_recovery_with_backoff(
            recovery_context,
            transient_error
        )

        # Should attempt recovery (not rejected by policy)
        assert result is not None

    def test_get_statistics_includes_circuit_breaker(self, mock_llm):
        """Test statistics include circuit breaker status."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_retry_policy=True,
            enable_circuit_breaker=True
        )

        stats = engine.get_statistics()

        assert "circuit_breaker" in stats
        assert stats["circuit_breaker"]["state"] == "CLOSED"

    def test_get_circuit_breaker_status(self, mock_llm):
        """Test getting circuit breaker status."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_circuit_breaker=True
        )

        status = engine.get_circuit_breaker_status()

        assert status is not None
        assert "state" in status
        assert "failure_count" in status

    def test_get_circuit_breaker_status_disabled(self, mock_llm):
        """Test getting status when circuit breaker disabled."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_circuit_breaker=False
        )

        status = engine.get_circuit_breaker_status()
        assert status is None

    def test_reset_circuit_breaker(self, mock_llm):
        """Test manually resetting circuit breaker."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_circuit_breaker=True
        )

        # Open circuit
        for _ in range(5):
            engine.circuit_breaker.record_failure()

        assert engine.circuit_breaker.state == "OPEN"

        # Reset
        engine.reset_circuit_breaker()

        assert engine.circuit_breaker.state == "CLOSED"
        assert engine.circuit_breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_recovery_updates_circuit_breaker_on_success(self, mock_llm, recovery_context):
        """Test successful recovery updates circuit breaker."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_circuit_breaker=True
        )

        initial_failures = engine.circuit_breaker.failure_count

        result = await engine.attempt_recovery_with_backoff(
            recovery_context,
            Exception("Test error")
        )

        # Should have provided a correction (success)
        assert result.corrected_args is not None

        # Circuit breaker should record success
        # In CLOSED state, success reduces failure count
        assert engine.circuit_breaker.failure_count <= initial_failures

    @pytest.mark.asyncio
    async def test_recovery_updates_circuit_breaker_on_failure(self, mock_llm, recovery_context):
        """Test failed recovery updates circuit breaker."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            enable_circuit_breaker=True
        )

        # Make LLM fail
        mock_llm.generate_async = AsyncMock(side_effect=Exception("LLM failed"))

        initial_failures = engine.circuit_breaker.failure_count

        result = await engine.attempt_recovery_with_backoff(
            recovery_context,
            Exception("Test error")
        )

        # Failure should increment failure count
        assert engine.circuit_breaker.failure_count > initial_failures

    @patch('asyncio.sleep', new_callable=AsyncMock)
    @pytest.mark.asyncio
    async def test_multiple_recovery_attempts_with_backoff(self, mock_sleep, mock_llm):
        """Test multiple recovery attempts with exponential backoff."""
        engine = ErrorRecoveryEngine(
            llm_client=mock_llm,
            max_attempts=4,
            enable_retry_policy=True,
            enable_circuit_breaker=False
        )

        # First attempt should not sleep
        context1 = RecoveryContext(attempt_number=1, max_attempts=4, error="Test", error_category=ErrorCategory.NETWORK, failed_tool="test", failed_args={}, previous_result=None, user_intent="Test", previous_commands=[])
        await engine.attempt_recovery_with_backoff(context1, Exception("Network timeout"))
        mock_sleep.assert_not_called()

        # Second attempt should sleep
        context2 = RecoveryContext(attempt_number=2, max_attempts=4, error="Test", error_category=ErrorCategory.NETWORK, failed_tool="test", failed_args={}, previous_result=None, user_intent="Test", previous_commands=[])
        await engine.attempt_recovery_with_backoff(context2, Exception("Network timeout"))
        mock_sleep.assert_awaited_once()
        assert 1.8 <= mock_sleep.call_args[0][0] <= 3.2
        mock_sleep.reset_mock()

        # Third attempt
        context3 = RecoveryContext(attempt_number=3, max_attempts=4, error="Test", error_category=ErrorCategory.NETWORK, failed_tool="test", failed_args={}, previous_result=None, user_intent="Test", previous_commands=[])
        await engine.attempt_recovery_with_backoff(context3, Exception("Network timeout"))
        mock_sleep.assert_awaited_once()
        assert 3.6 <= mock_sleep.call_args[0][0] <= 6.4
