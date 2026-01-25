"""
Circuit Breaker - Prevent Cascading Failures.

DAY 7 Enhancement: Recovery circuit breaker pattern.
"""

import logging
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class RecoveryCircuitBreaker:
    """Circuit breaker for recovery system to prevent cascading failures.

    States:
    - CLOSED: Normal operation, allow all requests
    - OPEN: Too many failures, reject all requests for timeout period
    - HALF_OPEN: Testing if system recovered, allow limited requests

    Prevents:
    - Infinite loops of failed recoveries
    - Resource exhaustion from repeated failures
    - Cascading failures across system
    """

    STATE_CLOSED = "CLOSED"
    STATE_OPEN = "OPEN"
    STATE_HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes to close circuit from half-open
            timeout: Seconds to wait before testing recovery (half-open)
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout

        self.failure_count = 0
        self.success_count = 0
        self.state = self.STATE_CLOSED
        self.last_failure_time: Optional[float] = None

        logger.info(
            f"Initialized RecoveryCircuitBreaker "
            f"(failures={failure_threshold}, successes={success_threshold}, "
            f"timeout={timeout}s)"
        )

    def record_success(self) -> None:
        """Record successful recovery attempt."""
        self.success_count += 1

        if self.state == self.STATE_HALF_OPEN:
            if self.success_count >= self.success_threshold:
                self.state = self.STATE_CLOSED
                self.failure_count = 0
                self.success_count = 0
                logger.info("Circuit breaker: CLOSED (system recovered)")

        elif self.state == self.STATE_CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def record_failure(self) -> None:
        """Record failed recovery attempt."""
        self.failure_count += 1
        self.success_count = 0
        self.last_failure_time = time.time()

        if self.state == self.STATE_CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = self.STATE_OPEN
                logger.warning(f"Circuit breaker: OPEN ({self.failure_count} consecutive failures)")

        elif self.state == self.STATE_HALF_OPEN:
            self.state = self.STATE_OPEN
            logger.warning("Circuit breaker: OPEN (failed during half-open test)")

    def should_allow_recovery(self) -> Tuple[bool, str]:
        """Check if recovery attempt is allowed.

        Returns:
            (allowed, reason)
        """
        if self.state == self.STATE_CLOSED:
            return True, "Circuit closed, normal operation"

        if self.state == self.STATE_OPEN:
            if self.last_failure_time is None:
                self.state = self.STATE_HALF_OPEN
                return True, "Circuit half-open (testing)"

            elapsed = time.time() - self.last_failure_time
            if elapsed >= self.timeout:
                self.state = self.STATE_HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker: HALF_OPEN (testing after {elapsed:.1f}s)")
                return True, "Circuit half-open (testing recovery)"
            else:
                remaining = self.timeout - elapsed
                return False, f"Circuit open, retry in {remaining:.0f}s"

        # HALF_OPEN: allow limited attempts
        return True, "Circuit half-open, testing recovery"

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "timeout": self.timeout,
        }

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self.state = self.STATE_CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker: RESET to CLOSED")
