"""
A2A Protocol gRPC Server
========================

Factory and exports for A2A gRPC server.

This module provides:
- Server factory function for easy setup
- Re-exports of TaskStore and A2AServiceImpl

Reference:
- A2A Spec: https://a2a-protocol.org/latest/specification/
- gRPC AsyncIO: https://grpc.github.io/grpc/python/grpc_asyncio.html

Example:
    >>> from vertice_core.a2a.grpc_server import create_grpc_server
    >>> server = await create_grpc_server(agent_card, port=50051)
    >>> await server.start()
    >>> await server.wait_for_termination()

Author: JuanCS Dev
Date: 2025-12-30
"""

from __future__ import annotations

import logging
from concurrent import futures
from typing import AsyncIterator, Callable, Optional

import grpc

from .proto import (
    Task,
    StreamChunk,
    AgentCard,
    add_A2AServiceServicer_to_server,
)
from .grpc_task_store import TaskStore
from .grpc_service import A2AServiceImpl

logger = logging.getLogger(__name__)


async def create_grpc_server(
    agent_card: AgentCard,
    task_processor: Optional[Callable[[Task], AsyncIterator[StreamChunk]]] = None,
    port: int = 50051,
    max_workers: int = 10,
) -> grpc.aio.Server:
    """Create and configure gRPC server for A2A protocol.

    Args:
        agent_card: Agent card for discovery
        task_processor: Custom task processor (optional)
        port: Server port (default: 50051)
        max_workers: Maximum worker threads (default: 10)

    Returns:
        Configured gRPC server (not started)

    Example:
        >>> card = AgentCard(name="my-agent", version="1.0.0")
        >>> server = await create_grpc_server(card, port=50051)
        >>> await server.start()
        >>> print("Server running on port 50051")
        >>> await server.wait_for_termination()

    Note:
        The server is returned in a configured but not started state.
        Call `await server.start()` to begin accepting connections.
    """
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=max_workers),
        options=[
            ("grpc.max_send_message_length", 50 * 1024 * 1024),
            ("grpc.max_receive_message_length", 50 * 1024 * 1024),
            ("grpc.keepalive_time_ms", 30000),
            ("grpc.keepalive_timeout_ms", 10000),
        ],
    )

    service = A2AServiceImpl(agent_card, task_processor)
    add_A2AServiceServicer_to_server(service, server)

    server.add_insecure_port(f"[::]:{port}")

    logger.info(f"[A2A] gRPC server configured on port {port}")
    return server


__all__ = [
    "TaskStore",
    "A2AServiceImpl",
    "create_grpc_server",
]
