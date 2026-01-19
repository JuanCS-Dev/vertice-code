# 🎨 RELATÓRIO DE AUDITORIA VISUAL: PROJETO NARCISSUS (2026)

**Data:** 10 de Janeiro de 2026
**Auditor:** Gemini-Native (Design Ops)
**Status:** ⚠️ **FRAGMENTAÇÃO VISUAL DETECTADA**

---

## 1. O DIAGNÓSTICO (A BELEZA VS. A BESTA)

Você perguntou se o nosso web-app é visualmente agradável e coeso. A resposta curta é: **Você tem dupla personalidade.**

### 🎭 O Conflito de Identidade
Encontrei três "almas" lutando pelo controle da UI:

1.  **A Landing Page (`landing_v2`):**
    *   **Vibe:** Cyberpunk Corporate, Deep Void (`#050505`) + Electric Cyan (`#06b6d4`).
    *   **Estética:** Bento Grids, Glassmorphism, Scanlines.
    *   **Veredito:** **Lindo. Moderno (2026).** É a cara do Vertice.

2.  **O WebApp Global (`globals.css`):**
    *   **Vibe:** "Toxic Neon".
    *   **Cor Primária:** Uma cor "Lime Green" (`#CCFF00`) definida como `--primary`.
    *   **Veredito:** **Datado (2023).** Conflita violentamente com o Cyan da Landing Page. Parece um template padrão da Vercel/Shadcn com cores trocadas.

3.  **O Chat Interface (`message-bubble.tsx`):**
    *   **Vibe:** Tentando ser a Landing Page.
    *   **Hardcoded:** Usa classes utilitárias `from-cyan-600 to-blue-700` diretamente no código, ignorando o tema global "Lime".
    *   **Veredito:** **Esquizofrênico.** O chat é azul, mas se você tiver um botão "Primary" em outra tela, ele será verde limão.

---

## 2. A "ALMA" DO PROMETHEUS (Streaming Personality)

Você mencionou amar os "emojis semânticos" do Prometheus CLI.
*   **No CLI:** Emojis são parsers visuais. `⚡` significa "Ação Rápida", `🧠` significa "Pensando".
*   **No WebApp:** Atualmente, é apenas texto Markdown.
*   **O Problema:** O chat renderiza os emojis como texto simples. Não há *animação*, não há *glow*, não há *significado* visual. O "streaming" é funcional, mas sem alma.

---

## 3. CHECKLIST 2026 (Estamos Atrasados?)

| Tendência 2026 | Status Vertice | Comentário |
| :--- | :--- | :--- |
| **Glassmorphism 3.0** | ✅ Presente | `backdrop-blur-xl` usado corretamente no chat. |
| **Semantic Streaming** | ❌ Ausente | Texto plano. Falta transformar `⚡` em ícones pulsantes. |
| **Fluid Typography** | ⚠️ Inconsistente | Landing usa `Inter`, App usa `Geist`. |
| **Adaptive Palettes** | ❌ Falha Crítica | Conflito Lime vs. Cyan. |
| **Micro-Interactions** | ⚠️ Básico | Hover states simples. Falta "physics-based motion". |

---

## 4. O PLANO DE UNIFICAÇÃO (PROJECT NARCISSUS)

Para não parecermos um "Frankenstein de UI", sugiro as seguintes ações imediatas:

### 🛠️ Ação 1: O "Expurgo do Limão" (Global Theme)
Alterar `globals.css` e `tailwind.config.ts` para adotar a paleta **"Deep Void + Electric Cyan"** da Landing V2 como a "Constituição Visual" do projeto.
*   Primary: `#06b6d4` (Cyan)
*   Background: `#050505` (Deep Void)
*   Surface: Glass (`rgba(255,255,255,0.03)`)

### 🛠️ Ação 2: O Componente "Semantic Streamer"
Criar um componente React que intercepta o streaming.
*   Se detectar `⚡`, renderiza um ícone de raio com efeito *glow* amarelo.
*   Se detectar `🧠`, renderiza um cérebro pulsante com efeito *fade-in*.
*   Isso traz a "personalidade" do Prometheus para a Web.

### 🛠️ Ação 3: Unificação Tipográfica
Padronizar tudo para **Geist Sans/Mono** (é mais moderna e legível para código que Inter). Atualizar a Landing Page para usar Geist também.

---

**Você autoriza o início do "Project Narcissus"?**
*Isso envolve reescrever o `globals.css` e refatorar o componente de chat para suportar Semantic Streaming.*
