"""
Caching Module - Semantic caching for LLM responses.

Provides:
- SemanticCache: Vector similarity-based caching
- ExactCache: Traditional exact-match caching
- CachingMixin: Agent integration mixin

References:
- GPTCache: Semantic cache for LLMs
- MeanCache: User-centric semantic caching (arXiv:2403.02694)
- GenerativeCache: Generative caching system (arXiv:2503.17603)
"""

from __future__ import annotations

from .types import (
    CacheConfig,
    CacheEntry,
    CacheStats,
    CacheHit,
    CacheMiss,
)
from .exact import ExactCache
from .semantic import SemanticCache
from .mixin import CachingMixin

__all__ = [
    # Types
    "CacheConfig",
    "CacheEntry",
    "CacheStats",
    "CacheHit",
    "CacheMiss",
    # Caches
    "ExactCache",
    "SemanticCache",
    # Mixin
    "CachingMixin",
]
