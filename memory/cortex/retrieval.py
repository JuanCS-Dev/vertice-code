"""
Active Retrieval - MIRIX context injection system.

Implements topic-based memory retrieval across all memory types
for automatic context injection into LLM prompts.
"""

from __future__ import annotations

from typing import Any, Dict, List, Protocol


class MemorySubsystem(Protocol):
    """Protocol for memory subsystems that support search."""

    def search(self, query: str, limit: int = 5) -> List[Any]: ...


class CoreMemoryProtocol(Protocol):
    """Protocol for core memory."""

    def get_persona(self) -> Dict[str, Any]: ...
    def to_context_string(self) -> str: ...


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

    def retrieve(
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
        results: Dict[str, List[Dict[str, Any]]] = {}

        # Core memory (always include)
        results["core"] = [self.core.get_persona()]

        # Episodic memory
        episodic_results = self.episodic.search(query=query, limit=limit_per_type)
        if episodic_results:
            results["episodic"] = episodic_results

        # Semantic memory
        semantic_results = self.semantic.search(query=query, limit=limit_per_type)
        if semantic_results:
            results["semantic"] = semantic_results

        # Procedural memory
        proc_results = self.procedural.search(query=query, limit=limit_per_type)
        if proc_results:
            results["procedural"] = [
                p.to_dict() if hasattr(p, "to_dict") else p for p in proc_results
            ]

        # Resource memory
        resource_results = self.resource.search(query=query, limit=limit_per_type)
        if resource_results:
            results["resource"] = [
                r.to_dict() if hasattr(r, "to_dict") else r for r in resource_results
            ]

        return results

    def to_context_prompt(self, query: str) -> str:
        """
        Generate context string for LLM prompt injection.

        Uses Active Retrieval to gather relevant context and
        formats it for system prompt inclusion.

        Args:
            query: Current topic or user input.

        Returns:
            Formatted context string with XML tags.
        """
        retrieved = self.retrieve(query)
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
