"""
Workflow Module - Multi-Step Workflow Orchestration Engine.

Implements Constitutional Layer 2 (Deliberation):
- Tree-of-Thought multi-path exploration (Claude pattern)
- Dependency graph with topological sort (Cursor AI pattern)
- Auto-critique with LEI metric (Constitutional requirement)
- Transactional execution with rollback (ACID pattern)
- Checkpoint system for state management

Best-of-breed: Cursor (orchestration) + Claude (reasoning) + Constitutional (guarantees)

Usage:
    from vertice_core.core.workflow import WorkflowEngine, WorkflowStep

    engine = WorkflowEngine(llm_client, recovery_engine, tool_registry)
    result = await engine.execute_workflow("Build and test the application")
"""

# Models
from .models import (
    StepStatus,
    WorkflowStep,
    ThoughtPath,
    Checkpoint,
    Critique,
    WorkflowResult,
)

# Components
from .dependency_graph import DependencyGraph
from .tree_of_thought import TreeOfThought
from .auto_critique import AutoCritique
from .checkpoint_manager import CheckpointManager
from .transaction import Transaction

# Rollback
from .git_rollback import GitRollback
from .partial_rollback import PartialRollback

# Engine
from .engine import WorkflowEngine

__all__ = [
    # Models
    "StepStatus",
    "WorkflowStep",
    "ThoughtPath",
    "Checkpoint",
    "Critique",
    "WorkflowResult",
    # Components
    "DependencyGraph",
    "TreeOfThought",
    "AutoCritique",
    "CheckpointManager",
    "Transaction",
    # Rollback
    "GitRollback",
    "PartialRollback",
    # Engine
    "WorkflowEngine",
]
