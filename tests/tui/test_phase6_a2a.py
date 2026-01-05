"""
Phase 6.3 Tests - A2A Integration

Tests for A2AManager, A2ACommandHandler, and Bridge delegation.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from typing import List


# =============================================================================
# A2A STATE TESTS
# =============================================================================


class TestA2AServerState:
    """Tests for A2AServerState dataclass."""

    def test_default_values(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AServerState

        state = A2AServerState()
        assert state.running is False
        assert state.port == 50051
        assert state.host == "0.0.0.0"
        assert state.agent_card_name == ""
        assert state.active_tasks == 0
        assert state.total_tasks_processed == 0
        assert state.error is None

    def test_custom_values(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AServerState

        state = A2AServerState(running=True, port=50052, agent_card_name="test")
        assert state.running is True
        assert state.port == 50052
        assert state.agent_card_name == "test"


class TestDiscoveredAgent:
    """Tests for DiscoveredAgent dataclass."""

    def test_default_values(self) -> None:
        from vertice_tui.core.managers.a2a_manager import DiscoveredAgent

        agent = DiscoveredAgent(
            agent_id="agent-1",
            name="Test Agent",
            version="1.0.0",
            url="grpc://localhost:50051",
        )
        assert agent.agent_id == "agent-1"
        assert agent.name == "Test Agent"
        assert agent.version == "1.0.0"
        assert agent.url == "grpc://localhost:50051"
        assert agent.description == ""
        assert agent.capabilities == []
        assert agent.skills == []


# =============================================================================
# A2A MANAGER TESTS
# =============================================================================


class TestA2AManager:
    """Tests for A2AManager."""

    def test_init(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()
        assert manager._server is None
        assert manager._server_state.running is False
        assert manager._discovered_agents == {}
        assert manager._local_agent_card is None
        assert manager._task_counter == 0

    def test_is_running_default_false(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()
        assert manager.is_running() is False

    def test_get_status_default(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()
        status = manager.get_status()

        assert "server" in status
        assert status["server"]["running"] is False
        assert status["discovered_agents"] == 0
        assert status["local_card"] is False

    @pytest.mark.asyncio
    async def test_start_server_already_running(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()
        manager._server_state.running = True

        result = await manager.start_server()
        assert result["success"] is False
        assert "already running" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_stop_server_not_running(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()

        result = await manager.stop_server()
        assert result["success"] is False
        assert "not running" in result["error"].lower()

    def test_add_discovered_agent(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager, DiscoveredAgent

        manager = A2AManager()
        agent = DiscoveredAgent(
            agent_id="agent-1",
            name="Test",
            version="1.0",
            url="grpc://localhost:50051",
        )

        manager.add_discovered_agent(agent)

        assert "agent-1" in manager._discovered_agents
        assert manager._discovered_agents["agent-1"].name == "Test"

    def test_get_discovered_agents_empty(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()
        agents = manager.get_discovered_agents()
        assert agents == []

    def test_get_discovered_agents_with_data(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager, DiscoveredAgent

        manager = A2AManager()
        manager._discovered_agents["agent-1"] = DiscoveredAgent(
            agent_id="agent-1",
            name="Test",
            version="1.0",
            url="grpc://localhost:50051",
        )

        agents = manager.get_discovered_agents()
        assert len(agents) == 1
        assert agents[0]["agent_id"] == "agent-1"

    def test_get_agent_found(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager, DiscoveredAgent

        manager = A2AManager()
        agent = DiscoveredAgent(
            agent_id="agent-1",
            name="Test",
            version="1.0",
            url="grpc://localhost",
        )
        manager._discovered_agents["agent-1"] = agent

        result = manager.get_agent("agent-1")
        assert result is not None
        assert result.name == "Test"

    def test_get_agent_not_found(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()
        result = manager.get_agent("nonexistent")
        assert result is None

    def test_clear_discoveries(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager, DiscoveredAgent

        manager = A2AManager()
        manager._discovered_agents["agent-1"] = DiscoveredAgent(
            agent_id="agent-1",
            name="Test",
            version="1.0",
            url="grpc://localhost",
        )

        manager.clear_discoveries()
        assert manager._discovered_agents == {}

    def test_get_local_card_none(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()
        assert manager.get_local_card() is None

    @pytest.mark.asyncio
    async def test_discover_agents_returns_cached(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager, DiscoveredAgent

        manager = A2AManager()
        manager._discovered_agents["agent-1"] = DiscoveredAgent(
            agent_id="agent-1",
            name="Test",
            version="1.0",
            url="grpc://localhost",
        )

        agents = await manager.discover_agents()
        assert len(agents) == 1

    @pytest.mark.asyncio
    async def test_call_agent_not_found(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()

        chunks: List[str] = []
        async for chunk in manager.call_agent("nonexistent", "test task"):
            chunks.append(chunk)

        combined = "".join(chunks)
        assert "not found" in combined.lower()

    @pytest.mark.asyncio
    async def test_sign_card_no_card(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()

        result = await manager.sign_card("/path/to/key")

        assert result["success"] is False
        assert "no local card" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_sign_card_with_generated_key(self) -> None:
        """Test sign_card with a real generated RSA key."""
        import tempfile
        import os
        from vertice_tui.core.managers.a2a_manager import A2AManager
        from core.security.jws import KeyManager
        from core.protocols.agent_card import AgentCard
        from core.protocols.types import AgentCapabilities

        # Generate RSA keypair
        keypair = KeyManager.generate_rsa_keypair(key_size=2048)

        # Write private key to temp file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pem', delete=False) as f:
            f.write(keypair.private_key)
            key_path = f.name

        try:
            manager = A2AManager()

            # Manually set up local agent card
            manager._local_agent_card = AgentCard(
                agent_id="test-agent",
                name="Test Agent",
                description="Test description",
                version="1.0.0",
                provider="vertice",
                url="grpc://localhost:50051",
                capabilities=AgentCapabilities(
                    streaming=True,
                    push_notifications=False,
                    state_transition_history=True,
                ),
            )

            # Test sign_card
            result = await manager.sign_card(key_path)

            assert result["success"] is True
            assert "signature" in result
            assert "protected" in result["signature"]
            assert "signature" in result["signature"]
            # Verify signature is base64url encoded
            assert len(result["signature"]["protected"]) > 0
            assert len(result["signature"]["signature"]) > 0

        finally:
            os.unlink(key_path)

    @pytest.mark.asyncio
    async def test_sign_card_file_not_found(self) -> None:
        """Test sign_card with non-existent key file."""
        from vertice_tui.core.managers.a2a_manager import A2AManager
        from core.protocols.agent_card import AgentCard
        from core.protocols.types import AgentCapabilities

        manager = A2AManager()

        # Set up local card
        manager._local_agent_card = AgentCard(
            agent_id="test",
            name="Test",
            description="Test",
            version="1.0.0",
            provider="vertice",
            url="grpc://localhost:50051",
            capabilities=AgentCapabilities(
                streaming=True,
                push_notifications=False,
                state_transition_history=True,
            ),
        )

        result = await manager.sign_card("/nonexistent/path/to/key.pem")

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# EXPORTS TEST
# =============================================================================


class TestA2AExports:
    """Tests for A2A module exports."""

    def test_a2a_manager_exported(self) -> None:
        from vertice_tui.core.managers import A2AManager, A2AServerState, DiscoveredAgent

        assert A2AManager is not None
        assert A2AServerState is not None
        assert DiscoveredAgent is not None

    def test_a2a_manager_has_methods(self) -> None:
        from vertice_tui.core.managers.a2a_manager import A2AManager

        manager = A2AManager()
        assert hasattr(manager, "start_server")
        assert hasattr(manager, "stop_server")
        assert hasattr(manager, "discover_agents")
        assert hasattr(manager, "call_agent")
        assert hasattr(manager, "get_status")
        assert hasattr(manager, "get_local_card")
        assert hasattr(manager, "sign_card")


# =============================================================================
# A2A COMMAND HANDLER TESTS
# =============================================================================


class TestA2ACommandHandler:
    """Tests for A2ACommandHandler."""

    def test_handler_init(self) -> None:
        from vertice_tui.handlers.a2a import A2ACommandHandler

        mock_app = MagicMock()
        handler = A2ACommandHandler(mock_app)
        assert handler.app is mock_app

    def test_handler_has_handle_method(self) -> None:
        from vertice_tui.handlers.a2a import A2ACommandHandler

        mock_app = MagicMock()
        handler = A2ACommandHandler(mock_app)
        assert callable(handler.handle)


# =============================================================================
# SUMMARY
# =============================================================================


def test_phase6_3_summary() -> None:
    """Summary test ensuring all Phase 6.3 components exist."""
    # A2AManager
    from vertice_tui.core.managers.a2a_manager import (
        A2AManager,
        A2AServerState,
        DiscoveredAgent,
    )

    assert A2AManager is not None
    assert A2AServerState is not None
    assert DiscoveredAgent is not None

    # A2ACommandHandler
    from vertice_tui.handlers.a2a import A2ACommandHandler

    assert A2ACommandHandler is not None

    # Verify A2AManager has all required methods
    manager = A2AManager()
    assert callable(manager.get_status)
    assert callable(manager.start_server)
    assert callable(manager.stop_server)
    assert callable(manager.discover_agents)
    assert callable(manager.call_agent)
    assert callable(manager.get_local_card)
    assert callable(manager.sign_card)
    assert callable(manager.add_discovered_agent)
    assert callable(manager.get_discovered_agents)
    assert callable(manager.clear_discoveries)
