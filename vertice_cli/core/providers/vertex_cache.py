"""
Vertex AI Context Caching Manager.

SCALE & SUSTAIN Phase 3 - Explicit Context Caching.

Provides:
- Create cached content for large contexts
- TTL management (update, extend, delete)
- Integration with stream_chat()

References:
- https://ai.google.dev/gemini-api/docs/caching
- https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache

Author: Vertice Team
Date: 2026-01-02
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Minimum token requirements by model
MIN_TOKENS = {
    "gemini-3-pro-preview": 4096,
    "gemini-3-flash-preview": 1024,
    "gemini-2.5-flash": 1024,
    "gemini-2.5-pro": 4096,
    "gemini-2.0-flash": 1024,
    "default": 2048,
}


class VertexCacheManager:
    """
    Manager for Vertex AI explicit context caching.

    Provides 90% cost reduction for cached tokens in subsequent requests.
    Caches require minimum 2048 tokens and have configurable TTL.

    Usage:
        manager = VertexCacheManager(project="my-project")
        cache_name = manager.create_cache(
            name="codebase-context",
            content=large_codebase_content,
            system_instruction="You are a code assistant.",
            ttl_seconds=3600
        )

        # Use with VertexAIProvider
        async for chunk in provider.stream_chat(
            messages,
            cached_content=cache_name
        ):
            print(chunk)

        # Cleanup
        manager.delete_cache("codebase-context")
    """

    def __init__(
        self,
        project: Optional[str] = None,
        location: str = "us-central1",
        model: str = "gemini-2.0-flash",
    ):
        """Initialize cache manager.

        Args:
            project: GCP project ID (defaults to GOOGLE_CLOUD_PROJECT env var)
            location: Vertex AI location
            model: Default model for cache creation
        """
        self.project = project or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location
        self.model = model
        self._client: Optional[Any] = None
        self._caches: Dict[str, Any] = {}

    def _ensure_client(self) -> None:
        """Lazy initialize the Gen AI client."""
        if self._client is None:
            try:
                from google import genai
                from google.genai.types import HttpOptions

                self._client = genai.Client(
                    vertexai=True,
                    project=self.project,
                    location=self.location,
                    http_options=HttpOptions(api_version="v1"),
                )
                logger.info(f"Gen AI cache client initialized for {self.project}")
            except ImportError:
                logger.error("google-genai not installed. Run: pip install google-genai")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize cache client: {e}")
                raise

    def _estimate_tokens(self, content: str) -> int:
        """Estimate token count (roughly 4 chars per token)."""
        return len(content) // 4

    def _get_min_tokens(self) -> int:
        """Get minimum tokens for current model."""
        return MIN_TOKENS.get(self.model, MIN_TOKENS["default"])

    def create_cache(
        self,
        name: str,
        content: str,
        system_instruction: Optional[str] = None,
        ttl_seconds: int = 3600,
    ) -> str:
        """Create explicit cache for large context.

        Args:
            name: Display name for the cache
            content: Large context to cache (must be >= 2048 tokens)
            system_instruction: Optional system instruction
            ttl_seconds: Time-to-live in seconds (default 1 hour)

        Returns:
            Cache resource name for use with stream_chat()

        Raises:
            ValueError: If content has fewer than minimum tokens
        """
        # Validate minimum tokens
        estimated_tokens = self._estimate_tokens(content)
        min_tokens = self._get_min_tokens()

        if estimated_tokens < min_tokens:
            raise ValueError(
                f"Content has ~{estimated_tokens} tokens, but minimum is {min_tokens} tokens for caching. "
                f"Add more context to enable caching."
            )

        self._ensure_client()

        try:
            from google.genai.types import CreateCachedContentConfig

            config = CreateCachedContentConfig(
                display_name=name,
                contents=[content],
                ttl=f"{ttl_seconds}s",
            )

            if system_instruction:
                config.system_instruction = system_instruction

            cache = self._client.caches.create(model=self.model, config=config)

            # Store cache reference
            self._caches[name] = cache
            logger.info(f"Cache created: {name} ({estimated_tokens} tokens, TTL={ttl_seconds}s)")

            return cache.name

        except Exception as e:
            logger.error(f"Failed to create cache {name}: {e}")
            raise

    def get_cache(self, name: str) -> Optional[Any]:
        """Retrieve cache by display name.

        Args:
            name: Display name of the cache

        Returns:
            CachedContent object or None if not found
        """
        return self._caches.get(name)

    def list_caches(self) -> List[str]:
        """List all active cache names.

        Returns:
            List of cache display names
        """
        return list(self._caches.keys())

    def extend_ttl(self, name: str, additional_seconds: int) -> None:
        """Extend cache TTL.

        Args:
            name: Display name of the cache
            additional_seconds: Additional seconds to add to TTL
        """
        cache = self._caches.get(name)
        if not cache:
            logger.warning(f"Cache not found: {name}")
            return

        try:
            self._ensure_client()
            from google.genai.types import UpdateCachedContentConfig

            self._client.caches.update(
                name=cache.name, config=UpdateCachedContentConfig(ttl=f"{additional_seconds}s")
            )
            logger.info(f"Cache TTL extended: {name} (+{additional_seconds}s)")

        except Exception as e:
            logger.error(f"Failed to extend TTL for {name}: {e}")

    def delete_cache(self, name: str) -> None:
        """Delete cache.

        Args:
            name: Display name of the cache
        """
        cache = self._caches.pop(name, None)
        if not cache:
            logger.debug(f"Cache not found for deletion: {name}")
            return

        try:
            self._ensure_client()
            self._client.caches.delete(cache.name)
            logger.info(f"Cache deleted: {name}")

        except Exception as e:
            logger.error(f"Failed to delete cache {name}: {e}")

    def get_cache_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get cache information.

        Args:
            name: Display name of the cache

        Returns:
            Dict with cache info or None if not found
        """
        cache = self._caches.get(name)
        if not cache:
            return None

        return {
            "name": name,
            "resource_name": cache.name,
            "model": self.model,
            "project": self.project,
            "location": self.location,
        }
