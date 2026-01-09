"""
Constitution Package - Constitutional AI governance for JUSTICA.

This package provides the Constitutional AI framework for multi-agent
governance, following Anthropic's Constitutional AI pattern (2022-2026).

Submodules:
    - types: Severity, ViolationType, EnforcementCategory enums
    - principles: ConstitutionalPrinciple, EnforcementResult dataclasses
    - defaults: Default principles, activities, red flags
    - core: Constitution class
    - enforcer: ConstitutionalEnforcer class
    - factory: Factory functions

Usage:
    from vertice_governance.justica.constitution import (
        Constitution,
        ConstitutionalEnforcer,
        create_default_constitution,
    )

    constitution = create_default_constitution()
    enforcer = ConstitutionalEnforcer(constitution)

    result = enforcer.enforce("User action to evaluate")
    if not result.allowed:
        print(f"Blocked: {result.message}")
"""

# Types (enums)
from .types import (
    EnforcementCategory,
    Severity,
    ViolationType,
)

# Data structures
from .principles import (
    ConstitutionalPrinciple,
    EnforcementResult,
)

# Default values
from .defaults import (
    get_allowed_activities,
    get_disallowed_activities,
    get_escalation_triggers,
    get_fundamental_principles,
    get_red_flags,
)

# Core classes
from .core import Constitution
from .enforcer import ConstitutionalEnforcer

# Factory functions
from .factory import (
    create_default_constitution,
    create_minimal_constitution,
    create_strict_constitution,
)


__all__ = [
    # Types
    "Severity",
    "ViolationType",
    "EnforcementCategory",
    # Data structures
    "ConstitutionalPrinciple",
    "EnforcementResult",
    # Defaults
    "get_fundamental_principles",
    "get_allowed_activities",
    "get_disallowed_activities",
    "get_red_flags",
    "get_escalation_triggers",
    # Core classes
    "Constitution",
    "ConstitutionalEnforcer",
    # Factory functions
    "create_default_constitution",
    "create_strict_constitution",
    "create_minimal_constitution",
]
