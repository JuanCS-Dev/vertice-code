"""
Refactorer Module - Enterprise Transactional Code Surgery.

This module provides comprehensive code refactoring capabilities:
- AST-aware surgical patching (LibCST for formatting preservation)
- Transactional memory with multi-level rollback
- Reinforcement learning-guided transformations
- Multi-file atomic refactoring (all-or-nothing)

Architecture:
    - models.py: Type-safe data structures (RefactoringType, CodeChange, etc.)
    - session.py: TransactionalSession with ACID properties
    - transformer.py: AST transformations (LibCST/fallback)
    - rl_policy.py: RL-based refactoring suggestions
    - agent.py: RefactorerAgent orchestrator

Usage:
    from vertice_core.agents.refactorer import RefactorerAgent, create_refactorer_agent

    agent = create_refactorer_agent(llm_client, mcp_client)
    response = await agent.execute(task)

Philosophy (Martin Fowler):
    "Refactoring is the process of changing a software system
     in such a way that it does not alter the external behavior
     of the code yet improves its internal structure."
"""

# Models
from .models import (
    RefactoringType,
    ChangeStatus,
    CodeChange,
    RefactoringPlan,
    ValidationResult,
    RefactoringAction,
    generate_change_id,
    generate_session_id,
)

# Session
from .session import TransactionalSession

# Transformer
from .transformer import ASTTransformer, HAS_LIBCST

# RL Policy
from .rl_policy import RLRefactoringPolicy

# Agent
from .agent import RefactorerAgent, create_refactorer_agent

__all__ = [
    # Models
    "RefactoringType",
    "ChangeStatus",
    "CodeChange",
    "RefactoringPlan",
    "ValidationResult",
    "RefactoringAction",
    "generate_change_id",
    "generate_session_id",
    # Session
    "TransactionalSession",
    # Transformer
    "ASTTransformer",
    "HAS_LIBCST",
    # RL Policy
    "RLRefactoringPolicy",
    # Agent
    "RefactorerAgent",
    "create_refactorer_agent",
]
