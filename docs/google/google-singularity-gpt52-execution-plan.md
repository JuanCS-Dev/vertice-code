# Google Singularity — Plano de Execução (GPT‑5.2) (2026-01-24)

Decisões (travadas):
- **Memória:** AlloyDB desde o início.
- **Backend runtime:** `agent-gateway`.
- **Execução:** tudo remoto (Google gerenciado), **zero execução local**.
- **Chaves:** Cloud KMS desde o início.

## Objetivo (curto)
Entregar um caminho executável e seguro para: (1) remover RCE/local exec, (2) desacoplar SaaS↔CLI, (3) criar `agent-gateway` como runtime, (4) preparar AlloyDB+KMS como fundamentos obrigatórios.

## Regras não-negociáveis
- Nenhum endpoint em `vertice-chat-webapp/backend` pode executar código localmente via `exec()`/`eval()`/subprocess “solto”.
- O backend não pode importar `src.*` do monorepo; só dependências instaláveis (`vertice_core.*`).
- Chaves/cripto **sem fallback efêmero** em ambientes que não sejam testes.
- “Google gerenciado” significa: execução de código via **Vertex AI Code Interpreter** (ou equivalente), segredos via **KMS/Secret Manager**, runtime via **Cloud Run/Vertex**.

## Sequência sugerida de PRs (pequenas e revisáveis)

### PR-0 — Guardrails de segurança (bloqueio imediato)
Entregáveis:
- Remover/invalidar o fallback `exec(open(...))` em `vertice-chat-webapp/backend/app/sandbox/executor.py`.
- Alterar o comportamento para **fail-closed**: se não houver runtime gerenciado configurado, retornar erro explícito (“capability not enabled”).
- Ajustar testes do backend que assumem execução local (desativar feature por flag/fixture).

Critérios de aceite:
- `rg -n "exec\\(" vertice-chat-webapp/backend/app` não encontra `exec(` em paths de execução.
- Nenhuma rota dispara execução local em ambiente padrão.

### PR-1 — Chaves: KMS desde o início (sem “ephemeral key”)
Entregáveis:
- Em `vertice-chat-webapp/backend/app/core/gdpr_crypto.py`, remover fallback de chave efêmera fora de testes.
- Definir 1 interface clara: `KeyProvider` (KMS) + implementação “test key provider”.
- Configurar variáveis/identificadores (ex.: `KMS_KEY_NAME`) e validar na inicialização (fail-fast).

Critérios de aceite:
- Iniciar backend sem KMS configurado falha com mensagem clara (exceto modo teste).
- Dados criptografados não se tornam irrecuperáveis por restart.

### PR-2 — Desacoplamento mínimo SaaS↔CLI (pacote core instalável)
Entregáveis:
- Criar `packages/vertice-core/` com `pyproject.toml` e `src/vertice_core/`.
- Mover o mínimo necessário para destravar o backend (começar por `agents.security.patterns` e interfaces).
- Alterar `vertice-chat-webapp/backend` para depender de `-e ../../packages/vertice-core` e remover hacks de `sys.path`.
- Atualizar `vertice-chat-webapp/backend/app/core/security.py` para importar `vertice_core.*` (sem `src.*`).

Critérios de aceite:
- `rg -n "from src\\.|import src\\." vertice-chat-webapp/backend` retorna vazio.
- Backend roda com `pip install -e ../../packages/vertice-core` sem PYTHONPATH manual.

### PR-3 — `apps/agent-gateway` (runtime) com contrato de streaming
Entregáveis:
- Criar `apps/agent-gateway/` (FastAPI) com endpoints mínimos: `/healthz` e `/agui/stream`.
- Definir contrato de eventos AG‑UI (mínimo viável) em `packages/vertice-core/agui/protocol.py`.
- Implementar um adapter `ag_ui_adk` (mesmo que inicialmente com “mock agent”) para estabilizar o streaming.

Critérios de aceite:
- Um cliente (web/tui) consegue consumir `/agui/stream` e renderizar um stream consistente.
- Teste de contrato básico para o schema (unit).

### PR-4 — AlloyDB desde o início (fundação de memória)
Entregáveis:
- Definir conector AlloyDB (config, pool, migrations) em `packages/vertice-core/memory/`.
- Criar schema mínimo para memória/vetores (sem triggers pesadas no primeiro corte).
- Documentar tuning/índices e um caminho de migração incremental (batch embeddings).

Critérios de aceite:
- Conexão estabelecida + operações CRUD básicas com latência aceitável local/dev.
- Sem dependência em SQLite para “memória oficial”.

### PR-5 — Troca real para Google gerenciado (Vertex AI)
Entregáveis:
- Trocar “mock agent” do gateway por chamada real ao Vertex AI (Reasoning Engines / runtime escolhido).
- Ativar Code Interpreter gerenciado no fluxo (substitui 100% o executor local).
- Observabilidade mínima (logs/trace) e quotas.

Critérios de aceite:
- “Execução de código” só existe via capacidade gerenciada (Vertex), nunca local.

## Checklists de verificação rápida (baratos)
- Acoplamento: `rg -n "src\\.vertice_cli" vertice-chat-webapp/backend` deve retornar vazio.
- Execução local: `rg -n "exec\\(|eval\\(" vertice-chat-webapp/backend` deve retornar vazio (ou apenas em testes).
- Chaves: iniciar backend sem `KMS_KEY_NAME` deve falhar (exceto testes).

## Perguntas que ainda precisam de resposta (para não travar no meio)
- Qual serviço vai hospedar o Next.js: **Firebase App Hosting** é obrigatório já na primeira etapa, ou pode entrar após `agent-gateway` estabilizar?
- “AG‑UI”: vocês querem aderência estrita a um schema específico (se existir internamente) ou basta um MVP compatível com CopilotKit primeiro?

