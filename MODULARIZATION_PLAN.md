# PLANO DE MODULARIZAÇÃO VERTICE-CODE

> **Lei Suprema**: CODE_CONSTITUTION.md
> **Objetivo**: Todos os arquivos < 500 linhas, zero TODOs, 99% test coverage

---

## RESUMO EXECUTIVO

| Problema | Atual | Meta | Redução |
|----------|-------|------|---------|
| planner/agent.py | 2.553 linhas | 14 módulos < 400 linhas | -85% |
| test_500_brutal_tests.py | 7.210 linhas | ~455 linhas parametrizadas | -93.7% |
| pytest collection errors | 12 erros | 0 erros | -100% |
| exception handlers genéricos | 1.099 | ~100 específicos | -91% |
| shell=True | 58 | 0 | -100% |

---

## FASE 0: FIX CRÍTICO (pytest collection errors)

**Prioridade**: CRÍTICA - Bloqueia todos os testes

**Arquivo**: `vertice_cli/core/llm.py` (381 linhas)

**Problema**: Missing exports causam 12 erros de coleção

**Fix**:
```python
# Adicionar no topo (após imports existentes):
from .providers.resilience import CircuitBreaker, CircuitState
from .resilience import RateLimiter

# Adicionar no final do arquivo:
llm_client: LLMClient = get_llm_client()

__all__ = [
    "LLMClient",
    "RequestMetrics",
    "get_llm_client",
    "llm_client",
    "CircuitBreaker",
    "CircuitState",
    "RateLimiter",
]
```

**Resultado**: 12 → 0 collection errors

---

## FASE 1: MODULARIZAÇÃO planner/agent.py

**Problema**: 2.553 linhas, 24 classes, 41 métodos misturando 11 concerns

**Estrutura Proposta**:

```
vertice_cli/agents/planner/
├── __init__.py           (~30 linhas)  - Re-exports públicos
├── types.py              (~200 linhas) - Enums + modelos simples
├── models.py             (~300 linhas) - Modelos de domínio complexos
├── analyzers.py          (~200 linhas) - GOAPPlanner + DependencyAnalyzer
├── context.py            (~80 linhas)  - Gathering de contexto
├── goap_integration.py   (~120 linhas) - Workflow GOAP
├── optimization.py       (~100 linhas) - Stage building
├── safety.py             (~50 linhas)  - Risk assessment
├── formatting.py         (~100 linhas) - Output formatting
├── confidence.py         (~100 linhas) - Confidence scoring (v6.0)
├── clarification.py      (~70 linhas)  - User interaction (v6.0)
├── artifacts.py          (~150 linhas) - Plan artifacts (v6.0)
├── multi_planning.py     (~350 linhas) - Multi-plan generation (v6.1)
├── validators.py         (~80 linhas)  - Plan validation
├── monitoring.py         (~30 linhas)  - Observability
└── agent.py              (~400 linhas) - Orquestrador principal
```

### Ordem de Extração (DAG sem ciclos):

**Step 1.1**: `types.py` - 6 enums (63 linhas)
- ExecutionStrategy, AgentPriority, CheckpointType
- PlanningMode, ConfidenceLevel, PlanStrategy

**Step 1.2**: `types.py` - 8 modelos simples (174 linhas)
- ClarifyingQuestion, ClarificationResponse, StepConfidence
- PlanProbabilities, GoalState, ExecutionEvent

**Step 1.3**: `models.py` - 5 modelos complexos (~300 linhas)
- WorldState, Action, SOPStep, ExecutionStage
- ExecutionPlan, AlternativePlan, MultiPlanResult

**Step 1.4**: `analyzers.py` - Algoritmos puros (~200 linhas)
- GOAPPlanner (73 linhas) - A* pathfinding
- DependencyAnalyzer (127 linhas) - Graph analysis

**Step 1.5**: Módulos de feature (560 linhas total)
- context.py, goap_integration.py, optimization.py
- safety.py, formatting.py

**Step 1.6**: Módulos v6.0/v6.1 (670 linhas total)
- confidence.py, clarification.py, artifacts.py
- multi_planning.py

**Step 1.7**: Infraestrutura (110 linhas total)
- validators.py, monitoring.py

**Step 1.8**: Refactor agent.py (~400 linhas)
- Converter para thin orchestrator
- Dependency injection

---

## FASE 2: REFATORAÇÃO test_500_brutal_tests.py

**Problema**: 7.210 linhas, 500 testes quase idênticos

**Padrões Identificados**:
| Categoria | Testes | Linhas | Padrão |
|-----------|--------|--------|--------|
| Type_Confusion | 001-100 | 1.210 | modulo % 2, % 3 |
| None_Injection | 101-200 | 1.410 | modulo % 2 |
| Boundary_Violation | 201-300 | 1.010 | test_id * 1000 |
| Race_Condition | 301-400 | 1.210 | modulo % 10 |
| Exception_Path | 401-500 | 1.810 | modulo % 2 |

**Estrutura Proposta**:

```
tests/brutal/
├── conftest.py               (~60 linhas)  - Fixtures compartilhados
├── test_type_confusion.py    (~50 linhas)  - 1 test parametrizado
├── test_none_injection.py    (~80 linhas)  - 1 test parametrizado
├── test_boundary_violation.py (~70 linhas) - 1 test parametrizado
├── test_race_condition.py    (~85 linhas)  - 1 test parametrizado
└── test_exception_path.py    (~110 linhas) - 1 test parametrizado
```

**Exemplo de Conversão**:
```python
# ANTES: 100 funções quase idênticas (1210 linhas)
def test_001_type_confusion(): ...
def test_002_type_confusion(): ...
# ... até 100

# DEPOIS: 1 função parametrizada (50 linhas)
@pytest.mark.parametrize("test_id", range(1, 101))
def test_type_confusion(test_id, gov_mock):
    variation = test_id % 2
    # lógica unificada
```

**Fixtures a Extrair**:
- gov_mock, agent_executor_mock, gov_with_pipeline_mock
- agent_response_mock, agent_task_with_request
- agent_task_without_request, mock_executor_role, async_context

**DECISÃO**: Após migração bem-sucedida, **DELETAR** `test_500_brutal_tests.py`

---

## FASE 3: EXCEPTION HANDLERS (1.099 → ~100)

**Problema**: 1.099 `except Exception:` + 570 bare `except:`

**Estratégia**:
1. Criar hierarquia de exceções específicas
2. Substituir bare except por exceções específicas
3. Logar sempre (nunca silenciar)

**Hierarquia Proposta**:
```python
# vertice_core/exceptions.py
class VerticeError(Exception): pass
class AgentError(VerticeError): pass
class LLMError(VerticeError): pass
class ToolError(VerticeError): pass
class ValidationError(VerticeError): pass
class TimeoutError(VerticeError): pass
```

**Padrão de Fix**:
```python
# ANTES (proibido)
except Exception:
    pass

# DEPOIS (obrigatório)
except (LLMError, TimeoutError) as e:
    logger.error(f"Operation failed: {e}")
    raise
```

---

## FASE 4: shell=True (58 → 0)

**Problema**: 58 usos de shell=True (vulnerabilidade de injection)

**Estratégia**:
1. Localizar todos os usos: `grep -r "shell=True"`
2. Converter para shell=False com lista de argumentos
3. Usar shlex.split() onde necessário

**Padrão de Fix**:
```python
# ANTES (proibido)
subprocess.run(f"git commit -m '{message}'", shell=True)

# DEPOIS (obrigatório)
subprocess.run(["git", "commit", "-m", message], shell=False)
```

---

## FASE 5: RESOLVER TODOs (135 → 0)

**Decisão do usuário**: Implementar TODOS os TODOs agora (não converter para issues)

**Estratégia**:
1. Listar todos os TODOs: `grep -rn "TODO\|FIXME\|HACK" --include="*.py"`
2. Categorizar por tipo:
   - Implementação faltante → Implementar
   - Bug conhecido → Corrigir
   - Refatoração necessária → Refatorar
   - Documentação → Documentar
3. Remover cada TODO após resolução
4. Nunca deixar placeholder

**Padrão CODE_CONSTITUTION**:
```python
# PROIBIDO (Padrão Pagani):
# TODO: implement later
# FIXME: this is broken
# HACK: workaround

# PERMITIDO APENAS:
raise NotImplementedError(
    "Feature X requires dependency Y. "
    "Tracking ticket: VERTICE-123"
)
```

---

## CRONOGRAMA DE EXECUÇÃO

| Fase | Descrição | Arquivos | Prioridade |
|------|-----------|----------|------------|
| 0 | Fix pytest collection | 1 arquivo | CRÍTICA (PRIMEIRO) |
| 1.1-1.4 | Extract types/models/analyzers | 4 arquivos | ALTA |
| 1.5-1.8 | Extract features + refactor agent | 10 arquivos | ALTA |
| 2 | Refactor brutal tests + DELETAR original | 6 arquivos | MÉDIA |
| 3 | Exception handlers | ~50 arquivos | MÉDIA |
| 4 | shell=True fixes | ~20 arquivos | MÉDIA |
| 5 | Resolver 135 TODOs | ~30 arquivos | MÉDIA |

---

## MÉTRICAS DE SUCESSO (CODE_CONSTITUTION.md)

| Métrica | Antes | Depois | Target |
|---------|-------|--------|--------|
| Maior arquivo | 7.210 linhas | < 400 linhas | < 500 |
| pytest collection errors | 12 | 0 | 0 |
| Test coverage | ? | ≥ 99% | ≥ 99% |
| TODOs em produção | 135 | 0 | 0 |
| Bare except handlers | 1.669 | 0 | 0 |
| shell=True | 58 | 0 | 0 |

---

## ARQUIVOS CRÍTICOS A MODIFICAR

### Fase 0:
- `vertice_cli/core/llm.py`

### Fase 1:
- `vertice_cli/agents/planner/agent.py` (dividir)
- `vertice_cli/agents/planner/__init__.py` (criar)
- `vertice_cli/agents/planner/types.py` (criar)
- `vertice_cli/agents/planner/models.py` (criar)
- `vertice_cli/agents/planner/analyzers.py` (criar)
- + 9 módulos adicionais

### Fase 2:
- `tests/test_500_brutal_tests.py` → **DELETAR** após migração
- `tests/brutal/conftest.py` (criar)
- `tests/brutal/test_*.py` (criar 5 arquivos)

### Fase 5:
- ~30 arquivos com TODOs → implementar e remover markers

---

## VALIDAÇÃO PRÉ-MERGE (Guardian Agent)

Antes de cada merge:
```bash
# 1. Verificar tamanho de arquivos
find . -name "*.py" -exec wc -l {} \; | awk '$1 > 500 {print "VETO: " $2}'

# 2. Verificar TODOs
grep -r "TODO\|FIXME\|HACK" --include="*.py" src/ && echo "VETO: Placeholders"

# 3. Verificar testes
pytest --cov --cov-fail-under=99

# 4. Verificar tipos
mypy --strict .
```

---

*Plano seguindo CODE_CONSTITUTION.md - Padrão Pagani*
*Prepared: 2025-12-31*
*Soli Deo Gloria*
