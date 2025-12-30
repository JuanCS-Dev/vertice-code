# PLANO DE EVOLUÇÃO DISRUPTIVA: VERTICE AGENTS 2028

> **Objetivo:** Evoluir 20+ agentes existentes para estado-da-arte 2025/2028 baseado em pesquisas de dezembro 2025
> **Método:** Auditoria brutal + Pesquisa profunda + Implementação faseada

---

## PARTE 1: PESQUISAS CONSOLIDADAS (Dezembro 2025)

### 1.1 Técnicas Disruptivas por Categoria de Agente

| Categoria | Técnica SOTA 2025 | Fonte | Métrica |
|-----------|-------------------|-------|---------|
| **Planning** | LLaMAR + Tree-of-Thought | [Long-Horizon Planning](https://openreview.net/forum?id=Y1rOWS2Z4i) | Plan-act-correct-verify |
| **Execution** | E2B + Firecracker microVMs | [E2B](https://e2b.dev/), [LLM Sandbox](https://github.com/vndee/llm-sandbox) | Secure isolation |
| **Exploration** | LocAgent (graph-based) | [LocAgent Yale/Stanford](https://www.marktechpost.com/2025/03/23/meet-locagent-graph-based-ai-agents-transforming-code-localization-for-scalable-software-maintenance/) | Graph code localization |
| **Refactoring** | MANTRA multi-agent + RL | [MANTRA](https://arxiv.org/html/2503.14340v2) | 582/703 compilable (50% melhor) |
| **Testing** | Meta ACH mutation-guided | [Meta ACH](https://engineering.fb.com/2025/02/05/security/revolutionizing-software-testing-llm-powered-bug-catchers-meta-ach/) | Mutation + test gen combined |
| **Security** | CodeMender Deep Think | [CodeMender DeepMind](https://deepmind.google/blog/introducing-codemender-an-ai-agent-for-code-security/) | 72 fixes upstream, 90% faster |
| **Performance** | Meta Zoomer auto-profiling | [Meta Zoomer](https://engineering.fb.com/2025/11/21/data-infrastructure/zoomer-powering-ai-performance-meta-intelligent-debugging-optimization/) | Tens of thousands profiles/day |
| **Documentation** | RepoAgent + ai-doc-gen | [RepoAgent](https://github.com/OpenBMB/RepoAgent) | Multi-agent AST-aware docs |
| **Database** | Oracle AI 26ai + dba.ai | [Oracle AI](https://www.oracle.com/database/ai-native-database-26ai/) | Autonomous DBA |
| **DevOps/SRE** | AWS DevOps Agent | [AWS DevOps Agent](https://aws.amazon.com/blogs/aws/aws-devops-agent-helps-you-accelerate-incident-response-and-improve-system-reliability-preview/) | 90% faster incident response |
| **Code Review** | CodeRabbit + Snyk DeepCode | [CodeRabbit](https://www.coderabbit.ai/) | 46% bug detection |
| **Self-Improvement** | Darwin Gödel Machine | [Sakana AI](https://sakana.ai/dgm/) | 20%→50% SWE-bench |

### 1.2 Infraestrutura Core

| Sistema | Técnica SOTA 2025 | Fonte |
|---------|-------------------|-------|
| **Memory** | MIRIX 6-type cognitive | [MIRIX](https://arxiv.org/html/2507.07957v1) |
| **Multi-Agent** | A2A + MCP protocols | [A2A](https://www.iguazio.com/blog/orchestrating-multi-agent-workflows-with-mcp-a2a/) |
| **Governance** | Constitutional AI + GaaS | [GaaS](https://arxiv.org/html/2508.18765v2) |
| **Evaluation** | AgentBench + CLASSic | [AgentBench](https://github.com/THUDM/AgentBench) |
| **Observability** | OpenTelemetry AI + Langfuse | [OpenTelemetry](https://opentelemetry.io/blog/2025/ai-agent-observability/) |
| **Cost** | Smart routing 80% reduction | [LLM Cost Optimization](https://ai.koombea.com/blog/llm-cost-optimization) |
| **Context** | Semantic chunking + MemAgent | [Context Engineering](https://blog.langchain.com/context-engineering-for-agents/) |
| **Recovery** | Self-healing + circuit breakers | [Fault Tolerance](https://www.getmonetizely.com/articles/how-to-build-resilient-agentic-ai-systems-designing-for-fault-tolerance-and-recovery) |

---

## PARTE 2: AUDITORIA BRUTAL DOS AGENTES

### 2.1 Resumo Executivo

```
TOTAL DE AGENTES: 20+
IMPLEMENTAÇÃO MÉDIA: 42%
PRODUCTION READY: 0%
GAPS CRÍTICOS: Memory Cortex não integrado, Providers não wired, 50% TODOs
```

### 2.2 Agentes Principais (agents/)

| Agente | Arquivo | Linhas | Implementação | Gaps Críticos |
|--------|---------|--------|---------------|---------------|
| **Orchestrator** | `agents/orchestrator/agent.py` | 253 | 50% | `plan()` é stub, zero Memory Cortex |
| **Coder** | `agents/coder/agent.py` | 231 | 70% | Imports quebrados, sem Memory |
| **Reviewer** | `agents/reviewer/agent.py` | 282 | 60% | Regex-only (inadequado), sem LLM |
| **Architect** | `agents/architect/agent.py` | 273 | 20% | 3 TODOs, ADR não gera via LLM |
| **Researcher** | `agents/researcher/agent.py` | 240 | 50% | Web search fake, summarize=truncate |
| **DevOps** | `agents/devops/agent.py` | 299 | 20% | Zero execução real, blacklist security |

### 2.3 Agentes Especializados (cli/agents/)

| Agente | Versão | Implementação | Risco |
|--------|--------|---------------|-------|
| **PlannerAgent** | 6.1 | 55% | ALTO - GOAP não funciona |
| **ExecutorAgent** | Nov 2025 | 85% | MÉDIO - E2B stub |
| **ExplorerAgent** | v1 | 90% | BAIXO - Funcional |
| **RefactorerAgent** | 8.0 | 45% | CRÍTICO - str.replace() danifica código |
| **TestingAgent** | ? | 60% | ALTO - Não gera testes |
| **SecurityAgent** | ? | 75% | MÉDIO - Sem tools CLI |
| **PerformanceAgent** | ? | 70% | MÉDIO - Sem profiling |
| **DocumentationAgent** | ? | 65% | MÉDIO - Não gera docs |
| **DataAgent** | 1.0 | 60% | ALTO - Não acessa DB |

### 2.4 Governance + Self-Improvement

| Sistema | Status | Gap Principal |
|---------|--------|---------------|
| **JUSTIÇA** | 80% framework, 0% integração | Nunca é chamado pelos agents |
| **SOFIA** | 70% teoria, 0% funcionando | String matching gera false positives |
| **Prometheus** | 85% estrutura, 5% funcionando | Sem persistência cross-sessão |
| **Memory Cortex** | 90% in-memory, 0% persistência | LanceDB config existe mas não usado |
| **MCP/A2A** | 50% agent cards, 0% messaging | Zero comunicação entre agents |

### 2.5 Gaps Cross-Cutting CRÍTICOS

1. **Memory Cortex não integrado** - Cortex EXISTS mas nenhum agent o usa
2. **Providers Router não wired** - Router exists mas agents não o chamam
3. **50% TODOs** - 11 explicit TODO comments = skeleton code
4. **Zero Error Handling** - 1 try/except em 1600 linhas
5. **Fake Async** - `async def` sem await interno

---

## PARTE 3: PLANO DE IMPLEMENTAÇÃO FASEADO

### FASE 0: FUNDAÇÃO (Dias 1-3) - BLOCKER
**Objetivo:** Wiring crítico para que QUALQUER coisa funcione

```
┌─────────────────────────────────────────────────────────────────────┐
│ DIA 1: WIRING PROVIDERS → AGENTS                                   │
├─────────────────────────────────────────────────────────────────────┤
│ □ Mover providers/ para location acessível a agents/               │
│ □ Criar agents/base.py com get_llm() que usa VerticeRouter         │
│ □ Cada agent herda BaseAgent e tem acesso a LLM real               │
│ □ Testar: Orchestrator consegue chamar Claude                      │
│                                                                     │
│ Arquivos a modificar:                                               │
│ - agents/__init__.py                                                │
│ - agents/base.py (criar)                                            │
│ - agents/orchestrator/agent.py                                      │
│ - providers/__init__.py                                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ DIA 2: WIRING MEMORY CORTEX → AGENTS                               │
├─────────────────────────────────────────────────────────────────────┤
│ □ Integrar get_cortex() em BaseAgent                                │
│ □ Cada action de agent loga para episodic memory                    │
│ □ Cada resultado consulta semantic memory para context              │
│ □ Testar: Coder lembra do que gerou na sessão anterior              │
│                                                                     │
│ Arquivos a modificar:                                               │
│ - agents/base.py                                                    │
│ - memory/cortex/memory.py (adicionar persistence)                   │
│ - agents/coder/agent.py                                             │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ DIA 3: ERROR HANDLING + OBSERVABILITY                               │
├─────────────────────────────────────────────────────────────────────┤
│ □ Adicionar try/except com retry em todos os async methods         │
│ □ Implementar circuit breaker pattern                               │
│ □ Adicionar logging estruturado (OpenTelemetry-compatible)          │
│ □ Testar: Agent falha gracefully e tenta de novo                   │
│                                                                     │
│ Arquivos a modificar:                                               │
│ - agents/base.py (error handling mixin)                             │
│ - cli/core/mcp.py (circuit breaker já existe, integrar)             │
└─────────────────────────────────────────────────────────────────────┘
```

### FASE 1: AGENTES CORE (Dias 4-10)
**Objetivo:** 6 agentes principais funcionais com LLM real

```
ORCHESTRATOR (Dia 4)
━━━━━━━━━━━━━━━━━━━
□ Implementar plan() com LLM call real
□ Implementar execute() com delegation real
□ Integrar com Memory Cortex para context
□ Técnica: Bounded Autonomy (L0-L3 sovereignty)
Fonte: SOTA → Hybrid Mesh Architecture

CODER (Dia 5)
━━━━━━━━━━━━
□ Corrigir imports de providers
□ Implementar syntax validation (ast.parse)
□ Adicionar test generation automático
□ Técnica: Streaming + validation loop
Fonte: SOTA → SWE-agent pattern

REVIEWER (Dia 6)
━━━━━━━━━━━━━━━
□ Substituir regex por LLM analysis
□ Integrar bandit/semgrep para SAST real
□ Implementar Deep Think reasoning
□ Técnica: Multi-pass security review
Fonte: SOTA → CodeMender (DeepMind)

ARCHITECT (Dia 7)
━━━━━━━━━━━━━━━━━
□ Implementar design() com LLM
□ Gerar ADRs reais via LLM
□ Integrar com Memory para patterns
□ Técnica: Three Loops Meta-Design
Fonte: SOTA → ADR + LLM

RESEARCHER (Dia 8)
━━━━━━━━━━━━━━━━━━
□ Implementar web search REAL (via MCP)
□ Substituir truncation por summarization LLM
□ Integrar com semantic memory
□ Técnica: Agentic RAG + System 2
Fonte: SOTA → DeepRetriever

DEVOPS (Dias 9-10)
━━━━━━━━━━━━━━━━━━
□ Implementar execução real em sandbox
□ Substituir blacklist por whitelist security
□ Integrar com Docker/K8s
□ Técnica: AWS DevOps Agent pattern
Fonte: SOTA → Autonomous SRE
```

### FASE 2: AGENTES ESPECIALIZADOS (Dias 11-20)
**Objetivo:** 9 agentes CLI funcionais

```
SEMANA 2.1 (Dias 11-13)
━━━━━━━━━━━━━━━━━━━━━━━
PLANNER (Dia 11)
□ Implementar GOAP real (A* pathfinding)
□ Clarifying questions via callback
□ Multi-plan generation

EXECUTOR (Dia 12)
□ Implementar E2B integration real
□ Token tracking funcional
□ Streaming LLM

EXPLORER (Dia 13)
□ Adicionar cache de resultados
□ Semantic pre-processing
□ Relationship analysis

SEMANA 2.2 (Dias 14-17)
━━━━━━━━━━━━━━━━━━━━━━━
REFACTORER (Dia 14) - CRÍTICO
□ Substituir str.replace() por LibCST real
□ Implementar semantic validation
□ Adicionar test running
Técnica: MANTRA multi-agent

TESTER (Dia 15)
□ Implementar test generation via LLM
□ Integrar pytest-cov
□ Mutation testing (mutmut)
Técnica: Meta ACH pattern

SECURITY (Dia 16)
□ Integrar bandit subprocess
□ OWASP scoring real
□ Remediation automation
Técnica: CrowdStrike MAS

PERFORMANCE (Dia 17)
□ Integrar cProfile
□ memory_profiler integration
□ Big-O estimation AST
Técnica: Meta Zoomer

SEMANA 2.3 (Dias 18-20)
━━━━━━━━━━━━━━━━━━━━━━━
DOCUMENTATION (Dia 18)
□ AST parsing real
□ Docstring generation via LLM
□ README auto-generation
Técnica: RepoAgent

DATA (Dias 19-20)
□ Query optimization via LLM
□ Schema analysis
□ Migration planning
Técnica: dba.ai pattern
```

### FASE 3: GOVERNANCE + SELF-IMPROVEMENT (Dias 21-27)
**Objetivo:** Constitutional AI + Darwin-Gödel funcionais

```
GOVERNANCE (Dias 21-23)
━━━━━━━━━━━━━━━━━━━━━━━
□ Integrar JUSTIÇA com todos os agents
□ Implementar trust scoring em tempo real
□ Sovereignty levels enforced
□ Sofia: substituir string matching por embedding similarity
□ GaaS: quantitative trust scores

SELF-IMPROVEMENT (Dias 24-27)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Persistir evolution_history (SQLite)
□ Implementar learn_pattern() calls em produção
□ Auto-trigger consolidation to vault
□ Curriculum que persiste cross-sessão
Técnica: Darwin Gödel Machine
```

### FASE 4: INTEGRATION + POLISH (Dias 28-30)
**Objetivo:** Sistema coeso e testado

```
A2A MESSAGING (Dia 28)
━━━━━━━━━━━━━━━━━━━━━━
□ Implementar agent-to-agent communication
□ Agent Cards → routing real
□ Handoff protocol funcional

LANCEDB INTEGRATION (Dia 29)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Embeddings via Gemini/Cohere
□ Semantic search real (não Jaccard)
□ Persistence to disk

TESTING + DOCS (Dia 30)
━━━━━━━━━━━━━━━━━━━━━━━
□ Unit tests para cada agent
□ Integration test multi-agent
□ Atualizar documentação
```

### FASE 5: AUDITORIA BRUTAL DE AIRGAPS + INTEGRAÇÃO TOTAL (Dias 31-35)
**Objetivo:** ZERO airgaps - Sistema 100% coeso e interconectado

> **PRINCÍPIO:** Implementar NÃO é suficiente. Integração PERFEITA é o segredo.
> Cada componente deve estar WIRED com todos os outros que dependem dele.

```
┌─────────────────────────────────────────────────────────────────────┐
│ DIA 31: AUDITORIA BRUTAL DE AIRGAPS                                │
├─────────────────────────────────────────────────────────────────────┤
│ Metodologia: Para CADA agent, verificar:                           │
│                                                                     │
│ □ AIRGAP #1: PROVIDERS                                              │
│   ├─ Agent usa get_router()? (não hardcoded)                        │
│   ├─ LLM calls passam pelo VerticeRouter?                           │
│   ├─ Fallback configurado (Claude→Gemini→Local)?                    │
│   └─ Cost tracking integrado?                                       │
│                                                                     │
│ □ AIRGAP #2: MEMORY CORTEX                                          │
│   ├─ Agent loga actions em episodic memory?                         │
│   ├─ Agent consulta semantic memory para context?                   │
│   ├─ Working memory limpa ao fim da task?                           │
│   └─ Resultados persistem em LanceDB (não apenas RAM)?              │
│                                                                     │
│ □ AIRGAP #3: GOVERNANCE                                             │
│   ├─ JUSTIÇA valida action ANTES de executar?                       │
│   ├─ Trust score é calculado e registrado?                          │
│   ├─ Sovereignty level (L0-L3) é enforced?                          │
│   └─ SOFIA aplica virtudes (não só string match)?                   │
│                                                                     │
│ □ AIRGAP #4: A2A COMMUNICATION                                      │
│   ├─ Agent pode receber mensagem de outro agent?                    │
│   ├─ Agent pode delegar para outro agent?                           │
│   ├─ Agent Cards são consultados para routing?                      │
│   └─ Handoff protocol funciona end-to-end?                          │
│                                                                     │
│ □ AIRGAP #5: OBSERVABILITY                                          │
│   ├─ Todas as calls têm trace_id?                                   │
│   ├─ Erros são logados com stack trace?                             │
│   ├─ Métricas de latência/tokens são coletadas?                     │
│   └─ Circuit breaker está integrado?                                │
│                                                                     │
│ ENTREGÁVEL: Matriz de airgaps por agent (20+ x 5 categorias)        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ DIA 32: DATA FLOW VERIFICATION                                      │
├─────────────────────────────────────────────────────────────────────┤
│ Verificar fluxo de dados END-TO-END:                                │
│                                                                     │
│ □ FLUXO 1: User Request → Orchestrator → Agent(s) → Response       │
│   ├─ Request é parseado corretamente?                               │
│   ├─ Orchestrator seleciona agent(s) correto(s)?                   │
│   ├─ Context é passado para agents?                                 │
│   └─ Response é aggregada e formatada?                              │
│                                                                     │
│ □ FLUXO 2: Agent → Memory Cortex → Agent                           │
│   ├─ Agent salva insight/resultado?                                 │
│   ├─ Outro agent consegue recuperar?                                │
│   └─ Persistence sobrevive restart?                                 │
│                                                                     │
│ □ FLUXO 3: Agent → Prometheus → Agent                               │
│   ├─ Agent registra pattern learned?                                │
│   ├─ Pattern é consolidado em skill?                                │
│   └─ Skill é aplicada em nova execução?                             │
│                                                                     │
│ □ FLUXO 4: Governance → Agent → Governance                          │
│   ├─ Pre-action validation funciona?                                │
│   ├─ Post-action logging funciona?                                  │
│   └─ Trust score é atualizado?                                      │
│                                                                     │
│ ENTREGÁVEL: Diagrama de fluxo verificado + test cases              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ DIAS 33-34: INTEGRATION FIXES                                       │
├─────────────────────────────────────────────────────────────────────┤
│ Para CADA airgap encontrado no Dia 31:                              │
│                                                                     │
│ □ Criar issue com descrição clara do gap                           │
│ □ Implementar fix minimal (sem over-engineering)                    │
│ □ Adicionar test que verifica integração                           │
│ □ Atualizar checklist de integração                                 │
│                                                                     │
│ PRIORIZAÇÃO:                                                        │
│ P0 (BLOCKER): Airgaps que impedem funcionamento básico              │
│ P1 (CRITICAL): Airgaps que causam perda de dados/contexto           │
│ P2 (HIGH): Airgaps que afetam observability                         │
│ P3 (MEDIUM): Airgaps que afetam performance                         │
│                                                                     │
│ REGRA: Não avançar até todos P0/P1 estarem resolvidos              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ DIA 35: INTEGRATION TEST SUITE + SMOKE TEST                         │
├─────────────────────────────────────────────────────────────────────┤
│ □ TEST 1: Multi-Agent Workflow                                      │
│   Input: "Refactor function X, test it, review security"            │
│   Verify: Coder → Tester → Security → todos usam Memory            │
│                                                                     │
│ □ TEST 2: Memory Persistence                                        │
│   Input: Task que gera insight                                      │
│   Restart sistema                                                   │
│   Verify: Insight persiste e é recuperável                          │
│                                                                     │
│ □ TEST 3: Governance Enforcement                                    │
│   Input: Task que viola política (ex: delete production)            │
│   Verify: JUSTIÇA bloqueia, SOFIA registra violação                │
│                                                                     │
│ □ TEST 4: Self-Improvement Loop                                     │
│   Input: Task repetida 3x com variações                             │
│   Verify: Prometheus detecta pattern, cria skill, aplica           │
│                                                                     │
│ □ TEST 5: Provider Failover                                         │
│   Input: Simular falha de Claude                                    │
│   Verify: Router fallback para Gemini funciona                      │
│                                                                     │
│ □ SMOKE TEST FINAL: 10 tasks reais em sequência                     │
│   Verify: Zero erros não tratados, logs completos, métricas ok     │
│                                                                     │
│ ENTREGÁVEL: Test suite automatizado + relatório de integração       │
└─────────────────────────────────────────────────────────────────────┘
```

#### 5.1 Checklist de Integração por Subsistema

```
PROVIDERS (VerticeRouter)
━━━━━━━━━━━━━━━━━━━━━━━━
□ Todos os 20+ agents usam get_router()
□ Zero LLM calls diretas (hardcoded)
□ Fallback chain testado
□ Cost tracking agregado
□ Rate limiting funcional

MEMORY CORTEX
━━━━━━━━━━━━
□ Todos os agents logam em episodic
□ Semantic memory populada com embeddings reais
□ Working memory não vaza entre tasks
□ LanceDB persistence verificada
□ Query performance < 100ms

GOVERNANCE (JUSTIÇA + SOFIA)
━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Pre-action hooks em todos os agents
□ Trust scores calculados (não fake)
□ Sovereignty levels enforced (L0-L3)
□ Audit log completo
□ Embedding similarity (não string match)

A2A + MCP
━━━━━━━━━
□ Agent Cards atualizados (20+)
□ Message passing funciona
□ Delegation chain testada (3+ deep)
□ Handoff protocol verificado
□ MCP tools expostos corretamente

PROMETHEUS (Self-Improvement)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Evolution history persiste
□ Pattern detection funciona
□ Skill consolidation automático
□ Curriculum cross-sessão
□ Metrics de improvement

OBSERVABILITY
━━━━━━━━━━━━━
□ Trace IDs em todas as calls
□ Error logging com context
□ Métricas de latência/tokens
□ Circuit breaker ativo
□ Dashboard/alertas configurados
```

#### 5.2 Matriz de Integração (Template)

```
| Agent           | Providers | Memory | Governance | A2A | Observ | TOTAL |
|-----------------|-----------|--------|------------|-----|--------|-------|
| Orchestrator    | □         | □      | □          | □   | □      | 0/5   |
| Coder           | □         | □      | □          | □   | □      | 0/5   |
| Reviewer        | □         | □      | □          | □   | □      | 0/5   |
| Architect       | □         | □      | □          | □   | □      | 0/5   |
| Researcher      | □         | □      | □          | □   | □      | 0/5   |
| DevOps          | □         | □      | □          | □   | □      | 0/5   |
| Planner         | □         | □      | □          | □   | □      | 0/5   |
| Executor        | □         | □      | □          | □   | □      | 0/5   |
| Explorer        | □         | □      | □          | □   | □      | 0/5   |
| Refactorer      | □         | □      | □          | □   | □      | 0/5   |
| Tester          | □         | □      | □          | □   | □      | 0/5   |
| Security        | □         | □      | □          | □   | □      | 0/5   |
| Performance     | □         | □      | □          | □   | □      | 0/5   |
| Documentation   | □         | □      | □          | □   | □      | 0/5   |
| Data            | □         | □      | □          | □   | □      | 0/5   |
| JUSTIÇA         | □         | □      | □          | □   | □      | 0/5   |
| SOFIA           | □         | □      | □          | □   | □      | 0/5   |
| Prometheus      | □         | □      | □          | □   | □      | 0/5   |
|-----------------|-----------|--------|------------|-----|--------|-------|
| TOTAL           | 0/18      | 0/18   | 0/18       |0/18 | 0/18   | 0/90  |

TARGET: 90/90 (100%) - Zero airgaps tolerados
```

---

## PARTE 4: ARQUIVOS CRÍTICOS A MODIFICAR

### Fase 0 (Fundação)
```
/media/juan/DATA/Vertice-Code/
├── agents/
│   ├── __init__.py              # Re-export + providers wiring
│   ├── base.py                  # CRIAR: BaseAgent com LLM + Memory
│   └── */agent.py               # Herdar de BaseAgent
├── providers/
│   └── __init__.py              # Export get_router()
└── memory/cortex/
    └── memory.py                # Adicionar persistence
```

### Fase 1 (Core Agents)
```
/media/juan/DATA/Vertice-Code/agents/
├── orchestrator/agent.py        # plan() + execute() reais
├── coder/agent.py               # Fix imports + validation
├── reviewer/agent.py            # LLM + SAST integration
├── architect/agent.py           # ADR via LLM
├── researcher/agent.py          # Web search real
└── devops/agent.py              # Sandbox execution
```

### Fase 2 (Specialized)
```
/media/juan/DATA/Vertice-Code/cli/agents/
├── planner/agent.py             # GOAP real
├── executor.py                  # E2B integration
├── explorer.py                  # Cache + semantic
├── refactorer.py                # LibCST (CRÍTICO)
├── testing.py                   # pytest + mutmut
├── security.py                  # bandit integration
├── performance.py               # cProfile integration
├── documentation.py             # AST + LLM docs
└── data_agent_production.py     # DB integration
```

### Fase 3 (Governance)
```
/media/juan/DATA/Vertice-Code/
├── vertice_governance/
│   ├── justica/                 # Trust enforcement real
│   └── sofia/                   # Embedding-based virtues
└── prometheus/
    ├── core/evolution.py        # Persistence
    └── memory/memory_system.py  # LanceDB real
```

---

## PARTE 5: DEPENDÊNCIAS A INSTALAR

```bash
# Fase 0: Core
pip install lancedb anthropic openai google-cloud-aiplatform

# Fase 1-2: Agents
pip install libcst bandit semgrep pytest-cov mutmut memory-profiler

# Fase 3: Governance
pip install sentence-transformers  # Para embeddings locais

# Fase 4: Integration
pip install opentelemetry-api opentelemetry-sdk langfuse
```

---

## PARTE 6: MÉTRICAS DE SUCESSO

| Fase | Métrica | Target |
|------|---------|--------|
| 0 | Agents chamam LLM real | 100% |
| 0 | Actions logados em Memory | 100% |
| 1 | Core agents funcionais | 6/6 |
| 2 | Specialized agents funcionais | 9/9 |
| 3 | Governance enforced | Trust scores calculados |
| 3 | Self-improvement | 1+ skill evolved |
| 4 | A2A messaging | Handoff funcional |
| 4 | Test coverage | >60% |
| **5** | **Matriz de Integração** | **90/90 (100%)** |
| **5** | **Airgaps P0/P1** | **ZERO** |
| **5** | **Data Flow E2E** | **4/4 fluxos** |
| **5** | **Integration Tests** | **5/5 passando** |
| **5** | **Smoke Test Final** | **10/10 tasks ok** |

### Critério de Conclusão FASE 5

```
┌────────────────────────────────────────────────────────────────┐
│ SISTEMA CONSIDERADO INTEGRADO SOMENTE QUANDO:                  │
├────────────────────────────────────────────────────────────────┤
│ ✓ Matriz de Integração = 90/90                                 │
│ ✓ Zero airgaps P0/P1 pendentes                                 │
│ ✓ Todos os 4 fluxos E2E verificados                            │
│ ✓ 5 integration tests passando                                 │
│ ✓ Smoke test com 10 tasks consecutivas sem erro               │
│ ✓ Memory persistence verificada (restart test)                 │
│ ✓ Provider failover testado                                    │
│ ✓ Governance blocking testado                                  │
└────────────────────────────────────────────────────────────────┘
```

---

## FONTES CONSOLIDADAS

### Agentes
- [SWE-agent](https://github.com/SWE-agent/SWE-agent) - SOTA coding agent
- [Refact.ai](https://refact.ai/) - 74.4% SWE-bench Verified
- [MANTRA](https://arxiv.org/html/2503.14340v2) - Multi-agent refactoring
- [Meta ACH](https://engineering.fb.com/2025/02/05/security/revolutionizing-software-testing-llm-powered-bug-catchers-meta-ach/) - Mutation testing
- [CodeMender](https://deepmind.google/blog/introducing-codemender-an-ai-agent-for-code-security/) - Security agent
- [AWS DevOps Agent](https://aws.amazon.com/blogs/aws/aws-devops-agent-helps-you-accelerate-incident-response-and-improve-system-reliability-preview/)
- [Azure SRE Agent](https://azure.microsoft.com/en-us/products/sre-agent)
- [LocAgent](https://www.marktechpost.com/2025/03/23/meet-locagent-graph-based-ai-agents-transforming-code-localization-for-scalable-software-maintenance/)
- [RepoAgent](https://github.com/OpenBMB/RepoAgent)
- [E2B](https://e2b.dev/)
- [LLM Sandbox](https://github.com/vndee/llm-sandbox)
- [CodeRabbit](https://www.coderabbit.ai/)

### Infraestrutura
- [MIRIX Memory](https://arxiv.org/html/2507.07957v1) - 6-type cognitive
- [Darwin Gödel Machine](https://sakana.ai/dgm/) - Self-improvement
- [A2A Protocol](https://www.iguazio.com/blog/orchestrating-multi-agent-workflows-with-mcp-a2a/)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Constitutional AI](https://constitutional.ai/)
- [GaaS Framework](https://arxiv.org/html/2508.18765v2)
- [AgentBench](https://github.com/THUDM/AgentBench)

### Observability & Cost
- [OpenTelemetry AI](https://opentelemetry.io/blog/2025/ai-agent-observability/)
- [Langfuse](https://langfuse.com/blog/2024-07-ai-agent-observability-with-langfuse)
- [LLM Cost Optimization](https://ai.koombea.com/blog/llm-cost-optimization)
- [Context Engineering](https://blog.langchain.com/context-engineering-for-agents/)
- [Fault Tolerance](https://www.getmonetizely.com/articles/how-to-build-resilient-agentic-ai-systems-designing-for-fault-tolerance-and-recovery)
- [Meta Zoomer](https://engineering.fb.com/2025/11/21/data-infrastructure/zoomer-powering-ai-performance-meta-intelligent-debugging-optimization/)

### Database & DBA
- [Oracle AI Database 26ai](https://www.oracle.com/database/ai-native-database-26ai/)
- [dba.ai](https://dba.ai/)
