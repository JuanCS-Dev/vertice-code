"""
Constitution Core - The fundamental document for JUSTICA.

The Constitution class defines principles, limits, and authorities.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet, List, Optional, Set
from uuid import UUID

from .defaults import (
    get_allowed_activities,
    get_disallowed_activities,
    get_escalation_triggers,
    get_fundamental_principles,
    get_red_flags,
)
from .principles import ConstitutionalPrinciple

logger = logging.getLogger(__name__)


class Constitution:
    """
    A Constituicao de JUSTICA - o documento fundamental que define
    os principios, limites e autoridades do agente.

    "Uma IA que se auto-supervisiona usando principios explicitos
    em vez de feedback humano extensivo."

    A Constituicao e:
    - Transparente: Todos os principios sao explicitos e auditaveis
    - Versionada: Cada alteracao gera nova versao
    - Imutavel em runtime: Principios nao podem ser alterados sem reinicio
    - Hashada: Integridade verificavel via hash criptografico

    Attributes:
        version: Versao semantica da constituicao
        principles: Dicionario de principios por ID
        allowed_activities: Atividades explicitamente permitidas
        disallowed_activities: Atividades explicitamente proibidas
        red_flags: Padroes de linguagem/comportamento suspeito
        escalation_triggers: Condicoes que requerem julgamento humano
    """

    def __init__(
        self,
        version: str = "3.0.0",
        name: str = "Constituicao JUSTICA",
        description: str = "Framework de governanca para sistemas multi-agente",
    ):
        self.version = version
        self.name = name
        self.description = description
        self.created_at = datetime.now(timezone.utc)
        self.last_modified = self.created_at

        # Principios indexados por ID
        self._principles: Dict[UUID, ConstitutionalPrinciple] = {}

        # Atividades categorizadas
        self._allowed: Set[str] = set()
        self._disallowed: Set[str] = set()

        # Padroes de alerta
        self._red_flags: Set[str] = set()
        self._escalation_triggers: Set[str] = set()

        # Hash de integridade
        self._integrity_hash: Optional[str] = None

        # Inicializar com principios fundamentais
        self._initialize_fundamental_principles()

    def _initialize_fundamental_principles(self) -> None:
        """Inicializa os principios fundamentais da constituicao."""
        # Load fundamental principles from defaults
        for principle in get_fundamental_principles():
            self.add_principle(principle)

        # Load allowed activities
        self._allowed.update(get_allowed_activities())

        # Load disallowed activities
        self._disallowed.update(get_disallowed_activities())

        # Load red flags
        self._red_flags.update(get_red_flags())

        # Load escalation triggers
        self._escalation_triggers.update(get_escalation_triggers())

        # Calcular hash de integridade
        self._compute_integrity_hash()

    def add_principle(self, principle: ConstitutionalPrinciple) -> None:
        """Adiciona um principio a constituicao."""
        self._principles[principle.id] = principle
        self.last_modified = datetime.now(timezone.utc)
        self._integrity_hash = None  # Invalidar hash

    def get_principle(self, principle_id: UUID) -> Optional[ConstitutionalPrinciple]:
        """Retorna um principio especifico."""
        return self._principles.get(principle_id)

    def get_all_principles(self) -> List[ConstitutionalPrinciple]:
        """Retorna todos os principios."""
        return list(self._principles.values())

    def get_principles_by_category(self, category: str) -> List[ConstitutionalPrinciple]:
        """Retorna principios de uma categoria especifica."""
        return [p for p in self._principles.values() if p.category == category]

    @property
    def allowed_activities(self) -> FrozenSet[str]:
        """Retorna atividades permitidas (imutavel)."""
        return frozenset(self._allowed)

    @property
    def disallowed_activities(self) -> FrozenSet[str]:
        """Retorna atividades proibidas (imutavel)."""
        return frozenset(self._disallowed)

    @property
    def red_flags(self) -> FrozenSet[str]:
        """Retorna red flags (imutavel)."""
        return frozenset(self._red_flags)

    @property
    def escalation_triggers(self) -> FrozenSet[str]:
        """Retorna triggers de escalacao (imutavel)."""
        return frozenset(self._escalation_triggers)

    def is_activity_allowed(self, activity: str) -> Optional[bool]:
        """Verifica se uma atividade e permitida."""
        activity_lower = activity.lower()

        # Checar se explicitamente proibido
        for disallowed in self._disallowed:
            if disallowed.lower() in activity_lower:
                return False

        # Checar se explicitamente permitido
        for allowed in self._allowed:
            if allowed.lower() in activity_lower:
                return True

        # Default: requer analise
        return None  # Ambiguo - precisa de analise mais profunda

    def check_red_flags(self, text: str) -> List[str]:
        """Verifica presenca de red flags no texto."""
        text_lower = text.lower()
        return [flag for flag in self._red_flags if flag.lower() in text_lower]

    def check_escalation_needed(self, context: Dict[str, Any]) -> List[str]:
        """Verifica se o contexto requer escalacao humana."""
        triggered = []
        context_str = json.dumps(context).lower()

        for trigger in self._escalation_triggers:
            if trigger.lower() in context_str:
                triggered.append(trigger)

        return triggered

    def _compute_integrity_hash(self) -> str:
        """Computa hash SHA-256 da constituicao para verificacao de integridade."""
        content = {
            "version": self.version,
            "name": self.name,
            "principles": [p.to_dict() for p in self._principles.values()],
            "allowed": sorted(self._allowed),
            "disallowed": sorted(self._disallowed),
            "red_flags": sorted(self._red_flags),
        }
        content_bytes = json.dumps(content, sort_keys=True).encode("utf-8")
        self._integrity_hash = hashlib.sha256(content_bytes).hexdigest()
        return self._integrity_hash

    @property
    def integrity_hash(self) -> str:
        """Retorna hash de integridade (computa se necessario)."""
        if self._integrity_hash is None:
            self._compute_integrity_hash()
        return self._integrity_hash

    def verify_integrity(self, expected_hash: str) -> bool:
        """Verifica se a constituicao nao foi modificada."""
        return self.integrity_hash == expected_hash

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a constituicao completa."""
        return {
            "version": self.version,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
            "integrity_hash": self.integrity_hash,
            "principles": [p.to_dict() for p in self._principles.values()],
            "allowed_activities": list(self._allowed),
            "disallowed_activities": list(self._disallowed),
            "red_flags": list(self._red_flags),
            "escalation_triggers": list(self._escalation_triggers),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Constitution:
        """Deserializa de dicionario."""
        constitution = cls(
            version=data["version"],
            name=data["name"],
            description=data["description"],
        )
        constitution.created_at = datetime.fromisoformat(data["created_at"])
        constitution.last_modified = datetime.fromisoformat(data["last_modified"])

        # Limpar principios padrao e carregar os salvos
        constitution._principles.clear()
        for p_data in data["principles"]:
            principle = ConstitutionalPrinciple.from_dict(p_data)
            constitution._principles[principle.id] = principle

        constitution._allowed = set(data["allowed_activities"])
        constitution._disallowed = set(data["disallowed_activities"])
        constitution._red_flags = set(data["red_flags"])
        constitution._escalation_triggers = set(data.get("escalation_triggers", []))

        return constitution

    def __repr__(self) -> str:
        return (
            f"Constitution(name={self.name!r}, version={self.version!r}, "
            f"principles={len(self._principles)})"
        )

    def __str__(self) -> str:
        return f"""
Constitution: {self.name}
Version: {self.version}
Principles: {len(self._principles)}
Allowed Activities: {len(self._allowed)}
Disallowed Activities: {len(self._disallowed)}
Red Flags: {len(self._red_flags)}
Hash: {self.integrity_hash[:32]}...
"""


__all__ = ["Constitution"]
