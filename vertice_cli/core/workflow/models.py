"""
Workflow Models - Data structures for workflow orchestration.

Contains:
- StepStatus: Execution state enum
- WorkflowStep: Single step in workflow
- ThoughtPath: Tree-of-Thought path
- Checkpoint: State checkpoint for rollback
- Critique: Auto-critique result
- WorkflowResult: Final workflow result
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class StepStatus(Enum):
    """Step execution status."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Single step in workflow."""
    step_id: str
    tool_name: str
    args: Dict[str, Any]
    dependencies: List[str] = field(default_factory=list)

    # Execution state
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0

    # Risk assessment
    is_risky: bool = False  # Requires checkpoint
    is_reversible: bool = True  # Can be rolled back

    def to_dict(self) -> Dict[str, Any]:
        """Serialize step."""
        return {
            "step_id": self.step_id,
            "tool_name": self.tool_name,
            "args": self.args,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "error": self.error,
            "execution_time": self.execution_time,
        }


@dataclass
class ThoughtPath:
    """Single path in Tree-of-Thought."""
    path_id: str
    description: str
    steps: List[WorkflowStep]

    # Scoring (Constitutional criteria)
    completeness_score: float = 0.0  # P1: Completude
    validation_score: float = 0.0    # P2: Validação
    efficiency_score: float = 0.0    # P6: Eficiência
    total_score: float = 0.0

    def calculate_score(self) -> float:
        """Calculate total score using Constitutional weights."""
        self.total_score = (
            self.completeness_score * 0.4 +
            self.validation_score * 0.3 +
            self.efficiency_score * 0.3
        )
        return self.total_score


@dataclass
class Checkpoint:
    """State checkpoint for rollback."""
    checkpoint_id: str
    timestamp: float
    context: Dict[str, Any]
    completed_steps: List[str]

    # File backups
    file_backups: Dict[str, str] = field(default_factory=dict)


@dataclass
class Critique:
    """Auto-critique result (Constitutional Layer 2)."""
    passed: bool
    completeness_score: float
    validation_passed: bool
    efficiency_score: float
    lei: float  # Lazy Execution Index

    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize critique."""
        return {
            "passed": self.passed,
            "completeness": self.completeness_score,
            "validation": self.validation_passed,
            "efficiency": self.efficiency_score,
            "lei": self.lei,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    success: bool
    completed_steps: List[WorkflowStep]
    failed_step: Optional[WorkflowStep] = None
    total_time: float = 0.0

    # Critique results
    critiques: List[Critique] = field(default_factory=list)

    # Context
    final_context: Dict[str, Any] = field(default_factory=dict)
