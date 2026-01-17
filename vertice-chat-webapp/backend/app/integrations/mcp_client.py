"""
MCP HTTP Client for Web App Integration
Provides HTTP-based communication with Prometheus MCP Server

Features:
- HTTP client with httpx
- Circuit breaker pattern
- Timeout protection (30s default)
- Streaming support via WebSocket
- Automatic retry on failures
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open."""

    pass


class MCPClient:
    """
    HTTP Client for MCP Server communication.

    Features:
    - Circuit breaker pattern for fault tolerance
    - Automatic retries with exponential backoff
    - Timeout protection
    - Connection pooling
    """

    def __init__(
        self,
        base_url: str = "http://localhost:3000",
        timeout: float = 30.0,
        max_retries: int = 3,
        circuit_breaker_threshold: int = 3,
        circuit_breaker_timeout: float = 60.0,
    ):
        """
        Initialize MCP HTTP Client.

        Args:
            base_url: Base URL of MCP server (default: http://localhost:3000)
            timeout: Request timeout in seconds (default: 30.0)
            max_retries: Maximum number of retries (default: 3)
            circuit_breaker_threshold: Failures before opening circuit (default: 3)
            circuit_breaker_timeout: Seconds to wait before retrying (default: 60.0)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        # Circuit breaker state
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.failure_count = 0
        self.last_failure_time = 0

        # HTTP client
        self._client: Optional[httpx.AsyncClient] = None

        logger.info(f"MCP Client initialized for {base_url}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self):
        """Start the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )
        logger.info("MCP HTTP client started")

    async def stop(self):
        """Stop the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("MCP HTTP client stopped")

    def _check_circuit_breaker(self) -> None:
        """Check if circuit breaker should block requests."""
        if self.failure_count >= self.circuit_breaker_threshold:
            current_time = asyncio.get_event_loop().time()
            if current_time - self.last_failure_time < self.circuit_breaker_timeout:
                raise CircuitBreakerOpenException(
                    f"Circuit breaker open. {self.failure_count} failures. "
                    f"Retry in {self.circuit_breaker_timeout - (current_time - self.last_failure_time):.1f}s"
                )
            else:
                # Reset circuit breaker after timeout
                self.failure_count = 0
                logger.info("Circuit breaker reset")

    def _record_failure(self):
        """Record a request failure for circuit breaker."""
        self.failure_count += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        logger.warning(f"Request failed. Failure count: {self.failure_count}")

    def _record_success(self):
        """Record a successful request."""
        if self.failure_count > 0:
            self.failure_count = 0
            logger.info("Request succeeded. Circuit breaker reset")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
    )
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make HTTP request with retry logic."""
        if not self._client:
            raise RuntimeError("Client not started. Use start() or async context manager.")

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Making {method} request to {url}")

        try:
            response = await self._client.request(method, url, **kwargs)

            # Raise for HTTP errors
            response.raise_for_status()

            self._record_success()
            return response

        except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError) as e:
            self._record_failure()
            logger.error(f"Request failed: {e}")
            raise

    async def call_mcp_method(
        self, method: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call MCP method via HTTP.

        Args:
            method: MCP method name (e.g., "tools/list", "tools/call")
            params: Method parameters

        Returns:
            MCP response as dict
        """
        self._check_circuit_breaker()

        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": f"mcp-{asyncio.get_event_loop().time()}",
        }

        try:
            response = await self._make_request(
                "POST",
                "/mcp",
                json=request_data,
                headers={"Content-Type": "application/json"},
            )

            result = response.json()
            logger.debug(f"MCP method {method} succeeded")
            return result

        except Exception as e:
            logger.error(f"MCP method {method} failed: {e}")
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": f"MCP request failed: {str(e)}"},
                "id": request_data["id"],
            }

    async def list_tools(self) -> Dict[str, Any]:
        """List available MCP tools."""
        return await self.call_mcp_method("tools/list")

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool."""
        params = {"name": tool_name, "arguments": arguments}
        return await self.call_mcp_method("tools/call", params)

    async def get_server_status(self) -> Dict[str, Any]:
        """Get MCP server status."""
        return await self.call_mcp_method("prometheus/status")

    async def health_check(self) -> bool:
        """Check if MCP server is healthy."""
        try:
            response = await self._make_request("GET", "/health")
            return response.status_code == 200
        except Exception:
            return False

    # Convenience methods for common tools
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute shell command via MCP."""
        return await self.call_tool("bash_command", {"command": command})

    async def read_file(
        self, path: str, offset: Optional[int] = None, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Read file via MCP."""
        args = {"path": path}
        if offset is not None:
            args["offset"] = offset
        if limit is not None:
            args["limit"] = limit
        return await self.call_tool("read_file", args)

    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write file via MCP."""
        return await self.call_tool("write_file", {"path": path, "content": content})

    async def list_directory(self, path: str) -> Dict[str, Any]:
        """List directory via MCP."""
        return await self.call_tool("list_directory", {"path": path})


# Global client instance
_default_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get the default MCP client instance."""
    global _default_client
    if _default_client is None:
        _default_client = MCPClient()
    return _default_client


def set_mcp_client(client: MCPClient):
    """Set the global MCP client instance."""
    global _default_client
    _default_client = client


@asynccontextmanager
async def managed_mcp_client(base_url: str = "http://localhost:3000", **kwargs):
    """
    Context manager for MCP client lifecycle.

    Usage:
        async with managed_mcp_client("http://localhost:3000") as client:
            result = await client.list_tools()
    """
    client = MCPClient(base_url, **kwargs)
    try:
        await client.start()
        yield client
    finally:
        await client.stop()
