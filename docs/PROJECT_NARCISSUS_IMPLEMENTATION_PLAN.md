# 🪞 PROJECT NARCISSUS: UI/UX UNIFICATION PLAN (2026)

**Data:** 10 de Janeiro de 2026
**Responsável:** Gemini-Native (Frontend Ops)
**Status:** 📝 PLANEJAMENTO
**Objetivo:** Unificar a identidade visual do Ecossistema Vertice (Landing + WebApp) e implementar "Semantic Streaming".

---

## 1. RESUMO EXECUTIVO
Este plano detalha a migração do WebApp Vertice de uma estética genérica ("Toxic Lime") para a identidade proprietária **"Deep Void & Electric Cyan"** definida na Landing Page V2. Além da correção visual, implementaremos o **Semantic Streaming Engine**, que transforma tokens de texto (emojis) em componentes de UI vivos e animados em tempo real.

---

## 2. FASE 1: A FUNDAÇÃO (THE VOID)
**Objetivo:** Eliminar a inconsistência de cores e tipografia.

### 1.1. Refatoração do `globals.css`
Substituir o sistema de cores atual (Shadcn default/Lime) pelas variáveis exatas da Landing V2.

| Variável | Valor Atual (Toxic Lime) | Novo Valor (Electric Cyan) |
| :--- | :--- | :--- |
| `--background` | `oklch(10% ...)` (Cinza) | `#050505` (Deep Void) |
| `--card` | `oklch(15% ...)` | `rgba(255, 255, 255, 0.03)` (Glass) |
| `--primary` | `oklch(85% ...)` (Lime) | `#06b6d4` (Cyan-500) |
| `--primary-foreground`| `oklch(5% ...)` | `#ffffff` (White) |
| `--ring` | `oklch(85% ...)` | `rgba(6, 182, 212, 0.5)` (Cyan Glow) |

### 1.2. Padronização Tipográfica
*   Garantir o carregamento da fonte **Geist Sans** e **Geist Mono** no `layout.tsx`.
*   Aplicar `--font-sans` globalmente no `body`.
*   Remover referências a `Inter` se existirem no WebApp.

### 1.3. Limpeza de Hardcoded Styles
*   Audit no `message-bubble.tsx` para remover classes arbitrárias (`bg-zinc-900`, `from-cyan-600`) e usar variáveis semânticas (`bg-card`, `bg-primary`).

---

## 3. FASE 2: A ALMA (SEMANTIC STREAMING)
**Objetivo:** Dar vida ao texto gerado pela IA. "Não leia o código, sinta o código."

### 2.1. Arquitetura do Semantic Parser
Implementar um pré-processador no `MarkdownRenderer` que intercepta tokens específicos antes da renderização final.

### 2.2. Dicionário Semântico (v1.0)

| Token | Significado | Componente React | Animação |
| :--- | :--- | :--- | :--- |
| `⚡` | Action/Exec | `<FlashAction />` | Glow Amarelo Pulsante |
| `🧠` | Reasoning | `<BrainProcess />` | Fade-in Suave + Pulso Rosa |
| `🔍` | Search | `<SearchRadar />` | Radar Sweep Animation |
| `🛡️` | Security | `<SecurityShield />` | Metallic Sheen |
| `💾` | Save | `<DiskWrite />` | Download Icon Bounce |
| `⚠️` | Warning | `<AlertBadge />` | Shake Vermelho |

### 2.3. Implementação Técnica
*   Criar componentes visuais em `components/chat/semantic-icons.tsx`.
*   Atualizar `components/chat/markdown-renderer.tsx` para usar `rehype-react` ou parsing customizado para substituir strings unicode pelos componentes.

---

## 4. FASE 3: O POLIMENTO (GLASS & GLOW)
**Objetivo:** Elevar o nível de "Premium Enterprise SaaS".

### 3.1. Glassmorphism System
*   Aplicar classes de backdrop-blur consistentes no Sidebar e Header.
*   Criar bordas sutis (`border-white/5`) para simular profundidade.

### 3.2. Micro-Interactions
*   Hover states nos botões de cópia e ações.
*   Transições suaves (`duration-300 ease-out-expo`) para entrada de mensagens.

---

## 5. CRITÉRIOS DE ACEITE (VERIFICAÇÃO)

### ✅ Check Visual
1.  [ ] O fundo do app é `#050505` absoluto?
2.  [ ] Botões primários são Cyan (`#06b6d4`)?
3.  [ ] Texto de código é `Geist Mono`?

### ✅ Check Funcional (Streaming)
1.  [ ] Ao digitar `🧠` no chat, ele vira um ícone animado?
2.  [ ] O ícone de `⚡` pulsa?
3.  [ ] A performance do streaming (FPS) se mantém estável?

### ✅ Check de Coesão
1.  [ ] Colocar a Landing Page e o App lado a lado: Parecem o mesmo produto?

---

## 6. ROLLBACK PLAN
*   Backup dos arquivos `globals.css` e `tailwind.config.ts` antes da alteração.
*   Se o parser semântico quebrar o streaming, reverter para `react-markdown` padrão via flag de feature.

---

*Aprovado para execução imediata.*
*Assinado: Juan Carlos de Souza (Arquiteto-Chefe)*
