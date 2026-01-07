"""
Prometheus Distributed Evolution - Skills Sharing Across Instances

This module implements peer-to-peer skills sharing between Prometheus instances,
enabling collective learning and evolution across distributed agents.

Created with love for the Prometheus ecosystem.
May 2026 - JuanCS Dev & Claude Opus 4.5
"""

import asyncio
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import aiohttp

from prometheus.skills.registry import LearnedSkill, PrometheusSkillsRegistry

logger = logging.getLogger(__name__)


@dataclass
class PeerInfo:
    """Information about a discovered peer instance."""

    instance_id: str
    endpoint: str  # http://host:port
    last_seen: datetime = field(default_factory=datetime.now)
    skills_count: int = 0
    version: str = "1.0.0"
    capabilities: Set[str] = field(default_factory=set)

    def is_alive(self, timeout_minutes: int = 5) -> bool:
        """Check if peer is considered alive."""
        return (datetime.now() - self.last_seen) < timedelta(minutes=timeout_minutes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "endpoint": self.endpoint,
            "last_seen": self.last_seen.isoformat(),
            "skills_count": self.skills_count,
            "version": self.version,
            "capabilities": list(self.capabilities),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PeerInfo":
        return cls(
            instance_id=data["instance_id"],
            endpoint=data["endpoint"],
            last_seen=datetime.fromisoformat(data["last_seen"]),
            skills_count=data.get("skills_count", 0),
            version=data.get("version", "1.0.0"),
            capabilities=set(data.get("capabilities", [])),
        )


class SkillsDiscoveryService:
    """
    Service for discovering and managing peer Prometheus instances.

    This service enables peer-to-peer communication between Prometheus instances,
    allowing them to share learned skills and collectively evolve.
    """

    def __init__(
        self,
        instance_id: str,
        listen_port: int = 8080,
        discovery_endpoints: Optional[List[str]] = None,
        heartbeat_interval: int = 30,
    ):
        self.instance_id = instance_id
        self.listen_port = listen_port
        self.discovery_endpoints = discovery_endpoints or []
        self.heartbeat_interval = heartbeat_interval

        # Peer management
        self.known_peers: Dict[str, PeerInfo] = {}
        self.peer_skills_cache: Dict[str, List[LearnedSkill]] = {}

        # HTTP client for peer communication
        self.session: Optional[aiohttp.ClientSession] = None

        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._discovery_task: Optional[asyncio.Task] = None

        # Configuration
        self.max_peers = 50  # Limit peer connections for stability
        self.peer_timeout = 10  # seconds for peer requests
        self.discovery_interval = 60  # seconds between discovery attempts

    async def start(self):
        """Start the discovery service and background tasks."""
        logger.info(f"Starting Skills Discovery Service for instance {self.instance_id}")

        # Create HTTP session
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.peer_timeout))

        # Start background tasks
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        self._discovery_task = asyncio.create_task(self._discovery_loop())

        logger.info(f"Skills Discovery Service started on port {self.listen_port}")

    async def stop(self):
        """Stop the discovery service and cleanup."""
        logger.info("Stopping Skills Discovery Service...")

        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass

        # Close HTTP session
        if self.session:
            await self.session.close()

        logger.info("Skills Discovery Service stopped")

    async def register_instance(self, skills_registry: PrometheusSkillsRegistry) -> str:
        """
        Register this instance with discovery endpoints.

        Returns the instance endpoint URL.
        """
        instance_endpoint = f"http://localhost:{self.listen_port}"

        # Register with discovery endpoints
        for endpoint in self.discovery_endpoints:
            try:
                await self._register_with_discovery_endpoint(endpoint, instance_endpoint)
            except Exception as e:
                logger.warning(f"Failed to register with discovery endpoint {endpoint}: {e}")

        # Create peer info for self
        self_peer = PeerInfo(
            instance_id=self.instance_id,
            endpoint=instance_endpoint,
            skills_count=len(skills_registry.learned_skills) if skills_registry else 0,
            capabilities={"skills_sharing", "evolution_sync"},
        )

        # Add self to known peers
        self.known_peers[self.instance_id] = self_peer

        logger.info(f"Instance {self.instance_id} registered at {instance_endpoint}")
        return instance_endpoint

    async def discover_peers(self) -> List[str]:
        """Discover available peer instances."""
        alive_peers = [
            peer.instance_id
            for peer in self.known_peers.values()
            if peer.is_alive() and peer.instance_id != self.instance_id
        ]
        return alive_peers

    async def get_peer_skills(self, peer_id: str) -> List[LearnedSkill]:
        """Get skills from a specific peer."""
        if peer_id not in self.known_peers:
            raise ValueError(f"Unknown peer: {peer_id}")

        peer = self.known_peers[peer_id]
        if not peer.is_alive():
            raise ValueError(f"Peer {peer_id} is not alive")

        # Check cache first
        if peer_id in self.peer_skills_cache:
            cache_time = getattr(self, f"_cache_time_{peer_id}", None)
            if cache_time and (datetime.now() - cache_time) < timedelta(minutes=5):
                return self.peer_skills_cache[peer_id]

        # Fetch from peer
        try:
            skills = await self._fetch_peer_skills(peer.endpoint)
            self.peer_skills_cache[peer_id] = skills
            setattr(self, f"_cache_time_{peer_id}", datetime.now())
            return skills
        except Exception as e:
            logger.warning(f"Failed to fetch skills from peer {peer_id}: {e}")
            # Return cached version if available
            return self.peer_skills_cache.get(peer_id, [])

    async def broadcast_skill(self, skill: LearnedSkill):
        """Broadcast a learned skill to all known peers."""
        if not self.session:
            return

        alive_peers = [
            p
            for p in self.known_peers.values()
            if p.is_alive() and p.instance_id != self.instance_id
        ]

        if not alive_peers:
            logger.debug("No alive peers to broadcast skill to")
            return

        # Broadcast to peers concurrently
        tasks = [self._send_skill_to_peer(peer.endpoint, skill) for peer in alive_peers]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if not isinstance(r, Exception))
        logger.info(f"Broadcasted skill '{skill.name}' to {success_count}/{len(alive_peers)} peers")

    async def request_skill(self, skill_name: str, peer_id: str) -> Optional[LearnedSkill]:
        """Request a specific skill from a peer."""
        if peer_id not in self.known_peers:
            return None

        peer = self.known_peers[peer_id]
        if not peer.is_alive():
            return None

        try:
            return await self._request_skill_from_peer(peer.endpoint, skill_name)
        except Exception as e:
            logger.warning(f"Failed to request skill '{skill_name}' from peer {peer_id}: {e}")
            return None

    async def _register_with_discovery_endpoint(
        self, discovery_endpoint: str, instance_endpoint: str
    ):
        """Register instance with a discovery endpoint."""
        if not self.session:
            return

        registration_data = {
            "instance_id": self.instance_id,
            "endpoint": instance_endpoint,
            "version": "1.0.0",
            "capabilities": ["skills_sharing", "evolution_sync"],
        }

        try:
            async with self.session.post(
                f"{discovery_endpoint}/register",
                json=registration_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 200:
                    logger.debug(
                        f"Successfully registered with discovery endpoint {discovery_endpoint}"
                    )
                else:
                    logger.warning(f"Registration failed with status {response.status}")
        except Exception as e:
            logger.error(f"Error registering with discovery endpoint: {e}")

    async def _heartbeat_loop(self):
        """Background task for sending heartbeats to peers."""
        while True:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(self.heartbeat_interval)

    async def _discovery_loop(self):
        """Background task for discovering new peers."""
        while True:
            try:
                await self._discover_new_peers()
                await asyncio.sleep(self.discovery_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}")
                await asyncio.sleep(self.discovery_interval)

    async def _send_heartbeat(self):
        """Send heartbeat to all known peers."""
        if not self.session:
            return

        alive_peers = [
            p
            for p in self.known_peers.values()
            if p.is_alive() and p.instance_id != self.instance_id
        ]

        if not alive_peers:
            return

        heartbeat_data = {
            "instance_id": self.instance_id,
            "timestamp": datetime.now().isoformat(),
            "status": "alive",
        }

        tasks = [
            self._send_heartbeat_to_peer(peer.endpoint, heartbeat_data) for peer in alive_peers
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    async def _discover_new_peers(self):
        """Discover new peers from discovery endpoints."""
        if not self.session:
            return

        for endpoint in self.discovery_endpoints:
            try:
                async with self.session.get(f"{endpoint}/peers") as response:
                    if response.status == 200:
                        peers_data = await response.json()
                        await self._process_discovered_peers(peers_data)
            except Exception as e:
                logger.debug(f"Failed to discover peers from {endpoint}: {e}")

    async def _process_discovered_peers(self, peers_data: List[Dict[str, Any]]):
        """Process list of discovered peers."""
        for peer_data in peers_data:
            try:
                peer_info = PeerInfo.from_dict(peer_data)

                # Skip self
                if peer_info.instance_id == self.instance_id:
                    continue

                # Add or update peer
                if peer_info.instance_id not in self.known_peers:
                    logger.info(
                        f"Discovered new peer: {peer_info.instance_id} at {peer_info.endpoint}"
                    )
                else:
                    # Update existing peer info
                    existing = self.known_peers[peer_info.instance_id]
                    existing.last_seen = peer_info.last_seen
                    existing.skills_count = peer_info.skills_count

                self.known_peers[peer_info.instance_id] = peer_info

            except Exception as e:
                logger.warning(f"Failed to process peer data {peer_data}: {e}")

        # Limit peer count
        if len(self.known_peers) > self.max_peers:
            # Remove oldest peers
            sorted_peers = sorted(self.known_peers.items(), key=lambda x: x[1].last_seen)
            to_remove = sorted_peers[: len(self.known_peers) - self.max_peers]
            for peer_id, _ in to_remove:
                del self.known_peers[peer_id]

    async def _fetch_peer_skills(self, peer_endpoint: str) -> List[LearnedSkill]:
        """Fetch skills list from a peer."""
        if not self.session:
            return []

        try:
            async with self.session.get(f"{peer_endpoint}/skills") as response:
                if response.status == 200:
                    skills_data = await response.json()
                    return [LearnedSkill.from_dict(s) for s in skills_data]
                else:
                    logger.warning(
                        f"Failed to fetch skills from {peer_endpoint}: HTTP {response.status}"
                    )
                    return []
        except Exception as e:
            logger.error(f"Error fetching skills from {peer_endpoint}: {e}")
            return []

    async def _send_skill_to_peer(self, peer_endpoint: str, skill: LearnedSkill):
        """Send a skill to a peer."""
        if not self.session:
            return

        try:
            async with self.session.post(
                f"{peer_endpoint}/skills/broadcast",
                json=skill.to_dict(),
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status not in (200, 201):
                    logger.debug(
                        f"Peer {peer_endpoint} rejected skill broadcast: HTTP {response.status}"
                    )
        except Exception as e:
            logger.debug(f"Failed to send skill to peer {peer_endpoint}: {e}")

    async def _request_skill_from_peer(
        self, peer_endpoint: str, skill_name: str
    ) -> Optional[LearnedSkill]:
        """Request a specific skill from a peer."""
        if not self.session:
            return None

        try:
            async with self.session.get(f"{peer_endpoint}/skills/{skill_name}") as response:
                if response.status == 200:
                    skill_data = await response.json()
                    return LearnedSkill.from_dict(skill_data)
                elif response.status == 404:
                    return None  # Skill not found
                else:
                    logger.warning(
                        f"Failed to request skill from {peer_endpoint}: HTTP {response.status}"
                    )
                    return None
        except Exception as e:
            logger.error(f"Error requesting skill from {peer_endpoint}: {e}")
            return None

    async def _send_heartbeat_to_peer(self, peer_endpoint: str, heartbeat_data: Dict[str, Any]):
        """Send heartbeat to a specific peer."""
        if not self.session:
            return

        try:
            async with self.session.post(
                f"{peer_endpoint}/heartbeat",
                json=heartbeat_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status not in (200, 201):
                    logger.debug(f"Heartbeat failed to {peer_endpoint}: HTTP {response.status}")
        except Exception as e:
            logger.debug(f"Heartbeat error to {peer_endpoint}: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get discovery service statistics."""
        alive_peers = [p for p in self.known_peers.values() if p.is_alive()]
        dead_peers = [p for p in self.known_peers.values() if not p.is_alive()]

        return {
            "instance_id": self.instance_id,
            "total_peers": len(self.known_peers),
            "alive_peers": len(alive_peers),
            "dead_peers": len(dead_peers),
            "cached_peer_skills": len(self.peer_skills_cache),
            "discovery_endpoints": len(self.discovery_endpoints),
            "heartbeat_interval": self.heartbeat_interval,
            "discovery_interval": self.discovery_interval,
        }
