# VERTICE: Unified Evolution Plan

> **Merge de:** `CLAUDE_CODE_PARITY_PLAN.md` + `GEMINI_CODE_EVOLUTION_PLAN.md`
> **Data:** 2026-01-05
> **Objetivo:** Production-ready code generation & review

---

## 1. DIAGNÓSTICO CONSOLIDADO

### Score Atual: 70% → Target: 90%

```
Geração de Código:     [███████░░░] 70% → [█████████░] 90%
Revisão de Código:     [██████░░░░] 60% → [████████░░] 85%
Edição de Arquivos:    [████████░░] 85% → [█████████░] 92%
Contexto/Memória:      [██░░░░░░░░] 20% → [████████░░] 80%
```

### Vantagens VERTICE (Preservar)

| Feature | Status | Ação |
|---------|--------|------|
| Smart Matching 5 camadas | Funcional | Manter |
| Undo/Redo 100 ops + persistência | Funcional | Manter |
| AST-Aware Edit (Tree-sitter) | Funcional | Manter |
| Atomic Multi-Edit | Funcional | Manter |
| Backup automático | Funcional | Manter |

### Gaps Críticos (Corrigir)

| Gap | Severidade | Solução |
|-----|------------|---------|
| Regex Fallback | CRÍTICA | tool_config strict (Gemini) |
| Sem execução real | CRÍTICA | TDD Loop (Gemini) |
| RAG é stub | ALTA | Híbrido: Cache + RAG |
| Sem type checking | ALTA | pyright (Gemini) |
| Dual codebase | MÉDIA | Consolidar |

---

## 2. ARQUITETURA TARGET

```
┌─────────────────────────────────────────────────────────────┐
│                    VERTICE Code Engine                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ Context Layer │    │ Execution    │    │ Validation   │   │
│  │              │    │ Layer        │    │ Layer        │   │
│  │ • Cache (60m)│    │ • Sandbox    │    │ • pyright    │   │
│  │ • RAG (∞)    │    │ • TDD Loop   │    │ • bandit     │   │
│  │ • Skeleton   │    │ • pytest     │    │ • ruff       │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│           │                  │                  │            │
│           └──────────────────┼──────────────────┘            │
│                              ▼                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Tool Protocol                        │  │
│  │  • Strict JSON (tool_config mode=ANY)                 │  │
│  │  • NO regex fallback                                  │  │
│  │  • Retry com hint se falhar                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                              │                               │
│           ┌──────────────────┼──────────────────┐            │
│           ▼                  ▼                  ▼            │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │ CoderAgent   │    │ ReviewerAgent│    │ SecurityAgent│   │
│  │              │    │              │    │              │   │
│  │ • Generate   │    │ • Analyze    │    │ • Scan       │   │
│  │ • TDD Loop   │    │ • Score      │    │ • Block      │   │
│  │ • Validate   │    │ • Recommend  │    │ • Report     │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. PLANO DE IMPLEMENTAÇÃO

### FASE 1: Fundação (Blockers)

#### 1.1 Strict Tool Protocol
**Origem:** Gemini (refinado)
**Arquivos:** `providers/vertex_ai.py`, `agents/coder/agent.py`

```python
# ANTES (perigoso)
if not tool_calls:
    pattern = r"write_file\s*\(..."  # REGEX FALLBACK
    matches = re.findall(pattern, response)

# DEPOIS (seguro)
tool_config = {
    "function_calling_config": {
        "mode": "ANY"  # Força JSON estruturado
    }
}
# Se falhar: retry com hint, não parsear markdown
```

**Tarefas:**
- [ ] Remover regex fallback em `agents/coder/agent.py:184-198`
- [ ] Adicionar tool_config em providers (Vertex, OpenAI, Anthropic)
- [ ] Implementar retry com hint se tool call falhar
- [ ] Fail fast após 3 retries

#### 1.2 TDD Loop (Execution Layer)
**Origem:** Gemini
**Arquivos:** Novo `vertice_cli/tools/pytest_runner.py`, `agents/coder/agent.py`

```
Fluxo TDD:
1. PLAN    → Agente propõe mudança
2. TEST    → Agente cria test que FALHA
3. EXECUTE → Roda test (confirma falha)
4. IMPLEMENT → Edita código fonte
5. VERIFY  → Roda test (confirma sucesso)
```

**Tarefas:**
- [ ] Criar `RunPytestTool` com output JSON (stdout, stderr, exit_code)
- [ ] Criar `vertice_cli/core/execution/sandbox.py` com rlimit
- [ ] Integrar no fluxo do CoderAgent
- [ ] Timeout 30s por execução

#### 1.3 Contexto Híbrido
**Origem:** Merge (Claude + Gemini)

```
┌─────────────────────────────────────────────┐
│           Context Strategy                   │
├─────────────────────────────────────────────┤
│                                              │
│  SHORT-TERM (Sessão)     LONG-TERM (∞)      │
│  ┌─────────────────┐    ┌─────────────────┐ │
│  │ Context Cache   │    │ RAG Engine      │ │
│  │                 │    │                 │ │
│  │ • Skeleton dump │    │ • Issue history │ │
│  │ • Type sigs     │    │ • Error patterns│ │
│  │ • TTL 60 min    │    │ • Team standards│ │
│  │ • Vertex AI API │    │ • ChromaDB      │ │
│  └─────────────────┘    └─────────────────┘ │
│                                              │
└─────────────────────────────────────────────┘
```

**Tarefas:**
- [ ] Criar `core/context/skeleton.py` - extrai assinaturas sem corpos
- [ ] Criar `core/context/caching.py` - gerencia TTL do cache
- [ ] Implementar RAG real em `vertice_cli/agents/reviewer/rag_engine.py`
- [ ] Persistir embeddings em `.vertice/embeddings/`

---

### FASE 2: Qualidade (Production Grade)

#### 2.1 Static Analysis Pipeline
**Origem:** Merge

| Ferramenta | Função | Threshold |
|------------|--------|-----------|
| pyright | Type checking | 0 errors |
| bandit | Security scan | 0 HIGH/CRITICAL |
| ruff | Lint + format | Score ≥ 8.0 |
| semgrep | Pattern matching | 0 findings |

**Tarefas:**
- [ ] Criar `vertice_cli/tools/type_check.py` (wrapper pyright)
- [ ] Criar `vertice_cli/tools/security_scan.py` (wrapper bandit + semgrep)
- [ ] Integrar pipeline em `CoderAgent.evaluate_code()`
- [ ] Auto-reject em violations críticas

#### 2.2 Expandir EvaluationResult
**Origem:** Claude
**Arquivo:** `agents/coder/types.py`

```python
@dataclass
class EvaluationResult:
    # Existentes
    valid_syntax: bool
    lint_score: float
    quality_score: float
    issues: List[str]
    suggestions: List[str]

    # NOVOS (Fase 2)
    type_errors: List[str]       # pyright output
    security_issues: List[str]   # bandit + semgrep
    test_passed: bool            # TDD result
    test_output: str             # pytest stdout
    execution_time: float        # Performance
    import_errors: List[str]     # Missing deps

    @property
    def production_ready(self) -> bool:
        return (
            self.valid_syntax and
            len(self.type_errors) == 0 and
            len(self.security_issues) == 0 and
            self.test_passed and
            self.quality_score >= 0.8
        )
```

#### 2.3 Docstring Enforcement
**Origem:** Gemini
**Padrão:** Google Style Guide

**Tarefas:**
- [ ] Criar `AuditDocsTool` que verifica cobertura
- [ ] Threshold: 100% funções públicas documentadas
- [ ] Auto-generate docstrings se missing

---

### FASE 3: Consolidação

#### 3.1 Unificar Codebase
**Origem:** Claude

```
ANTES:
agents/reviewer/          ← Legacy (Deep Think)
vertice_cli/agents/reviewer/  ← Production

DEPOIS:
vertice_cli/agents/reviewer/  ← Único, com Deep Think integrado
```

**Tarefas:**
- [ ] Mover `agents/reviewer/deep_think.py` para `vertice_cli/`
- [ ] Deprecar diretório `agents/reviewer/`
- [ ] Atualizar todos os imports
- [ ] Atualizar testes

#### 3.2 Configuração por Projeto
**Arquivo:** `.vertice/quality.yaml`

```yaml
# .vertice/quality.yaml
thresholds:
  max_cyclomatic: 15
  max_cognitive: 20
  min_coverage: 80
  min_doc_coverage: 100

tools:
  pyright: strict
  bandit: medium
  ruff: all

execution:
  timeout: 30
  sandbox: true
```

---

## 4. ARTEFATOS A CRIAR

| Componente | Função | LOC Est. |
|------------|--------|----------|
| `vertice_cli/tools/pytest_runner.py` | TDD Loop executor | ~150 |
| `vertice_cli/core/execution/sandbox.py` | Isolamento com rlimit | ~200 |
| `vertice_cli/tools/type_check.py` | Wrapper pyright | ~100 |
| `vertice_cli/tools/security_scan.py` | Wrapper bandit + semgrep | ~150 |
| `core/context/skeleton.py` | Extrator de assinaturas | ~200 |
| `core/context/caching.py` | Gerenciador de cache | ~150 |
| Refactor `rag_engine.py` | RAG real com embeddings | ~300 |

**Total estimado:** ~1,250 LOC novos

---

## 5. PRIORIZAÇÃO

### Sprint 1 (Quick Wins)
1. **Remover regex fallback** - 1h, elimina risco crítico
2. **Adicionar tool_config strict** - 2h, força JSON
3. **Expandir EvaluationResult** - 1h, estrutura

### Sprint 2 (Execution)
4. **Criar sandbox.py** - 4h
5. **Criar pytest_runner.py** - 3h
6. **Integrar TDD Loop** - 4h

### Sprint 3 (Validation)
7. **Criar type_check.py** - 2h
8. **Criar security_scan.py** - 3h
9. **Integrar pipeline** - 2h

### Sprint 4 (Context)
10. **Implementar skeleton.py** - 4h
11. **Implementar caching.py** - 3h
12. **RAG real** - 6h

### Sprint 5 (Polish)
13. **Consolidar codebase** - 4h
14. **Config por projeto** - 2h
15. **Testes E2E** - 4h

---

## 6. MÉTRICAS DE SUCESSO

| Métrica | Antes | Target | Como Medir |
|---------|-------|--------|------------|
| Code executa sem crash | 60% | 95% | TDD Loop pass rate |
| Type errors detectados | 0% | 100% | pyright integration |
| Security issues blocked | 80% | 99% | bandit + semgrep |
| Context relevância | 20% | 80% | Cache hit rate |
| False positive rate | 15% | 5% | Review audit |

---

## 7. DECISÕES ARQUITETURAIS

### D1: pyright > mypy
**Razão:** 10x mais rápido, melhor para CI/CD

### D2: Context Cache + RAG (não OR)
**Razão:** Cache para sessão, RAG para memória longa

### D3: TDD obrigatório para mudanças
**Razão:** Código sem teste = código não validado

### D4: tool_config strict sem fallback
**Razão:** Regex é inseguro e imprevisível

### D5: Sandbox com rlimit (não Docker)
**Razão:** Menor overhead, suficiente para Python

---

## 8. RISCOS E MITIGAÇÕES

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| LLM não usa tools | Média | Alto | Retry com hint, fail after 3 |
| Sandbox escape | Baixa | Crítico | rlimit + no network |
| Cache miss | Alta | Médio | Fallback para full context |
| pyright lento em projetos grandes | Média | Médio | Cache incremental |

---

## 9. CONCLUSÃO

Este plano unifica:
- **Análise de arquitetura** (Claude) - preserva vantagens VERTICE
- **Rigor de execução** (Gemini) - TDD Loop, strict tooling
- **Contexto híbrido** - Cache curto prazo + RAG longo prazo

**Resultado esperado:** 90% de paridade com Claude Code, com vantagens em edição (smart match, undo/redo) e execução (TDD obrigatório).

---

## Referências

- [Vertex AI: Context Caching](https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview)
- [Vertex AI: Function Calling](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling)
- [pyright](https://github.com/microsoft/pyright)
- [bandit](https://bandit.readthedocs.io/)

---

*VERTICE Framework - Unified Evolution Plan*
*2026-01-05 - Soli Deo Gloria*