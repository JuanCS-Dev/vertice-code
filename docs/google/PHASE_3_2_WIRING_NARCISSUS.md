# PHASE 3.2: WIRING NARCISSUS (THE SOVEREIGN FACE)

**STATUS:** PLANNING / READY FOR EXECUTION
**CONTEXT:** 2026 Google Singularity Architecture
**OBJECTIVE:** Connect the Agent Gateway to the Immersive UI/UX using CopilotKit and the Narcissus design language.

---

## 1. ESTRATÉGIA DE CONEXÃO (WIRING)

Não faremos uma simples integração de chat. Vamos injetar o protocolo **AG-UI** diretamente nos componentes imersivos rascunhados no **Google Stitch**.

### 1.1 O Elo Perdido: CopilotRuntime Adapter
No Next.js (`apps/web-console`), implementaremos um runtime customizado que atua como ponte:
- **Input:** Interações do usuário via componentes UI Narcissus.
- **Middleware:** `src/app/api/copilot/route.ts` consumindo o `/agui/tasks` do Gateway.
- **Output:** Stream SSE convertido para o formato esperado pelo CopilotKit, mantendo fidelidade aos eventos `delta`, `tool` e `error`.

---

## 2. ENTREGÁVEIS TÁTICOS (DIVISÃO DE PRs)

### PR 3.2-A: UI Foundation (O Esqueleto)
Foco em infraestrutura de frontend e conectividade.
- **Framework:** Setup do Next.js 16 no diretório `apps/web-console`.
- **Dependencies:** Instalação de `@copilotkit/react-core`, `@copilotkit/react-ui`, `framer-motion`, e `lucide-react`.
- **Styling:** Configuração base do **Tailwind v4** com o tema **Obsidian** (#0B1416) e variáveis **Neon Cyan** (#00E5FF).
- **Runtime:** Endpoint `/api/copilot` funcional, realizando o handshake com o `agent-gateway`.

### PR 3.2-B: Immersive Entry (A Face)
Implementação da primeira "camada" da visão Narcissus.
- **Landing Page:** Transformação do `vertice-lading-page/code.html` em componentes React funcionais.
- **Direct Command Input:** Um input central massivo que, ao receber o ENTER, dispara uma `Task` no backend e redireciona para o Stream Dashboard.
- **Status Mesh:** Indicador visual de "SYSTEM ONLINE" sincronizado com o `/healthz` do gateway.

### PR 3.2-C: Stream Visualization (A Consciência)
Onde o pensamento se torna visível.
- **CoT Dashboard:** Implementação do `refined_cot_logic_stream` usando o stream da tarefa ativa.
- **Task Progress:** Visualização de sub-tarefas e chamadas de ferramentas (eventos `tool` do AG-UI).
- **Code Preview:** Integração do componente de exibição de código gerado em tempo real.

---

## 3. REGRAS NÃO-NEGOCIÁVEIS (CONSTITUCIONAIS)

1. **Zero Chat Convencional:** A interface deve ser focada em "Command & Stream", não em balões de chat clássicos.
2. **Performance Obsessiva:** O streaming de texto deve ser renderizado sem "jank" (uso de buffers suaves).
3. **Fidelidade Estética:** Proibido o uso de cores fora da paleta Obsidian/Cyan/Emerald.
4. **Desacoplamento:** O frontend não acessa banco de dados nem APIs de terceiros diretamente; tudo passa pelo `agent-gateway`.

---

## 4. CRITÉRIOS DE ACEITE DA FASE 3.2

- [ ] `npm run build` no `apps/web-console` sem erros de tipo.
- [ ] Handshake `/api/copilot` -> `agent-gateway` validado via logs.
- [ ] Landing page renderiza a 60fps com animações Framer Motion.
- [ ] O comando digitado no frontend gera uma `task_id` real no backend.

**Signed,**
*Vertice-MAXIMUS*

---

## Pré‑requisito de Segurança (25 JAN 2026) — PR‑0/PR‑1

Antes do wiring do frontend, foi aplicado hardening no backend SaaS:
- **PR‑0 (RCE):** execução local de Python desabilitada (fail‑closed).
- **PR‑1 (GDPR/KMS):** master key obrigatória (sem geração efêmera).

Detalhes e validação: `docs/google/DETAILED_SURGERY_PREP_REPORT_2026.md`.
