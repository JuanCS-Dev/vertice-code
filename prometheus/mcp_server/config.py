"""
MCP Server Configuration

Configuration classes and settings for the Prometheus MCP Server.

Created with love for configurable AI services.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MCPServerConfig:
    """
    Configuration for the Prometheus MCP Server.

    Defines all settings needed to run a standalone MCP server
    exposing Prometheus capabilities.
    """

    # Server identity
    server_name: str = "prometheus-mcp-server"
    server_version: str = "1.0.0"
    instance_id: str = field(default_factory=lambda: f"prometheus-mcp-{os.getpid()}")

    # Network configuration
    host: str = "localhost"
    port: int = 3000
    allowed_origins: List[str] = field(default_factory=lambda: ["*"])

    # Prometheus components
    enable_skills_registry: bool = True
    enable_memory_system: bool = True
    enable_distributed_features: bool = False

    # Distributed settings (if enabled)
    discovery_endpoints: List[str] = field(default_factory=list)
    peer_sync_interval: int = 300  # seconds

    # Resource limits
    max_concurrent_requests: int = 10
    request_timeout: int = 30  # seconds
    max_memory_usage: Optional[int] = None  # MB

    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # Authentication (optional)
    require_auth: bool = False
    api_keys: List[str] = field(default_factory=list)

    # Performance tuning
    enable_caching: bool = True
    cache_ttl: int = 300  # seconds
    enable_metrics: bool = True

    @classmethod
    def from_env(cls) -> "MCPServerConfig":
        """Create configuration from environment variables."""
        return cls(
            host=os.getenv("MCP_HOST", "localhost"),
            port=int(os.getenv("MCP_PORT", "3000")),
            log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
            log_file=os.getenv("MCP_LOG_FILE"),
            require_auth=os.getenv("MCP_REQUIRE_AUTH", "false").lower() == "true",
            api_keys=os.getenv("MCP_API_KEYS", "").split(",") if os.getenv("MCP_API_KEYS") else [],
            enable_distributed_features=os.getenv("MCP_DISTRIBUTED", "false").lower() == "true",
            discovery_endpoints=(
                os.getenv("MCP_DISCOVERY_ENDPOINTS", "").split(",")
                if os.getenv("MCP_DISCOVERY_ENDPOINTS")
                else []
            ),
        )

    @classmethod
    def from_file(cls, config_path: str) -> "MCPServerConfig":
        """Load configuration from a JSON/YAML file."""
        import json

        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path, "r") as f:
            if path.suffix.lower() in [".yaml", ".yml"]:
                try:
                    import yaml

                    data = yaml.safe_load(f)
                except ImportError:
                    raise ImportError("PyYAML required for YAML config files")
            else:
                data = json.load(f)

        # Create instance with defaults, then update with file data
        config = cls()
        for key, value in data.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "server_name": self.server_name,
            "server_version": self.server_version,
            "instance_id": self.instance_id,
            "host": self.host,
            "port": self.port,
            "allowed_origins": self.allowed_origins,
            "enable_skills_registry": self.enable_skills_registry,
            "enable_memory_system": self.enable_memory_system,
            "enable_distributed_features": self.enable_distributed_features,
            "discovery_endpoints": self.discovery_endpoints,
            "peer_sync_interval": self.peer_sync_interval,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout,
            "max_memory_usage": self.max_memory_usage,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "require_auth": self.require_auth,
            "enable_caching": self.enable_caching,
            "cache_ttl": self.cache_ttl,
            "enable_metrics": self.enable_metrics,
        }

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        if self.port < 1 or self.port > 65535:
            issues.append(f"Invalid port number: {self.port}")

        if self.request_timeout < 1:
            issues.append(f"Invalid request timeout: {self.request_timeout}")

        if self.cache_ttl < 0:
            issues.append(f"Invalid cache TTL: {self.cache_ttl}")

        if self.max_concurrent_requests < 1:
            issues.append(f"Invalid max concurrent requests: {self.max_concurrent_requests}")

        if self.enable_distributed_features and not self.discovery_endpoints:
            issues.append("Distributed features enabled but no discovery endpoints configured")

        return issues
