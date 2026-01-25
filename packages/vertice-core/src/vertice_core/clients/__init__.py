"""
Vertice Clients - Unified LLM Client Layer.

This module provides the VerticeClient, a unified facade for all
LLM providers with automatic failover and FREE FIRST priority.

Example:
    >>> from vertice_core.clients import get_client
    >>> client = get_client()
    >>> async for chunk in client.stream_chat(messages):
    ...     print(chunk, end="")
"""

from .vertice_coreent import (
    VerticeClient,
    VerticeClientConfig,
    VerticeClientError,
    AllProvidersExhaustedError,
    RateLimitError,
    ProviderProtocol,
    get_client,
    DEFAULT_PRIORITY,
)

__all__ = [
    "VerticeClient",
    "VerticeClientConfig",
    "VerticeClientError",
    "AllProvidersExhaustedError",
    "RateLimitError",
    "ProviderProtocol",
    "get_client",
    "DEFAULT_PRIORITY",
]
