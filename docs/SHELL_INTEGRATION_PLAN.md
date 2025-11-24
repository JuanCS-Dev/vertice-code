# 🔧 SHELL INTEGRATION PLAN - Systematic Approach

**Objetivo:** Integrar funcionalidades JÁ IMPLEMENTADAS no shell enhanced sem quebrar nada.

---

## 📊 MAPEAMENTO DO QUE TEMOS

### ✅ Já Implementado (Desconectado)

#### 1. **Context Awareness** 🧠
- `core/context.py` - ContextBuilder básico
- `intelligence/context_enhanced.py` - RichContext (Git, Workspace, Terminal)
- `tools/context.py` - Context tools
- `tui/components/context_awareness.py` - UI components

#### 2. **Agents Squad** 👥
- `agents/architect.py` ✅
- `agents/planner.py` ✅
- `agents/reviewer.py` ✅
- `agents/refactorer.py` ✅
- `agents/testing.py` ✅
- `agents/security.py` ✅
- `agents/performance.py` ✅
- `agents/documentation.py` ✅
- `agents/explorer.py` ✅

#### 3. **Tools System** 🛠️
- `tools/file_ops.py` - File operations
- `tools/git_ops.py` - Git operations
- `tools/search.py` - Code search
- `tools/web_search.py` - Web search
- `tools/exec.py` - Command execution
- `tools/terminal.py` - Terminal interaction

#### 4. **TUI Components** 🎨
- `tui/components/autocomplete.py` - Fuzzy autocomplete
- `tui/components/dashboard.py` - Status dashboard
- `tui/components/palette.py` - Command palette
- `tui/components/progress.py` - Progress bars
- `tui/components/toasts.py` - Toast notifications
- `tui/minimal_output.py` - Minimal output formatter

#### 5. **Intelligence Layer** 🤖
- `intelligence/engine.py` - Intent detection
- `intelligence/patterns.py` - Pattern matching
- `intelligence/context_suggestions.py` - Context-aware suggestions
- `intelligence/workflows.py` - Workflow automation

---

## 🎯 FASES DE INTEGRAÇÃO

### **FASE 1: Context Awareness Foundation** 🧠
**Objetivo:** Shell entende ONDE está e O QUE pode fazer

#### Tarefas:
1. ✅ Integrar `RichContext` no shell
2. ✅ Auto-detectar working directory, Git status, project type
3. ✅ Injetar context no system prompt do Gemini
4. ✅ Adicionar `/context` command para debug

#### Testes:
```bash
# Test 1: Context detection
qwen ⚡ › /context
# Should show: CWD, Git branch, project type

# Test 2: Project awareness
qwen ⚡ › analyze this project
# Should: Read files, not ask for details

# Test 3: File resolution
qwen ⚡ › review that file
# Should: Resolve "that file" from context
```

**Critério de Sucesso:** Shell NUNCA mais pergunta "qual projeto?"

---

### **FASE 2: Agent Auto-Detection** 🤖
**Objetivo:** Detectar intent e chamar agent automaticamente

#### Tarefas:
1. ✅ Integrar `intelligence/engine.py` (intent detection)
2. ✅ Criar mapeamento: keywords → agents
3. ✅ Auto-route para agent quando detectado
4. ✅ Mostrar qual agent foi ativado (toast notification)

#### Mapeamento de Intents:
```python
INTENT_TO_AGENT = {
    "review|analyze|audit": ReviewerAgent,
    "plan|roadmap|strategy": PlannerAgent,
    "refactor|improve|optimize": RefactorerAgent,
    "test|coverage|unit": TestingAgent,
    "security|vulnerability|exploit": SecurityAgent,
    "architecture|design|structure": ArchitectAgent,
    "document|readme|docs": DocumentationAgent,
    "explore|navigate|find": ExplorerAgent,
}
```

#### Testes:
```bash
# Test 1: Plan detection
qwen ⚡ › create a plan for world domination
# Should: Auto-call PlannerAgent

# Test 2: Review detection
qwen ⚡ › review this codebase
# Should: Auto-call ReviewerAgent + ExplorerAgent

# Test 3: Security detection
qwen ⚡ › find vulnerabilities
# Should: Auto-call SecurityAgent
```

**Critério de Sucesso:** 80%+ das queries vão pro agent correto sem `/comando`

---

### **FASE 3: Tools Integration** 🛠️
**Objetivo:** LLM pode EXECUTAR ações (read files, run commands, search)

#### Tarefas:
1. ✅ Registrar tools no Gemini function calling
2. ✅ Implementar executors para cada tool
3. ✅ Adicionar confirmação para comandos destrutivos
4. ✅ Mostrar execução em tempo real (progress bars)

#### Tools a Registrar:
```python
TOOLS = [
    "read_file",       # Ler arquivo
    "write_file",      # Escrever arquivo (com confirmação)
    "search_code",     # Buscar em código
    "run_command",     # Executar comando (com confirmação)
    "git_status",      # Status git
    "git_diff",        # Diff git
    "web_search",      # Buscar na web
]
```

#### Testes:
```bash
# Test 1: Auto-read files
qwen ⚡ › what's in main.py?
# Should: Call read_file("main.py") automatically

# Test 2: Code search
qwen ⚡ › where is the ContextBuilder class?
# Should: Call search_code("ContextBuilder")

# Test 3: Command execution
qwen ⚡ › run the tests
# Should: Ask confirmation → Execute → Show results
```

**Critério de Sucesso:** LLM executa ações sem precisar de `/comando` manual

---

### **FASE 4: TUI Polish** 🎨
**Objetivo:** Output bonito, minimalista e informativo

#### Tarefas:
1. ✅ Integrar `tui/minimal_output.py` (Claude/Cursor style)
2. ✅ Implementar toast notifications (tool calls)
3. ✅ Adicionar progress bars (streaming, execution)
4. ✅ Implementar fuzzy autocomplete (`Ctrl+Space`)
5. ✅ Command palette upgrade (`Ctrl+P`)

#### Testes:
```bash
# Test 1: Minimal output
qwen ⚡ › explain async/await
# Should: Show concise, formatted answer (not wall of text)

# Test 2: Toast notifications
qwen ⚡ › analyze project
# Should: Show toasts: "🔍 Reading files...", "✅ Analysis complete"

# Test 3: Fuzzy search
qwen ⚡ › /[Ctrl+Space]
# Should: Show fuzzy-matched commands

# Test 4: Command palette
qwen ⚡ › [Ctrl+P]
# Should: Show rich command palette with previews
```

**Critério de Sucesso:** Shell visual = Cursor/Claude level

---

### **FASE 5: Advanced Features** 🚀
**Objetivo:** Features premium (LSP, workflows, multi-agent)

#### Tarefas:
1. ⚠️ LSP integration (code navigation)
2. ⚠️ Workflow automation (multi-step tasks)
3. ⚠️ Multi-agent collaboration (squad mode)
4. ⚠️ Session persistence (resume conversations)

#### Testes:
```bash
# Test 1: LSP navigation
qwen ⚡ › go to definition of ContextBuilder
# Should: Use LSP to find exact location

# Test 2: Workflow
qwen ⚡ › create a REST API with auth
# Should: Execute multi-step workflow automatically

# Test 3: Squad mode
qwen ⚡ › /squad review and refactor auth.py
# Should: ReviewerAgent → RefactorerAgent → TestingAgent
```

**Critério de Sucesso:** Features únicos que nenhum CLI tem

---

## 🔥 REGRAS DE OURO

1. **NUNCA quebrar o shell atual** - Cada fase deve ser backward compatible
2. **Testar ANTES de prosseguir** - Sem testes = não avança
3. **Feature flags** - Todas features novas devem ter toggle on/off
4. **Rollback fácil** - Git commits pequenos e atômicos
5. **Zero alucination** - Context > Criatividade

---

## 📈 MÉTRICAS DE SUCESSO

### Fase 1:
- ✅ Context detection = 100% working directory
- ✅ Project type detection = 90%+ accuracy

### Fase 2:
- ✅ Intent detection = 80%+ correct agent
- ✅ Auto-routing = 0 manual `/comando` needed

### Fase 3:
- ✅ Tool calls = 100% execution success
- ✅ File operations = 0 errors

### Fase 4:
- ✅ Output quality = Claude/Cursor level
- ✅ UI responsiveness = <100ms interactions

### Fase 5:
- ✅ LSP accuracy = 95%+ correct navigation
- ✅ Workflow success = 90%+ completion rate

---

## 🚀 ORDEM DE EXECUÇÃO

```
FASE 1 (Context) → Test → Commit
    ↓
FASE 2 (Agents) → Test → Commit
    ↓
FASE 3 (Tools) → Test → Commit
    ↓
FASE 4 (TUI) → Test → Commit
    ↓
FASE 5 (Advanced) → Test → Ship 🎉
```

---

## 🎯 PRÓXIMOS PASSOS

**AGORA:** Começar **FASE 1** - Context Awareness
**Arquivo:** `qwen_dev_cli/cli/repl_masterpiece.py`
**Branch:** `feature/context-awareness`

Vamos? 🚀
