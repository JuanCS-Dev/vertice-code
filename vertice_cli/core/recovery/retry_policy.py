"""
Retry Policy - Exponential Backoff with Jitter.

DAY 7 Enhancement: Sophisticated retry logic for error recovery.
"""

import logging
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class RetryPolicy:
    """Sophisticated retry policy with exponential backoff and jitter.

    Implements best practices:
    - Exponential backoff to prevent thundering herd
    - Jitter to prevent synchronized retries
    - Max delay cap to prevent excessive waits
    - Smart retry decisions based on error type
    """

    # Transient error patterns (worth retrying)
    TRANSIENT_PATTERNS = [
        "timeout",
        "timed out",
        "connection",
        "connect",
        "temporary",
        "temporarily",
        "unavailable",
        "not available",
        "rate limit",
        "too many requests",
        "service unavailable",
        "bad gateway",
        "502",
        "503",
        "504",
    ]

    # Permanent error patterns (don't retry)
    PERMANENT_PATTERNS = [
        "not found",
        "404",
        "unauthorized",
        "401",
        "403",
        "forbidden",
        "invalid",
        "malformed",
        "syntax error",
        "parse error",
    ]

    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """Initialize retry policy.

        Args:
            base_delay: Base delay in seconds (default: 1.0)
            max_delay: Maximum delay in seconds (default: 60.0)
            exponential_base: Base for exponential backoff (default: 2.0)
            jitter: Add random jitter (default: True)
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt with exponential backoff.

        Formula: min(base * (exp_base ^ (attempt - 1)), max_delay) + jitter

        Args:
            attempt: Attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)

        if self.jitter:
            jitter_amount = delay * 0.25 * random.random()
            delay += jitter_amount

        return delay

    def should_retry(self, attempt: int, max_attempts: int, error: Exception) -> bool:
        """Decide if we should retry based on error type.

        Args:
            attempt: Current attempt number
            max_attempts: Maximum attempts allowed
            error: Exception that occurred

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= max_attempts:
            return False

        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            return False

        error_str = str(error).lower()

        is_transient = any(p in error_str for p in self.TRANSIENT_PATTERNS)
        if is_transient:
            logger.info(f"Error appears transient, will retry: {error}")
            return True

        is_permanent = any(p in error_str for p in self.PERMANENT_PATTERNS)
        if is_permanent:
            logger.info(f"Error appears permanent, won't retry: {error}")
            return False

        # Default: retry unknown errors (conservative approach)
        return True
