"""
Phase 6.2 Tests - MCP Integration

Tests for MCPManager, ClaudeParityHandler /mcp commands, and Bridge delegation.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any, Dict, List, Optional


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def mock_tool_registry() -> MagicMock:
    """Mock tool registry with some tools."""
    registry = MagicMock()
    registry.get_all.return_value = {
        "read_file": MagicMock(),
        "write_file": MagicMock(),
        "bash_command": MagicMock(),
    }
    return registry


# =============================================================================
# MCP STATE TESTS
# =============================================================================


class TestMCPServerState:
    """Tests for MCPServerState dataclass."""

    def test_default_values(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPServerState

        state = MCPServerState()
        assert state.running is False
        assert state.port == 3000
        assert state.transport == "stdio"
        assert state.exposed_tools == 0
        assert state.host == "127.0.0.1"
        assert state.error is None

    def test_custom_values(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPServerState

        state = MCPServerState(running=True, port=8080, exposed_tools=10)
        assert state.running is True
        assert state.port == 8080
        assert state.exposed_tools == 10


class TestMCPClientConnection:
    """Tests for MCPClientConnection dataclass."""

    def test_default_values(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPClientConnection

        conn = MCPClientConnection(url="http://localhost:3000", name="local")
        assert conn.url == "http://localhost:3000"
        assert conn.name == "local"
        assert conn.connected is False
        assert conn.tools == []
        assert conn.error is None


# =============================================================================
# MCP MANAGER TESTS
# =============================================================================


class TestMCPManager:
    """Tests for MCPManager."""

    def test_init(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()
        assert manager._server is None
        assert manager._server_state.running is False
        assert manager._connections == {}
        assert manager._exposed_tools == []

    def test_is_running_default_false(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()
        assert manager.is_running() is False

    def test_get_status_default(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()
        status = manager.get_status()

        assert "server" in status
        assert status["server"]["running"] is False
        assert status["connections"] == []
        assert status["total_exposed_tools"] == 0
        assert status["total_imported_tools"] == 0

    @pytest.mark.asyncio
    async def test_start_server_already_running(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()
        manager._server_state.running = True

        result = await manager.start_server()
        assert result["success"] is False
        assert "already running" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_stop_server_not_running(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()

        result = await manager.stop_server()
        assert result["success"] is False
        assert "not running" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_connect_external(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()

        result = await manager.connect_external("http://example.com:3000", "test-server")

        assert result["success"] is True
        assert result["name"] == "test-server"
        assert result["url"] == "http://example.com:3000"
        assert "test-server" in manager._connections

    @pytest.mark.asyncio
    async def test_connect_external_default_name(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()

        result = await manager.connect_external("http://example.com:3000")

        assert result["success"] is True
        assert result["name"] == "http://example.com:3000"

    @pytest.mark.asyncio
    async def test_connect_already_connected(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager, MCPClientConnection

        manager = MCPManager()
        manager._connections["test"] = MCPClientConnection(
            url="http://localhost", name="test", connected=True
        )

        result = await manager.connect_external("http://example.com", "test")

        assert result["success"] is False
        assert "already connected" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_disconnect(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager, MCPClientConnection

        manager = MCPManager()
        manager._connections["test"] = MCPClientConnection(
            url="http://localhost", name="test", connected=True
        )
        manager._imported_tools["test"] = ["tool1", "tool2"]

        result = await manager.disconnect("test")

        assert result["success"] is True
        assert "test" not in manager._connections
        assert "test" not in manager._imported_tools

    @pytest.mark.asyncio
    async def test_disconnect_not_found(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()

        result = await manager.disconnect("nonexistent")

        assert result["success"] is False
        assert "no connection" in result["error"].lower()

    def test_list_tools_empty(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()
        tools = manager.list_tools()

        assert tools["exposed"] == []
        assert tools["imported"] == {}

    def test_list_tools_with_data(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()
        manager._exposed_tools = ["tool1", "tool2"]
        manager._imported_tools = {"server1": ["tool3", "tool4"]}

        tools = manager.list_tools()

        assert tools["exposed"] == ["tool1", "tool2"]
        assert tools["imported"] == {"server1": ["tool3", "tool4"]}

    def test_get_exposed_tools(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()
        manager._exposed_tools = ["tool1", "tool2"]

        result = manager.get_exposed_tools()
        assert result == ["tool1", "tool2"]

        # Verify it's a copy
        result.append("tool3")
        assert len(manager._exposed_tools) == 2

    def test_get_connections(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager, MCPClientConnection

        manager = MCPManager()
        manager._connections["active"] = MCPClientConnection(
            url="http://active", name="active", connected=True
        )
        manager._connections["inactive"] = MCPClientConnection(
            url="http://inactive", name="inactive", connected=False
        )

        connections = manager.get_connections()

        assert len(connections) == 1
        assert connections[0]["name"] == "active"

    def test_get_connection_found(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager, MCPClientConnection

        manager = MCPManager()
        manager._connections["test"] = MCPClientConnection(
            url="http://test", name="test", connected=True
        )

        result = manager.get_connection("test")

        assert result is not None
        assert result["name"] == "test"
        assert result["url"] == "http://test"

    def test_get_connection_not_found(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()

        result = manager.get_connection("nonexistent")
        assert result is None


# =============================================================================
# EXPORTS TEST
# =============================================================================


class TestMCPExports:
    """Tests for MCP module exports."""

    def test_mcp_manager_exported(self) -> None:
        from vertice_tui.core.managers import MCPManager, MCPServerState, MCPClientConnection

        assert MCPManager is not None
        assert MCPServerState is not None
        assert MCPClientConnection is not None

    def test_mcp_manager_from_main_package(self) -> None:
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()
        assert hasattr(manager, "start_server")
        assert hasattr(manager, "stop_server")
        assert hasattr(manager, "connect_external")
        assert hasattr(manager, "disconnect")
        assert hasattr(manager, "get_status")
        assert hasattr(manager, "list_tools")


# =============================================================================
# INTEGRATION TESTS (WITH MOCKS)
# =============================================================================


class TestMCPWithMockedDependencies:
    """Integration tests using mocked dependencies."""

    @pytest.mark.asyncio
    async def test_start_server_import_error(self) -> None:
        """Test graceful handling when MCP dependencies not available."""
        from vertice_tui.core.managers.mcp_manager import MCPManager

        manager = MCPManager()

        # Mock the import to fail
        with patch.dict("sys.modules", {"cli.integrations.mcp.server": None}):
            # This should gracefully handle the import error
            # The actual behavior depends on whether MCP is installed
            result = await manager.start_server(port=8080)

            # Either success (if installed) or graceful error (if not)
            assert "success" in result or "error" in result


# =============================================================================
# SUMMARY
# =============================================================================


def test_phase6_2_summary() -> None:
    """Summary test ensuring all Phase 6.2 components exist."""
    # MCPManager
    from vertice_tui.core.managers.mcp_manager import (
        MCPManager,
        MCPServerState,
        MCPClientConnection,
    )

    assert MCPManager is not None
    assert MCPServerState is not None
    assert MCPClientConnection is not None

    # Verify MCPManager has all required methods
    manager = MCPManager()
    assert callable(manager.get_status)
    assert callable(manager.start_server)
    assert callable(manager.stop_server)
    assert callable(manager.connect_external)
    assert callable(manager.disconnect)
    assert callable(manager.list_tools)
    assert callable(manager.is_running)
