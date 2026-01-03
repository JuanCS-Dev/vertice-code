"""
Trust Package - Trust factor management for JUSTICA governance.

"Trust Factor = 1 - (weighted_violations + severity_score) / total_actions"
"Confianca e conquistada lentamente e perdida rapidamente."

Performance: 78.4% precision, 81.7% recall

Submodules:
    - types: AuthorizationLevel, AuthorizationContext, TrustLevel
    - events: TrustEvent dataclass
    - factor: TrustFactor dataclass
    - engine: TrustEngine class

Usage:
    from vertice_governance.justica.trust import (
        TrustEngine,
        TrustFactor,
        TrustLevel,
        ViolationType,
    )

    engine = TrustEngine()
    engine.record_good_action("agent-001", "Completed task successfully")
    tf = engine.get_trust_factor("agent-001")
    print(f"Trust: {tf.current_factor:.2%}")
"""

# Types
from .types import (
    AuthorizationContext,
    AuthorizationLevel,
    TrustLevel,
)

# Events
from .events import TrustEvent

# Factor
from .factor import TrustFactor

# Engine
from .engine import TrustEngine


__all__ = [
    # Types
    "AuthorizationLevel",
    "AuthorizationContext",
    "TrustLevel",
    # Events
    "TrustEvent",
    # Factor
    "TrustFactor",
    # Engine
    "TrustEngine",
]
