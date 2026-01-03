# VERTICE TUI Visual Upgrade Plan
## "ESPETACULAR" - Claude Code Level Quality

### Objetivo
Elevar a TUI VERTICE ao nivel visual do Claude Code Web/CLI, integrando widgets avancados do Textual e melhores praticas de interfaces modernas (Gemini CLI, Cursor, Codex).

---

## Analise Atual

### Pontos Fortes Identificados
- **StreamingMarkdownWidget** (30fps markdown, 60fps code) - `vertice_cli/tui/components/streaming_markdown/`
- **BlockDetector** com 13 tipos de blocos - `vertice_cli/tui/components/block_detector.py`
- **IncrementalSyntaxHighlighter** (Pygments, 50+ linguagens) - `vertice_cli/tui/components/streaming_code_block.py`
- **ThemeManager** com 4 temas e WCAG AAA - `vertice_tui/themes/theme_manager.py`
- **Facade Pattern** no Bridge - `vertice_tui/core/bridge.py`

### Gaps vs Concorrencia
| Feature | Claude Code | Gemini CLI | Cursor | VERTICE |
|---------|-------------|------------|--------|---------|
| Modal dialogs | Yes | Yes | Yes | **No** |
| Toast notifications | Yes | Yes | Yes | **No** |
| Command palette (Cmd+K) | Yes | Yes | Yes | **No** |
| Diff view side-by-side | Yes | No | Yes | **No** |
| File tree sidebar | Yes | No | Yes | **No** |
| Tab sessions | Yes | No | Yes | **No** |
| Copy feedback visual | Yes | Yes | Yes | **No** |
| Loading animations | Yes | Yes | Yes | **Basico** |
| Syntax highlighting | Yes | Yes | Yes | Yes |
| Markdown tables | Yes | Yes | Yes | Yes |

---

## Metodologia

**IMPORTANTE:** Em cada fase, SEMPRE reobtener contexto antes de implementar:
1. Buscar arquivos existentes relacionados (Grep/Glob)
2. Ler implementacoes atuais
3. Identificar gaps vs plano
4. Implementar apenas o necessario

---

## Plano de Implementacao - 5 Fases

### FASE 1: Foundation (P0 - Critico) ✅ COMPLETA
**Objetivo**: Infraestrutura basica para UX moderna

#### 1.1 Modal System
**Arquivo**: `vertice_tui/widgets/modal.py` (novo)
```python
# Usar Textual Screen modal pattern
# - ConfirmDialog (Yes/No)
# - InputDialog (prompt + input)
# - AlertDialog (message only)
# - FilePickerDialog
```
**Dependencias**: Textual Screen, ModalScreen

#### 1.2 Toast Notifications
**Arquivo**: `vertice_tui/widgets/toast.py` (novo)
- Notificacoes temporarias (3-5s)
- Tipos: success, error, warning, info
- Posicao: top-right corner
- Stack de multiplos toasts

#### 1.3 Auto-Theme Detection
**Arquivo**: `vertice_tui/themes/theme_manager.py` (modificar)
- Detectar tema do sistema (dark/light)
- Transicao suave entre temas
- Persistir preferencia do usuario

#### 1.4 Copy Feedback Visual
**Arquivos**:
- `vertice_tui/widgets/response_view.py` (modificar)
- `vertice_cli/tui/components/streaming_code_block.py` (modificar)
- Adicionar botao de copy em code blocks
- Toast "Copied!" ao copiar
- Animacao de highlight no texto copiado

---

### FASE 2: Streaming Enhancement (P0 - Critico)
**Objetivo**: Outputs visuais de nivel profissional

#### 2.1 Enhanced Code Blocks
**Arquivo**: `vertice_cli/tui/components/streaming_code_block.py` (modificar)
- Header com linguagem + filename
- Line numbers sempre visiveis
- Word wrap toggle
- Collapse/expand para blocos grandes (>50 linhas)
- Decorators visuais (borders, shadows)

#### 2.2 Diff View Side-by-Side
**Arquivo**: `vertice_tui/widgets/diff_view.py` (novo)
- Split view: original | modified
- Syntax highlighting em ambos lados
- Line-by-line highlighting (+/-)
- Scroll sincronizado
- Mini-map de mudancas

#### 2.3 Tool Call Visualization
**Arquivo**: `vertice_tui/widgets/tool_call.py` (novo)
- Card visual para cada tool call
- Status: pending -> running -> success/error
- Spinner animado durante execucao
- Expandable details (input/output)
- Timeline visual de chamadas

#### 2.4 Table Enhancements
**Arquivo**: `vertice_cli/tui/components/streaming_table.py` (modificar)
- Sortable columns (click header)
- Horizontal scroll para tabelas largas
- Zebra striping
- Cell selection
- Export to clipboard

---

### FASE 3: Interactive Components (P1 - Importante)
**Objetivo**: Interatividade avancada

**REOBTENER CONTEXTO PRIMEIRO!**

#### 3.1 Command Palette Integration
**JA EXISTE:** `vertice_cli/tui/components/palette.py` (397 linhas completo!)
- FuzzyMatcher com scoring
- 20 agents (14 CLI + 6 Core)
- Categories com icons
- Recent commands

**FALTA:** Integrar no `vertice_tui/app.py`:
- Adicionar keybinding Ctrl+K (Ctrl+P ja e help)
- Usar Textual Provider pattern ou ModalScreen
- Conectar com CommandPaletteBridge

#### 3.2 Search & Filter
**Arquivo**: `vertice_tui/widgets/search_bar.py` (novo)
- Global search (Ctrl+F)
- Filter por tipo (code, text, tables)
- Highlight matches
- Navigate between results (N/P)

#### 3.3 Input Syntax Highlighting
**Arquivo**: `vertice_tui/widgets/input_area.py` (modificar)
- Code detection no input
- Syntax highlighting inline
- Multiline support aprimorado
- Bracket matching
- Auto-indent

#### 3.4 Context Menu (Right-Click)
**Arquivo**: `vertice_tui/widgets/context_menu.py` (novo)
- Copy, Paste, Select All
- Copy as Markdown/Code
- Search selection
- Explain selection (AI)

---

### FASE 4: Layout & Navigation (P1 - Importante)
**Objetivo**: Navegacao e organizacao profissional

#### 4.1 Sidebar com File Explorer
**Arquivo**: `vertice_tui/widgets/sidebar.py` (novo)
- Tree view de arquivos
- Recent files section
- Bookmarks
- Toggle visibility (Ctrl+B)
- Resize handle

#### 4.2 Tab System para Sessions
**Arquivo**: `vertice_tui/widgets/tab_bar.py` (novo)
- Multiple chat sessions
- Tab reorder (drag)
- Close tab (X)
- Tab overflow menu
- Session persistence

#### 4.3 Split View
**Arquivo**: `vertice_tui/widgets/split_container.py` (novo)
- Horizontal/Vertical split
- Resize handles
- Independent scroll
- Sync scroll option

#### 4.4 Breadcrumb Navigation
**Arquivo**: `vertice_tui/widgets/breadcrumb.py` (novo)
- Context path visual
- Click to navigate
- Truncation inteligente

---

### FASE 5: Polish & Delight (P2 - Nice-to-Have)
**Objetivo**: Detalhes que encantam

#### 5.1 Loading Animations
**Arquivo**: `vertice_tui/widgets/loading.py` (novo)
- Skeleton screens
- Shimmer effect
- Progress bars animados
- Spinner variants (dots, bars, circle)

#### 5.2 Sparkline para Tokens
**Arquivo**: `vertice_tui/widgets/sparkline.py` (novo)
- Minigrafico de uso de tokens
- Historico da sessao
- Hover para detalhes

#### 5.3 Mermaid Diagram Support
**Arquivo**: `vertice_cli/tui/components/mermaid_block.py` (novo)
- Parse Mermaid syntax
- Render ASCII art
- Fallback para code block

#### 5.4 Image Preview (ASCII)
**Arquivo**: `vertice_tui/widgets/image_preview.py` (novo)
- Converter imagens para ASCII art
- Thumbnail em outputs
- Expand para full view

---

## Arquivos Criticos a Modificar

| Arquivo | Modificacao | Prioridade |
|---------|-------------|------------|
| `vertice_tui/app.py` | Layout principal, keybindings | P0 |
| `vertice_tui/widgets/response_view.py` | Copy, tool calls | P0 |
| `vertice_cli/tui/components/streaming_code_block.py` | Header, collapse | P0 |
| `vertice_cli/tui/components/streaming_table.py` | Sort, scroll | P1 |
| `vertice_tui/themes/theme_manager.py` | Auto-detect | P0 |
| `vertice_tui/core/bridge.py` | Modal/toast integration | P0 |

## Novos Arquivos a Criar

| Arquivo | Descricao | Prioridade |
|---------|-----------|------------|
| `vertice_tui/widgets/modal.py` | Modal system | P0 |
| `vertice_tui/widgets/toast.py` | Toast notifications | P0 |
| `vertice_tui/widgets/diff_view.py` | Diff side-by-side | P0 |
| `vertice_tui/widgets/tool_call.py` | Tool call cards | P0 |
| `vertice_tui/widgets/command_palette.py` | Cmd+K | P1 |
| `vertice_tui/widgets/sidebar.py` | File explorer | P1 |
| `vertice_tui/widgets/tab_bar.py` | Sessions tabs | P1 |
| `vertice_tui/widgets/loading.py` | Animations | P2 |

---

## Ordem de Execucao Recomendada

```
SEMANA 1-2: Foundation
├── Modal System
├── Toast Notifications
├── Copy Feedback
└── Auto-theme

SEMANA 3-4: Streaming
├── Enhanced Code Blocks
├── Diff View
├── Tool Call Visualization
└── Table Enhancements

SEMANA 5-6: Interactive
├── Command Palette
├── Search/Filter
├── Input Highlighting
└── Context Menu

SEMANA 7-8: Layout
├── Sidebar
├── Tab System
├── Split View
└── Breadcrumb

SEMANA 9+: Polish
├── Loading Animations
├── Sparklines
├── Mermaid
└── Image Preview
```

---

## Referencias Textual Widget Gallery

Widgets a integrar do Textual:
- `ModalScreen` - Para dialogs
- `Toast` - Notifications (ja existe!)
- `DataTable` - Sortable tables
- `DirectoryTree` - File explorer
- `TabbedContent` - Tab sessions
- `Collapsible` - Expandable sections
- `LoadingIndicator` - Spinners
- `Sparkline` - Mini charts
- `ProgressBar` - Progress visual
- `RichLog` - Streaming output

---

## Metricas de Sucesso

- [ ] Modal dialogs funcionando (confirm, alert, input)
- [ ] Toast notifications em todas as acoes
- [ ] Copy button em code blocks com feedback
- [ ] Diff view para file changes
- [ ] Tool calls com status visual
- [ ] Command palette com fuzzy search
- [ ] Sidebar toggle funcional
- [ ] Tab system com persistencia
- [ ] Loading animations consistentes
- [ ] Auto-theme detection

---

*Plan created: 2026-01-03*
*Co-Author: Claude Opus 4.5*
*Target: Claude Code Level Quality (minimum)*
