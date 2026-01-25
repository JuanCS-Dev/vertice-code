from __future__ import annotations

from vertice_core.integrations.mcp.config import MCPConfig
from vertice_core.integrations.mcp.server import QwenMCPServer
from vertice_core.tools.registry_helper import get_default_registry


def test_mcp_server_initialize_smoke() -> None:
    registry = get_default_registry()
    server = QwenMCPServer(MCPConfig(enabled=False))

    assert server.is_running() is False

    # fastmcp may be unavailable/incompatible in some environments.
    # The important part is: importing/constructing the server should not crash the app.
    if server.mcp is None:
        assert server._init_error
        return

    server.initialize(registry)
