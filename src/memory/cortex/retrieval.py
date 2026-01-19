"""
Active Retrieval - MIRIX context injection system.

Implements topic-based memory retrieval across all memory types
for automatic context injection into LLM prompts.
"""

from __future__ import annotations
import asyncio
from typing import Any, Coroutine, Dict, List, Protocol
from .timing import timing_decorator


class MemorySubsystem(Protocol):
    """Protocol for memory subsystems that support search."""

    def search(self, query: str, limit: int = 5) -> Coroutine[Any, Any, List[Any]]:
        ...


class CoreMemoryProtocol(Protocol):
    """Protocol for core memory."""

    def get_persona(self) -> Dict[str, Any]:
        ...

    def to_context_string(self) -> str:
        ...


class ActiveRetrieval:
    """
    MIRIX Active Retrieval - Automatic context injection.

    Retrieves relevant entries from ALL memory types based on
    the current query/topic. Results are tagged by source for
    injection into LLM system prompt.
    """

    def __init__(
        self,
        core: CoreMemoryProtocol,
        episodic: MemorySubsystem,
        semantic: MemorySubsystem,
        procedural: MemorySubsystem,
        resource: MemorySubsystem,
    ) -> None:
        self.core = core
        self.episodic = episodic
        self.semantic = semantic
        self.procedural = procedural
        self.resource = resource

    @timing_decorator
    async def retrieve(
        self,
        query: str,
        limit_per_type: int = 5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retrieve relevant context from all memory types.

        Args:
            query: Current topic or user input.
            limit_per_type: Max entries per memory type.

        Returns:
            Dictionary with tagged results from each memory type.
        """
        tasks = {
            "episodic": self.episodic.search(query=query, limit=limit_per_type),
            "semantic": self.semantic.search(query=query, limit=limit_per_type),
            "procedural": self.procedural.search(query=query, limit=limit_per_type),
            "resource": self.resource.search(query=query, limit=limit_per_type),
        }

        search_results = await asyncio.gather(*tasks.values())

        results: Dict[str, List[Dict[str, Any]]] = {}
        results["core"] = [self.core.get_persona()]

        # Process results
        for memory_type, search_result in zip(tasks.keys(), search_results):
            if search_result:
                if memory_type == "procedural" or memory_type == "resource":
                    results[memory_type] = [
                        p.to_dict() if hasattr(p, "to_dict") else p for p in search_result
                    ]
                else:
                    results[memory_type] = search_result

        return results

    async def to_context_prompt(self, query: str) -> str:
        """
        Generate context string for LLM prompt injection.

        Uses Active Retrieval to gather relevant context and
        formats it for system prompt inclusion.

        Args:
            query: Current topic or user input.

        Returns:
            Formatted context string with XML tags.
        """
        retrieved = await self.retrieve(query)
        parts = ["<memory_context>"]

        # Core memory
        if "core" in retrieved:
            parts.append(self.core.to_context_string())

        # Episodic memories
        if "episodic" in retrieved and retrieved["episodic"]:
            parts.append("<episodic_memory>")
            for ep in retrieved["episodic"][:3]:
                timestamp = ep.get("timestamp", "unknown")
                content = ep.get("content", "")[:200]
                parts.append(f"  [{timestamp}] {content}")
            parts.append("</episodic_memory>")

        # Procedural memories
        if "procedural" in retrieved and retrieved["procedural"]:
            parts.append("<procedural_memory>")
            for proc in retrieved["procedural"][:2]:
                description = proc.get("description", "")
                parts.append(f"  Workflow: {description}")
            parts.append("</procedural_memory>")

        # Resource memories
        if "resource" in retrieved and retrieved["resource"]:
            parts.append("<resource_memory>")
            for res in retrieved["resource"][:3]:
                res_type = res.get("resource_type", "unknown")
                title = res.get("title", "")
                summary = res.get("summary", "")[:100]
                parts.append(f"  [{res_type}] {title}: {summary}")
            parts.append("</resource_memory>")

        parts.append("</memory_context>")

        return "\n".join(parts)
