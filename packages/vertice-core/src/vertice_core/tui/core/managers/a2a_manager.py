"""
A2A Manager - Agent-to-Agent Protocol integration for TUI.

Commands:
- /a2a status: Server state
- /a2a serve [port]: Start gRPC server
- /a2a stop: Stop server
- /a2a discover: Discover agents on network
- /a2a call <agent> <task>: Send task to remote agent
- /a2a card: Show local AgentCard
- /a2a sign <key>: Sign AgentCard with JWS

Follows CODE_CONSTITUTION: <500 lines, 100% type hints
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from typing import Any, AsyncIterator, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from vertice_core.a2a.agent_card import AgentCard

logger = logging.getLogger(__name__)


# =============================================================================
# STATE DATACLASSES
# =============================================================================


@dataclass
class A2AServerState:
    """State of the local A2A gRPC server."""

    running: bool = False
    port: int = 50051
    host: str = "0.0.0.0"
    agent_card_name: str = ""
    active_tasks: int = 0
    total_tasks_processed: int = 0
    error: Optional[str] = None


@dataclass
class DiscoveredAgent:
    """Information about a discovered remote agent."""

    agent_id: str
    name: str
    version: str
    url: str
    description: str = ""
    capabilities: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    last_seen: Optional[str] = None


# =============================================================================
# A2A MANAGER
# =============================================================================


class A2AManager:
    """
    Manages A2A protocol operations for TUI.

    Provides:
    - Start/stop local gRPC server
    - Agent discovery (network scan)
    - Remote task execution
    - AgentCard management

    Example:
        manager = A2AManager()
        await manager.start_server(agent_name="vertice-vertice_core.tui", port=50051)
        agents = await manager.discover_agents()
        async for chunk in manager.call_agent("remote-agent", "Analyze code"):
            print(chunk, end='')
    """

    def __init__(self) -> None:
        """Initialize A2A manager."""
        self._server: Optional[Any] = None
        self._server_state = A2AServerState()
        self._discovered_agents: Dict[str, DiscoveredAgent] = {}
        self._local_agent_card: Optional["AgentCard"] = None
        self._task_counter: int = 0

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self) -> Dict[str, Any]:
        """
        Get A2A server and discovery status.

        Returns:
            Status dict with server and agent info
        """
        return {
            "server": asdict(self._server_state),
            "discovered_agents": len(self._discovered_agents),
            "local_card": self._local_agent_card is not None,
        }

    def is_running(self) -> bool:
        """Check if server is running."""
        return self._server_state.running

    # =========================================================================
    # SERVER MANAGEMENT
    # =========================================================================

    async def start_server(
        self,
        agent_name: str = "vertice-vertice_core.tui",
        port: int = 50051,
    ) -> Dict[str, Any]:
        """
        Start the A2A gRPC server.

        Args:
            agent_name: Name for local agent
            port: Port to listen on

        Returns:
            Result dict with success status
        """
        if self._server_state.running:
            return {"success": False, "error": "Server already running"}

        try:
            # Lazy import to avoid dependency issues
            from vertice_core.a2a.grpc_server import create_grpc_server
            from vertice_core.a2a.proto import (
                AgentCard as AgentCardProto,
                AgentCapabilities as AgentCapabilitiesProto,
            )

            # Create local agent card using protobuf types
            capabilities = AgentCapabilitiesProto(
                streaming=True,
                push_notifications=False,
                state_transition_history=True,
            )

            proto_card = AgentCardProto(
                agent_id=f"vertice-{agent_name}",
                name=agent_name,
                description="Vertice TUI Agent",
                version="1.0.0",
                provider="vertice",
                capabilities=capabilities,
            )
            # Store as dataclass for local use
            from vertice_core.a2a.agent_card import AgentCard
            from vertice_core.a2a.types import AgentCapabilities

            self._local_agent_card = AgentCard(
                agent_id=proto_card.agent_id,
                name=proto_card.name,
                description=proto_card.description,
                version=proto_card.version,
                provider=proto_card.provider,
                url=f"grpc://localhost:{port}",
                capabilities=AgentCapabilities(
                    streaming=True,
                    push_notifications=False,
                    state_transition_history=True,
                ),
            )

            # Create and start server with protobuf card
            self._server = await create_grpc_server(
                agent_card=proto_card,
                port=port,
            )
            await self._server.start()

            # Update state
            self._server_state.running = True
            self._server_state.port = port
            self._server_state.agent_card_name = agent_name
            self._server_state.error = None

            logger.info(f"A2A server started on port {port}")
            return {
                "success": True,
                "port": port,
                "agent_name": agent_name,
            }

        except ImportError as e:
            error_msg = f"A2A/gRPC dependencies not installed: {e}"
            self._server_state.error = error_msg
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        except Exception as e:
            error_msg = f"Failed to start A2A server: {e}"
            self._server_state.error = error_msg
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    async def stop_server(self) -> Dict[str, Any]:
        """
        Stop the A2A gRPC server.

        Returns:
            Result dict with success status
        """
        if not self._server_state.running:
            return {"success": False, "error": "Server not running"}

        try:
            if self._server is not None:
                await self._server.stop(grace=5.0)

            self._server = None
            self._server_state.running = False
            self._server_state.error = None

            logger.info("A2A server stopped")
            return {"success": True}

        except Exception as e:
            error_msg = f"Error stopping server: {e}"
            self._server_state.error = error_msg
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    # =========================================================================
    # AGENT DISCOVERY
    # =========================================================================

    async def discover_agents(
        self,
        network_range: str = "localhost",
        timeout: float = 5.0,
    ) -> List[DiscoveredAgent]:
        """
        Discover A2A agents on the network.

        Args:
            network_range: Network to scan (currently only localhost)
            timeout: Discovery timeout in seconds

        Returns:
            List of discovered agents
        """
        # Placeholder: In production, this would:
        # 1. Check well-known URLs (/.well-known/agent.json)
        # 2. Use mDNS/DNS-SD for local discovery
        # 3. Query configured registries

        # For now, check localhost on common ports
        common_ports = [50051, 50052, 50053]

        for port in common_ports:
            try:
                # Placeholder: actual discovery would fetch agent card
                # via HTTP GET /.well-known/agent.json
                pass
            except Exception as e:
                logger.debug(f"A2A discovery failed on port {port}: {e}")
                continue

        # Return cached discoveries
        return list(self._discovered_agents.values())

    def add_discovered_agent(self, agent: DiscoveredAgent) -> None:
        """Add agent to discovery cache."""
        self._discovered_agents[agent.agent_id] = agent

    def get_discovered_agents(self) -> List[Dict[str, Any]]:
        """Get list of discovered agents as dicts."""
        return [asdict(agent) for agent in self._discovered_agents.values()]

    def get_agent(self, agent_id: str) -> Optional[DiscoveredAgent]:
        """Get specific discovered agent."""
        return self._discovered_agents.get(agent_id)

    def clear_discoveries(self) -> None:
        """Clear discovery cache."""
        self._discovered_agents.clear()

    # =========================================================================
    # REMOTE TASK EXECUTION
    # =========================================================================

    async def call_agent(
        self,
        agent_id: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """
        Send task to remote agent and stream response.

        Args:
            agent_id: ID of discovered agent
            task: Task description
            context: Optional context dict

        Yields:
            Response chunks from remote agent
        """
        agent = self._discovered_agents.get(agent_id)
        if agent is None:
            yield f"Agent '{agent_id}' not found. Run /a2a discover first.\n"
            return

        try:
            import grpc

            # Parse URL to get host:port
            url = agent.url.replace("grpc://", "")

            yield f"[A2A] Connecting to {agent.name} at {url}...\n"

            async with grpc.aio.insecure_channel(url):
                # Placeholder: actual gRPC call
                yield f"[A2A] Sending task to {agent.name}...\n"

                # Increment task counter
                self._task_counter += 1
                self._server_state.active_tasks += 1

                try:
                    # In production, this would:
                    # 1. Create A2AServiceStub
                    # 2. Call Execute with Task proto
                    # 3. Stream response chunks
                    yield "[A2A] Task sent. Waiting for response...\n"
                    yield "[A2A] Note: Full gRPC client not yet implemented.\n"
                finally:
                    self._server_state.active_tasks -= 1

        except ImportError as e:
            yield f"[A2A] gRPC not available: {e}\n"

        except Exception as e:
            yield f"[A2A] Error calling agent: {e}\n"

    # =========================================================================
    # AGENT CARD MANAGEMENT
    # =========================================================================

    def get_local_card(self) -> Optional[Dict[str, Any]]:
        """Get local agent card as dict."""
        if self._local_agent_card is not None:
            return self._local_agent_card.to_dict()
        return None

    async def sign_card(self, private_key_path: str) -> Dict[str, Any]:
        """
        Sign the local agent card with JWS.

        Args:
            private_key_path: Path to private key file (PEM format)

        Returns:
            Result dict with signed card
        """
        if self._local_agent_card is None:
            return {"success": False, "error": "No local card. Start server first."}

        try:
            from vertice_core.security.jws import JWSSigner, KeyPair, JWSAlgorithm

            # Read private key PEM from file
            with open(private_key_path, "rb") as f:
                private_pem = f.read()

            # Extract public key from private key
            from cryptography.hazmat.primitives import serialization
            from cryptography.hazmat.backends import default_backend

            private_key = serialization.load_pem_private_key(
                private_pem, password=None, backend=default_backend()
            )
            public_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )

            # Create KeyPair for JWSSigner
            keypair = KeyPair(
                private_key=private_pem,
                public_key=public_pem,
                key_id=f"a2a-{self._local_agent_card.agent_id}",
                algorithm=JWSAlgorithm.RS256,  # Default to RS256
            )

            # Sign card
            signer = JWSSigner(keypair)
            card_dict = self._local_agent_card.to_dict()
            signature = signer.sign_agent_card(card_dict)

            logger.info("Agent card signed with JWS")
            return {
                "success": True,
                "signature": {
                    "protected": signature.protected,
                    "signature": signature.signature,
                },
            }

        except ImportError as e:
            return {"success": False, "error": f"JWS dependencies not available: {e}"}

        except FileNotFoundError:
            return {"success": False, "error": f"Key file not found: {private_key_path}"}

        except Exception as e:
            return {"success": False, "error": f"Failed to sign card: {e}"}
