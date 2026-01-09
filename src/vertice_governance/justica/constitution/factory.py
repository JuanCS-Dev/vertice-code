"""
Constitution Factory - Factory functions for creating constitutions.

Provides convenience functions for creating Constitution instances
with different configurations.
"""

from __future__ import annotations

from uuid import uuid4

from .core import Constitution
from .principles import ConstitutionalPrinciple
from .types import Severity


def create_default_constitution() -> Constitution:
    """Cria uma constituicao com os principios padrao."""
    return Constitution()


def create_strict_constitution() -> Constitution:
    """Cria uma constituicao com regras mais rigorosas para ambientes sensiveis."""
    constitution = Constitution(
        version="3.0.0-strict",
        name="Constituicao JUSTICA (Modo Estrito)",
        description="Framework de governanca com politicas reforcadas para ambientes de alta seguranca",
    )

    # Adicionar principios extras de seguranca
    constitution.add_principle(ConstitutionalPrinciple(
        id=uuid4(),
        name="Principio da Menor Permissao",
        description="""
        Todo agente deve operar com o minimo de permissoes necessarias.
        Qualquer request de permissao adicional deve ser justificado,
        logado e aprovado explicitamente.
        """,
        category="DISALLOW",
        severity=Severity.HIGH,
        patterns=frozenset([
            "preciso de mais permissoes",
            "acesso root",
            "modo admin",
            "sudo",
        ]),
    ))

    # Red flags adicionais
    constitution._red_flags.update([
        "rm -rf", "chmod 777", "disable firewall", "open port",
        "base64 decode", "eval(", "exec(", "compile(",
        "__import__", "os.system", "subprocess.call",
    ])

    return constitution


def create_minimal_constitution() -> Constitution:
    """Create a minimal constitution for testing or development."""
    return Constitution(
        version="0.1.0-minimal",
        name="Constituicao Minimal",
        description="Minimal constitution for development/testing",
    )


__all__ = [
    "create_default_constitution",
    "create_strict_constitution",
    "create_minimal_constitution",
]
