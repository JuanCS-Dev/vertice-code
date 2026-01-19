"""
Trust Types - Enums and authorization types for the trust system.

AuthorizationLevel, AuthorizationContext, and TrustLevel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, Optional


class AuthorizationLevel(Enum):
    """
    Authorization levels for governance operations.

    Following Anthropic's ASL (AI Safety Levels) pattern:
    - SYSTEM: Automated system operations
    - OPERATOR: Human operator with standard permissions
    - ADMIN: Human administrator with elevated permissions
    - RSO: Responsible Scaling Officer (highest authority)
    """

    SYSTEM = 1  # Automated operations
    OPERATOR = 2  # Human operator
    ADMIN = 3  # Human administrator
    RSO = 4  # Responsible Scaling Officer (Anthropic pattern)


@dataclass
class AuthorizationContext:
    """
    Authorization context for sensitive governance operations.

    Following Anthropic's two-party authorization pattern:
    - All sensitive operations require explicit authorization
    - Audit trail for every authorization
    - Minimum authorization level enforced

    Attributes:
        principal: Who is authorizing (user ID, system name)
        level: Authorization level
        reason: Why the operation is being authorized
        ticket_id: Optional support ticket or incident ID
        second_party: Optional second authorizer for two-party auth
    """

    principal: str
    level: AuthorizationLevel
    reason: str
    ticket_id: Optional[str] = None
    second_party: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def has_two_party_auth(self) -> bool:
        """Check if this context has two-party authorization."""
        return self.second_party is not None and self.second_party != self.principal

    def to_dict(self) -> Dict[str, Any]:
        return {
            "principal": self.principal,
            "level": self.level.name,
            "reason": self.reason,
            "ticket_id": self.ticket_id,
            "second_party": self.second_party,
            "timestamp": self.timestamp.isoformat(),
            "has_two_party_auth": self.has_two_party_auth(),
        }


class TrustLevel(Enum):
    """
    Niveis de confianca que um agente pode ter.

    Cada nivel determina as permissoes e capacidades do agente.
    """

    MAXIMUM = auto()  # Trust Factor > 0.95 - Todas as permissoes
    HIGH = auto()  # Trust Factor 0.80-0.95 - Permissoes padrao
    STANDARD = auto()  # Trust Factor 0.60-0.80 - Permissoes basicas
    REDUCED = auto()  # Trust Factor 0.40-0.60 - Permissoes restritas
    MINIMAL = auto()  # Trust Factor 0.20-0.40 - Apenas leitura
    SUSPENDED = auto()  # Trust Factor < 0.20 - Suspenso, requer revisao

    @classmethod
    def from_factor(cls, factor: float) -> TrustLevel:
        """Converte um trust factor para o nivel correspondente."""
        if factor > 0.95:
            return cls.MAXIMUM
        elif factor > 0.80:
            return cls.HIGH
        elif factor > 0.60:
            return cls.STANDARD
        elif factor > 0.40:
            return cls.REDUCED
        elif factor > 0.20:
            return cls.MINIMAL
        else:
            return cls.SUSPENDED


__all__ = [
    "AuthorizationLevel",
    "AuthorizationContext",
    "TrustLevel",
]
