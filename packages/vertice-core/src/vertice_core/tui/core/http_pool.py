"""
HTTP Connection Pooling and Optimization for Vertice-Code.

Provides efficient HTTP connection reuse, automatic retries,
and performance optimization for API calls.
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import aiohttp
from aiohttp import ClientTimeout, ClientError
import backoff

logger = logging.getLogger(__name__)


@dataclass
class ConnectionPoolConfig:
    """Configuration for HTTP connection pooling."""

    max_connections: int = 100
    max_connections_per_host: int = 20
    keepalive_timeout: float = 60.0
    timeout: float = 30.0
    retry_attempts: int = 3
    retry_backoff: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


@dataclass
class PoolStats:
    """Statistics for connection pool usage."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_response_time: float = 0.0
    active_connections: int = 0
    queued_requests: int = 0
    last_reset: float = field(default_factory=time.time)


class HTTPConnectionPool:
    """
    High-performance HTTP connection pool with automatic retries and circuit breaking.

    Features:
    - Connection reuse for performance
    - Automatic retries with exponential backoff
    - Circuit breaker for failing endpoints
    - Request/response metrics
    - Configurable timeouts and limits
    """

    def __init__(self, config: Optional[ConnectionPoolConfig] = None):
        self.config = config or ConnectionPoolConfig()
        self._session: Optional[aiohttp.ClientSession] = None
        self._stats = PoolStats()
        self._circuit_breaker: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def initialize(self):
        """Initialize the connection pool."""
        if self._session:
            return

        timeout = ClientTimeout(
            total=self.config.timeout,
            connect=self.config.timeout / 3,
            sock_read=self.config.timeout / 3,
            sock_connect=self.config.timeout / 3,
        )

        connector = aiohttp.TCPConnector(
            limit=self.config.max_connections,
            limit_per_host=self.config.max_connections_per_host,
            keepalive_timeout=self.config.keepalive_timeout,
            enable_cleanup_closed=True,
        )

        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            trust_env=True,  # Use environment proxy settings
        )

        logger.info(
            f"HTTP connection pool initialized: max={self.config.max_connections}, per_host={self.config.max_connections_per_host}"
        )

    async def close(self):
        """Close the connection pool."""
        if self._session:
            await self._session.close()
            self._session = None
            logger.info("HTTP connection pool closed")

    def _is_circuit_open(self, url: str) -> bool:
        """Check if circuit breaker is open for URL."""
        host = self._extract_host(url)
        if host not in self._circuit_breaker:
            return False

        breaker = self._circuit_breaker[host]
        if breaker["failures"] >= self.config.circuit_breaker_threshold:
            if time.time() - breaker["last_failure"] < self.config.circuit_breaker_timeout:
                return True  # Circuit is open

            # Reset circuit breaker after timeout
            breaker["failures"] = 0

        return False

    def _record_failure(self, url: str):
        """Record a failure for circuit breaker."""
        host = self._extract_host(url)
        if host not in self._circuit_breaker:
            self._circuit_breaker[host] = {"failures": 0, "last_failure": 0}

        self._circuit_breaker[host]["failures"] += 1
        self._circuit_breaker[host]["last_failure"] = time.time()

    def _record_success(self, url: str):
        """Record a success for circuit breaker."""
        host = self._extract_host(url)
        if host in self._circuit_breaker:
            self._circuit_breaker[host]["failures"] = max(
                0, self._circuit_breaker[host]["failures"] - 1
            )

    def _extract_host(self, url: str) -> str:
        """Extract host from URL."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            return parsed.netloc or parsed.path
        except Exception:
            return url

    @backoff.on_exception(
        backoff.expo,
        (ClientError, asyncio.TimeoutError),
        max_tries=lambda: ConnectionPoolConfig().retry_attempts,
        giveup=lambda e: isinstance(e, aiohttp.ClientResponseError)
        and e.status in [400, 401, 403, 404],
    )
    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """
        Make HTTP request with connection pooling and automatic retries.

        Args:
            method: HTTP method
            url: URL to request
            **kwargs: Additional arguments for aiohttp

        Returns:
            ClientResponse object

        Raises:
            ClientError: On request failure
            CircuitBreakerError: When circuit is open
        """
        if not self._session:
            await self.initialize()

        # Check circuit breaker
        if self._is_circuit_open(url):
            raise aiohttp.ClientError(f"Circuit breaker open for {self._extract_host(url)}")

        start_time = time.time()

        try:
            async with self._session.request(method, url, **kwargs) as response:
                response_time = time.time() - start_time

                # Update statistics
                async with self._lock:
                    self._stats.total_requests += 1
                    self._stats.successful_requests += 1
                    self._stats.average_response_time = (
                        (self._stats.average_response_time * (self._stats.successful_requests - 1))
                        + response_time
                    ) / self._stats.successful_requests

                # Record success for circuit breaker
                self._record_success(url)

                return response

        except Exception as e:
            response_time = time.time() - start_time

            # Update statistics
            async with self._lock:
                self._stats.total_requests += 1
                self._stats.failed_requests += 1

            # Record failure for circuit breaker
            self._record_failure(url)

            logger.warning(f"HTTP request failed: {method} {url} - {e} ({response_time:.2f}s)")
            raise

    async def get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make GET request."""
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make POST request."""
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make PUT request."""
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Make DELETE request."""
        return await self.request("DELETE", url, **kwargs)

    async def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        async with self._lock:
            return {
                "total_requests": self._stats.total_requests,
                "successful_requests": self._stats.successful_requests,
                "failed_requests": self._stats.failed_requests,
                "success_rate": (
                    self._stats.successful_requests / max(1, self._stats.total_requests)
                )
                * 100,
                "average_response_time": round(self._stats.average_response_time, 3),
                "active_connections": (
                    getattr(self._session.connector, "_conns", {}).get("total", 0)
                    if self._session
                    else 0
                ),
                "circuit_breakers": {
                    host: {
                        "failures": data["failures"],
                        "last_failure": data["last_failure"],
                        "is_open": self._is_circuit_open(f"http://{host}"),
                    }
                    for host, data in self._circuit_breaker.items()
                },
            }

    async def reset_stats(self):
        """Reset pool statistics."""
        async with self._lock:
            self._stats = PoolStats()
            self._circuit_breaker.clear()


# Global connection pool instance
_connection_pool: Optional[HTTPConnectionPool] = None


async def get_http_pool() -> HTTPConnectionPool:
    """Get global HTTP connection pool instance."""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = HTTPConnectionPool()
        await _connection_pool.initialize()
    return _connection_pool


async def make_http_request(method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
    """Convenience function for making HTTP requests with pooling."""
    pool = await get_http_pool()
    return await pool.request(method, url, **kwargs)
