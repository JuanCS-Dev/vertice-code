"""
Tests for Distributed Evolution System - Phase 9

Tests peer-to-peer skills sharing, consensus mechanisms, and distributed learning
across multiple Prometheus instances.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from prometheus.distributed.skills_discovery import SkillsDiscoveryService, PeerInfo
from prometheus.distributed.registry import (
    DistributedSkillsRegistry,
    SkillsConsensusManager,
)
from prometheus.distributed.peer_protocol import SkillsPeerProtocol, PeerMessage
from prometheus.skills.registry import LearnedSkill


class TestSkillsDiscoveryService:
    """Test Skills Discovery Service functionality."""

    @pytest.fixture
    def discovery_service(self):
        """Create a test discovery service."""
        return SkillsDiscoveryService(
            instance_id="test_instance_1",
            listen_port=8080,
            heartbeat_interval=1,  # Fast for testing
        )

    def test_peer_info_creation(self):
        """Test PeerInfo dataclass functionality."""
        peer = PeerInfo(
            instance_id="peer_1",
            endpoint="http://localhost:8081",
            skills_count=5,
            capabilities={"skills_sharing", "evolution_sync"},
        )

        assert peer.instance_id == "peer_1"
        assert peer.endpoint == "http://localhost:8081"
        assert peer.skills_count == 5
        assert peer.capabilities == {"skills_sharing", "evolution_sync"}
        assert peer.is_alive()  # Should be alive initially

    def test_peer_info_serialization(self):
        """Test PeerInfo to/from dict conversion."""
        original = PeerInfo(
            instance_id="peer_1",
            endpoint="http://localhost:8081",
            skills_count=5,
        )

        data = original.to_dict()
        restored = PeerInfo.from_dict(data)

        assert restored.instance_id == original.instance_id
        assert restored.endpoint == original.endpoint
        assert restored.skills_count == original.skills_count

    @pytest.mark.asyncio
    async def test_discovery_service_start_stop(self, discovery_service):
        """Test starting and stopping the discovery service."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            # Start service
            await discovery_service.start()
            assert discovery_service.session is not None
            assert discovery_service._heartbeat_task is not None
            assert discovery_service._discovery_task is not None

            # Stop service
            await discovery_service.stop()
            assert discovery_service.session is None
            assert discovery_service._heartbeat_task.done()
            assert discovery_service._discovery_task.done()

    @pytest.mark.asyncio
    async def test_register_instance(self, discovery_service):
        """Test instance registration."""
        mock_registry = MagicMock()
        mock_registry.learned_skills = {"skill1": MagicMock(), "skill2": MagicMock()}

        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            await discovery_service.start()

            # Register instance
            endpoint = await discovery_service.register_instance(mock_registry)

            assert endpoint == "http://localhost:8080"
            assert discovery_service.instance_id in discovery_service.known_peers
            assert discovery_service.known_peers[discovery_service.instance_id].skills_count == 2

            await discovery_service.stop()

    @pytest.mark.asyncio
    async def test_broadcast_skill(self, discovery_service):
        """Test skill broadcasting to peers."""
        with patch("aiohttp.ClientSession") as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session

            await discovery_service.start()

            # Setup peers
            discovery_service.known_peers = {
                "peer1": PeerInfo("peer1", "http://localhost:8081"),
                "peer2": PeerInfo("peer2", "http://localhost:8082"),
            }

            # Create test skill
            skill = LearnedSkill(
                name="test_skill",
                description="A test skill",
                category="test",
                procedure_steps=["step1", "step2"],
                success_rate=0.9,
                usage_count=5,
            )

            # Mock the broadcast method
            with patch.object(
                discovery_service, "_send_skill_to_peer", new_callable=AsyncMock
            ) as mock_send:
                mock_send.return_value = None

                await discovery_service.broadcast_skill(skill)

                # Should be called for both peers
                assert mock_send.call_count == 2

            await discovery_service.stop()


class TestSkillsConsensusManager:
    """Test consensus manager functionality."""

    @pytest.fixture
    def consensus_manager(self):
        """Create test consensus manager."""
        return SkillsConsensusManager()

    def test_skill_conflict_creation(self, consensus_manager):
        """Test SkillConflict creation."""
        local_skill = LearnedSkill(
            name="test_skill",
            description="Test skill",
            procedure_steps=["step1"],
            success_rate=0.8,
            learned_at=datetime.now() - timedelta(days=1),
        )
        peer_skill = LearnedSkill(
            name="test_skill",
            description="Test skill",
            procedure_steps=["step1"],
            success_rate=0.9,
            learned_at=datetime.now(),
        )

        conflict = consensus_manager.resolve_skill_conflict(
            "test_skill", local_skill, peer_skill, "peer1"
        )

        assert len(consensus_manager.conflict_history) == 1
        assert consensus_manager.conflict_history[0].resolution_strategy == "peer_higher_score"

    def test_resolve_skill_conflict_higher_score(self, consensus_manager):
        """Test conflict resolution with higher peer score."""
        local_skill = LearnedSkill(
            name="test_skill",
            description="Test skill",
            procedure_steps=["step1"],
            success_rate=0.7,
            usage_count=5,
            learned_at=datetime.now() - timedelta(days=10),
        )
        peer_skill = LearnedSkill(
            name="test_skill",
            description="Test skill",
            procedure_steps=["step1"],
            success_rate=0.9,
            usage_count=10,
            learned_at=datetime.now(),
        )

        winner = consensus_manager.resolve_skill_conflict(
            "test_skill", local_skill, peer_skill, "peer1"
        )

        assert winner is peer_skill
        assert consensus_manager.conflict_history[0].resolution_strategy == "peer_higher_score"


class TestDistributedSkillsRegistry:
    """Test Distributed Skills Registry functionality."""

    @pytest.fixture
    def registry(self):
        """Create test distributed registry."""
        return DistributedSkillsRegistry(instance_id="test_instance")

    @pytest.fixture
    def mock_discovery_service(self):
        """Mock discovery service."""
        service = AsyncMock()
        service.discover_peers = AsyncMock(return_value=["peer1", "peer2"])
        service.get_peer_skills = AsyncMock(return_value=[])
        return service

    def test_registry_initialization(self, registry):
        """Test registry initialization."""
        assert registry.instance_id == "test_instance"
        assert registry.auto_sync_enabled is True
        assert registry.quality_threshold == 0.7
        assert registry.consensus_manager is not None

    def test_set_discovery_service(self, registry, mock_discovery_service):
        """Test setting discovery service."""
        registry.set_discovery_service(mock_discovery_service)
        assert registry.discovery_service is mock_discovery_service

    @pytest.mark.asyncio
    async def test_sync_with_peers_no_service(self, registry):
        """Test sync when no discovery service configured."""
        result = await registry.sync_with_peers()
        assert result["error"] == "No discovery service configured"


class TestSkillsPeerProtocol:
    """Test Peer-to-Peer Protocol functionality."""

    @pytest.fixture
    def registry(self):
        """Create mock registry."""
        registry = AsyncMock()
        registry.get_skill = AsyncMock()
        registry._register_peer_skill = AsyncMock()
        return registry

    @pytest.fixture
    def protocol(self, registry):
        """Create test protocol."""
        return SkillsPeerProtocol(registry, "test_instance")

    def test_peer_message_creation(self):
        """Test PeerMessage creation."""
        message = PeerMessage(
            message_type="skill_request",
            sender_id="sender",
            receiver_id="receiver",
            payload={"skill_name": "test_skill"},
        )

        assert message.message_type == "skill_request"
        assert message.sender_id == "sender"
        assert message.receiver_id == "receiver"
        assert "skill_name" in message.payload

    @pytest.mark.asyncio
    async def test_handle_skill_request_found(self, protocol, registry):
        """Test handling skill request when skill is found."""
        # Setup mock skill
        skill = LearnedSkill(
            "requested_skill",
            description="Test skill",
            procedure_steps=["step1", "step2"],
            success_rate=0.8,
        )
        registry.get_skill.return_value = skill

        message = PeerMessage(
            message_type="skill_request",
            sender_id="peer1",
            payload={"skill_name": "requested_skill"},
        )

        response = await protocol.handle_incoming_message(message)

        assert response is not None
        assert response.message_type == "skill_response"
        assert response.payload["found"] is True
        assert "skill" in response.payload

    @pytest.mark.asyncio
    async def test_handle_skill_broadcast(self, protocol, registry):
        """Test handling skill broadcast."""
        skill = LearnedSkill(
            "broadcast_skill",
            description="Test skill",
            procedure_steps=["step1", "step2"],
            success_rate=0.8,
        )

        message = PeerMessage(
            message_type="skill_broadcast",
            sender_id="peer1",
            payload={"skill": skill.to_dict()},
        )

        response = await protocol.handle_incoming_message(message)

        assert response is not None
        assert response.message_type == "skill_ack"
        assert response.payload["accepted"] is True
        registry._register_peer_skill.assert_called_once()
