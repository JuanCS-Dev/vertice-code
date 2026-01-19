"""
Mock Builders for MAXIMUS E2E Tests.

Factory pattern for building realistic MAXIMUS mock responses.

Follows CODE_CONSTITUTION: <500 lines, 100% type hints, Google docstrings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class TribunalResponse:
    """Builder for Tribunal evaluation responses.

    Attributes:
        decision: Tribunal decision (PASS, REVIEW, FAIL, CAPITAL).
        consensus_score: Consensus score between judges (0.0-1.0).
        verdicts: Individual judge verdicts.
        reasoning: Combined reasoning from judges.
    """

    decision: str = "PASS"
    consensus_score: float = 0.85
    verdicts: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = "All judges approved the execution."

    def __post_init__(self) -> None:
        """Initialize default verdicts if not provided."""
        if not self.verdicts:
            self.verdicts = {
                "VERITAS": {
                    "vote": "PASS",
                    "confidence": 0.9,
                    "reasoning": "Factually accurate execution.",
                },
                "SOPHIA": {
                    "vote": "PASS",
                    "confidence": 0.85,
                    "reasoning": "Appropriate depth of analysis.",
                },
                "DIKE": {
                    "vote": "PASS",
                    "confidence": 0.8,
                    "reasoning": "Authorized within scope.",
                },
            }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response dict."""
        return {
            "decision": self.decision,
            "consensus_score": self.consensus_score,
            "verdicts": self.verdicts,
            "reasoning": self.reasoning,
            "timestamp": datetime.utcnow().isoformat(),
        }


@dataclass
class MemoryResponse:
    """Builder for Memory service responses.

    Attributes:
        memory_id: Unique memory identifier.
        content: Memory content.
        memory_type: Type of memory (episodic, semantic, etc).
        importance: Importance score (0.0-1.0).
        tags: Memory tags.
    """

    memory_id: str = "mem-001"
    content: str = "Test memory content"
    memory_type: str = "episodic"
    importance: float = 0.7
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response dict."""
        return {
            "id": self.memory_id,
            "content": self.content,
            "memory_type": self.memory_type,
            "importance": self.importance,
            "tags": self.tags or ["test"],
            "timestamp": datetime.utcnow().isoformat(),
            "access_count": 0,
        }


@dataclass
class FactoryResponse:
    """Builder for Tool Factory responses.

    Attributes:
        tool_name: Generated tool name.
        description: Tool description.
        code: Generated code.
        success: Whether generation succeeded.
    """

    tool_name: str = "test_tool"
    description: str = "A test tool for E2E testing"
    code: str = "def test_tool(): return 'Hello from test tool'"
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to API response dict."""
        return {
            "name": self.tool_name,
            "description": self.description,
            "code": self.code,
            "success": self.success,
            "created_at": datetime.utcnow().isoformat(),
        }


class MaximusMockFactory:
    """Factory for creating MAXIMUS mock responses.

    Provides methods to build realistic responses for all MAXIMUS services.
    """

    @staticmethod
    def health_response(status: str = "ok") -> Dict[str, Any]:
        """Build health check response.

        Args:
            status: Health status (ok, degraded, error).

        Returns:
            Health response dict.
        """
        return {
            "status": status,
            "version": "2.0.0",
            "services": {
                "tribunal": "ok",
                "memory": "ok",
                "factory": "ok",
            },
            "mcp_enabled": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def tribunal_evaluate(
        decision: str = "PASS",
        consensus_score: float = 0.85,
    ) -> Dict[str, Any]:
        """Build Tribunal evaluation response.

        Args:
            decision: Tribunal decision.
            consensus_score: Consensus score.

        Returns:
            Tribunal evaluation response.
        """
        return TribunalResponse(
            decision=decision,
            consensus_score=consensus_score,
        ).to_dict()

    @staticmethod
    def tribunal_stats() -> Dict[str, Any]:
        """Build Tribunal statistics response.

        Returns:
            Tribunal stats response.
        """
        return {
            "total_evaluations": 1000,
            "pass_rate": 0.85,
            "review_rate": 0.10,
            "fail_rate": 0.04,
            "capital_rate": 0.01,
            "avg_consensus_score": 0.82,
        }

    @staticmethod
    def memory_store(memory_id: str = "mem-001") -> Dict[str, Any]:
        """Build memory store response.

        Args:
            memory_id: Memory identifier.

        Returns:
            Memory store response.
        """
        return MemoryResponse(memory_id=memory_id).to_dict()

    @staticmethod
    def memory_search(count: int = 3) -> Dict[str, Any]:
        """Build memory search response.

        Args:
            count: Number of memories to return.

        Returns:
            Memory search response.
        """
        memories = [
            MemoryResponse(
                memory_id=f"mem-{i:03d}",
                content=f"Memory content {i}",
                importance=0.8 - (i * 0.1),
            ).to_dict()
            for i in range(count)
        ]
        return {"memories": memories, "total": count}

    @staticmethod
    def memory_context(task: str = "test task") -> Dict[str, Any]:
        """Build memory context response.

        Args:
            task: Task description.

        Returns:
            Memory context response.
        """
        return {
            "task": task,
            "relevant_memories": [
                MemoryResponse(memory_id="mem-ctx-001").to_dict(),
            ],
            "context_summary": f"Context for: {task}",
        }

    @staticmethod
    def memory_consolidate() -> Dict[str, int]:
        """Build memory consolidate response.

        Returns:
            Consolidation counts by type.
        """
        return {
            "episodic": 5,
            "semantic": 3,
            "procedural": 2,
        }

    @staticmethod
    def factory_generate(tool_name: str = "new_tool") -> Dict[str, Any]:
        """Build factory generate response.

        Args:
            tool_name: Name of generated tool.

        Returns:
            Factory generation response.
        """
        return FactoryResponse(tool_name=tool_name).to_dict()

    @staticmethod
    def factory_list() -> Dict[str, Any]:
        """Build factory list response.

        Returns:
            List of available tools.
        """
        tools = [FactoryResponse(tool_name=f"tool_{i}").to_dict() for i in range(3)]
        return {"tools": tools}

    @staticmethod
    def factory_execute(tool_name: str, result: Any = "success") -> Dict[str, Any]:
        """Build factory execute response.

        Args:
            tool_name: Tool name.
            result: Execution result.

        Returns:
            Execution response.
        """
        return {
            "tool_name": tool_name,
            "result": result,
            "success": True,
            "execution_time_ms": 50,
        }
