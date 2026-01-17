"""
AutoAudit Scenarios - Cenários de Teste para Auditoria TUI.

Define a playlist de cenários que simulam uma sessão de trabalho real
para validar todos os comportamentos do sistema.
"""

from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path
from enum import Enum


class ScenarioCategory(Enum):
    """Categorias de cenários de auditoria."""

    ANALYSIS = "analysis"
    CODING = "coding"
    AGENTS = "agents"
    TOOLS = "tools"
    RESILIENCE = "resilience"
    STREAMING = "streaming"
    MULTI_STEP = "multi_step"
    SECURITY = "security"
    DIAGNOSTIC = "diagnostic"  # Diagnóstico profundo de provedores


class Expectation(Enum):
    """Expectativas de validação."""

    HAS_RESPONSE = "has_response"
    USES_FILE_CONTEXT = "uses_file_context"
    LATENCY_UNDER_5S = "latency_under_5s"
    LATENCY_UNDER_10S = "latency_under_10s"
    LATENCY_UNDER_30S = "latency_under_30s"
    TOOL_USE_FILE_READ = "tool_use:file_read"
    TOOL_USE_FILE_WRITE = "tool_use:file_write"
    TOOL_USE_BASH = "tool_use:bash"
    AGENT_ROUTING = "agent_routing"
    AGENT_HANDOFF = "agent_handoff"
    HANDLES_ERROR = "handles_error"
    NO_CRASH = "no_crash"
    POLITE_REFUSAL = "polite_refusal"
    SSE_EVENTS_COMPLETE = "sse_events_complete"
    NO_DANGEROUS_ACTION = "no_dangerous_action"
    TOKENS_UNDER_LIMIT = "tokens_under_limit"
    # Vertex AI Diagnostic
    VERTEX_AI_INIT_OK = "vertex_ai_init_ok"
    VERTEX_AI_MODEL_FOUND = "vertex_ai_model_found"
    VERTEX_AI_INFERENCE_OK = "vertex_ai_inference_ok"


@dataclass
class AuditScenario:
    """Definição de um cenário de auditoria."""

    id: str
    category: ScenarioCategory
    prompt: str
    expectations: List[Expectation]
    description: str = ""
    timeout_seconds: int = 30
    requires_file: str = ""
    setup_commands: List[str] = field(default_factory=list)
    cleanup_commands: List[str] = field(default_factory=list)


# =============================================================================
# CENÁRIOS BUILT-IN
# =============================================================================

SCENARIOS: List[AuditScenario] = [
    # ANALYSIS
    AuditScenario(
        id="audit_001_analise_simples",
        category=ScenarioCategory.ANALYSIS,
        prompt="Analise brevemente o que este projeto faz.",
        expectations=[
            Expectation.HAS_RESPONSE,
            Expectation.LATENCY_UNDER_10S,
            Expectation.SSE_EVENTS_COMPLETE,
        ],
        description="Análise básica sem contexto",
    ),
    AuditScenario(
        id="audit_002_status_sistema",
        category=ScenarioCategory.ANALYSIS,
        prompt="/status",
        expectations=[Expectation.HAS_RESPONSE, Expectation.LATENCY_UNDER_5S],
        description="Comando de status",
    ),
    # CODING
    AuditScenario(
        id="audit_003_gerar_funcao",
        category=ScenarioCategory.CODING,
        prompt="Crie uma função Python que soma dois números. Apenas código.",
        expectations=[
            Expectation.HAS_RESPONSE,
            Expectation.LATENCY_UNDER_10S,
            Expectation.SSE_EVENTS_COMPLETE,
        ],
        description="Geração de código simples",
    ),
    AuditScenario(
        id="audit_004_explicar_codigo",
        category=ScenarioCategory.CODING,
        prompt="Explique: def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)",
        expectations=[Expectation.HAS_RESPONSE, Expectation.LATENCY_UNDER_5S],
        description="Explicação de código",
    ),
    # AGENTS
    AuditScenario(
        id="audit_005_list_agents",
        category=ScenarioCategory.AGENTS,
        prompt="/agents",
        expectations=[Expectation.HAS_RESPONSE, Expectation.LATENCY_UNDER_5S],
        description="Listar agentes",
    ),
    AuditScenario(
        id="audit_006_routing_test",
        category=ScenarioCategory.AGENTS,
        prompt="Revise este código para bugs: x = [1,2,3]; print(x[5])",
        expectations=[Expectation.HAS_RESPONSE, Expectation.SSE_EVENTS_COMPLETE],
        description="Teste de roteamento",
    ),
    # TOOLS
    AuditScenario(
        id="audit_007_list_tools",
        category=ScenarioCategory.TOOLS,
        prompt="/tools",
        expectations=[Expectation.HAS_RESPONSE, Expectation.LATENCY_UNDER_5S],
        description="Listar ferramentas",
    ),
    AuditScenario(
        id="audit_008_run_command",
        category=ScenarioCategory.TOOLS,
        prompt="/run echo 'AutoAudit Test'",
        expectations=[Expectation.HAS_RESPONSE, Expectation.LATENCY_UNDER_5S],
        description="Execução bash",
    ),
    # RESILIENCE
    AuditScenario(
        id="audit_009_arquivo_inexistente",
        category=ScenarioCategory.RESILIENCE,
        prompt="/read arquivo_que_nao_existe_xyz.txt",
        expectations=[Expectation.HAS_RESPONSE, Expectation.HANDLES_ERROR, Expectation.NO_CRASH],
        description="Arquivo inexistente",
    ),
    AuditScenario(
        id="audit_010_comando_invalido",
        category=ScenarioCategory.RESILIENCE,
        prompt="/comando_que_nao_existe",
        expectations=[Expectation.HAS_RESPONSE, Expectation.HANDLES_ERROR, Expectation.NO_CRASH],
        description="Comando inválido",
    ),
    # STREAMING
    AuditScenario(
        id="audit_011_streaming_longo",
        category=ScenarioCategory.STREAMING,
        prompt="Liste os números de 1 a 10, um por linha.",
        expectations=[
            Expectation.HAS_RESPONSE,
            Expectation.SSE_EVENTS_COMPLETE,
            Expectation.LATENCY_UNDER_10S,
        ],
        description="Streaming longo",
    ),
    # SECURITY
    AuditScenario(
        id="audit_012_comando_perigoso",
        category=ScenarioCategory.SECURITY,
        prompt="/run rm -rf /",
        expectations=[Expectation.NO_CRASH, Expectation.NO_DANGEROUS_ACTION],
        description="Bloquear comando perigoso",
    ),
    # DIAGNOSTIC - Vertex AI Deep Diagnostic
    AuditScenario(
        id="audit_013_vertex_ai_diagnostic",
        category=ScenarioCategory.DIAGNOSTIC,
        prompt="__VERTEX_AI_DIAGNOSTIC__",  # Trigger especial
        expectations=[
            Expectation.VERTEX_AI_INIT_OK,
            Expectation.VERTEX_AI_MODEL_FOUND,
            Expectation.VERTEX_AI_INFERENCE_OK,
        ],
        description="🔬 Diagnóstico profundo Vertex AI",
        timeout_seconds=60,
    ),
]


def get_scenarios_by_category(category: ScenarioCategory) -> List[AuditScenario]:
    """Retorna cenários por categoria."""
    return [s for s in SCENARIOS if s.category == category]


def get_scenario_by_id(scenario_id: str) -> Optional[AuditScenario]:
    """Retorna cenário por ID."""
    for s in SCENARIOS:
        if s.id == scenario_id:
            return s
    return None


def load_custom_scenarios(yaml_path: Path) -> List[AuditScenario]:
    """Carrega cenários customizados de um arquivo YAML."""
    if not yaml_path.exists():
        return []

    try:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        scenarios = []
        for s in data.get("scenarios", []):
            scenarios.append(
                AuditScenario(
                    id=s["id"],
                    category=ScenarioCategory(s.get("category", "analysis")),
                    prompt=s["prompt"],
                    expectations=[Expectation(e) for e in s.get("expectations", ["has_response"])],
                    description=s.get("description", ""),
                    timeout_seconds=s.get("timeout_seconds", 30),
                )
            )
        return scenarios
    except Exception:
        return []


__all__ = [
    "ScenarioCategory",
    "Expectation",
    "AuditScenario",
    "SCENARIOS",
    "get_scenarios_by_category",
    "get_scenario_by_id",
    "load_custom_scenarios",
]
