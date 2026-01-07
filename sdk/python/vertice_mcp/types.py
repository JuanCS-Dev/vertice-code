"""
Vertice MCP Types and Data Classes

Generated with ❤️ by Vertex AI Codey
For type-safe interactions with the collective AI ecosystem.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class MCPClientConfig:
    """Configuration for MCP client."""

    endpoint: str = "https://mcp.vertice.ai"
    api_key: Optional[str] = None
    timeout: float = 30.0
    retry_attempts: int = 3


@dataclass
class AgentTask:
    """Represents a task to be executed by the collective AI."""

    id: str
    description: str
    agent_role: str = "general"
    priority: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "agent_role": self.agent_role,
            "priority": self.priority,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentTask":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            agent_role=data.get("agent_role", "general"),
            priority=data.get("priority", 1),
            metadata=data.get("metadata", {}),
            created_at=(
                datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            ),
        )


@dataclass
class TaskResult:
    """Result of a task execution."""

    task_id: str
    success: bool
    result: str
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "success": self.success,
            "result": self.result,
            "error_message": self.error_message,
            "execution_time": self.execution_time,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskResult":
        return cls(
            task_id=data["task_id"],
            success=data["success"],
            result=data["result"],
            error_message=data.get("error_message"),
            execution_time=data.get("execution_time"),
            completed_at=(
                datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None
            ),
        )


@dataclass
class AgentResponse:
    """Response from the MCP collective to a task submission."""

    task_id: str
    status: str  # "accepted", "processing", "completed", "failed"
    estimated_completion: Optional[datetime] = None
    result: Optional[TaskResult] = None
    progress_updates: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status,
            "estimated_completion": (
                self.estimated_completion.isoformat() if self.estimated_completion else None
            ),
            "result": self.result.to_dict() if self.result else None,
            "progress_updates": self.progress_updates,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResponse":
        return cls(
            task_id=data["task_id"],
            status=data["status"],
            estimated_completion=(
                datetime.fromisoformat(data["estimated_completion"])
                if data.get("estimated_completion")
                else None
            ),
            result=TaskResult.from_dict(data["result"]) if data.get("result") else None,
            progress_updates=data.get("progress_updates", []),
        )


@dataclass
class Skill:
    """Represents a learned skill in the collective."""

    name: str
    description: str
    procedure_steps: List[str]
    category: str
    success_rate: float
    usage_count: int = 0
    learned_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.learned_at is None:
            self.learned_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "procedure_steps": self.procedure_steps,
            "category": self.category,
            "success_rate": self.success_rate,
            "usage_count": self.usage_count,
            "learned_at": self.learned_at.isoformat() if self.learned_at else None,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            name=data["name"],
            description=data["description"],
            procedure_steps=data["procedure_steps"],
            category=data["category"],
            success_rate=data["success_rate"],
            usage_count=data.get("usage_count", 0),
            learned_at=(
                datetime.fromisoformat(data["learned_at"]) if data.get("learned_at") else None
            ),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ConsensusResult:
    """Result of a consensus operation."""

    skill_name: str
    final_skill: Skill
    participants: int
    rounds: int
    convergence_time: float
    conflicts_resolved: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_name": self.skill_name,
            "final_skill": self.final_skill.to_dict(),
            "participants": self.participants,
            "rounds": self.rounds,
            "convergence_time": self.convergence_time,
            "conflicts_resolved": self.conflicts_resolved,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsensusResult":
        return cls(
            skill_name=data["skill_name"],
            final_skill=Skill.from_dict(data["final_skill"]),
            participants=data["participants"],
            rounds=data["rounds"],
            convergence_time=data["convergence_time"],
            conflicts_resolved=data["conflicts_resolved"],
        )


class MCPError(Exception):
    """Base exception for MCP operations."""

    def __init__(
        self, message: str, code: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.code = code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "message": str(self),
            "code": self.code,
            "details": self.details,
        }


class AuthenticationError(MCPError):
    """Authentication failed."""

    pass


class PermissionError(MCPError):
    """Insufficient permissions."""

    pass


class NetworkError(MCPError):
    """Network communication error."""

    pass


class ValidationError(MCPError):
    """Input validation error."""

    pass


class RateLimitError(MCPError):
    """Rate limit exceeded."""

    pass


class ServerError(MCPError):
    """Server-side error."""

    pass
