"""
MAXIMUS Configuration.

Configuration dataclass for MAXIMUS provider with MCP and resilience settings.

Based on 2025 best practices:
- MCP (Model Context Protocol) as primary transport
- HTTP fallback for compatibility
- Resilience patterns (retry, circuit breaker)

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum

from .resilience import (
    CircuitBreakerConfig,
    ConnectionPoolConfig,
    RetryConfig,
)


class TransportMode(Enum):
    """Transport mode for MAXIMUS connection."""

    MCP = "mcp"  # Model Context Protocol (preferred)
    HTTP = "http"  # HTTP REST API (fallback)
    AUTO = "auto"  # MCP with HTTP fallback


@dataclass
class MCPConfig:
    """MCP (Model Context Protocol) configuration.

    Attributes:
        server_name: MCP server name to connect to
        transport: Transport type (stdio, http, sse)
        timeout: MCP request timeout in seconds
        enable_streaming: Enable streaming responses
    """

    server_name: str = "maximus"
    transport: str = "http"  # stdio, http, sse
    timeout: float = 30.0
    enable_streaming: bool = True


@dataclass
class MaximusConfig:
    """Configuration for MAXIMUS provider.

    Provides configuration for connecting to MAXIMUS backend via
    MCP or HTTP with resilience patterns (retry, circuit breaker).

    Attributes:
        base_url: MAXIMUS backend URL for HTTP
        mcp_url: MCP server URL
        timeout: Request timeout in seconds
        transport_mode: Transport mode (mcp, http, auto)
        enable_tribunal: Enable Tribunal evaluation
        enable_memory: Enable memory operations
        enable_factory: Enable tool factory
        tribunal_threshold: Consensus threshold for PASS
        memory_consolidation_threshold: Threshold for memory consolidation
        retry: Retry configuration
        circuit_breaker: Circuit breaker configuration
        pool: Connection pool configuration
        mcp: MCP configuration
    """

    # Connection settings
    base_url: str = field(
        default_factory=lambda: os.getenv("MAXIMUS_URL", "http://localhost:8100")
    )
    mcp_url: str = field(
        default_factory=lambda: os.getenv("MAXIMUS_MCP_URL", "http://localhost:8100/mcp")
    )
    timeout: float = 30.0
    transport_mode: TransportMode = TransportMode.AUTO

    # Feature flags
    enable_tribunal: bool = True
    enable_memory: bool = True
    enable_factory: bool = True

    # Tribunal settings
    tribunal_threshold: float = 0.7

    # Memory settings
    memory_consolidation_threshold: float = 0.8

    # Resilience settings
    retry: RetryConfig = field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    pool: ConnectionPoolConfig = field(default_factory=ConnectionPoolConfig)

    # MCP settings
    mcp: MCPConfig = field(default_factory=MCPConfig)

    @classmethod
    def from_env(cls) -> MaximusConfig:
        """Create configuration from environment variables.

        Environment variables:
            MAXIMUS_URL: HTTP base URL
            MAXIMUS_MCP_URL: MCP server URL
            MAXIMUS_TIMEOUT: Request timeout
            MAXIMUS_TRANSPORT: Transport mode (mcp, http, auto)
            MAXIMUS_TRIBUNAL: Enable tribunal (true/false)
            MAXIMUS_MEMORY: Enable memory (true/false)
            MAXIMUS_FACTORY: Enable factory (true/false)
            MAXIMUS_RETRY_ATTEMPTS: Maximum retry attempts
            MAXIMUS_CB_THRESHOLD: Circuit breaker failure threshold

        Returns:
            Configured MaximusConfig instance.
        """
        transport_str = os.getenv("MAXIMUS_TRANSPORT", "auto").lower()
        transport_map = {
            "mcp": TransportMode.MCP,
            "http": TransportMode.HTTP,
            "auto": TransportMode.AUTO,
        }
        transport = transport_map.get(transport_str, TransportMode.AUTO)

        retry = RetryConfig(
            max_attempts=int(os.getenv("MAXIMUS_RETRY_ATTEMPTS", "3")),
        )

        circuit_breaker = CircuitBreakerConfig(
            failure_threshold=int(os.getenv("MAXIMUS_CB_THRESHOLD", "5")),
        )

        return cls(
            base_url=os.getenv("MAXIMUS_URL", "http://localhost:8100"),
            mcp_url=os.getenv("MAXIMUS_MCP_URL", "http://localhost:8100/mcp"),
            timeout=float(os.getenv("MAXIMUS_TIMEOUT", "30.0")),
            transport_mode=transport,
            enable_tribunal=os.getenv("MAXIMUS_TRIBUNAL", "true").lower() == "true",
            enable_memory=os.getenv("MAXIMUS_MEMORY", "true").lower() == "true",
            enable_factory=os.getenv("MAXIMUS_FACTORY", "true").lower() == "true",
            retry=retry,
            circuit_breaker=circuit_breaker,
        )

    def get_effective_url(self) -> str:
        """Get effective URL based on transport mode.

        Returns:
            MCP URL for MCP mode, HTTP URL otherwise.
        """
        if self.transport_mode == TransportMode.MCP:
            return self.mcp_url
        return self.base_url

    def should_use_mcp(self) -> bool:
        """Check if MCP transport should be used.

        Returns:
            True if MCP should be used.
        """
        return self.transport_mode in (TransportMode.MCP, TransportMode.AUTO)

    def should_fallback_to_http(self) -> bool:
        """Check if HTTP fallback should be used.

        Returns:
            True if HTTP fallback is enabled.
        """
        return self.transport_mode in (TransportMode.HTTP, TransportMode.AUTO)
