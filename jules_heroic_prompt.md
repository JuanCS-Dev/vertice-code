# 🎯 MISSÃO HEROICA: AUDITORIA TOTAL DE FLUXO DE DADOS - VERTICE-CODE

## 🚨 CONTEXTO CRÍTICO - JANEIRO 2026

Você é **Grok Code Fast 1** (xAI), um modelo de raciocínio especializado em agentic coding. Sua missão é VITAL: auditar AGORA, em **ONE SHOT**, cada centímetro do repositório **vertice-code** (https://github.com/JuanCS-Dev/vertice-code) para identificar TODAS as desconexões que impedem a fluidez na produção de código.

**PROBLEMA ATUAL**: Claude Code reportou 90%+ de paridade funcional, mas o desenvolvedor sente que "nada está interligado" quando usa a aplicação. Isso indica:
- ❌ Fluxos de dados quebrados
- ❌ Integrações não funcionais entre componentes
- ❌ Orquestração de agents falhando
- ❌ Arquivos não sendo criados/salvos/lidos corretamente
- ❌ Review de código inconsistente
- ❌ Ferramentas não conectadas aos agents
- ❌ Context management falhando

**SETUP ATUAL (Janeiro 2026)**:
- **Provedor único**: Vertex AI (Google Cloud)
- **Modelo principal**: Gemini 3 Flash/Pro
- **Context window**: 1M tokens (Gemini 3)
- **Ferramenta de execução**: opencode CLI
- **Modelo executor**: Grok Code Fast 1 (VOCÊ!)

---

## 🧠 SUAS CAPACIDADES (Grok Code Fast 1)

### Especificações Técnicas
- **Context Window**: 256K tokens
- **Velocidade**: ~90 tokens/segundo (RIDICULAMENTE RÁPIDO)
- **Prompt Caching**: >90% hit rate com opencode
- **SWE-Bench Score**: 70.8% (comprovado em bugs reais)
- **Especialização**: TypeScript, Python, Java, Rust, C++, Go
- **Reasoning**: Visible reasoning traces para steering
- **Tool Mastery**: grep, terminal, file editing (treinado especificamente)

### Pricing (para referência)
- Input: $0.20 / 1M tokens
- Output: $1.50 / 1M tokens  
- Cached: $0.02 / 1M tokens

### Como Funciona a Auditoria via opencode

O desenvolvedor vai executar você através do **opencode CLI** (anomalyco/opencode):

```bash
# Instalar opencode (se ainda não tem)
curl -fsSL https://opencode.ai/install | bash

# Autenticar com xAI
opencode auth login
# Selecionar: xAI
# Inserir: XAI_API_KEY

# Executar VOCÊ nesta auditoria
cd vertice-code
opencode run -p "$(cat PROMPT_HEROICO.md)" --model xai/grok-code-fast-1
```

**Ferramentas que você tem via opencode**:
- ✅ `bash` - Execute comandos shell
- ✅ `read` - Leia qualquer arquivo do repo
- ✅ `write` - Crie/modifique arquivos
- ✅ `edit` - Substituições exatas de texto
- ✅ `grep` - Search com regex
- ✅ `glob` - Find files por pattern
- ✅ `list` - Liste diretórios
- ✅ `lsp` - Code intelligence (diagnostics, definitions, refs)
- ✅ `web_fetch` - Buscar docs online se necessário

---

## 🎯 OBJETIVOS DA AUDITORIA

### 1. MAPEAMENTO COMPLETO DE FLUXO DE DADOS

**Trace TODOS os caminhos de dados desde a entrada do usuário até a saída:**

```
USER INPUT → CLI/TUI → VERTICE CLIENT → GEMINI 3 → AGENT → TOOL → FILE SYSTEM → RESPONSE → USER
```

Para CADA caminho, use suas tools do opencode:

```bash
# 1. Analise entry points
read vertice_cli/__main__.py
read vertice_tui/app.py

# 2. Trace client initialization
grep -r "VerticeClient" . --include="*.py"
read clients/vertice_client.py

# 3. Mapeie agent routing
read agents/orchestrator/router.py
grep -r "semantic_routing" . --include="*.py"

# 4. Valide tool registration
read tools/__init__.py
grep -r "register_tool" . --include="*.py"

# 5. Teste fluxo completo com LSP
lsp goToDefinition vertice_cli/main.py VerticeClient
lsp findReferences vertice_cli/main.py VerticeClient
```

✅ **Para CADA ponto**: Identifique falhas, validações, tratamento de erros, serialização

---

### 2. ANÁLISE DE INTEGRAÇÃO ENTRE COMPONENTES

Use reasoning traces visíveis para documentar sua análise:

#### 2.1 CLI → Core Framework
```python
# Verificar em: vertice_cli/__main__.py
# Execute:
read vertice_cli/__main__.py
read vertice_core/config.py

# Perguntas críticas a responder:
- O CLI consegue instanciar o VerticeClient?
- Os comandos estão mapeados corretamente para os agents?
- O context manager está sendo inicializado?
- As ferramentas estão sendo registradas?

# Use lsp para validar imports
lsp diagnostics vertice_cli/__main__.py
```

#### 2.2 TUI → Core Framework
```python
# Verificar em: vertice_tui/app.py e vertice_tui/core/bridge.py
read vertice_tui/app.py
read vertice_tui/core/bridge.py

# Perguntas críticas:
- O bridge está conectando TUI → Gemini 3 → Agents → Tools?
- O streaming de tokens funciona de ponta a ponta?
- O status bar reflete estado real dos providers?
- O token meter está conectado ao context manager?

# Trace dependencies
lsp goToDefinition vertice_tui/app.py VerticeBridge
```

#### 2.3 Agents → Tools
```python
# Verificar em: agents/*/__init__.py e tools/*/
list agents/
bash "find agents/ -name '*.py' -type f | head -20"

# Para cada agent, verifique:
read agents/coder/__init__.py
grep "tools" agents/coder/__init__.py

# Perguntas críticas:
- Cada agent tem acesso às ferramentas que declara?
- As ferramentas retornam objetos serializáveis?
- O formato de resposta das tools é compatível com agents?
- Há ferramentas registradas mas não usadas?
```

#### 2.4 Tools → File System
```python
# Verificar em: tools/file_ops/, tools/bash/, tools/git/
read tools/file_ops/read_file.py
read tools/file_ops/write_file.py

# Perguntas críticas:
- As operações de arquivo são atômicas?
- Há locks para evitar race conditions?
- Os caminhos são validados contra directory traversal?
- Permissões são verificadas antes de operações?

# Teste na prática
bash "cd /tmp && python3 -c 'import sys; sys.path.insert(0, \"$(pwd)\"); from tools.file_ops import write_file; print(write_file.__doc__)'"
```

#### 2.5 Gemini 3 Client → Agents
```python
# Verificar em: clients/vertice_client.py
read clients/vertice_client.py

# Perguntas CRÍTICAS para Gemini 3 (2026):
- O VerticeClient está corretamente instanciado?
- As credenciais do Vertex AI estão sendo carregadas?
- As requisições para Gemini 3 (Flash/Pro) estão funcionando?
- O thinking_level está sendo usado? (MINIMAL/LOW/MEDIUM/HIGH)
- Thought signatures são retornadas e passadas nas conversas?
- O context window de 1M tokens está sendo respeitado?
- Rate limiting está implementado?
- Erros de API são tratados graciosamente?
- Timeout de requisições está configurado?

# Valide imports e tipos
lsp diagnostics clients/vertice_client.py
```

#### 2.6 Governance → Agents
```python
# Verificar em: vertice_governance/ e agents/
read vertice_governance/justica.py
read vertice_governance/sofia.py
read vertice_governance/tribunal.py

# Perguntas críticas:
- Os agents estão realmente respeitando JUSTIÇA e SOFIA?
- O TRIBUNAL é invocado para ações de alto risco?
- Os sovereignty levels estão implementados?
- Há logs de decisões de governança?

# Procure por violações
grep -r "sovereignty_level" . --include="*.py"
grep -r "TRIBUNAL" . --include="*.py"
```

---

### 3. VALIDAÇÃO DE ORQUESTRAÇÃO DE AGENTS

**Teste o ciclo completo de orquestração:**

#### 3.1 Semantic Routing
```python
# Verificar em: agents/orchestrator/router.py (se existir)
glob "agents/**/router.py"
glob "agents/**/semantic*.py"

# Se encontrar, analise:
read <arquivo_encontrado>

# Tarefas:
- Testar embedding de inputs variados
- Verificar cálculo de similaridade coseno
- Confirmar threshold de confiança (>0.7)
- Validar fallback para Coder agent
- Testar com queries ambíguas

# Se NÃO encontrar, REPORTE IMEDIATAMENTE: 
# "🔴 CRÍTICO: Semantic routing não implementado"
```

#### 3.2 Agent-to-Agent (A2A) Protocol
```python
# Verificar em: core/a2a/ e core/mesh/
list core/a2a/
list core/mesh/

read core/a2a/protocol.py  # se existir
read core/mesh/network.py  # se existir

# Tarefas:
- Confirmar que agents podem se descobrir
- Testar envio de mensagens entre agents
- Validar sincronização de estado distribuído
- Verificar resolução de conflitos
- Testar handoff entre agents

# Procure por uso real
grep -r "A2AProtocol" . --include="*.py"
grep -r "mesh" . --include="*.py"
```

#### 3.3 Consenso e Votação
```python
# Verificar em: vertice_governance/tribunal.py
read vertice_governance/tribunal.py

# Tarefas:
- Simular decisão que requer consenso
- Verificar que 3+ agents são consultados
- Confirmar votação por maioria
- Validar que humano é notificado quando necessário
- Testar timeout de deliberação

# Encontre uso real
grep -r "tribunal" . --include="*.py" -i
```

---

### 4. AUDITORIA DE CRIAÇÃO/LEITURA/ESCRITA DE ARQUIVOS

**Verificar cada operação de arquivo:**

#### 4.1 File Creation Flow
```python
# Caminho completo esperado:
# User: "criar arquivo hello.py" 
#   → CLI parser 
#   → Coder agent 
#   → Tool: write_file 
#   → Validation 
#   → Governance check 
#   → File system write 
#   → Confirmation to user

# TRACE COMPLETO:
read vertice_cli/commands/create.py  # ou similar
read agents/coder/actions.py
read tools/file_ops/write_file.py
read vertice_governance/validators.py

# Verificar em cada etapa:
# ❓ O comando é parseado corretamente?
# ❓ O agent entende a intenção?
# ❓ A tool recebe os parâmetros corretos?
# ❓ O path é validado?
# ❓ Governança permite a operação?
# ❓ O arquivo é criado no local correto?
# ❓ O usuário recebe confirmação?

# Teste na prática (não execute, apenas analise):
bash "find . -name 'write_file.py' -type f"
read $(bash "find . -name 'write_file.py' -type f | head -1")
```

#### 4.2 File Reading Flow
```python
# Verificar:
read tools/file_ops/read_file.py

# ❓ read_file tool retorna conteúdo correto?
# ❓ Encoding é detectado automaticamente?
# ❓ Arquivos grandes são tratados (streaming)?
# ❓ Erros de permissão são capturados?
# ❓ Conteúdo é adicionado ao context manager?

# Validar com LSP
lsp diagnostics tools/file_ops/read_file.py
```

#### 4.3 File Editing Flow
```python
# Verificar:
read tools/file_ops/edit_file.py

# ❓ edit_file tool faz diff corretamente?
# ❓ Backup é criado antes de editar?
# ❓ Mudanças são atômicas (rollback em erro)?
# ❓ Git tracking funciona após edição?

# Procure por testes
glob "tests/**/test_file_ops.py"
glob "tests/**/test_edit*.py"
```

---

### 5. TESTE DE REVIEW DE CÓDIGO

**Validar pipeline completo de code review:**

```python
# Fluxo esperado:
# User: "revisar código"
#   → Reviewer agent ativado
#   → read_file tool carrega código
#   → Análise de segurança (SOFIA)
#   → Análise de qualidade (linting tools)
#   → Análise de padrões (architect agent consultado?)
#   → Relatório gerado
#   → Sugestões de melhoria
#   → Opção de aplicar fixes

# TRACE COMPLETO:
read agents/reviewer/__init__.py
read agents/reviewer/analyzer.py  # se existir

# Verificar:
# ❓ Reviewer tem acesso a TODAS as tools necessárias?
grep "tools" agents/reviewer/__init__.py

# ❓ Consegue ler múltiplos arquivos?
grep -r "read_file" agents/reviewer/ --include="*.py"

# ❓ Análise de segurança é real (não superficial)?
read vertice_governance/sofia.py
grep "SOFIA" agents/reviewer/ --include="*.py" -r

# ❓ Linting tools são invocados?
grep -r "ruff\|pylint\|mypy" agents/reviewer/ --include="*.py"

# ❓ Relatório é estruturado e acionável?
grep -r "generate_report\|create_report" agents/reviewer/ --include="*.py"
```

---

### 6. ANÁLISE DE CONTEXT MANAGEMENT (1M tokens - Gemini 3)

**Testar limites e compactação:**

```python
# Verificar em: core/context/
list core/context/
read core/context/manager.py  # ou similar

# Testes conceituais (não execute, analise código):
# 1. ❓ Há código para adicionar arquivos até 800K tokens?
# 2. ❓ Auto-compaction é acionada aos 80%?
# 3. ❓ Informações críticas são preservadas?
# 4. ❓ Sliding window compressor existe?
# 5. ❓ Thought signatures são salvos entre sessões?
# 6. ❓ Comandos /compact, /context, /tokens existem?

grep -r "compact" core/context/ --include="*.py"
grep -r "thought_signature" . --include="*.py"

# IMPORTANTE PARA GEMINI 3 (2026):
# Thought signatures devem ser retornados em TODAS as chamadas
# Function calls SEMPRE retornam thought signature (mesmo em MINIMAL)
# Verificar se implementado:
grep -r "thinking_level" clients/ --include="*.py"
```

---

### 7. VALIDAÇÃO DE GEMINI 3 + VERTEX AI

**Testar integração completa:**

```python
# Verificar em: clients/vertice_client.py
read clients/vertice_client.py

# Testes conceituais ONE SHOT:
# 1. ❓ Credenciais GCP estão sendo carregadas (GOOGLE_APPLICATION_CREDENTIALS)?
grep "GOOGLE_APPLICATION_CREDENTIALS" clients/vertice_client.py

# 2. ❓ Chamada para Gemini 3 Flash está implementada?
grep -i "gemini.*3.*flash\|gemini-3-flash" clients/vertice_client.py

# 3. ❓ Gemini 3 Pro usado para tarefas complexas?
grep -i "gemini.*3.*pro\|gemini-3-pro" clients/vertice_client.py

# 4. ❓ thinking_level está configurado?
grep -i "thinking_level" clients/vertice_client.py

# 5. ❓ Thought signatures são capturadas?
grep -i "thought.*signature" clients/vertice_client.py

# 6. ❓ Context window de 1M tokens é respeitado?
grep -i "max_tokens\|context_window" clients/vertice_client.py

# 7. ❓ Tratamento de erros (quota, auth, timeout)?
grep -r "except\|try\|Exception" clients/vertice_client.py

# 8. ❓ Respostas são parseadas corretamente?
grep -r "parse\|json\|response" clients/vertice_client.py

# 9. ❓ Client é singleton ou gerenciado?
grep -r "class.*Client\|__new__\|singleton" clients/vertice_client.py

# 10. ❓ Multimodal input (texto + imagem)?
grep -i "image\|multimodal" clients/vertice_client.py

# 11. ❓ Streaming funciona?
grep -i "stream" clients/vertice_client.py

# 12. ❓ Knowledge cutoff (Janeiro 2025) respeitado?
# Procure por hardcoded dates ou configs
grep -r "2025\|cutoff" clients/ --include="*.py"
```

**Recursos Específicos do Gemini 3 para Verificar:**
```python
# Thinking levels: Se agents complexos usam HIGH, agents rápidos usam LOW/MINIMAL
grep -r "HIGH\|LOW\|MINIMAL\|MEDIUM" agents/ --include="*.py" -i | grep thinking

# Context caching: Se habilitado (90% economia)
grep -r "cache\|caching" clients/ --include="*.py" -i

# Batch API: Se usado para operações assíncronas (50% economia)
grep -r "batch" clients/ --include="*.py" -i

# Function calling: Crítico para tool use
grep -r "function_call\|tool_call" clients/ --include="*.py" -i
```

---

### 8. TESTE DE FERRAMENTAS CRÍTICAS (47 tools)

**Validar tools uma por uma usando opencode:**

```python
# ESTRATÉGIA: Para cada categoria, leia os arquivos e analise

# File Operations (12 tools)
bash "find tools/file_ops/ -name '*.py' -type f | grep -v __pycache__ | grep -v test"
# Para cada arquivo encontrado:
# read <arquivo>
# lsp diagnostics <arquivo>
# grep "def " <arquivo>  # Liste todas as funções

# Bash Execution (8 tools)
bash "find tools/bash/ -name '*.py' -type f | grep -v __pycache__"
# Mesma análise

# Git Integration (10 tools)
bash "find tools/git/ -name '*.py' -type f | grep -v __pycache__"
# Mesma análise

# Web Operations (6 tools)
bash "find tools/web/ -name '*.py' -type f | grep -v __pycache__" 
# Mesma análise

# MCP Integration (5 tools)
bash "find tools/mcp/ -name '*.py' -type f | grep -v __pycache__"
# Mesma análise

# Code Analysis (6 tools)
bash "find tools/code/ -name '*.py' -type f | grep -v __pycache__"
# Mesma análise

# Para CADA tool, verifique:
# ✅ Está registrada no __init__.py?
# ✅ Tem docstring explicando uso?
# ✅ Parâmetros têm type hints?
# ✅ Retorna tipo consistente?
# ✅ Tratamento de erros?
# ✅ É usada por algum agent?
```

---

### 9. AUDITORIA DE TESTES

**Validar cobertura real dos 732+ testes:**

```python
# Verificar estrutura de testes
list tests/
bash "find tests/ -name '*.py' -type f | wc -l"

# Analise test runners
read pytest.ini
read pyproject.toml | grep -A 20 "tool.pytest"

# Perguntas:
# ❓ Os testes realmente passam?
bash "pytest tests/ --collect-only | grep 'test session starts'"

# ❓ Cobertura está acima de 80%?
# (não execute, apenas verifique se o comando existe)
bash "which pytest-cov"

# ❓ Testes de integração testam fluxos completos?
list tests/integration/

# ❓ E2E tests simulam uso real?
list tests/e2e/

# ❓ Há testes para casos de erro?
grep -r "test.*error\|test.*exception\|test.*fail" tests/ --include="*.py" | head -20

# ❓ Mocks estão corretos?
grep -r "Mock\|patch\|mock" tests/ --include="*.py" | head -20
```

---

### 10. IDENTIFICAÇÃO DE "ARQUITETURA FANTASMA"

**Encontrar código declarado mas não conectado:**

```python
# 1. Classes definidas mas nunca instanciadas
bash "grep -r '^class ' vertice_* agents/ core/ --include='*.py' | cut -d: -f2 | cut -d'(' -f1 | sed 's/class //' | sort -u > /tmp/defined_classes.txt"
bash "grep -rh '\b[A-Z][a-zA-Z]*(' vertice_* agents/ core/ --include='*.py' | grep -oP '[A-Z][a-zA-Z]*(?=\()' | sort -u > /tmp/used_classes.txt"
# Compare com: comm -23 /tmp/defined_classes.txt /tmp/used_classes.txt

# 2. Funções definidas mas nunca chamadas
bash "grep -r '^def ' vertice_* agents/ core/ tools/ --include='*.py' | cut -d: -f2 | cut -d'(' -f1 | sed 's/def //' | sort -u > /tmp/defined_funcs.txt"
bash "grep -rh '\b[a-z_][a-z0-9_]*(' vertice_* agents/ core/ --include='*.py' | grep -oP '[a-z_][a-z0-9_]*(?=\()' | sort -u > /tmp/used_funcs.txt"

# 3. Imports não utilizados
bash "ruff check . --select F401 | head -50"

# 4. Configurações não aplicadas
read .vertice/config.yaml
grep -r "config\[" vertice_* --include="*.py" | head -30

# 5. Agents registrados mas não roteados
bash "ls agents/ | grep -v __pycache__"
grep -r "register.*agent\|add.*agent" . --include="*.py"

# 6. Tools registradas mas não acessíveis
bash "ls tools/ | grep -v __pycache__"
grep -r "register.*tool\|add.*tool" . --include="*.py"

# 7. Eventos definidos mas não emitidos
grep -r "Event\|event" . --include="*.py" | grep -i "class\|def"
grep -r "emit\|fire\|trigger" . --include="*.py" | head -20

# 8. Callbacks registrados mas não invocados
grep -r "callback\|on_" . --include="*.py" | head -30
```

---

## 📋 PLANO DE EXECUÇÃO ONE-SHOT VIA OPENCODE

**Faça TUDO agora, de forma sistemática via suas tools:**

### Fase Única: Análise Completa e Paralela

```bash
# O desenvolvedor já clonou e está no diretório:
# cd vertice-code

# VOCÊ (Grok Code Fast 1) vai executar TODAS essas análises:

# 1. OVERVIEW ESTRUTURAL
list .
bash "find . -maxdepth 2 -type d | grep -v '__pycache__\|\.git' | sort"
bash "cloc . --exclude-dir=node_modules,.git,__pycache__ --json"

# 2. ANÁLISE ESTÁTICA
bash "ruff check . --output-format=json 2>&1 | head -200"
bash "mypy . --strict 2>&1 | head -100"

# 3. VALIDAÇÃO DE CONFIGURAÇÃO
read .vertice/config.yaml
read pyproject.toml
read requirements.txt
bash "grep -r 'GOOGLE_APPLICATION_CREDENTIALS' . --include='*.py'"

# 4. TESTE DE IMPORTAÇÕES
bash "python3 -c 'import sys; sys.path.insert(0, \".\"); import vertice_cli' 2>&1"
bash "python3 -c 'import sys; sys.path.insert(0, \".\"); import vertice_tui' 2>&1"
bash "python3 -c 'import sys; sys.path.insert(0, \".\"); import vertice_core' 2>&1"

# 5. EXECUÇÃO DE TESTES (apenas collect, não execute todos)
bash "pytest tests/ --collect-only 2>&1 | tail -50"

# 6. ANÁLISE DE DEPENDÊNCIAS
bash "pipdeptree 2>&1 || pip list | head -50"

# 7. TRACE DE FLUXOS CRÍTICOS (via LSP)
lsp diagnostics vertice_cli/__main__.py
lsp diagnostics vertice_tui/app.py
lsp diagnostics clients/vertice_client.py

# 8. BUSCA DE PADRÕES SUSPEITOS
bash "grep -r 'TODO\|FIXME\|XXX\|HACK' . --include='*.py' | wc -l"
bash "grep -r 'pass$' . --include='*.py' | wc -l"  # Funções vazias
bash "grep -r 'raise NotImplementedError' . --include='*.py' | wc -l"
```

---

## 🎯 DELIVERABLES ESPERADOS

### 1. MAPA DE FLUXO DE DADOS COMPLETO

```markdown
## FLUXO DE DADOS - VERTICE-CODE

### Entry Point: CLI
FILE: vertice_cli/__main__.py
STATUS: ✅ OK / ❌ BROKEN / ⚠️ PARCIAL
CONECTA A: VerticeClient em clients/vertice_client.py
PROBLEMAS: [lista aqui]

### Entry Point: TUI
FILE: vertice_tui/app.py
STATUS: ✅ OK / ❌ BROKEN / ⚠️ PARCIAL
CONECTA A: VerticeBridge em vertice_tui/core/bridge.py
PROBLEMAS: [lista aqui]

### Client Layer: Gemini 3
FILE: clients/vertice_client.py
STATUS: ✅ OK / ❌ BROKEN / ⚠️ PARCIAL
CONECTA A: Vertex AI API
CONFIGURAÇÕES DETECTADAS:
  - thinking_level: [ENCONTRADO/NÃO ENCONTRADO]
  - thought_signatures: [IMPLEMENTADO/NÃO IMPLEMENTADO]
  - context_caching: [HABILITADO/DESABILITADO]
PROBLEMAS: [lista aqui]

### Agent Layer
AGENTS DETECTADOS: [lista completa]
SEMANTIC ROUTER: [IMPLEMENTADO/NÃO IMPLEMENTADO]
AGENTS CONECTADOS: [X de Y]
AGENTS ÓRFÃOS: [lista]
PROBLEMAS: [lista aqui]

### Tool Layer
TOOLS DETECTADAS: [lista completa]
TOOLS REGISTRADAS: [X de 47]
TOOLS ACESSÍVEIS AOS AGENTS: [Y de 47]
TOOLS ÓRFÃS: [lista]
PROBLEMAS: [lista aqui]

### Governance Layer
JUSTIÇA: [IMPLEMENTADO/PARCIAL/NÃO IMPLEMENTADO]
SOFIA: [IMPLEMENTADO/PARCIAL/NÃO IMPLEMENTADO]
TRIBUNAL: [IMPLEMENTADO/PARCIAL/NÃO IMPLEMENTADO]
SOVEREIGNTY LEVELS: [RESPEITADOS/IGNORADOS]
PROBLEMAS: [lista aqui]

### Context Management
MAX_TOKENS: [valor configurado vs 1M do Gemini 3]
AUTO_COMPACTION: [IMPLEMENTADO/NÃO IMPLEMENTADO]
THOUGHT_SIGNATURES: [SALVOS/NÃO SALVOS]
PROBLEMAS: [lista aqui]
```

### 2. RELATÓRIO DE DESCONEXÕES

Para cada desconexão encontrada:

```markdown
## 🔴 DESCONEXÃO #1: [Título Descritivo]

**Severidade**: 🔴 IMPEDITIVO / 🟡 CRÍTICO / 🟢 IMPORTANTE

**Localização**: 
- Arquivo: `path/to/file.py`
- Linha: 123
- Função/Classe: `nome_funcao`

**Problema**:
[Descrição clara do que não está conectado]
[Use seu reasoning trace para explicar em detalhes]

**Evidência**:
```python
# Código atual que comprova o problema:
def broken_function():
    # ...
```

**Impacto**:
[Como isso afeta a usabilidade do sistema]
[Que funcionalidades ficam quebradas]

**Root Cause**:
[Análise técnica profunda da causa raiz]
[Por que isso aconteceu]

**Fix Sugerido**:
```python
# Código atual (quebrado):
def broken_function():
    