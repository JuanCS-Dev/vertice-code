"""
JUSTICA Agent Package - Multi-agent governance system.

This package provides the JusticaAgent and related components
for governing multi-agent systems.

Submodules:
    - types: JusticaState, JusticaConfig, JusticaVerdict
    - evaluator: VerdictEvaluator for decision logic
    - core: JusticaAgent main class
    - factory: Factory functions

Usage:
    from vertice_governance.justica.agent import (
        JusticaAgent,
        JusticaConfig,
        JusticaVerdict,
        create_justica,
    )

    justica = create_justica()
    justica.start()

    verdict = justica.evaluate_input(
        agent_id="agent-001",
        content="User request to process",
    )
"""

# Types
from .types import (
    JusticaConfig,
    JusticaState,
    JusticaVerdict,
)

# Evaluator
from .evaluator import VerdictEvaluator

# Core agent
from .core import JusticaAgent, JUSTICA_BANNER

# Factory functions
from .factory import (
    create_justica,
    create_minimal_justica,
    create_strict_justica,
)


__all__ = [
    # Types
    "JusticaState",
    "JusticaConfig",
    "JusticaVerdict",
    # Evaluator
    "VerdictEvaluator",
    # Core
    "JusticaAgent",
    "JUSTICA_BANNER",
    # Factory
    "create_justica",
    "create_strict_justica",
    "create_minimal_justica",
]
