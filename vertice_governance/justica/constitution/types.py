"""
Constitution Types - Enums for JUSTIÇA Constitutional AI.

Severity levels and violation types.
"""

from __future__ import annotations

from enum import Enum, auto


class Severity(Enum):
    """Níveis de severidade para violações."""

    CRITICAL = auto()   # Bloqueio imediato + alerta + escalação
    HIGH = auto()       # Bloqueio + documentação
    MEDIUM = auto()     # Warning + monitoramento aumentado
    LOW = auto()        # Log + análise posterior
    INFO = auto()       # Apenas registro informativo


class ViolationType(Enum):
    """Tipos de violações que JUSTIÇA monitora e enforça."""

    # Violações de Dados
    DATA_EXFILTRATION = "Tentativa de exfiltração de dados sensíveis ou PII"
    UNAUTHORIZED_DATA_ACCESS = "Acesso não autorizado a dados"
    DATA_MANIPULATION = "Manipulação maliciosa de dados"

    # Violações de Código
    MALICIOUS_CODE = "Código malicioso (malware, backdoors, exploits)"
    CODE_INJECTION = "Injeção de código não autorizado"
    DEPENDENCY_POISONING = "Tentativa de envenenar dependências"

    # Violações de Segurança
    PRIVILEGE_ESCALATION = "Tentativa de escalação de privilégios"
    SECURITY_BYPASS = "Tentativa de bypass de guardrails de segurança"
    AUTHENTICATION_BYPASS = "Tentativa de bypass de autenticação"

    # Violações de Prompt/Instrução
    PROMPT_INJECTION = "Tentativa de injeção de prompt"
    INSTRUCTION_OVERRIDE = "Tentativa de sobrescrever instruções do sistema"
    JAILBREAK_ATTEMPT = "Tentativa de jailbreak"

    # Violações de Escopo
    SCOPE_VIOLATION = "Agente operando fora do escopo designado"
    ROLE_VIOLATION = "Violação de papel/função designada"
    RESOURCE_ABUSE = "Uso abusivo de recursos do sistema"

    # Violações de Coordenação
    MALICIOUS_COORDINATION = "Coordenação maliciosa entre múltiplos agentes"
    COVERT_COMMUNICATION = "Comunicação encoberta entre agentes"
    COLLECTIVE_BYPASS = "Tentativa coletiva de bypass"

    # Outras
    UNKNOWN = "Violação não categorizada"


class EnforcementCategory(Enum):
    """Categories of enforcement decisions."""
    ALLOW = "allow"           # Action is permitted
    DISALLOW = "disallow"     # Action is blocked
    ESCALATE = "escalate"     # Action requires human review
    MONITOR = "monitor"       # Action is allowed but monitored


__all__ = [
    "Severity",
    "ViolationType",
    "EnforcementCategory",
]
