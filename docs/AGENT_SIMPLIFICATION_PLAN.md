# Plano de Simplificação dos Agentes MCP - Implementação Segura

**Data**: 22 Janeiro 2026
**Objetivo**: Simplificar agentes sem quebrar funcionalidades
**Metodologia**: Fases incrementais com testes e benchmarks

---

## Visão Geral das Fases

```
┌─────────────────────────────────────────────────────────────────┐
│ FASE 0: Baseline de Testes e Benchmarks (ANTES de qualquer     │
│         mudança)                                                 │
├─────────────────────────────────────────────────────────────────┤
│ FASE 1: Quick Wins - Mover mixins para BaseAgent               │
│         (Zero breaking changes)                                  │
├─────────────────────────────────────────────────────────────────┤
│ FASE 2: Unificar ThreeLoops + BoundedAutonomy                   │
│         (Consolidação conceitual)                                │
├─────────────────────────────────────────────────────────────────┤
│ FASE 3: Deprecar Darwin Gödel                                   │
│         (Remover código morto)                                   │
├─────────────────────────────────────────────────────────────────┤
│ FASE 4: Simplificar DeepThink (4 → 2 stages)                    │
│         (Reduzir complexidade)                                   │
├─────────────────────────────────────────────────────────────────┤
│ FASE 5: Converter RAG sub-agents para tools                     │
│         (Alinhamento com Google ADK)                             │
├─────────────────────────────────────────────────────────────────┤
│ FASE 6: Benchmark Final e Relatório                             │
│         (Validar melhorias)                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## FASE 0: Baseline de Testes e Benchmarks

### 0.1 Objetivo
Capturar o estado atual do sistema para comparação posterior.

### 0.2 Criar Suite de Testes de Regressão

**Arquivo**: `tests/refactor/test_agents_baseline.py`

```python
"""
Baseline Tests - Captura comportamento atual dos agentes.
EXECUTE ANTES DE QUALQUER MUDANÇA.
"""

import pytest
import time
import json
from pathlib import Path
from datetime import datetime

BASELINE_FILE = Path("tests/refactor/baseline_results.json")


class TestAgentBaseline:
    """Testes que capturam comportamento atual."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup para cada teste."""
        self.results = {}
        self.start_time = time.time()

    def teardown_method(self):
        """Salva tempo de cada teste."""
        duration = time.time() - self.start_time
        self.results["duration"] = duration

    # ========== ORCHESTRATOR ==========

    def test_orchestrator_instantiation(self):
        """Orchestrator pode ser instanciado."""
        from agents import OrchestratorAgent
        agent = OrchestratorAgent()
        assert agent.name == "orchestrator"
        assert hasattr(agent, "decomposer")
        assert hasattr(agent, "router")

    def test_orchestrator_has_bounded_autonomy(self):
        """Orchestrator tem BoundedAutonomy."""
        from agents import orchestrator
        assert hasattr(orchestrator, "check_autonomy")
        assert hasattr(orchestrator, "AUTONOMY_RULES")

    def test_orchestrator_has_mesh(self):
        """Orchestrator tem HybridMesh."""
        from agents import orchestrator
        assert hasattr(orchestrator, "_init_mesh")
        assert hasattr(orchestrator, "route_task")

    @pytest.mark.asyncio
    async def test_orchestrator_plan(self):
        """Orchestrator decompõe tarefas."""
        from agents import OrchestratorAgent
        orch = OrchestratorAgent()
        tasks = await orch.plan("Create a function")
        assert len(tasks) >= 1
        assert tasks[0].id.startswith("task-")

    # ========== CODER ==========

    def test_coder_instantiation(self):
        """Coder pode ser instanciado."""
        from agents import CoderAgent
        agent = CoderAgent()
        assert agent.name == "coder"
        assert hasattr(agent, "LANGUAGES")

    def test_coder_has_darwin_godel(self):
        """Coder tem DarwinGodel (verificar se usado)."""
        from agents import coder
        # Verificar se mixin existe
        assert hasattr(coder, "get_archive")
        assert hasattr(coder, "evolve")

    def test_coder_evaluate_code(self):
        """Coder avalia código."""
        from agents import coder
        result = coder.evaluate_code("def f(): pass", "python")
        assert result.valid_syntax is True
        assert 0 <= result.quality_score <= 1

    def test_coder_evaluate_invalid(self):
        """Coder detecta código inválido."""
        from agents import coder
        result = coder.evaluate_code("def f(", "python")
        assert result.valid_syntax is False

    # ========== REVIEWER ==========

    def test_reviewer_instantiation(self):
        """Reviewer pode ser instanciado."""
        from agents import ReviewerAgent
        agent = ReviewerAgent()
        assert agent.name == "reviewer"

    def test_reviewer_has_deep_think(self):
        """Reviewer tem DeepThink."""
        from agents import reviewer
        assert hasattr(reviewer, "deep_think_review")
        assert hasattr(reviewer, "_stage_static_analysis")
        assert hasattr(reviewer, "_stage_deep_reasoning")
        assert hasattr(reviewer, "_stage_critique")
        assert hasattr(reviewer, "_stage_validation")

    def test_reviewer_security_scan(self):
        """Reviewer faz scan de segurança."""
        from agents import reviewer
        code = 'os.system("rm -rf /")'
        issues = reviewer._quick_security_scan(code)
        assert len(issues) > 0
        assert "Command injection" in issues[0]

    # ========== ARCHITECT ==========

    def test_architect_instantiation(self):
        """Architect pode ser instanciado."""
        from agents import ArchitectAgent
        agent = ArchitectAgent()
        assert agent.name == "architect"

    def test_architect_has_three_loops(self):
        """Architect tem ThreeLoops."""
        from agents import architect
        assert hasattr(architect, "select_loop")
        assert hasattr(architect, "classify_decision")

    def test_architect_classify_decision(self):
        """Architect classifica decisões."""
        from agents import architect
        context = architect.classify_decision("Design new database schema")
        assert context.impact is not None
        assert context.risk is not None

    # ========== RESEARCHER ==========

    def test_researcher_instantiation(self):
        """Researcher pode ser instanciado."""
        from agents import ResearcherAgent
        agent = ResearcherAgent()
        assert agent.name == "researcher"

    def test_researcher_has_agentic_rag(self):
        """Researcher tem AgenticRAG."""
        from agents import researcher
        assert hasattr(researcher, "agentic_research")
        assert hasattr(researcher, "_retrieval_agents") or hasattr(researcher, "_init_retrieval_agents")

    # ========== DEVOPS ==========

    def test_devops_instantiation(self):
        """DevOps pode ser instanciado."""
        from agents import DevOpsAgent
        agent = DevOpsAgent()
        assert agent.name == "devops"

    def test_devops_has_incident_handler(self):
        """DevOps tem IncidentHandler."""
        from agents import devops
        assert hasattr(devops, "investigate_incident")
        assert hasattr(devops, "build_topology")

    # ========== MIXINS COMUNS ==========

    def test_all_agents_have_resilience(self):
        """Todos agentes têm ResilienceMixin."""
        from agents import coder, reviewer, architect, researcher, devops
        for agent in [coder, reviewer, architect, researcher, devops]:
            assert hasattr(agent, "resilient_call")
            assert hasattr(agent, "_init_resilience")

    def test_all_agents_have_status(self):
        """Todos agentes têm get_status()."""
        from agents import orchestrator, coder, reviewer, architect, researcher, devops
        for agent in [orchestrator, coder, reviewer, architect, researcher, devops]:
            status = agent.get_status()
            assert "name" in status
            assert status["name"] == agent.name


class TestBenchmarkBaseline:
    """Benchmarks para comparação."""

    @pytest.fixture
    def benchmark_results(self):
        return {}

    @pytest.mark.asyncio
    async def test_benchmark_orchestrator_plan(self, benchmark_results):
        """Benchmark: tempo de planejamento."""
        from agents import OrchestratorAgent

        orch = OrchestratorAgent()

        start = time.time()
        for _ in range(10):
            await orch.plan("Create a function")
        duration = time.time() - start

        benchmark_results["orchestrator_plan_10x"] = duration
        assert duration < 5.0  # Deve completar em menos de 5s

    def test_benchmark_coder_evaluate(self, benchmark_results):
        """Benchmark: avaliação de código."""
        from agents import coder

        code = '''
def fibonacci(n: int) -> int:
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
'''

        start = time.time()
        for _ in range(100):
            coder.evaluate_code(code, "python")
        duration = time.time() - start

        benchmark_results["coder_evaluate_100x"] = duration
        assert duration < 2.0  # Deve completar em menos de 2s

    def test_benchmark_reviewer_scan(self, benchmark_results):
        """Benchmark: scan de segurança."""
        from agents import reviewer

        code = '''
import os
def run_command(cmd):
    os.system(cmd)
'''

        start = time.time()
        for _ in range(100):
            reviewer._quick_security_scan(code)
        duration = time.time() - start

        benchmark_results["reviewer_scan_100x"] = duration
        assert duration < 1.0


def save_baseline_results():
    """Salva resultados do baseline."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "version": "pre-simplification",
        "metrics": {
            "total_agent_files": 28,
            "total_loc": 5487,
            "total_types": 67,
        }
    }

    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BASELINE_FILE, "w") as f:
        json.dump(results, f, indent=2)

    return results
```

### 0.3 Comandos para Executar Baseline

```bash
# 1. Criar diretório de testes de refactoring
mkdir -p tests/refactor

# 2. Rodar testes baseline e salvar resultados
pytest tests/refactor/test_agents_baseline.py -v --tb=short 2>&1 | tee tests/refactor/baseline_output.txt

# 3. Contar LOC atual
find src/agents -name "*.py" | xargs wc -l | tail -1

# 4. Rodar benchmark existente
python tests/coder_e2e_benchmark.py 2>&1 | tee tests/refactor/benchmark_baseline.txt
```

### 0.4 Checklist Fase 0
- [ ] Criar `tests/refactor/test_agents_baseline.py`
- [ ] Executar todos os testes e verificar que passam
- [ ] Salvar output em `tests/refactor/baseline_output.txt`
- [ ] Documentar LOC atual (5,487)
- [ ] Executar benchmark e salvar baseline

---

## FASE 1: Quick Wins - Mover Mixins para BaseAgent

### 1.1 Objetivo
Mover `ResilienceMixin` e `CachingMixin` para `BaseAgent` para eliminar duplicação.

### 1.2 Mudanças

**Arquivo**: `src/agents/base.py`

```python
# ANTES (62 LOC)
class BaseAgent(ObservabilityMixin):
    ...

# DEPOIS
from vertice_core.resilience import ResilienceMixin
from vertice_core.caching import CachingMixin

class BaseAgent(ResilienceMixin, CachingMixin, ObservabilityMixin):
    """
    Base class for all Vertice agents.

    Provides:
    - Distributed tracing (ObservabilityMixin)
    - Resilience: retry, circuit breaker, rate limiting (ResilienceMixin)
    - Caching: semantic and exact match (CachingMixin)
    """

    name: str = "base"
    agent_id: Optional[str] = None

    def __init__(self) -> None:
        if self.agent_id is None:
            self.agent_id = getattr(self, "name", "unknown")

    def get_status(self) -> Dict[str, Any]:
        """Get agent status. Override in subclasses."""
        return {
            "name": self.name,
            "agent_id": self.agent_id,
        }
```

**Arquivos a modificar** (remover mixins redundantes):

1. `src/agents/orchestrator/agent.py`:
```python
# ANTES
class OrchestratorAgent(HybridMeshMixin, ResilienceMixin, CachingMixin, BoundedAutonomyMixin, BaseAgent):

# DEPOIS
class OrchestratorAgent(HybridMeshMixin, BoundedAutonomyMixin, BaseAgent):
```

2. `src/agents/architect/agent.py`:
```python
# ANTES
class ArchitectAgent(ResilienceMixin, CachingMixin, ThreeLoopsMixin, BaseAgent):

# DEPOIS
class ArchitectAgent(ThreeLoopsMixin, BaseAgent):
```

3. `src/agents/coder/agent.py`:
```python
# ANTES
class CoderAgent(ResilienceMixin, CachingMixin, DarwinGodelMixin, BaseAgent):

# DEPOIS
class CoderAgent(DarwinGodelMixin, BaseAgent):
```

4. `src/agents/reviewer/agent.py`:
```python
# ANTES
class ReviewerAgent(ResilienceMixin, CachingMixin, DeepThinkMixin, BaseAgent):

# DEPOIS
class ReviewerAgent(DeepThinkMixin, BaseAgent):
```

5. `src/agents/researcher/agent.py`:
```python
# ANTES
class ResearcherAgent(ResilienceMixin, CachingMixin, AgenticRAGMixin, BaseAgent):

# DEPOIS
class ResearcherAgent(AgenticRAGMixin, BaseAgent):
```

6. `src/agents/devops/agent.py`:
```python
# ANTES
class DevOpsAgent(ResilienceMixin, CachingMixin, IncidentHandlerMixin, BaseAgent):

# DEPOIS
class DevOpsAgent(IncidentHandlerMixin, BaseAgent):
```

### 1.3 Teste de Verificação Fase 1

```bash
# 1. Rodar testes de regressão
pytest tests/refactor/test_agents_baseline.py -v

# 2. Rodar testes E2E
pytest tests/e2e/test_all_agents.py -v

# 3. Verificar que mixins ainda funcionam
pytest -k "resilience or caching" -v

# 4. Verificar imports
python -c "from agents import orchestrator, coder, reviewer, architect, researcher, devops; print('OK')"
```

### 1.4 Checklist Fase 1
- [ ] Modificar `base.py` para incluir mixins
- [ ] Remover imports duplicados de cada agent.py
- [ ] Rodar `black` e `ruff`
- [ ] Rodar testes baseline
- [ ] Confirmar que todos os testes passam
- [ ] Commit: `refactor(agents): move ResilienceMixin and CachingMixin to BaseAgent`

---

## FASE 2: Unificar ThreeLoops + BoundedAutonomy

### 2.1 Objetivo
Consolidar dois sistemas que implementam o mesmo conceito (InfoQ Three Loops).

### 2.2 Decisão de Design

**Manter**: `BoundedAutonomy` (mais completo, com L0-L3)
**Deprecar**: `ThreeLoops` (criar wrapper de compatibilidade)

### 2.3 Mudanças

**Novo arquivo**: `src/agents/architect/bounded_autonomy_compat.py`

```python
"""
Compatibility layer for ThreeLoops -> BoundedAutonomy migration.

Maps:
- IN_THE_LOOP (AITL) -> L2_APPROVE / L3_HUMAN_ONLY
- ON_THE_LOOP (AOTL) -> L1_NOTIFY
- OUT_OF_LOOP (AOOTL) -> L0_AUTONOMOUS
"""

from agents.orchestrator.bounded_autonomy import BoundedAutonomyMixin
from agents.orchestrator.types import AutonomyLevel

# Backward compatibility aliases
class ArchitectLoop:
    """Deprecated: Use AutonomyLevel instead."""
    IN_THE_LOOP = AutonomyLevel.L2_APPROVE
    ON_THE_LOOP = AutonomyLevel.L1_NOTIFY
    OUT_OF_LOOP = AutonomyLevel.L0_AUTONOMOUS


class ThreeLoopsCompatMixin(BoundedAutonomyMixin):
    """
    Compatibility mixin that provides ThreeLoops API on top of BoundedAutonomy.

    Deprecated: Migrate to BoundedAutonomyMixin directly.
    """

    def select_loop(self, context):
        """Map ThreeLoops select_loop to BoundedAutonomy."""
        import warnings
        warnings.warn(
            "select_loop is deprecated. Use check_autonomy instead.",
            DeprecationWarning
        )
        # Implementation that maps to new system
        ...
```

**Modificar**: `src/agents/architect/agent.py`

```python
# ANTES
from .three_loops import ThreeLoopsMixin

class ArchitectAgent(ThreeLoopsMixin, BaseAgent):

# DEPOIS
from .bounded_autonomy_compat import ThreeLoopsCompatMixin

class ArchitectAgent(ThreeLoopsCompatMixin, BaseAgent):
```

### 2.4 Teste de Verificação Fase 2

```bash
# 1. Rodar testes específicos do Architect
pytest tests/e2e/test_all_agents.py::TestArchitectAgentE2E -v

# 2. Testar que select_loop ainda funciona (com warning)
python -c "
from agents import architect
import warnings
warnings.filterwarnings('error')
try:
    architect.classify_decision('test')
    print('PASS: classify_decision works')
except DeprecationWarning:
    print('WARNING emitted as expected')
"

# 3. Rodar baseline completo
pytest tests/refactor/test_agents_baseline.py -v
```

### 2.5 Checklist Fase 2
- [ ] Criar `bounded_autonomy_compat.py`
- [ ] Modificar `architect/agent.py`
- [ ] Adicionar testes de deprecation
- [ ] Rodar testes baseline
- [ ] Commit: `refactor(architect): unify ThreeLoops with BoundedAutonomy`

---

## FASE 3: Deprecar Darwin Gödel

### 3.1 Objetivo
Marcar como deprecated e preparar para remoção futura.

### 3.2 Evidência de Código Morto

```bash
# Verificar que evolve() nunca é chamado
grep -r "\.evolve\(" src/agents/ --include="*.py"
# Resultado esperado: NENHUM (apenas a definição)
```

### 3.3 Mudanças

**Modificar**: `src/agents/coder/darwin_godel.py`

```python
"""
Darwin Gödel Machine Evolution System

DEPRECATED: This module is not used in production and will be removed
in a future version. LLMs are sufficiently capable without prompt evolution.

If you need this functionality, please open an issue.
"""

import warnings

class DarwinGodelMixin:
    """
    DEPRECATED: Darwin Gödel evolution capabilities.
    """

    def evolve(self, *args, **kwargs):
        warnings.warn(
            "DarwinGodelMixin.evolve() is deprecated and will be removed. "
            "Modern LLMs don't require prompt evolution.",
            DeprecationWarning,
            stacklevel=2
        )
        # Keep implementation for backward compat
        ...
```

### 3.4 Teste de Verificação Fase 3

```bash
# 1. Confirmar que nada quebrou
pytest tests/refactor/test_agents_baseline.py::TestAgentBaseline::test_coder_instantiation -v
pytest tests/refactor/test_agents_baseline.py::TestAgentBaseline::test_coder_evaluate_code -v

# 2. Testar que funcionalidades core do Coder ainda funcionam
pytest tests/e2e/test_all_agents.py::TestCoderAgentE2E -v
```

### 3.5 Checklist Fase 3
- [ ] Adicionar deprecation warnings
- [ ] Atualizar docstrings
- [ ] Rodar testes
- [ ] Commit: `deprecate(coder): mark DarwinGodelMixin as deprecated`

---

## FASE 4: Simplificar DeepThink (4 → 2 stages)

### 4.1 Objetivo
Reduzir de 4 estágios para 2, mantendo funcionalidade essencial.

### 4.2 Análise dos Estágios Atuais

| Estágio | Função Real | Decisão |
|---------|-------------|---------|
| Static Analysis | Regex + AST | **MANTER** |
| Deep Reasoning | Ajusta confidence | MERGE |
| Critique | Gera sugestões | MERGE |
| Validation | Filtra low confidence | **MANTER** |

### 4.3 Novo Design: 2 Estágios

```
Stage 1: Analysis (Static + Reasoning)
    - Pattern matching
    - AST inspection
    - Context-aware confidence adjustment

Stage 2: Validation (Critique + Filter)
    - Generate suggestions
    - Filter false positives
    - Build final result
```

### 4.4 Mudanças

**Novo arquivo**: `src/agents/reviewer/deep_think_v2.py`

```python
"""
Deep Think Security Analysis V2

Simplified 2-stage pipeline (was 4 stages).
Maintains same output format for backward compatibility.
"""

class DeepThinkV2Mixin:
    """
    Simplified Deep Think with 2 stages:
    1. Analysis: static + reasoning
    2. Validation: critique + filter
    """

    async def deep_think_review(self, code: str, file_path: str, language: str = None):
        """Perform Deep Think security review (V2)."""
        # Stage 1: Analysis
        findings, steps = self._stage_analysis(code, file_path, language)

        # Stage 2: Validation
        validated, rejected = self._stage_validation(findings)

        return ReviewResult(...)

    def _stage_analysis(self, code, file_path, language):
        """Combined static analysis + reasoning."""
        # Merge logic from:
        # - _stage_static_analysis
        # - _stage_deep_reasoning
        ...

    def _stage_validation(self, findings):
        """Combined critique + validation."""
        # Merge logic from:
        # - _stage_critique
        # - _stage_validation
        ...
```

### 4.5 Migração Gradual

```python
# src/agents/reviewer/agent.py

# Fase 4a: Usar V2 com flag
DEEP_THINK_V2 = os.environ.get("DEEP_THINK_V2", "0") == "1"

if DEEP_THINK_V2:
    from .deep_think_v2 import DeepThinkV2Mixin as DeepThinkMixin
else:
    from .deep_think import DeepThinkMixin
```

### 4.6 Teste de Verificação Fase 4

```bash
# 1. Testar V1 (default)
pytest tests/e2e/test_all_agents.py::TestReviewerAgentE2E -v

# 2. Testar V2
DEEP_THINK_V2=1 pytest tests/e2e/test_all_agents.py::TestReviewerAgentE2E -v

# 3. Comparar resultados
python tests/refactor/compare_deep_think_versions.py
```

### 4.7 Checklist Fase 4
- [ ] Criar `deep_think_v2.py`
- [ ] Implementar migração com flag
- [ ] Criar testes de comparação
- [ ] Validar que output é equivalente
- [ ] Commit: `refactor(reviewer): simplify DeepThink to 2 stages`

---

## FASE 5: Converter RAG Sub-Agents para Tools

### 5.1 Objetivo
Alinhar com Google ADK 2026: usar tools ao invés de sub-agents.

### 5.2 Mudanças

**Novo arquivo**: `src/agents/researcher/research_tools.py`

```python
"""
Research Tools - Replaces sub-agents with simple tools.
Follows Google ADK 2026 pattern.
"""

from vertice_cli.tools.base import BaseTool

class DocumentationSearchTool(BaseTool):
    """Search local documentation."""
    name = "doc_search"
    description = "Search local docs/ and README files"

    async def _execute(self, query: str, limit: int = 5):
        # Logic from DocumentationAgent.retrieve()
        ...

class WebSearchTool(BaseTool):
    """Search the web."""
    name = "web_search"
    description = "Search the web using DuckDuckGo"

    async def _execute(self, query: str, limit: int = 5):
        # Logic from WebSearchAgent.retrieve()
        ...

class CodebaseSearchTool(BaseTool):
    """Search the codebase."""
    name = "code_search"
    description = "Search codebase using grep"

    async def _execute(self, query: str, limit: int = 5):
        # Logic from CodebaseAgent.retrieve()
        ...
```

**Modificar**: `src/agents/researcher/agent.py`

```python
# ANTES (sub-agents)
class ResearcherAgent(AgenticRAGMixin, BaseAgent):
    def _init_retrieval_agents(self):
        self._retrieval_agents = {
            "docs": DocumentationAgent(),
            "web": WebSearchAgent(),
            "code": CodebaseAgent(),
        }

# DEPOIS (tools)
class ResearcherAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.tools = [
            DocumentationSearchTool(),
            WebSearchTool(),
            CodebaseSearchTool(),
        ]

    async def research(self, query: str):
        """Research using tools instead of sub-agents."""
        results = []
        for tool in self.tools:
            result = await tool.execute(query)
            results.extend(result)
        return self._synthesize(query, results)
```

### 5.3 Teste de Verificação Fase 5

```bash
# 1. Testar funcionalidade de pesquisa
pytest tests/e2e/test_all_agents.py::TestResearcherAgentE2E -v

# 2. Benchmark de latência (deve melhorar)
python -c "
import asyncio
import time
from agents import researcher

async def bench():
    start = time.time()
    async for _ in researcher.research('Python async patterns'):
        pass
    print(f'Duration: {time.time() - start:.2f}s')

asyncio.run(bench())
"
```

### 5.4 Checklist Fase 5
- [ ] Criar `research_tools.py`
- [ ] Modificar `researcher/agent.py`
- [ ] Remover sub-agents não utilizados
- [ ] Rodar testes
- [ ] Commit: `refactor(researcher): convert sub-agents to tools (Google ADK pattern)`

---

## FASE 6: Benchmark Final e Relatório

### 6.1 Métricas a Comparar

| Métrica | Baseline | Target | Como Medir |
|---------|----------|--------|------------|
| Total LOC | 5,487 | < 4,000 | `wc -l` |
| Tipos | 67 | < 50 | `grep -r "class\|@dataclass"` |
| Tempo instantiation | X ms | < X ms | pytest benchmark |
| Tempo plan() | X ms | < X ms | pytest benchmark |
| Tempo evaluate_code() | X ms | < X ms | pytest benchmark |

### 6.2 Script de Benchmark Final

**Arquivo**: `tests/refactor/benchmark_final.py`

```python
"""
Benchmark Final - Compara antes/depois da simplificação.
"""

import json
import time
import asyncio
from pathlib import Path

BASELINE_FILE = Path("tests/refactor/baseline_results.json")
FINAL_FILE = Path("tests/refactor/final_results.json")


async def run_benchmarks():
    results = {
        "timestamp": datetime.now().isoformat(),
        "version": "post-simplification",
    }

    # 1. Instantiation time
    from agents import orchestrator, coder, reviewer, architect, researcher, devops

    start = time.time()
    for _ in range(100):
        from agents import OrchestratorAgent
        OrchestratorAgent()
    results["instantiation_100x"] = time.time() - start

    # 2. Plan time
    start = time.time()
    for _ in range(10):
        await orchestrator.plan("Create a function")
    results["plan_10x"] = time.time() - start

    # 3. Evaluate time
    code = "def f(): pass"
    start = time.time()
    for _ in range(100):
        coder.evaluate_code(code, "python")
    results["evaluate_100x"] = time.time() - start

    # 4. LOC count
    import subprocess
    loc = subprocess.check_output(
        "find src/agents -name '*.py' | xargs wc -l | tail -1",
        shell=True
    ).decode().strip().split()[0]
    results["total_loc"] = int(loc)

    return results


def compare_results():
    with open(BASELINE_FILE) as f:
        baseline = json.load(f)
    with open(FINAL_FILE) as f:
        final = json.load(f)

    print("=" * 60)
    print("BENCHMARK COMPARISON: BEFORE vs AFTER")
    print("=" * 60)

    for key in final:
        if key in baseline and isinstance(final[key], (int, float)):
            before = baseline[key]
            after = final[key]
            improvement = ((before - after) / before) * 100
            print(f"{key}: {before} -> {after} ({improvement:+.1f}%)")


if __name__ == "__main__":
    results = asyncio.run(run_benchmarks())

    with open(FINAL_FILE, "w") as f:
        json.dump(results, f, indent=2)

    compare_results()
```

### 6.3 Checklist Fase 6
- [ ] Executar benchmark final
- [ ] Comparar com baseline
- [ ] Documentar melhorias
- [ ] Criar release notes
- [ ] Commit: `docs: add simplification benchmark results`

---

## Comandos de Verificação por Fase

```bash
# FASE 0
pytest tests/refactor/test_agents_baseline.py -v
python -c "from agents import *; print('Imports OK')"

# FASE 1
pytest tests/e2e/test_all_agents.py -v
black src/agents/ && ruff check src/agents/ --fix

# FASE 2
pytest tests/e2e/test_all_agents.py::TestArchitectAgentE2E -v

# FASE 3
pytest tests/e2e/test_all_agents.py::TestCoderAgentE2E -v

# FASE 4
DEEP_THINK_V2=1 pytest tests/e2e/test_all_agents.py::TestReviewerAgentE2E -v

# FASE 5
pytest tests/e2e/test_all_agents.py::TestResearcherAgentE2E -v

# FASE 6
python tests/refactor/benchmark_final.py
```

---

## Rollback Plan

Se qualquer fase falhar:

```bash
# 1. Reverter commits da fase atual
git revert HEAD~N  # N = número de commits da fase

# 2. Verificar que baseline passa
pytest tests/refactor/test_agents_baseline.py -v

# 3. Documentar o problema em ISSUES.md
```

---

## Timeline Estimada

| Fase | Duração | Risco |
|------|---------|-------|
| 0 | 1h | Baixo |
| 1 | 2h | Baixo |
| 2 | 3h | Médio |
| 3 | 1h | Baixo |
| 4 | 4h | Médio |
| 5 | 4h | Alto |
| 6 | 1h | Baixo |
| **Total** | **~16h** | - |

---

*Plano criado em 22/01/2026. Siga as fases na ordem para máxima segurança.*
