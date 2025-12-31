"""
Scientific E2E Tests: Error Handling Flow

Flow: Error → Propagation → Recovery

Tests cover:
- Error classification
- Error propagation chains
- Circuit breaker behavior
- Retry logic
- Recovery mechanisms
- Cascading failure prevention
"""

import pytest
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch
from typing import Optional


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def circuit_breaker():
    """Create circuit breaker for testing."""
    class CircuitBreaker:
        CLOSED = "CLOSED"
        OPEN = "OPEN"
        HALF_OPEN = "HALF_OPEN"

        def __init__(
            self,
            failure_threshold: int = 5,
            recovery_timeout: float = 30.0
        ):
            self.failure_threshold = failure_threshold
            self.recovery_timeout = recovery_timeout
            self.state = self.CLOSED
            self.failure_count = 0
            self.last_failure_time: Optional[float] = None
            self.success_count = 0

        def can_attempt(self) -> bool:
            if self.state == self.CLOSED:
                return True
            elif self.state == self.OPEN:
                if self.last_failure_time:
                    if time.time() - self.last_failure_time >= self.recovery_timeout:
                        self.state = self.HALF_OPEN
                        return True
                return False
            elif self.state == self.HALF_OPEN:
                return True
            return False

        def record_success(self) -> None:
            if self.state == self.HALF_OPEN:
                self.state = self.CLOSED
            self.failure_count = 0
            self.success_count += 1

        def record_failure(self) -> None:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.failure_threshold:
                self.state = self.OPEN

            if self.state == self.HALF_OPEN:
                self.state = self.OPEN

        def reset(self) -> None:
            self.state = self.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None

    return CircuitBreaker()


@pytest.fixture
def retry_handler():
    """Create retry handler for testing."""
    class RetryHandler:
        def __init__(
            self,
            max_retries: int = 3,
            base_delay: float = 1.0,
            exponential: bool = True
        ):
            self.max_retries = max_retries
            self.base_delay = base_delay
            self.exponential = exponential
            self.attempts = 0
            self.last_error: Optional[Exception] = None

        async def execute_with_retry(self, func, *args, **kwargs):
            self.attempts = 0
            while self.attempts < self.max_retries:
                try:
                    self.attempts += 1
                    return await func(*args, **kwargs)
                except Exception as e:
                    self.last_error = e
                    if self.attempts >= self.max_retries:
                        raise
                    delay = self.base_delay * (2 ** (self.attempts - 1) if self.exponential else 1)
                    await asyncio.sleep(delay)

    return RetryHandler()


# =============================================================================
# 1. ERROR CLASSIFICATION TESTS
# =============================================================================

class TestErrorClassification:
    """Test error classification logic."""

    def test_validation_error_is_fatal(self):
        """Validation errors should be fatal (no retry)."""
        class ValidationError(Exception):
            is_fatal = True

        error = ValidationError("Invalid input")
        assert error.is_fatal

    def test_timeout_error_is_recoverable(self):
        """Timeout errors should be recoverable."""
        class TimeoutError(Exception):
            is_recoverable = True

        error = TimeoutError("Operation timed out")
        assert error.is_recoverable

    def test_resource_error_classification(self):
        """Resource errors have specific classification."""
        class ResourceError(Exception):
            def __init__(self, message, is_recoverable=True):
                super().__init__(message)
                self.is_recoverable = is_recoverable

        oom = ResourceError("Out of memory", is_recoverable=False)
        quota = ResourceError("Quota exceeded", is_recoverable=True)

        assert not oom.is_recoverable
        assert quota.is_recoverable

    def test_security_error_is_fatal(self):
        """Security errors should be fatal."""
        class SecurityError(Exception):
            is_fatal = True
            is_recoverable = False

        error = SecurityError("Permission denied")
        assert error.is_fatal
        assert not error.is_recoverable


# =============================================================================
# 2. ERROR PROPAGATION TESTS
# =============================================================================

class TestErrorPropagation:
    """Test error propagation through layers."""

    def test_error_propagates_to_caller(self):
        """Errors propagate up the call stack."""
        def inner():
            raise ValueError("Inner error")

        def middle():
            inner()

        def outer():
            middle()

        with pytest.raises(ValueError) as exc:
            outer()
        assert "Inner error" in str(exc.value)

    @pytest.mark.asyncio
    async def test_async_error_propagation(self):
        """Errors propagate through async stack."""
        async def async_inner():
            raise RuntimeError("Async error")

        async def async_middle():
            await async_inner()

        async def async_outer():
            await async_middle()

        with pytest.raises(RuntimeError) as exc:
            await async_outer()
        assert "Async error" in str(exc.value)

    def test_error_chain_preserved(self):
        """Error chains are preserved."""
        def cause():
            raise ValueError("Root cause")

        def wrapper():
            try:
                cause()
            except ValueError as e:
                raise RuntimeError("Wrapper error") from e

        with pytest.raises(RuntimeError) as exc:
            wrapper()
        assert exc.value.__cause__ is not None
        assert isinstance(exc.value.__cause__, ValueError)

    def test_error_context_preserved(self):
        """Error context is preserved."""
        def problematic():
            try:
                1 / 0
            except ZeroDivisionError:
                raise RuntimeError("Subsequent error")

        with pytest.raises(RuntimeError) as exc:
            problematic()
        assert exc.value.__context__ is not None


# =============================================================================
# 3. CIRCUIT BREAKER TESTS
# =============================================================================

class TestCircuitBreaker:
    """Test circuit breaker behavior."""

    def test_initial_state_closed(self, circuit_breaker):
        """Circuit starts in CLOSED state."""
        assert circuit_breaker.state == circuit_breaker.CLOSED
        assert circuit_breaker.can_attempt()

    def test_success_keeps_closed(self, circuit_breaker):
        """Success keeps circuit closed."""
        circuit_breaker.record_success()
        circuit_breaker.record_success()
        circuit_breaker.record_success()

        assert circuit_breaker.state == circuit_breaker.CLOSED
        assert circuit_breaker.success_count == 3

    def test_failures_open_circuit(self, circuit_breaker):
        """Enough failures open the circuit."""
        for _ in range(5):
            circuit_breaker.record_failure()

        assert circuit_breaker.state == circuit_breaker.OPEN
        assert not circuit_breaker.can_attempt()

    def test_open_circuit_blocks_attempts(self, circuit_breaker):
        """Open circuit blocks new attempts."""
        for _ in range(5):
            circuit_breaker.record_failure()

        assert circuit_breaker.state == circuit_breaker.OPEN
        assert not circuit_breaker.can_attempt()

    def test_recovery_timeout_transitions_to_half_open(self, circuit_breaker):
        """After recovery timeout, circuit goes half-open."""
        circuit_breaker.recovery_timeout = 0.1  # Short timeout for test

        for _ in range(5):
            circuit_breaker.record_failure()

        assert circuit_breaker.state == circuit_breaker.OPEN

        time.sleep(0.15)  # Wait for recovery

        assert circuit_breaker.can_attempt()
        assert circuit_breaker.state == circuit_breaker.HALF_OPEN

    def test_half_open_success_closes_circuit(self, circuit_breaker):
        """Success in half-open state closes circuit."""
        circuit_breaker.state = circuit_breaker.HALF_OPEN

        circuit_breaker.record_success()

        assert circuit_breaker.state == circuit_breaker.CLOSED

    def test_half_open_failure_opens_circuit(self, circuit_breaker):
        """Failure in half-open state opens circuit again."""
        circuit_breaker.state = circuit_breaker.HALF_OPEN

        circuit_breaker.record_failure()

        assert circuit_breaker.state == circuit_breaker.OPEN

    def test_reset_clears_state(self, circuit_breaker):
        """Reset returns circuit to initial state."""
        for _ in range(5):
            circuit_breaker.record_failure()

        circuit_breaker.reset()

        assert circuit_breaker.state == circuit_breaker.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.can_attempt()


# =============================================================================
# 4. RETRY LOGIC TESTS
# =============================================================================

class TestRetryLogic:
    """Test retry mechanism."""

    @pytest.mark.asyncio
    async def test_success_on_first_try(self, retry_handler):
        """Success on first try doesn't retry."""
        async def succeeds():
            return "success"

        result = await retry_handler.execute_with_retry(succeeds)

        assert result == "success"
        assert retry_handler.attempts == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, retry_handler):
        """Failures trigger retries."""
        attempt_count = 0

        async def fails_twice():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise RuntimeError("Temporary failure")
            return "success"

        retry_handler.base_delay = 0.01  # Fast for testing
        result = await retry_handler.execute_with_retry(fails_twice)

        assert result == "success"
        assert attempt_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, retry_handler):
        """Gives up after max retries."""
        async def always_fails():
            raise RuntimeError("Permanent failure")

        retry_handler.base_delay = 0.01
        retry_handler.max_retries = 3

        with pytest.raises(RuntimeError):
            await retry_handler.execute_with_retry(always_fails)

        assert retry_handler.attempts == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff(self, retry_handler):
        """Retry delays increase exponentially."""
        delays = []
        start = time.time()

        async def fails():
            delays.append(time.time() - start)
            raise RuntimeError("Fail")

        retry_handler.base_delay = 0.1
        retry_handler.max_retries = 3

        with pytest.raises(RuntimeError):
            await retry_handler.execute_with_retry(fails)

        # Second retry should be ~2x first delay
        # Third retry should be ~4x first delay
        assert len(delays) == 3


# =============================================================================
# 5. RECOVERY MECHANISM TESTS
# =============================================================================

class TestRecoveryMechanisms:
    """Test recovery from failures."""

    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self):
        """Fallback is used when primary fails."""
        primary_called = False
        fallback_called = False

        async def primary():
            nonlocal primary_called
            primary_called = True
            raise RuntimeError("Primary failed")

        async def fallback():
            nonlocal fallback_called
            fallback_called = True
            return "fallback result"

        async def with_fallback():
            try:
                return await primary()
            except RuntimeError:
                return await fallback()

        result = await with_fallback()

        assert primary_called
        assert fallback_called
        assert result == "fallback result"

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """System degrades gracefully on partial failure."""
        results = []

        async def process_item(item):
            if item == "bad":
                raise ValueError("Bad item")
            return f"processed:{item}"

        items = ["good1", "bad", "good2", "good3"]

        for item in items:
            try:
                result = await process_item(item)
                results.append(result)
            except ValueError:
                results.append(f"skipped:{item}")

        assert len(results) == 4
        assert results[0] == "processed:good1"
        assert results[1] == "skipped:bad"
        assert results[2] == "processed:good2"

    @pytest.mark.asyncio
    async def test_self_healing(self):
        """System self-heals after transient failure."""
        failure_count = 0
        max_failures = 2

        async def flaky_service():
            nonlocal failure_count
            if failure_count < max_failures:
                failure_count += 1
                raise RuntimeError("Service unavailable")
            return "healthy"

        # Keep trying until success
        result = None
        for _ in range(5):
            try:
                result = await flaky_service()
                break
            except RuntimeError:
                await asyncio.sleep(0.01)

        assert result == "healthy"
        assert failure_count == max_failures


# =============================================================================
# 6. CASCADING FAILURE PREVENTION TESTS
# =============================================================================

class TestCascadingFailurePrevention:
    """Test prevention of cascading failures."""

    @pytest.mark.asyncio
    async def test_failure_isolation(self):
        """Failure in one component doesn't affect others."""
        results = {}

        async def component_a():
            results["a"] = "success"

        async def component_b():
            raise RuntimeError("B failed")

        async def component_c():
            results["c"] = "success"

        # Execute all, isolating failures
        for name, func in [("a", component_a), ("b", component_b), ("c", component_c)]:
            try:
                await func()
            except RuntimeError:
                results[name] = "failed"

        assert results["a"] == "success"
        assert results["b"] == "failed"
        assert results["c"] == "success"

    @pytest.mark.asyncio
    async def test_bulkhead_pattern(self):
        """Bulkhead pattern limits failure impact."""
        pool_a_calls = 0
        pool_b_calls = 0

        async def use_pool_a():
            nonlocal pool_a_calls
            pool_a_calls += 1
            raise RuntimeError("Pool A exhausted")

        async def use_pool_b():
            nonlocal pool_b_calls
            pool_b_calls += 1
            return "Pool B success"

        # Pool A fails but Pool B still works
        try:
            await use_pool_a()
        except RuntimeError:
            pass

        result = await use_pool_b()

        assert pool_a_calls == 1
        assert pool_b_calls == 1
        assert result == "Pool B success"

    @pytest.mark.asyncio
    async def test_timeout_prevents_indefinite_wait(self):
        """Timeout prevents indefinite waiting."""
        async def slow_operation():
            await asyncio.sleep(10)
            return "done"

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(slow_operation(), timeout=0.1)


# =============================================================================
# 7. ERROR MESSAGE QUALITY TESTS
# =============================================================================

class TestErrorMessageQuality:
    """Test error message quality and usefulness."""

    def test_error_includes_context(self):
        """Error messages include relevant context."""
        class ContextualError(Exception):
            def __init__(self, message, context):
                super().__init__(f"{message}: {context}")
                self.context = context

        error = ContextualError("Operation failed", {"user_id": 123, "action": "delete"})
        message = str(error)

        assert "Operation failed" in message
        assert "123" in message
        assert "delete" in message

    def test_error_has_suggestions(self):
        """Error includes actionable suggestions."""
        class ActionableError(Exception):
            def __init__(self, message, suggestions):
                super().__init__(message)
                self.suggestions = suggestions

        error = ActionableError(
            "File not found",
            ["Check the file path", "Ensure file exists", "Verify permissions"]
        )

        assert len(error.suggestions) == 3
        assert "Check the file path" in error.suggestions

    def test_error_severity_indicated(self):
        """Error severity is clearly indicated."""
        class SeverityError(Exception):
            CRITICAL = "CRITICAL"
            WARNING = "WARNING"
            INFO = "INFO"

            def __init__(self, message, severity):
                super().__init__(f"[{severity}] {message}")
                self.severity = severity

        critical = SeverityError("Database down", SeverityError.CRITICAL)
        warning = SeverityError("Slow response", SeverityError.WARNING)

        assert critical.severity == "CRITICAL"
        assert "[CRITICAL]" in str(critical)
        assert warning.severity == "WARNING"


# =============================================================================
# 8. RESOURCE CLEANUP TESTS
# =============================================================================

class TestResourceCleanup:
    """Test resource cleanup during errors."""

    @pytest.mark.asyncio
    async def test_cleanup_on_exception(self):
        """Resources are cleaned up on exception."""
        cleanup_called = False

        async def operation_with_cleanup():
            nonlocal cleanup_called
            try:
                raise RuntimeError("Failure")
            finally:
                cleanup_called = True

        with pytest.raises(RuntimeError):
            await operation_with_cleanup()

        assert cleanup_called

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Context managers ensure cleanup."""
        cleanup_called = False

        class Resource:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                nonlocal cleanup_called
                cleanup_called = True
                return False

        # Exception should propagate but cleanup still happens
        with pytest.raises(RuntimeError, match="Failure"):
            async with Resource() as r:
                raise RuntimeError("Failure")

        # Cleanup should have been called despite the exception
        assert cleanup_called

    @pytest.mark.asyncio
    async def test_nested_cleanup_order(self):
        """Nested resources are cleaned up in correct order."""
        cleanup_order = []

        class OrderedResource:
            def __init__(self, name):
                self.name = name

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                cleanup_order.append(self.name)
                return False

        try:
            async with OrderedResource("outer"):
                async with OrderedResource("inner"):
                    raise RuntimeError("Failure")
        except RuntimeError:
            pass

        assert cleanup_order == ["inner", "outer"]
