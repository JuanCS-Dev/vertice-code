# 🔀 Relatório de Arquitetura de Roteamento

## Bug #5: Conflito de Roteamento com /plan

**Status:** 🔴 CRÍTICO
**Score Atual:** Routing Logic 60%
**Impacto:** Comandos especiais (`/plan`, `/help`) não funcionam corretamente

---

## 📊 Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENTRADA DO USUÁRIO                                │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐    │
│   │ Terminal CLI    │  │ REPL Shell      │  │ Shell Main (Interativo)│    │
│   │ maestro agent X │  │ /comando msg    │  │ /comando msg            │    │
│   └────────┬────────┘  └────────┬────────┘  └───────────┬─────────────┘    │
└────────────┼────────────────────┼───────────────────────┼──────────────────┘
             │                    │                       │
             ▼                    ▼                       ▼
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────────┐
│    maestro.py      │  │ repl_masterpiece.py│  │     shell_main.py          │
│                    │  │                    │  │                            │
│ @agent_app.command │  │ self.commands[]    │  │ _handle_system_command()   │
│ "plan" → agent_plan│  │ "/plan" → handler  │  │ "/plan" → ❌ NÃO EXISTE    │
└─────────┬──────────┘  └─────────┬──────────┘  └────────────┬───────────────┘
          │                       │                          │
          │ ✅                    │ ⚠️                       │ ❌
          │                       │                          │
          ▼                       ▼                          ▼
┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────────┐
│ execute_agent_task │  │ _invoke_agent()    │  │ COMANDO NÃO RECONHECIDO    │
│                    │  │                    │  │                            │
│ • AgentTask struct │  │ • LLM direto       │  │ • Erro ou fallthrough      │
│ • Governance ✅    │  │ • Sem governance ⚠️│  │ • Tenta como path ❌       │
│ • Agent.execute()  │  │ • stream_chat()    │  │                            │
└─────────┬──────────┘  └─────────┬──────────┘  └────────────────────────────┘
          │                       │
          ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENTS LAYER                                   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ PlannerAgent │  │ CoderAgent   │  │ExplorerAgent │  │ RefactorAgent│    │
│  │              │  │              │  │              │  │              │    │
│  │ base.py      │  │ coder.py     │  │ explorer.py  │  │ refactorer.py│    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│                         executor_nextgen.py                                 │
│                    (ReAct Pattern + Streaming)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Arquivos Envolvidos no Roteamento

### Camada 1: Entry Points

| Arquivo | Localização | Responsabilidade | Status |
|---------|-------------|------------------|--------|
| `maestro.py` | `qwen_dev_cli/maestro.py` | CLI Typer principal | ✅ Funciona |
| `cli.py` | `qwen_dev_cli/cli.py` | Entry point `qwen-dev` | ✅ Funciona |
| `repl_masterpiece.py` | `qwen_dev_cli/cli/repl_masterpiece.py` | Shell REPL interativo | ⚠️ Parcial |
| `shell_main.py` | `qwen_dev_cli/shell_main.py` | Shell principal | ❌ Bug |

### Camada 2: Roteamento de Comandos

| Arquivo | Linhas Críticas | O que faz |
|---------|-----------------|-----------|
| `maestro.py` | 347-369 | `@agent_app.async_command("plan")` |
| `repl_masterpiece.py` | 514-519 | Registro de `/plan` no dicionário |
| `repl_masterpiece.py` | 952-986 | `_process_command()` |
| `shell_main.py` | 972-1031 | `_handle_system_command()` |

### Camada 3: Execução de Agents

| Arquivo | Localização | Responsabilidade |
|---------|-------------|------------------|
| `base.py` | `qwen_dev_cli/agents/base.py` | Protocolo BaseAgent |
| `executor_nextgen.py` | `qwen_dev_cli/agents/executor_nextgen.py` | ReAct + Streaming |
| `planner.py` | `qwen_dev_cli/agents/planner.py` | PlannerAgent |

---

## 🔍 Análise Detalhada do Bug

### O Problema

Existem **TRÊS sistemas de roteamento separados** que não se comunicam:

```
┌─────────────────────────────────────────────────────────────────┐
│                    SISTEMA 1: MAESTRO.PY                        │
│                                                                 │
│  Comando: maestro agent plan "criar autenticação"               │
│                                                                 │
│  Flow:                                                          │
│  1. Typer parseia argumentos                                    │
│  2. @agent_app.async_command("plan") é invocado                │
│  3. agent_plan() chama execute_agent_task("planner", goal)     │
│  4. Cria AgentTask estruturado                                  │
│  5. Aplica Governance Pipeline                                  │
│  6. Chama PlannerAgent.execute(task)                           │
│  7. Retorna AgentResponse formatado                             │
│                                                                 │
│  ✅ FUNCIONA CORRETAMENTE                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                 SISTEMA 2: REPL_MASTERPIECE.PY                  │
│                                                                 │
│  Comando: /plan criar autenticação                              │
│                                                                 │
│  Flow:                                                          │
│  1. _process_command() detecta /plan                           │
│  2. Busca handler em self.commands["/plan"]                    │
│  3. Executa: lambda msg: asyncio.run(_invoke_agent("planner")) │
│  4. _invoke_agent() chama LLM diretamente via stream_chat()    │
│  5. ⚠️ NÃO cria AgentTask                                       │
│  6. ⚠️ NÃO aplica Governance                                    │
│  7. Retorna resposta raw do LLM                                │
│                                                                 │
│  ⚠️ FUNCIONA MAS BYPASS GOVERNANCE                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   SISTEMA 3: SHELL_MAIN.PY                      │
│                                                                 │
│  Comando: /plan criar autenticação                              │
│                                                                 │
│  Flow:                                                          │
│  1. _handle_system_command() recebe "/plan ..."                │
│  2. Verifica: if cmd == "/help"? NO                            │
│  3. Verifica: if cmd == "/exit"? NO                            │
│  4. Verifica: if cmd == "/tools"? NO                           │
│  5. ... (nenhum match)                                         │
│  6. ❌ COMANDO NÃO TRATADO                                      │
│  7. Fallthrough → erro ou tenta processar como path            │
│                                                                 │
│  ❌ BUG: HANDLER AUSENTE                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Código do Bug

**Arquivo:** `qwen_dev_cli/shell_main.py`
**Linhas:** 972-1031

```python
async def _handle_system_command(self, cmd: str) -> tuple[bool, Optional[str]]:
    """Handle system commands (/help, /exit, etc.)."""
    cmd = cmd.strip()

    if cmd in ["/exit", "/quit"]:
        # ... handles exit
    elif cmd == "/help":
        # ... handles help
    elif cmd == "/tools":
        # ... handles tools listing
    elif cmd == "/context":
        # ... handles context
    # ... mais comandos do sistema ...

    # ❌ NÃO EXISTE CASE PARA /plan !
    # O comando cai no fallthrough e gera erro
```

---

## 📋 Arquivos que Precisam ser Modificados

### Prioridade 1: CRÍTICA (Fix do Bug)

#### 1. `qwen_dev_cli/shell_main.py`

**Problema:** Não tem handler para `/plan`

**Modificação Necessária:**
```python
# Adicionar em _handle_system_command() (após linha ~1020)

elif cmd.startswith("/plan"):
    # Extrair goal do comando
    goal = cmd[5:].strip()  # Remove "/plan "
    if not goal:
        self.console.print("[yellow]Usage: /plan <goal>[/yellow]")
        return False, None

    # Rotear para PlannerAgent via execute_agent_task
    from qwen_dev_cli.maestro import execute_agent_task
    result = await execute_agent_task("planner", goal, {})
    self._render_plan_result(result)
    return False, None
```

**Linhas a modificar:** ~1020-1031

---

#### 2. `qwen_dev_cli/cli/repl_masterpiece.py`

**Problema:** Handler usa LLM direto, bypassa governance

**Modificação Necessária:**
```python
# Modificar em self.commands (linhas 514-519)

"/plan": {
    "icon": "📋",
    "description": "Planner agent - strategic planning",
    "category": CommandCategory.AGENT,
    # ANTES: lambda msg: asyncio.run(self._invoke_agent("planner", msg))
    # DEPOIS: Usar execute_agent_task para consistência
    "handler": lambda msg: asyncio.run(self._execute_with_governance("planner", msg))
},

# Adicionar método _execute_with_governance (após linha ~880)
async def _execute_with_governance(self, agent_name: str, goal: str):
    """Execute agent with proper governance pipeline."""
    from qwen_dev_cli.maestro import execute_agent_task
    result = await execute_agent_task(agent_name, goal, {})
    self._display_agent_result(result)
```

**Linhas a modificar:** 514-519, adicionar método ~880

---

### Prioridade 2: ALTA (Unificação)

#### 3. `qwen_dev_cli/maestro.py`

**Problema:** Lógica de governance está acoplada ao CLI

**Modificação Recomendada:**
```python
# Extrair execute_agent_task para módulo separado
# para que possa ser reutilizado em shell_main.py e repl_masterpiece.py

# Criar: qwen_dev_cli/core/agent_router.py
```

**Linhas relevantes:** 191-282 (execute_agent_task)

---

#### 4. Criar novo arquivo: `qwen_dev_cli/core/command_router.py`

**Propósito:** Centralizar roteamento de comandos

```python
"""
Centralized Command Router
==========================

Single source of truth for all command routing.
"""

from typing import Dict, Callable, Optional
from dataclasses import dataclass
from enum import Enum

class CommandType(Enum):
    SYSTEM = "system"      # /help, /exit, /clear
    AGENT = "agent"        # /plan, /explore, /review
    TOOL = "tool"          # /bash, /file, /search
    META = "meta"          # /config, /status

@dataclass
class CommandSpec:
    name: str
    type: CommandType
    handler: Callable
    description: str
    usage: str
    requires_arg: bool = False

class CommandRouter:
    """Unified command router for all entry points."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_commands()
        return cls._instance

    def _init_commands(self):
        self.commands: Dict[str, CommandSpec] = {}
        self._register_system_commands()
        self._register_agent_commands()

    def _register_system_commands(self):
        """Register system commands (/help, /exit, etc.)."""
        self.register(CommandSpec(
            name="/help",
            type=CommandType.SYSTEM,
            handler=self._handle_help,
            description="Show help",
            usage="/help [command]"
        ))
        # ... mais comandos

    def _register_agent_commands(self):
        """Register agent commands (/plan, /explore, etc.)."""
        self.register(CommandSpec(
            name="/plan",
            type=CommandType.AGENT,
            handler=self._handle_plan,
            description="Generate execution plan",
            usage="/plan <goal>",
            requires_arg=True
        ))
        # ... mais comandos

    def register(self, spec: CommandSpec):
        self.commands[spec.name] = spec

    async def route(self, input_text: str) -> Optional[str]:
        """Route command to appropriate handler."""
        if not input_text.startswith("/"):
            return None  # Not a command

        parts = input_text.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd not in self.commands:
            return f"Unknown command: {cmd}. Type /help for available commands."

        spec = self.commands[cmd]
        if spec.requires_arg and not args:
            return f"Usage: {spec.usage}"

        return await spec.handler(args)

    async def _handle_plan(self, goal: str) -> str:
        """Handle /plan command with governance."""
        from qwen_dev_cli.maestro import execute_agent_task
        result = await execute_agent_task("planner", goal, {})
        return self._format_result(result)
```

---

### Prioridade 3: MÉDIA (Limpeza)

#### 5. `qwen_dev_cli/agents/executor.py`

**Problema:** Executor legado causa confusão

**Recomendação:** Deprecar ou remover em favor de `executor_nextgen.py`

---

## 🎯 Plano de Correção

### Fase 1: Fix Imediato (Bug #5)

```bash
# Arquivos a modificar:
1. qwen_dev_cli/shell_main.py          # Adicionar /plan handler
2. qwen_dev_cli/cli/repl_masterpiece.py # Unificar com governance
```

### Fase 2: Refatoração (Unificação)

```bash
# Novos arquivos a criar:
1. qwen_dev_cli/core/command_router.py  # Router centralizado
2. qwen_dev_cli/core/agent_dispatcher.py # Dispatcher unificado

# Arquivos a refatorar:
3. qwen_dev_cli/maestro.py              # Extrair execute_agent_task
4. qwen_dev_cli/shell_main.py           # Usar CommandRouter
5. qwen_dev_cli/cli/repl_masterpiece.py # Usar CommandRouter
```

### Fase 3: Testes

```bash
# Testes a adicionar:
1. tests/unit/test_command_router.py
2. tests/integration/test_routing_consistency.py
3. tests/e2e/test_slash_commands.py
```

---

## 📐 Diagrama de Fluxo Corrigido (Proposta)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ENTRADA DO USUÁRIO                                │
│                                                                             │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐    │
│   │ Terminal CLI    │  │ REPL Shell      │  │ Shell Main              │    │
│   │ maestro agent X │  │ /plan msg       │  │ /plan msg               │    │
│   └────────┬────────┘  └────────┬────────┘  └───────────┬─────────────┘    │
└────────────┼────────────────────┼───────────────────────┼──────────────────┘
             │                    │                       │
             │                    ▼                       │
             │         ┌──────────────────────┐           │
             │         │   CommandRouter      │◄──────────┘
             │         │   (Centralizado)     │
             │         │                      │
             │         │ • Detecta /comando   │
             │         │ • Valida argumentos  │
             │         │ • Roteia p/ handler  │
             │         └──────────┬───────────┘
             │                    │
             ▼                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AGENT DISPATCHER                                    │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    execute_agent_task()                               │  │
│  │                                                                       │  │
│  │  1. Cria AgentTask estruturado                                       │  │
│  │  2. Aplica Governance Pipeline                                        │  │
│  │  3. Seleciona Agent correto                                          │  │
│  │  4. Chama Agent.execute(task)                                        │  │
│  │  5. Processa AgentResponse                                           │  │
│  │  6. Retorna resultado formatado                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENTS LAYER                                   │
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ PlannerAgent │  │ CoderAgent   │  │ExplorerAgent │  │ RefactorAgent│    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                                             │
│                         executor_nextgen.py                                 │
│                    (ReAct Pattern + Streaming)                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

---

## 🐛 Bug #6: Falso Positivo no Intent Detection

**Status:** 🔴 CRÍTICO
**Descoberto:** Durante teste de "cria uma calculadora... test.html"

### O Problema

A mensagem:
```
cria uma calculadora em html e salva na pasta /home/juan/Videos com o nome test.html
```

Foi roteada para **TestingAgent** em vez de **Executor/Coder** porque:

1. A palavra `"test"` no nome do arquivo `test.html`
2. É um keyword para `IntentType.TESTING` (linha 156 de `integration_coordinator.py`)
3. O sistema não diferencia "test" como **intenção** vs "test" como **dado** (nome de arquivo)

### Fluxo do Bug

```
User: "cria uma calculadora... test.html"
         │
         ▼
┌────────────────────────────────────┐
│   integration_coordinator.py       │
│   detect_intent()                  │
│                                    │
│   message_lower.contains("test")   │
│   → TRUE (nome do arquivo)         │
│                                    │
│   IntentType.TESTING matches!      │
│   confidence = 0.5 (1 keyword)     │
└────────────────────────────────────┘
         │
         ▼ (confidence 0.5 >= 0.3)
┌────────────────────────────────────┐
│   Route to TestingAgent            │
│                                    │
│   TestingAgent.execute() expects:  │
│   - source_code OR                 │
│   - file_path                      │
│                                    │
│   Neither provided → ERROR         │
└────────────────────────────────────┘
         │
         ▼
❌ "source_code or file_path required in task context"
```

### Arquivos Afetados

| Arquivo | Problema |
|---------|----------|
| `qwen_dev_cli/core/integration_coordinator.py:155-157` | Keywords muito genéricos |
| `qwen_dev_cli/cli/intent_detector.py:56-66` | Mesmo problema |
| `qwen_dev_cli/agents/testing.py:296-302` | Erro não informativo |

### Código Problemático

**integration_coordinator.py:155-157**
```python
IntentType.TESTING: [
    "test", "coverage", "unit", "integration", "e2e"  # ← "test" muito genérico!
],
```

**intent_detector.py:56-66**
```python
"test": {
    "keywords": [
        "test", "teste", "testes", "testing",  # ← Mesmos problemas
        "unit test", "integration test", "e2e",
        "coverage", "cobertura", "pytest", "jest"
    ],
    ...
}
```

### Solução Proposta

#### 1. Keywords mais específicos (não match parcial)

```python
IntentType.TESTING: [
    # Remover "test" sozinho - muito genérico
    "create test", "write test", "add test",
    "unit test", "integration test", "e2e test",
    "test coverage", "pytest", "jest",
    "criar teste", "escrever teste", "testar código"
],
```

#### 2. Negative matching (excluir falsos positivos)

```python
def detect_intent(self, message: str) -> Intent:
    message_lower = message.lower()

    # NOVO: Excluir matches em nomes de arquivos
    # Remove .html, .py, .js etc do matching
    clean_message = re.sub(r'\b\w+\.(html|py|js|ts|css|json)\b', '', message_lower)

    # Agora match em clean_message em vez de message_lower
    for intent_type, keywords in self._intent_keywords.items():
        matches = sum(1 for kw in keywords if kw in clean_message)
        ...
```

#### 3. Contexto semântico

```python
# Verificar se "test" aparece em contexto de testing vs como dado
def _is_testing_context(self, message: str) -> bool:
    testing_verbs = ["criar teste", "escrever teste", "testar", "add test"]
    return any(verb in message.lower() for verb in testing_verbs)
```

#### 4. Fallback para Executor

Se nenhum agent específico for detectado com alta confiança, a mensagem deveria ir para o **ExecutorAgent** (que pode criar arquivos, código, etc):

```python
# Em process_message()
if intent.type == IntentType.GENERAL or intent.confidence < 0.5:
    # Fallback to executor for general tasks
    return await self._executor_agent.execute(message)
```

### Arquivos a Modificar

1. **`qwen_dev_cli/core/integration_coordinator.py`**
   - Linhas 155-157: Keywords mais específicos
   - Linhas 357-389: Adicionar negative matching
   - Linhas 425-453: Fallback para executor

2. **`qwen_dev_cli/cli/intent_detector.py`**
   - Linhas 56-66: Keywords mais específicos
   - Método `detect()`: Adicionar limpeza de nomes de arquivos

3. **`qwen_dev_cli/agents/testing.py`**
   - Linhas 296-302: Mensagem de erro mais útil
   - Sugerir agent correto quando contexto inválido

---

## ✅ Checklist de Correção

### Bug #5: /plan routing
- [ ] Adicionar handler `/plan` em `shell_main.py`
- [ ] Modificar handler `/plan` em `repl_masterpiece.py` para usar governance
- [ ] Criar `CommandRouter` centralizado
- [ ] Extrair `execute_agent_task` para módulo reutilizável

### Bug #6: False positive intent detection
- [ ] Refatorar keywords em `integration_coordinator.py` (remover "test" sozinho)
- [ ] Refatorar keywords em `intent_detector.py` (remover "test" sozinho)
- [ ] Adicionar negative matching para nomes de arquivos
- [ ] Implementar fallback para Executor quando intent incerto
- [ ] Melhorar mensagem de erro em `testing.py`

### Geral
- [ ] Adicionar testes de integração para roteamento
- [ ] Documentar fluxo de roteamento para desenvolvedores
- [ ] Deprecar `executor.py` legado

---

## 📚 Referências

- `qwen_dev_cli/maestro.py:191-282` - execute_agent_task atual
- `qwen_dev_cli/maestro.py:347-369` - agent_plan CLI handler
- `qwen_dev_cli/cli/repl_masterpiece.py:514-539` - command registry
- `qwen_dev_cli/cli/repl_masterpiece.py:952-986` - _process_command
- `qwen_dev_cli/shell_main.py:972-1031` - _handle_system_command
- `qwen_dev_cli/agents/base.py:220-224` - BaseAgent.execute protocol
