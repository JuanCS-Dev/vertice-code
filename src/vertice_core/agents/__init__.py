"""
Unified Agent System - Sprint 2.

Components:
- UnifiedContext: Shared state across agents (Swarm + Claude patterns)
- SemanticRouter: Embedding-based intent routing with LLM fallback
- ActiveOrchestrator: State machine orchestration
- HandoffManager: Agent transfer system

Phase 10: Sprint 2 - Agent Rewrite

Soli Deo Gloria
"""

from __future__ import annotations

from .context import (
    ContextState,
    DecisionType,
    Decision,
    ErrorContext,
    FileContext,
    ExecutionResult,
    ThoughtSignature,
    UnifiedContext,
    get_context,
    set_context,
    new_context,
)

from .router import (
    AgentType,
    TaskComplexity,
    RouteDefinition,
    RoutingDecision,
    SemanticRouter,
    get_router,
    DEFAULT_ROUTES,
)

from .orchestrator import (
    OrchestratorState,
    HandoffType,
    StateTransition,
    ExecutionStep,
    ExecutionPlan,
    Handoff,
    AgentProtocol,
    ActiveOrchestrator,
    orchestrate,
)

from .handoff import (
    HandoffStatus,
    HandoffReason,
    AgentCapability,
    HandoffRequest,
    HandoffResult,
    EscalationChain,
    HandoffManager,
    handoff,
    DEFAULT_CAPABILITIES,
    DEFAULT_ESCALATION_CHAINS,
)

from .compaction import (
    CompactionStrategy,
    CompactionTrigger,
    CompactionConfig,
    CompactionResult,
    MaskedObservation,
    ObservationMaskingStrategy,
    HierarchicalStrategy,
    LLMSummaryStrategy,
    ContextCompactor,
    auto_compact,
    compact_with_strategy,
)

__all__ = [
    # Context
    "ContextState",
    "DecisionType",
    "Decision",
    "ErrorContext",
    "FileContext",
    "ExecutionResult",
    "ThoughtSignature",
    "UnifiedContext",
    "get_context",
    "set_context",
    "new_context",
    # Router
    "AgentType",
    "TaskComplexity",
    "RouteDefinition",
    "RoutingDecision",
    "SemanticRouter",
    "get_router",
    "DEFAULT_ROUTES",
    # Orchestrator
    "OrchestratorState",
    "HandoffType",
    "StateTransition",
    "ExecutionStep",
    "ExecutionPlan",
    "Handoff",
    "AgentProtocol",
    "ActiveOrchestrator",
    "orchestrate",
    # Handoff
    "HandoffStatus",
    "HandoffReason",
    "AgentCapability",
    "HandoffRequest",
    "HandoffResult",
    "EscalationChain",
    "HandoffManager",
    "handoff",
    "DEFAULT_CAPABILITIES",
    "DEFAULT_ESCALATION_CHAINS",
    # Compaction
    "CompactionStrategy",
    "CompactionTrigger",
    "CompactionConfig",
    "CompactionResult",
    "MaskedObservation",
    "ObservationMaskingStrategy",
    "HierarchicalStrategy",
    "LLMSummaryStrategy",
    "ContextCompactor",
    "auto_compact",
    "compact_with_strategy",
]
