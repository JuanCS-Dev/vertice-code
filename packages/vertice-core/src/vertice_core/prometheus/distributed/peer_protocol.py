"""
Peer-to-Peer Skills Protocol - Direct Communication Between Prometheus Instances

This module implements the protocol for direct peer-to-peer communication
between Prometheus instances for skills sharing and collaborative evolution.

Created with love for distributed AI collaboration.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import hashlib

from prometheus.skills.registry import LearnedSkill
from prometheus.distributed.registry import DistributedSkillsRegistry

logger = logging.getLogger(__name__)


@dataclass
class PeerMessage:
    """Represents a message exchanged between peers."""

    message_id: str = field(
        default_factory=lambda: hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[
            :8
        ]
    )
    message_type: str = ""  # skill_request, skill_broadcast, skill_response, heartbeat
    sender_id: str = ""
    receiver_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    payload: Dict[str, Any] = field(default_factory=dict)
    ttl: int = 5  # Time to live for message forwarding

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "ttl": self.ttl,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PeerMessage":
        return cls(
            message_id=data["message_id"],
            message_type=data["message_type"],
            sender_id=data["sender_id"],
            receiver_id=data.get("receiver_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            payload=data.get("payload", {}),
            ttl=data.get("ttl", 5),
        )

    def is_expired(self) -> bool:
        """Check if message has expired."""
        return self.ttl <= 0

    def decrement_ttl(self):
        """Decrement time to live."""
        self.ttl -= 1


class SkillsPeerProtocol:
    """
    Protocol for peer-to-peer skills communication.

    Handles direct communication between Prometheus instances including:
    - Skill requests and responses
    - Skill broadcasting
    - Heartbeat monitoring
    - Quality validation
    """

    def __init__(self, skills_registry: DistributedSkillsRegistry, instance_id: str):
        self.registry = skills_registry
        self.instance_id = instance_id

        # Message handlers
        self.message_handlers: Dict[str, Callable] = {
            "skill_request": self.handle_skill_request,
            "skill_broadcast": self.handle_skill_broadcast,
            "skill_response": self.handle_skill_response,
            "heartbeat": self.handle_heartbeat,
            "ping": self.handle_ping,
            "pong": self.handle_pong,
        }

        # Connection management
        self.active_connections: Dict[str, Any] = {}  # peer_id -> connection
        self.pending_requests: Dict[str, asyncio.Future] = {}  # message_id -> future

        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.skills_shared = 0
        self.skills_requested = 0

        logger.info(f"Initialized Skills Peer Protocol for instance {instance_id}")

    async def handle_incoming_message(
        self, message: PeerMessage, peer_connection=None
    ) -> Optional[PeerMessage]:
        """
        Handle an incoming message from a peer.

        Returns a response message if needed.
        """
        self.messages_received += 1

        # Validate message
        if message.is_expired():
            logger.debug(f"Received expired message: {message.message_id}")
            return None

        if message.receiver_id and message.receiver_id != self.instance_id:
            logger.debug(f"Message not for this instance: {message.receiver_id}")
            return None

        # Handle message
        handler = self.message_handlers.get(message.message_type)
        if handler:
            try:
                response = await handler(message, peer_connection)
                if response:
                    response.receiver_id = message.sender_id
                    response.sender_id = self.instance_id
                    self.messages_sent += 1
                return response
            except Exception as e:
                logger.error(f"Error handling message {message.message_type}: {e}")
                return self._create_error_response(message, str(e))
        else:
            logger.warning(f"Unknown message type: {message.message_type}")
            return self._create_error_response(
                message, f"Unknown message type: {message.message_type}"
            )

    async def handle_skill_request(
        self, message: PeerMessage, peer_connection=None
    ) -> Optional[PeerMessage]:
        """Handle a request for a specific skill."""
        skill_name = message.payload.get("skill_name")
        if not skill_name:
            return self._create_error_response(message, "Missing skill_name in request")

        self.skills_requested += 1

        # Get skill from registry
        skill = await self.registry.get_skill(skill_name)

        if skill and self._validate_skill_quality(skill):
            # Send skill back
            response = PeerMessage(
                message_type="skill_response", payload={"skill": skill.to_dict(), "found": True}
            )
            logger.debug(f"Sending skill '{skill_name}' to peer {message.sender_id}")
            return response
        else:
            # Skill not found or not good enough
            response = PeerMessage(
                message_type="skill_response",
                payload={
                    "skill_name": skill_name,
                    "found": False,
                    "reason": "not_found_or_low_quality",
                },
            )
            return response

    async def handle_skill_broadcast(
        self, message: PeerMessage, peer_connection=None
    ) -> Optional[PeerMessage]:
        """Handle a skill broadcast from a peer."""
        skill_data = message.payload.get("skill")
        if not skill_data:
            return self._create_error_response(message, "Missing skill in broadcast")

        try:
            skill = LearnedSkill.from_dict(skill_data)

            # Validate quality before accepting
            if self._validate_skill_quality(skill):
                # Register the skill
                await self.registry._register_peer_skill(skill, message.sender_id)
                self.skills_shared += 1

                logger.debug(
                    f"Accepted broadcasted skill '{skill.name}' from peer {message.sender_id}"
                )

                # Send acknowledgment
                return PeerMessage(
                    message_type="skill_ack", payload={"skill_name": skill.name, "accepted": True}
                )
            else:
                # Reject low-quality skill
                return PeerMessage(
                    message_type="skill_ack",
                    payload={"skill_name": skill.name, "accepted": False, "reason": "low_quality"},
                )

        except Exception as e:
            logger.error(f"Error processing skill broadcast: {e}")
            return self._create_error_response(message, f"Invalid skill data: {str(e)}")

    async def handle_skill_response(self, message: PeerMessage, peer_connection=None) -> None:
        """Handle a response to a skill request."""
        message_id = message.payload.get("original_message_id")
        if message_id and message_id in self.pending_requests:
            future = self.pending_requests.pop(message_id)

            if message.payload.get("found"):
                skill_data = message.payload["skill"]
                skill = LearnedSkill.from_dict(skill_data)
                future.set_result(skill)
            else:
                future.set_result(None)
        else:
            logger.debug(f"No pending request for message {message_id}")

    async def handle_heartbeat(
        self, message: PeerMessage, peer_connection=None
    ) -> Optional[PeerMessage]:
        """Handle heartbeat message."""
        # Update peer liveness in discovery service
        if hasattr(self.registry, "discovery_service") and self.registry.discovery_service:
            # This would update the peer's last_seen timestamp
            pass

        # Respond with heartbeat ack
        return PeerMessage(
            message_type="heartbeat_ack",
            payload={"status": "alive", "instance_id": self.instance_id},
        )

    async def handle_ping(
        self, message: PeerMessage, peer_connection=None
    ) -> Optional[PeerMessage]:
        """Handle ping message."""
        return PeerMessage(
            message_type="pong", payload={"timestamp": message.timestamp.isoformat()}
        )

    async def handle_pong(self, message: PeerMessage, peer_connection=None) -> None:
        """Handle pong response."""
        # Update latency measurements, etc.
        pass

    def _validate_skill_quality(self, skill: LearnedSkill) -> bool:
        """Validate if a skill meets quality standards."""
        # Basic quality checks
        if skill.success_rate < 0.6:  # Minimum 60% success rate
            return False

        if len(skill.procedure_steps) < 2:  # Must have at least 2 steps
            return False

        if not skill.description or len(skill.description.strip()) < 10:
            return False

        return True

    def _create_error_response(self, original_message: PeerMessage, error: str) -> PeerMessage:
        """Create an error response message."""
        return PeerMessage(
            message_type="error",
            payload={"original_message_id": original_message.message_id, "error": error},
        )

    async def request_skill_from_peer(
        self, peer_id: str, skill_name: str, timeout: float = 10.0
    ) -> Optional[LearnedSkill]:
        """Request a specific skill from a peer."""
        message = PeerMessage(
            message_type="skill_request", receiver_id=peer_id, payload={"skill_name": skill_name}
        )

        # Create future for response
        future = asyncio.Future()
        self.pending_requests[message.message_id] = future

        try:
            # Send message (this would be implemented by the transport layer)
            await self._send_message_to_peer(peer_id, message)

            # Wait for response
            skill = await asyncio.wait_for(future, timeout=timeout)
            return skill

        except asyncio.TimeoutError:
            logger.debug(f"Timeout waiting for skill '{skill_name}' from peer {peer_id}")
            return None
        finally:
            # Clean up pending request
            self.pending_requests.pop(message.message_id, None)

    async def broadcast_skill_to_peers(self, skill: LearnedSkill, peer_ids: List[str]) -> int:
        """Broadcast a skill to multiple peers."""
        if not peer_ids:
            return 0

        message = PeerMessage(message_type="skill_broadcast", payload={"skill": skill.to_dict()})

        # Send to all peers concurrently
        tasks = [self._send_message_to_peer(peer_id, message) for peer_id in peer_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.debug(f"Broadcasted skill '{skill.name}' to {success_count}/{len(peer_ids)} peers")

        return success_count

    async def send_heartbeat_to_peer(self, peer_id: str) -> bool:
        """Send heartbeat to a specific peer."""
        message = PeerMessage(
            message_type="heartbeat",
            receiver_id=peer_id,
            payload={"status": "alive", "skills_count": len(self.registry.learned_skills)},
        )

        try:
            await self._send_message_to_peer(peer_id, message)
            return True
        except Exception as e:
            logger.debug(f"Failed to send heartbeat to peer {peer_id}: {e}")
            return False

    async def _send_message_to_peer(self, peer_id: str, message: PeerMessage) -> None:
        """
        Send a message to a peer.

        This is a placeholder - actual implementation would use the transport layer
        (HTTP, WebSocket, etc.) configured in the discovery service.
        """
        # This would be implemented by the actual transport mechanism
        # For now, it's a placeholder that assumes messages are sent via
        # the discovery service's HTTP client

        if hasattr(self.registry, "discovery_service") and self.registry.discovery_service:
            # Use discovery service to send message
            # This is transport-layer specific and would be implemented
            # based on the chosen communication protocol (HTTP, WebSocket, etc.)
            pass
        else:
            logger.warning(f"No transport available to send message to peer {peer_id}")

    def get_protocol_stats(self) -> Dict[str, Any]:
        """Get protocol statistics."""
        return {
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "skills_shared": self.skills_shared,
            "skills_requested": self.skills_requested,
            "pending_requests": len(self.pending_requests),
            "active_connections": len(self.active_connections),
        }

    async def cleanup_expired_requests(self):
        """Clean up expired pending requests."""
        expired_ids = []
        for message_id, future in self.pending_requests.items():
            if future.done():
                expired_ids.append(message_id)

        for message_id in expired_ids:
            del self.pending_requests[message_id]

        if expired_ids:
            logger.debug(f"Cleaned up {len(expired_ids)} expired requests")
