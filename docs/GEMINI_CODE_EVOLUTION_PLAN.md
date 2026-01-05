# VERTICE: The Gemini Evolution Protocol
> *Supersedes `CLAUDE_CODE_PARITY_PLAN.md`*
> **Date:** 2026-01-05
> **Engine:** Vertex AI / Gemini 3 Pro
> **Doctrine:** Google Cloud Architecture Framework

## 1. BRUTAL AUDIT: The "Silent Failures"

O plano anterior do Claude identificou sintomas, mas errou no diagnóstico da causa raiz em pontos críticos.

### 1.1. O Falácia do RAG vs. Long Context
*   **Diagnóstico Claude:** "RAG Engine é um Stub. Precisamos de ChromaDB."
*   **Realidade Gemini:** RAG é uma muleta para modelos com janelas pequenas (4k-32k). O Gemini 1.5/2.0+ possui janelas de 1M+ tokens.
*   **Problema Real:** Não é a falta de busca vetorial, é a falta de **Relevância Estrutural**. Injetar snippets aleatórios via RAG confunde o modelo.
*   **Solução Google:** **Vertex AI Context Caching**. Podemos fazer cache da estrutura inteira do projeto (árvore de arquivos, assinaturas de tipos, docs principais) e reutilizar esse token cache a baixo custo.

### 1.2. O "Airgap" de Execução
*   **Diagnóstico Claude:** "CoderAgent valida sintaxe mas não roda."
*   **Realidade:** Isso torna o agente um "Consultor", não um "Engenheiro". Se ele não vê o `stderr`, ele está cego.
*   **Risco Crítico:** O código atual pode gerar imports circulares ou dependências fantasmas que o `ast.parse` aprova, mas o runtime explode.

### 1.3. A Vergonha do Regex Fallback
*   **Diagnóstico:** "Uso de Regex para catar tool calls."
*   **Veredito:** **Inaceitável em 2026.** Isso é programação de 2023.
*   **Correção:** O Vertex AI suporta `tool_config = { "function_calling_config": { "mode": "ANY" } }`. Isso obriga o modelo a retornar JSON estruturado ou falhar. Não deve haver "plano B" de texto.

---

## 2. IMPLEMENTATION PLAN (Google Stack)

### FASE 1: A "Fundação de Titânio" (Core Integrity)

#### 1.1 Strict Tooling Protocol
**Objetivo:** Eliminar alucinação de formato.
*   **Ação:** Refatorar `providers/vertex_ai.py`.
*   **Configuração:** Definir `tool_config` forçando output estruturado.
*   **Extermínio:** Remover *todo* código de regex parsing em `agents/coder/agent.py`. Se o modelo falhar em chamar a tool, o agente deve relatar "Tool Use Failure" e tentar novamente com hint, não tentar parsear markdown.

#### 1.2 The TDD Loop (Execution is King)
**Objetivo:** O agente escreve o teste *antes* ou *junto* com o código.
*   **Novo Fluxo:**
    1.  `Plan`: Agente propõe mudança.
    2.  `Test`: Agente cria `tests/temp/repro_issue.py` que falha.
    3.  `Execute`: Agente roda o teste (falha esperada).
    4.  `Implement`: Agente edita o código fonte.
    5.  `Verify`: Agente roda o teste (sucesso esperado).
*   **Ferramenta:** Criar `RunPytestTool` que retorna `stdout`, `stderr` e `exit_code`.

#### 1.3 Context Caching (Substituindo RAG inicial)
**Objetivo:** Onisciência do Codebase sem latência de RAG.
*   **Implementação:**
    *   Criar um "Skeleton Dump" do projeto (apenas assinaturas de classes/funções, sem corpos longos).
    *   Enviar isso para o Context Cache do Vertex AI com TTL de 60 min.
    *   Todos os agentes compartilham esse ID de cache.

---

### FASE 2: Qualidade e Segurança (Production Grade)

#### 2.1 Static Analysis Pipeline
Não basta o linter. Precisamos de deep static analysis.
*   **Ferramentas:**
    *   Integrar `pyright` (mais rápido que mypy) para type checking estrito.
    *   Integrar `bandit` para análise de segurança (hardcoded secrets, eval, etc).
*   **Policy:** O `CodeReviewer` rejeita automaticamente PRs com score baixo nessas ferramentas.

#### 2.2 "Google-Style" Docstrings
*   **Ação:** O agente deve garantir que toda função pública tenha docstrings no formato Google Style Guide.
*   **Automação:** Criar uma tool `AuditDocs` que verifica cobertura de documentação.

---

## 3. ARTEFATOS TÉCNICOS A CRIAR

| Componente | Função | Stack |
|:---|:---|:---|
| `vertice_cli/core/execution/sandbox.py` | Executa código do usuário isolado | `subprocess` com `rlimit` (inicial) |
| `vertice_cli/tools/pytest_runner.py` | Roda testes e formata output JSON | `pytest` |
| `providers/vertex_ai_strict.py` | Provider com enforcement de tools | Vertex AI SDK |
| `core/context/caching.py` | Gerencia o ciclo de vida do Context Cache | Vertex AI API |

## 4. IMMEDIATE NEXT STEPS

1.  **Purge:** Remover a lógica de Regex no `agents/coder`.
2.  **Enable:** Ativar `Function Calling` estrito no Vertex Provider.
3.  **Build:** Implementar `sandbox.py` para permitir que o agente rode seus próprios testes.

---
*Reference Docs:*
- [Vertex AI: Context Caching](https://cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview)
- [Vertex AI: Function Calling Config](https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling)
