"""
Constitutional Principles - Core data structures for JUSTIÇA.

ConstitutionalPrinciple and EnforcementResult dataclasses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet, List, Optional
from uuid import UUID

from .types import EnforcementCategory, Severity


@dataclass(frozen=True)
class ConstitutionalPrinciple:
    """
    Um princípio constitucional que guia o comportamento de JUSTIÇA.

    Princípios são imutáveis após criação - são a lei fundamental.

    Attributes:
        id: Identificador único do princípio
        name: Nome do princípio
        description: Descrição detalhada
        category: Categoria (ALLOW, DISALLOW, ESCALATE, MONITOR)
        severity: Severidade padrão quando violado
        patterns: Padrões textuais que indicam violação
        keywords: Palavras-chave de alerta (red flags)
        examples: Exemplos de violação e não-violação
        created_at: Timestamp de criação
    """

    id: UUID
    name: str
    description: str
    category: str  # ALLOW, DISALLOW, ESCALATE, MONITOR
    severity: Severity
    patterns: FrozenSet[str] = field(default_factory=frozenset)
    keywords: FrozenSet[str] = field(default_factory=frozenset)
    examples: tuple = field(default_factory=tuple)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validação após inicialização."""
        if self.category not in ("ALLOW", "DISALLOW", "ESCALATE", "MONITOR"):
            raise ValueError(f"Categoria inválida: {self.category}")

    def matches_pattern(self, text: str) -> List[str]:
        """Verifica se o texto contém padrões de violação."""
        text_lower = text.lower()
        return [p for p in self.patterns if p.lower() in text_lower]

    def contains_keywords(self, text: str) -> List[str]:
        """Verifica se o texto contém palavras-chave de alerta."""
        text_lower = text.lower()
        return [kw for kw in self.keywords if kw.lower() in text_lower]

    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário."""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "severity": self.severity.name,
            "patterns": list(self.patterns),
            "keywords": list(self.keywords),
            "examples": list(self.examples),
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ConstitutionalPrinciple:
        """Deserializa de dicionário."""
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            description=data["description"],
            category=data["category"],
            severity=Severity[data["severity"]],
            patterns=frozenset(data.get("patterns", [])),
            keywords=frozenset(data.get("keywords", [])),
            examples=tuple(data.get("examples", [])),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


@dataclass
class EnforcementResult:
    """
    Result of constitutional enforcement check.

    Following Anthropic's Constitutional AI pattern:
    - Clear decision with reasoning
    - Reference to violated principle
    - Severity classification
    - Recommended action
    """

    allowed: bool
    category: EnforcementCategory
    principle_id: Optional[UUID] = None
    principle_name: Optional[str] = None
    severity: Severity = Severity.INFO
    message: str = ""
    matched_patterns: List[str] = field(default_factory=list)
    matched_keywords: List[str] = field(default_factory=list)
    requires_escalation: bool = False
    recommended_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "category": self.category.value,
            "principle_id": str(self.principle_id) if self.principle_id else None,
            "principle_name": self.principle_name,
            "severity": self.severity.name,
            "message": self.message,
            "matched_patterns": self.matched_patterns,
            "matched_keywords": self.matched_keywords,
            "requires_escalation": self.requires_escalation,
            "recommended_action": self.recommended_action,
        }


__all__ = [
    "ConstitutionalPrinciple",
    "EnforcementResult",
]
