"""
Tests for A2A Protocol Phase 4 - gRPC & Security Cards.

Tests Protocol Buffers, gRPC service, and JWS signatures.

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

# Protocol Buffers
from core.protocols.proto import (
    TaskState,
    Task,
    MessageRole,
    Message,
    StreamChunk,
    StreamEventType,
    AgentCard as AgentCardProto,
    AgentCapabilities as AgentCapabilitiesProto,
    AgentSkill as AgentSkillProto,
    HealthStatus,
)

# gRPC Server
from core.protocols.grpc_server import (
    TaskStore,
    A2AServiceImpl,
)
from core.protocols.proto.task_pb2 import (
    SendMessageRequest,
    GetTaskRequest,
    ListTasksRequest,
    CancelTaskRequest,
)
from core.protocols.proto.service_pb2 import (
    HealthCheckRequest,
)
from core.protocols.proto.agent_card_pb2 import (
    GetAgentCardRequest,
)

# JWS Security
from core.security.jws import (
    JWSAlgorithm,
    JWSHeader,
    KeyPair,
    KeyManager,
    JWSSigner,
    SignedAgentCard,
    base64url_encode,
    base64url_decode,
    canonicalize_json,
)


# =============================================================================
# PROTOCOL BUFFERS TESTS
# =============================================================================


class TestProtocolBuffers:
    """Tests for Protocol Buffers types."""

    def test_task_state_enum(self) -> None:
        """TaskState enum has all required values."""
        assert TaskState.TASK_STATE_UNSPECIFIED == 0
        assert TaskState.TASK_STATE_SUBMITTED == 1
        assert TaskState.TASK_STATE_WORKING == 2
        assert TaskState.TASK_STATE_COMPLETED == 3
        assert TaskState.TASK_STATE_FAILED == 4
        assert TaskState.TASK_STATE_CANCELLED == 5
        assert TaskState.TASK_STATE_INPUT_REQUIRED == 6
        assert TaskState.TASK_STATE_REJECTED == 7
        assert TaskState.TASK_STATE_AUTH_REQUIRED == 8

    def test_message_role_enum(self) -> None:
        """MessageRole enum has all required values."""
        assert MessageRole.MESSAGE_ROLE_UNSPECIFIED == 0
        assert MessageRole.MESSAGE_ROLE_USER == 1
        assert MessageRole.MESSAGE_ROLE_AGENT == 2
        assert MessageRole.MESSAGE_ROLE_SYSTEM == 3

    def test_stream_event_type_enum(self) -> None:
        """StreamEventType enum has all required values."""
        assert StreamEventType.STREAM_EVENT_TYPE_UNSPECIFIED == 0
        assert StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE == 1
        assert StreamEventType.STREAM_EVENT_TYPE_MESSAGE_CHUNK == 2
        assert StreamEventType.STREAM_EVENT_TYPE_ARTIFACT_UPDATE == 3
        assert StreamEventType.STREAM_EVENT_TYPE_ERROR == 4
        assert StreamEventType.STREAM_EVENT_TYPE_HEARTBEAT == 5

    def test_health_status_enum(self) -> None:
        """HealthStatus enum has all required values."""
        assert HealthStatus.HEALTH_STATUS_UNSPECIFIED == 0
        assert HealthStatus.HEALTH_STATUS_HEALTHY == 1
        assert HealthStatus.HEALTH_STATUS_DEGRADED == 2
        assert HealthStatus.HEALTH_STATUS_UNHEALTHY == 3

    def test_task_message_creation(self) -> None:
        """Task message can be created and populated."""
        task = Task(
            id="test-123",
            state=TaskState.TASK_STATE_SUBMITTED,
        )

        assert task.id == "test-123"
        assert task.state == TaskState.TASK_STATE_SUBMITTED
        assert len(task.messages) == 0

    def test_message_creation(self) -> None:
        """Message can be created with parts."""
        msg = Message(
            id="msg-123",
            role=MessageRole.MESSAGE_ROLE_USER,
            task_id="task-123",
        )

        assert msg.id == "msg-123"
        assert msg.role == MessageRole.MESSAGE_ROLE_USER
        assert msg.task_id == "task-123"

    def test_stream_chunk_creation(self) -> None:
        """StreamChunk can be created."""
        chunk = StreamChunk(
            event_type=StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE,
            task_id="task-123",
            sequence=1,
        )

        assert chunk.event_type == StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE
        assert chunk.task_id == "task-123"
        assert chunk.sequence == 1

    def test_agent_card_proto_creation(self) -> None:
        """AgentCard protobuf can be created."""
        card = AgentCardProto(
            agent_id="test-agent",
            name="Test Agent",
            description="A test agent",
            version="1.0.0",
            provider="vertice",
        )

        assert card.agent_id == "test-agent"
        assert card.name == "Test Agent"
        assert card.version == "1.0.0"

    def test_agent_capabilities_proto(self) -> None:
        """AgentCapabilities protobuf works correctly."""
        caps = AgentCapabilitiesProto(
            streaming=True,
            push_notifications=False,
            state_transition_history=True,
        )

        assert caps.streaming is True
        assert caps.push_notifications is False
        assert caps.state_transition_history is True

    def test_agent_skill_proto(self) -> None:
        """AgentSkill protobuf works correctly."""
        skill = AgentSkillProto(
            id="skill-1",
            name="Test Skill",
            description="A test skill",
        )
        skill.tags.append("test")
        skill.tags.append("demo")

        assert skill.id == "skill-1"
        assert skill.name == "Test Skill"
        assert len(skill.tags) == 2


# =============================================================================
# TASK STORE TESTS
# =============================================================================


class TestTaskStore:
    """Tests for TaskStore."""

    @pytest.fixture
    def store(self) -> TaskStore:
        """Create fresh task store."""
        return TaskStore()

    @pytest.fixture
    def sample_message(self) -> Message:
        """Create sample message."""
        msg = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.MESSAGE_ROLE_USER,
        )
        return msg

    @pytest.mark.asyncio
    async def test_create_task(self, store: TaskStore, sample_message: Message) -> None:
        """Create task from message."""
        task = await store.create_task(sample_message)

        assert task.id is not None
        assert task.state == TaskState.TASK_STATE_SUBMITTED
        assert len(task.messages) == 1

    @pytest.mark.asyncio
    async def test_get_task(self, store: TaskStore, sample_message: Message) -> None:
        """Get task by ID."""
        created = await store.create_task(sample_message)
        retrieved = await store.get_task(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, store: TaskStore) -> None:
        """Get non-existent task returns None."""
        result = await store.get_task("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_task_state(self, store: TaskStore, sample_message: Message) -> None:
        """Update task state."""
        task = await store.create_task(sample_message)
        updated = await store.update_task(
            task.id,
            state=TaskState.TASK_STATE_WORKING,
        )

        assert updated is not None
        assert updated.state == TaskState.TASK_STATE_WORKING
        assert len(updated.history) == 1

    @pytest.mark.asyncio
    async def test_update_task_message(self, store: TaskStore, sample_message: Message) -> None:
        """Add message to task."""
        task = await store.create_task(sample_message)

        new_msg = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.MESSAGE_ROLE_AGENT,
        )

        updated = await store.update_task(task.id, message=new_msg)

        assert updated is not None
        assert len(updated.messages) == 2

    @pytest.mark.asyncio
    async def test_list_tasks(self, store: TaskStore, sample_message: Message) -> None:
        """List all tasks."""
        await store.create_task(sample_message)
        await store.create_task(sample_message)

        tasks = await store.list_tasks()

        assert len(tasks) == 2

    @pytest.mark.asyncio
    async def test_list_tasks_by_state(self, store: TaskStore, sample_message: Message) -> None:
        """List tasks filtered by state."""
        task1 = await store.create_task(sample_message)
        await store.create_task(sample_message)

        await store.update_task(task1.id, state=TaskState.TASK_STATE_COMPLETED)

        completed = await store.list_tasks(states=[TaskState.TASK_STATE_COMPLETED])
        submitted = await store.list_tasks(states=[TaskState.TASK_STATE_SUBMITTED])

        assert len(completed) == 1
        assert len(submitted) == 1

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, store: TaskStore, sample_message: Message) -> None:
        """Subscribe and unsubscribe from task updates."""
        task = await store.create_task(sample_message)

        queue = await store.subscribe(task.id)
        assert queue is not None

        await store.unsubscribe(task.id, queue)


# =============================================================================
# A2A SERVICE TESTS
# =============================================================================


class TestA2AServiceImpl:
    """Tests for A2AServiceImpl."""

    @pytest.fixture
    def agent_card(self) -> AgentCardProto:
        """Create sample agent card."""
        return AgentCardProto(
            agent_id="test-agent",
            name="Test Agent",
            description="A test agent for unit tests",
            version="1.0.0",
            provider="vertice",
        )

    @pytest.fixture
    def service(self, agent_card: AgentCardProto) -> A2AServiceImpl:
        """Create service instance."""
        return A2AServiceImpl(agent_card)

    @pytest.fixture
    def mock_context(self) -> AsyncMock:
        """Create mock gRPC context."""
        context = AsyncMock()
        context.abort = AsyncMock()
        return context

    @pytest.mark.asyncio
    async def test_health_check(self, service: A2AServiceImpl, mock_context: AsyncMock) -> None:
        """Health check returns healthy status."""
        request = HealthCheckRequest()
        response = await service.HealthCheck(request, mock_context)

        assert response.status == HealthStatus.HEALTH_STATUS_HEALTHY
        assert response.version == "1.0.0"
        assert response.uptime_seconds >= 0

    @pytest.mark.asyncio
    async def test_get_agent_card(self, service: A2AServiceImpl, mock_context: AsyncMock) -> None:
        """GetAgentCard returns configured card."""
        request = GetAgentCardRequest()
        response = await service.GetAgentCard(request, mock_context)

        assert response.card.agent_id == "test-agent"
        assert response.card.name == "Test Agent"

    @pytest.mark.asyncio
    async def test_send_message_creates_task(
        self, service: A2AServiceImpl, mock_context: AsyncMock
    ) -> None:
        """SendMessage creates new task."""
        msg = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.MESSAGE_ROLE_USER,
        )
        request = SendMessageRequest(message=msg)

        response = await service.SendMessage(request, mock_context)

        assert response.task is not None
        assert response.task.id != ""
        assert response.task.state == TaskState.TASK_STATE_COMPLETED

    @pytest.mark.asyncio
    async def test_get_task(self, service: A2AServiceImpl, mock_context: AsyncMock) -> None:
        """GetTask retrieves existing task."""
        # First create a task
        msg = Message(id=str(uuid.uuid4()), role=MessageRole.MESSAGE_ROLE_USER)
        send_response = await service.SendMessage(SendMessageRequest(message=msg), mock_context)
        task_id = send_response.task.id

        # Then get it
        get_response = await service.GetTask(GetTaskRequest(task_id=task_id), mock_context)

        assert get_response.id == task_id

    @pytest.mark.asyncio
    async def test_list_tasks(self, service: A2AServiceImpl, mock_context: AsyncMock) -> None:
        """ListTasks returns all tasks."""
        # Create some tasks
        for _ in range(3):
            msg = Message(id=str(uuid.uuid4()), role=MessageRole.MESSAGE_ROLE_USER)
            await service.SendMessage(SendMessageRequest(message=msg), mock_context)

        response = await service.ListTasks(ListTasksRequest(limit=10), mock_context)

        assert len(response.tasks) == 3

    @pytest.mark.asyncio
    async def test_cancel_task_success(
        self, service: A2AServiceImpl, mock_context: AsyncMock
    ) -> None:
        """CancelTask successfully cancels in-progress task."""
        # Create task
        msg = Message(id=str(uuid.uuid4()), role=MessageRole.MESSAGE_ROLE_USER)
        await service._task_store.create_task(msg)

        tasks = await service._task_store.list_tasks()
        task_id = tasks[0].id

        # Set to working state
        await service._task_store.update_task(task_id, state=TaskState.TASK_STATE_WORKING)

        # Cancel
        response = await service.CancelTask(
            CancelTaskRequest(task_id=task_id, reason="Test cancellation"),
            mock_context,
        )

        assert response.success is True
        assert response.task.state == TaskState.TASK_STATE_CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_completed_task_fails(
        self, service: A2AServiceImpl, mock_context: AsyncMock
    ) -> None:
        """CancelTask fails for completed task."""
        # Create and complete task
        msg = Message(id=str(uuid.uuid4()), role=MessageRole.MESSAGE_ROLE_USER)
        send_response = await service.SendMessage(SendMessageRequest(message=msg), mock_context)
        task_id = send_response.task.id

        # Try to cancel
        response = await service.CancelTask(CancelTaskRequest(task_id=task_id), mock_context)

        assert response.success is False

    @pytest.mark.asyncio
    async def test_send_streaming_message(
        self, service: A2AServiceImpl, mock_context: AsyncMock
    ) -> None:
        """SendStreamingMessage returns stream of chunks."""
        msg = Message(id=str(uuid.uuid4()), role=MessageRole.MESSAGE_ROLE_USER)
        request = SendMessageRequest(message=msg)

        chunks = []
        async for chunk in service.SendStreamingMessage(request, mock_context):
            chunks.append(chunk)

        # Should have at least status updates
        assert len(chunks) >= 2

        # First should be working status
        assert chunks[0].event_type == StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE

        # Last should be completed status
        assert chunks[-1].event_type == StreamEventType.STREAM_EVENT_TYPE_STATUS_UPDATE


# =============================================================================
# JWS SECURITY TESTS
# =============================================================================


class TestBase64URLEncoding:
    """Tests for Base64URL encoding utilities."""

    def test_encode_decode_roundtrip(self) -> None:
        """Encode and decode produces original data."""
        original = b"Hello, World!"
        encoded = base64url_encode(original)
        decoded = base64url_decode(encoded)

        assert decoded == original

    def test_encode_no_padding(self) -> None:
        """Encoded string has no padding."""
        data = b"test"
        encoded = base64url_encode(data)

        assert "=" not in encoded

    def test_decode_with_padding(self) -> None:
        """Decode handles missing padding."""
        # Manually create string without padding
        encoded = "dGVzdA"  # "test" without padding
        decoded = base64url_decode(encoded)

        assert decoded == b"test"


class TestCanonicalization:
    """Tests for JSON canonicalization."""

    def test_deterministic_key_order(self) -> None:
        """Keys are sorted deterministically."""
        data1 = {"b": 1, "a": 2, "c": 3}
        data2 = {"a": 2, "c": 3, "b": 1}

        canon1 = canonicalize_json(data1)
        canon2 = canonicalize_json(data2)

        assert canon1 == canon2

    def test_nested_objects(self) -> None:
        """Nested objects are also sorted."""
        data = {"outer": {"b": 1, "a": 2}}
        canon = canonicalize_json(data)

        # Should have 'a' before 'b' in output
        assert b'"a":2' in canon or b'"a": 2' in canon

    def test_no_whitespace(self) -> None:
        """Canonical form has minimal whitespace."""
        data = {"key": "value"}
        canon = canonicalize_json(data)

        # Should not have pretty-printing spaces
        assert b"  " not in canon


class TestKeyManager:
    """Tests for KeyManager."""

    def test_generate_rsa_keypair(self) -> None:
        """Generate RSA key pair."""
        keypair = KeyManager.generate_rsa_keypair(key_size=2048)

        assert keypair.private_key is not None
        assert keypair.public_key is not None
        assert keypair.algorithm == JWSAlgorithm.RS256
        assert keypair.key_id.startswith("rsa-")

    def test_generate_rsa_custom_key_id(self) -> None:
        """Generate RSA with custom key ID."""
        keypair = KeyManager.generate_rsa_keypair(key_id="my-key-123")

        assert keypair.key_id == "my-key-123"

    def test_generate_ec_keypair_p256(self) -> None:
        """Generate EC P-256 key pair."""
        keypair = KeyManager.generate_ec_keypair(curve="P-256")

        assert keypair.private_key is not None
        assert keypair.public_key is not None
        assert keypair.algorithm == JWSAlgorithm.ES256
        assert keypair.key_id.startswith("ec-")

    def test_generate_ec_keypair_p384(self) -> None:
        """Generate EC P-384 key pair."""
        keypair = KeyManager.generate_ec_keypair(curve="P-384")

        assert keypair.algorithm == JWSAlgorithm.ES384

    def test_generate_ec_keypair_p521(self) -> None:
        """Generate EC P-521 key pair."""
        keypair = KeyManager.generate_ec_keypair(curve="P-521")

        assert keypair.algorithm == JWSAlgorithm.ES512

    def test_generate_ec_invalid_curve(self) -> None:
        """Invalid curve raises error."""
        with pytest.raises(ValueError, match="Unsupported curve"):
            KeyManager.generate_ec_keypair(curve="P-999")


class TestJWSHeader:
    """Tests for JWSHeader."""

    def test_header_to_dict_minimal(self) -> None:
        """Header converts to dict with required fields."""
        header = JWSHeader(alg=JWSAlgorithm.RS256)
        result = header.to_dict()

        assert result["alg"] == "RS256"
        assert result["typ"] == "JWS"
        assert "kid" not in result
        assert "jku" not in result

    def test_header_to_dict_full(self) -> None:
        """Header converts to dict with all fields."""
        header = JWSHeader(
            alg=JWSAlgorithm.ES256,
            typ="JWS",
            kid="key-123",
            jku="https://example.com/.well-known/jwks.json",
        )
        result = header.to_dict()

        assert result["alg"] == "ES256"
        assert result["kid"] == "key-123"
        assert result["jku"] == "https://example.com/.well-known/jwks.json"


class TestJWSSigner:
    """Tests for JWSSigner."""

    @pytest.fixture
    def rsa_keypair(self) -> KeyPair:
        """Create RSA key pair."""
        return KeyManager.generate_rsa_keypair(key_size=2048)

    @pytest.fixture
    def ec_keypair(self) -> KeyPair:
        """Create EC key pair."""
        return KeyManager.generate_ec_keypair(curve="P-256")

    @pytest.fixture
    def sample_agent_card(self) -> dict:
        """Create sample agent card dict."""
        return {
            "agentId": "test-agent",
            "name": "Test Agent",
            "description": "A test agent",
            "version": "1.0.0",
            "provider": "vertice",
            "capabilities": {
                "streaming": True,
                "pushNotifications": False,
            },
            "skills": [],
        }

    def test_sign_agent_card_rsa(self, rsa_keypair: KeyPair, sample_agent_card: dict) -> None:
        """Sign agent card with RSA."""
        signer = JWSSigner(rsa_keypair)
        signature = signer.sign_agent_card(sample_agent_card)

        assert signature.protected is not None
        assert signature.signature is not None

    def test_sign_agent_card_ec(self, ec_keypair: KeyPair, sample_agent_card: dict) -> None:
        """Sign agent card with EC."""
        signer = JWSSigner(ec_keypair)
        signature = signer.sign_agent_card(sample_agent_card)

        assert signature.protected is not None
        assert signature.signature is not None

    def test_verify_signature_rsa(self, rsa_keypair: KeyPair, sample_agent_card: dict) -> None:
        """Verify RSA signature."""
        signer = JWSSigner(rsa_keypair)
        signature = signer.sign_agent_card(sample_agent_card)

        is_valid = signer.verify_signature(sample_agent_card, signature)

        assert is_valid is True

    def test_verify_signature_ec(self, ec_keypair: KeyPair, sample_agent_card: dict) -> None:
        """Verify EC signature."""
        signer = JWSSigner(ec_keypair)
        signature = signer.sign_agent_card(sample_agent_card)

        is_valid = signer.verify_signature(sample_agent_card, signature)

        assert is_valid is True

    def test_verify_tampered_card_fails(
        self, rsa_keypair: KeyPair, sample_agent_card: dict
    ) -> None:
        """Tampered card fails verification."""
        signer = JWSSigner(rsa_keypair)
        signature = signer.sign_agent_card(sample_agent_card)

        # Tamper with card
        tampered = dict(sample_agent_card)
        tampered["name"] = "Tampered Agent"

        is_valid = signer.verify_signature(tampered, signature)

        assert is_valid is False

    def test_signature_excludes_signatures_field(
        self, rsa_keypair: KeyPair, sample_agent_card: dict
    ) -> None:
        """Signing excludes signatures field from payload."""
        card_with_signatures = dict(sample_agent_card)
        card_with_signatures["signatures"] = [{"previous": "signature"}]

        signer = JWSSigner(rsa_keypair)
        signature = signer.sign_agent_card(card_with_signatures)

        # Should still verify against card without signatures
        is_valid = signer.verify_signature(sample_agent_card, signature)
        assert is_valid is True

    def test_sign_with_jku(self, rsa_keypair: KeyPair, sample_agent_card: dict) -> None:
        """Sign with JKU field."""
        signer = JWSSigner(
            rsa_keypair,
            jku="https://example.com/.well-known/jwks.json",
        )
        signature = signer.sign_agent_card(sample_agent_card)

        assert signature.jku == "https://example.com/.well-known/jwks.json"


class TestSignedAgentCard:
    """Tests for SignedAgentCard."""

    @pytest.fixture
    def keypair(self) -> KeyPair:
        """Create key pair."""
        return KeyManager.generate_rsa_keypair()

    @pytest.fixture
    def sample_card(self) -> dict:
        """Create sample card."""
        return {
            "agentId": "signed-agent",
            "name": "Signed Agent",
            "version": "1.0.0",
        }

    def test_add_signature(self, keypair: KeyPair, sample_card: dict) -> None:
        """Add signature to card."""
        signed = SignedAgentCard(card=sample_card)
        signer = JWSSigner(keypair)

        signed.add_signature(signer)

        assert len(signed.signatures) == 1

    def test_add_multiple_signatures(self, keypair: KeyPair, sample_card: dict) -> None:
        """Add multiple signatures."""
        keypair2 = KeyManager.generate_rsa_keypair()
        signed = SignedAgentCard(card=sample_card)

        signed.add_signature(JWSSigner(keypair))
        signed.add_signature(JWSSigner(keypair2))

        assert len(signed.signatures) == 2

    def test_verify_all_signatures(self, keypair: KeyPair, sample_card: dict) -> None:
        """Verify all signatures."""
        signed = SignedAgentCard(card=sample_card)
        signer = JWSSigner(keypair)

        signed.add_signature(signer)
        is_valid = signed.verify_all([signer])

        assert is_valid is True

    def test_to_dict(self, keypair: KeyPair, sample_card: dict) -> None:
        """Convert to A2A-compliant dict."""
        signed = SignedAgentCard(card=sample_card)
        signed.add_signature(JWSSigner(keypair))

        result = signed.to_dict()

        assert "signatures" in result
        assert len(result["signatures"]) == 1
        assert "protected" in result["signatures"][0]
        assert "signature" in result["signatures"][0]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestA2AIntegration:
    """Integration tests for A2A Phase 4."""

    @pytest.mark.asyncio
    async def test_full_task_lifecycle(self) -> None:
        """Test complete task lifecycle through gRPC service."""
        # Setup
        card = AgentCardProto(
            agent_id="integration-agent",
            name="Integration Test Agent",
            version="1.0.0",
        )
        service = A2AServiceImpl(card)
        context = AsyncMock()

        # 1. Send message (creates task)
        msg = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.MESSAGE_ROLE_USER,
        )
        response = await service.SendMessage(SendMessageRequest(message=msg), context)

        assert response.task.state == TaskState.TASK_STATE_COMPLETED

        # 2. Get task
        task = await service.GetTask(GetTaskRequest(task_id=response.task.id), context)

        assert task.id == response.task.id

        # 3. List tasks
        tasks_response = await service.ListTasks(ListTasksRequest(limit=10), context)

        assert len(tasks_response.tasks) >= 1

    @pytest.mark.asyncio
    async def test_signed_agent_card_roundtrip(self) -> None:
        """Test signing and verifying agent card."""
        # Create card
        card = {
            "agentId": "roundtrip-agent",
            "name": "Roundtrip Test Agent",
            "description": "Tests signing roundtrip",
            "version": "1.0.0",
            "provider": "vertice",
            "capabilities": {"streaming": True},
            "skills": [{"id": "skill-1", "name": "Test Skill"}],
        }

        # Sign with multiple keys
        keypair1 = KeyManager.generate_rsa_keypair(key_id="key-1")
        keypair2 = KeyManager.generate_ec_keypair(curve="P-256", key_id="key-2")

        signer1 = JWSSigner(keypair1)
        signer2 = JWSSigner(keypair2)

        signed = SignedAgentCard(card=card)
        signed.add_signature(signer1)
        signed.add_signature(signer2)

        # Verify both signatures
        assert signer1.verify_signature(card, signed.signatures[0]) is True
        assert signer2.verify_signature(card, signed.signatures[1]) is True

        # Export to dict
        exported = signed.to_dict()
        assert len(exported["signatures"]) == 2

    @pytest.mark.asyncio
    async def test_proto_to_dict_compatibility(self) -> None:
        """Test protobuf to dict compatibility."""
        from google.protobuf.json_format import MessageToDict

        # Create proto message
        task = Task(
            id="proto-test",
            state=TaskState.TASK_STATE_WORKING,
        )

        # Convert to dict
        task_dict = MessageToDict(task)

        assert task_dict["id"] == "proto-test"
        assert task_dict["state"] == "TASK_STATE_WORKING"
