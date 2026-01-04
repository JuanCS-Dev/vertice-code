# Jules API Analysis - Nossa Implementação vs Documentação Oficial

## Fontes Oficiais
- https://developers.google.com/jules/api
- https://jules.google/docs/api/reference/types/

---

## 1. SessionState Enum

### Oficial (API v1alpha):
```
STATE_UNSPECIFIED  - Unset
QUEUED             - Awaiting processing
PLANNING           - Creating plan
AWAITING_PLAN_APPROVAL - Needs approval
AWAITING_USER_FEEDBACK - Needs user input
IN_PROGRESS        - Actively executing
PAUSED             - Suspended
FAILED             - Error occurred
COMPLETED          - Success
```

### Nossa Implementação:
```python
QUEUED = "QUEUED"                           # ✓ OK
PLANNING = "PLANNING"                       # ✓ OK
AWAITING_PLAN_APPROVAL = "AWAITING_PLAN_APPROVAL"  # ✓ OK
IN_PROGRESS = "IN_PROGRESS"                 # ✓ OK
COMPLETED = "COMPLETED"                     # ✓ OK
FAILED = "FAILED"                           # ✓ OK
CANCELLED = "CANCELLED"                     # ✗ NÃO EXISTE NA API
```

### Discrepâncias:
| Issue | Severidade | Fix |
|-------|-----------|-----|
| Falta `AWAITING_USER_FEEDBACK` | MÉDIA | Adicionar |
| Falta `PAUSED` | MÉDIA | Adicionar |
| `CANCELLED` não existe | BAIXA | Remover ou manter como fallback |

---

## 2. ActivityType Enum

### Oficial (API v1alpha):
```
planGenerated     - { plan: Plan }
planApproved      - { planId: string }
userMessaged      - { userMessage: string }
agentMessaged     - { agentMessage: string }
progressUpdated   - { title: string, description: string }
sessionCompleted  - {}
sessionFailed     - { reason: string }
```

### Nossa Implementação:
```python
PLAN_GENERATED = "planGenerated"      # ✓ OK
PLAN_APPROVED = "planApproved"        # ✓ OK
PROGRESS_UPDATED = "progressUpdated"  # ✓ OK
SESSION_COMPLETED = "sessionCompleted" # ✓ OK
FILE_CREATED = "fileCreated"          # ✗ NÃO É ACTIVITY TYPE (é artifact)
FILE_MODIFIED = "fileModified"        # ✗ NÃO É ACTIVITY TYPE (é artifact)
ERROR_OCCURRED = "errorOccurred"      # ✗ DEVERIA SER sessionFailed
MESSAGE_RECEIVED = "messageReceived"  # ✗ DEVERIA SER userMessaged
MESSAGE_SENT = "messageSent"          # ✗ DEVERIA SER agentMessaged
```

### Discrepâncias:
| Issue | Severidade | Fix |
|-------|-----------|-----|
| `FILE_CREATED` não existe | ALTA | Remover (files vêm em artifacts) |
| `FILE_MODIFIED` não existe | ALTA | Remover (files vêm em artifacts) |
| `ERROR_OCCURRED` → `SESSION_FAILED` | ALTA | Renomear |
| `MESSAGE_RECEIVED` → `USER_MESSAGED` | ALTA | Renomear |
| `MESSAGE_SENT` → `AGENT_MESSAGED` | ALTA | Renomear |

---

## 3. PlanStep Schema

### Oficial:
```
id          - string (step identifier)
index       - int32 (position in plan)
title       - string (step name)
description - string (step details)
```

### Nossa Implementação:
```python
step_id: str              # ✓ Mapeia para id
description: str          # ✓ OK
action: str               # ✗ NÃO EXISTE NA API
parameters: Dict          # ✗ NÃO EXISTE NA API
dependencies: List[str]   # ✗ NÃO EXISTE NA API
# FALTA: index: int
# FALTA: title: str
```

### Discrepâncias:
| Issue | Severidade | Fix |
|-------|-----------|-----|
| Falta `index` | MÉDIA | Adicionar |
| Falta `title` | MÉDIA | Adicionar |
| `action` não existe | BAIXA | Remover ou manter como extensão |
| `parameters` não existe | BAIXA | Remover ou manter |
| `dependencies` não existe | BAIXA | Remover ou manter |

---

## 4. Activity Schema

### Oficial:
```
name        - string (resource identifier: sessions/{}/activities/{})
id          - string (activity ID)
originator  - string (user | agent | system)
description - string (activity summary)
createTime  - datetime
artifacts   - Artifact[] (changeSet, bashOutput, media)
+ ONE event type field (planGenerated, planApproved, etc.)
```

### Nossa Implementação:
```python
activity_id: str                    # ✓ Mapeia para name
type: JulesActivityType             # ✓ OK (mas valores errados)
timestamp: datetime                 # ✓ Mapeia para createTime
data: Dict[str, Any]                # ✓ Flexível, captura event data
message: str                        # ✓ Extração customizada (OK)
# FALTA: originator
# FALTA: description (campo da API)
# FALTA: artifacts parsing
```

### Discrepâncias:
| Issue | Severidade | Fix |
|-------|-----------|-----|
| Falta `originator` | BAIXA | Adicionar |
| Falta parsing de `artifacts` | MÉDIA | Adicionar estruturas |

---

## 5. Session Schema

### Oficial:
```
name               - string (resource: sessions/{id})
id                 - string (session ID)
prompt             - string (required)
title              - string (optional)
state              - SessionState
url                - string (web app link)
sourceContext      - SourceContext
requirePlanApproval - boolean
automationMode     - AutomationMode (AUTO_CREATE_PR)
outputs            - SessionOutput[] (pullRequest)
createTime         - datetime
updateTime         - datetime
```

### Nossa Implementação:
```python
session_id: str                     # ✓ Mapeia para name
state: JulesSessionState            # ✓ OK
title: str                          # ✓ OK
prompt: str                         # ✓ OK
created_at: datetime                # ✓ Mapeia para createTime
updated_at: datetime                # ✓ Mapeia para updateTime
plan: Optional[JulesPlan]           # ✓ OK (extraído de activities)
activities: List[JulesActivity]     # ✓ OK (buscado separadamente)
source_context: Optional[Dict]      # ✓ OK
result_url: Optional[str]           # ✓ Mapeia para outputs.pullRequest.url
error_message: Optional[str]        # ✓ OK
# FALTA: url (link web app)
# FALTA: automationMode
```

### Discrepâncias:
| Issue | Severidade | Fix |
|-------|-----------|-----|
| Falta `url` (web app link) | BAIXA | Adicionar |
| Falta `automationMode` | BAIXA | Considerar adicionar |

---

## 6. Provider Parser Issues

### `_parse_activity()` - Problemas Identificados:

1. **progressUpdated structure:**
   - Oficial: `{ title: string, description: string }`
   - Atual: Buscamos `title`, `text`, `message` - OK após fix

2. **sessionFailed vs errorOccurred:**
   - Oficial usa `sessionFailed` com `{ reason: string }`
   - Nosso código busca `errorOccurred` - PRECISA CORRIGIR

3. **userMessaged vs messageReceived:**
   - Oficial usa `userMessaged` com `{ userMessage: string }`
   - Nosso código busca `messageReceived` - PRECISA CORRIGIR

4. **agentMessaged vs messageSent:**
   - Oficial usa `agentMessaged` com `{ agentMessage: string }`
   - Nosso código busca `messageSent` - PRECISA CORRIGIR

---

## 7. Artifacts (Novo - Não Implementado)

### Oficial:
```
Artifact:
  - changeSet: { source, gitPatch }
  - bashOutput: { command, output, exitCode }
  - media: { mimeType, data }

GitPatch:
  - baseCommitId: string
  - unidiffPatch: string
  - suggestedCommitMessage: string
```

### Recomendação:
Adicionar parsing de artifacts para extrair:
- Patches de código (diffs)
- Saídas de comandos bash
- Screenshots/mídia

---

## 8. Plano de Correções

### ALTA PRIORIDADE:
1. [ ] Corrigir `JulesActivityType` enum com nomes oficiais
2. [ ] Atualizar parser para `sessionFailed`, `userMessaged`, `agentMessaged`
3. [ ] Adicionar estados faltantes: `AWAITING_USER_FEEDBACK`, `PAUSED`

### MÉDIA PRIORIDADE:
4. [ ] Adicionar `index` e `title` ao `JulesPlanStep`
5. [ ] Adicionar `originator` ao `JulesActivity`
6. [ ] Implementar parsing de artifacts

### BAIXA PRIORIDADE:
7. [ ] Adicionar `url` ao `JulesSession`
8. [ ] Considerar `automationMode`
9. [ ] Limpar campos não-existentes (action, parameters, dependencies)

---

## 9. Validação com API Real

Sessão ativa para testes: `9641116486441618141`

Campos observados na resposta real da API:
- `planGenerated.plan.steps[].title` ✓
- `progressUpdated.title` ✓
- `progressUpdated` vazio `{}` também ocorre ✓
- `planApproved` ✓

---

## 10. Correções Aplicadas (2026-01-04)

### JulesSessionState
```python
# ANTES (incorreto)
CANCELLED = "CANCELLED"  # Não existe na API

# DEPOIS (correto)
STATE_UNSPECIFIED = "STATE_UNSPECIFIED"
AWAITING_USER_FEEDBACK = "AWAITING_USER_FEEDBACK"
PAUSED = "PAUSED"
```

### JulesActivityType
```python
# ANTES (incorreto)
FILE_CREATED, FILE_MODIFIED  # Não são activity types
ERROR_OCCURRED              # Nome errado
MESSAGE_RECEIVED, MESSAGE_SENT  # Nomes errados

# DEPOIS (correto v1alpha)
SESSION_FAILED = "sessionFailed"      # { reason: string }
USER_MESSAGED = "userMessaged"        # { userMessage: string }
AGENT_MESSAGED = "agentMessaged"      # { agentMessage: string }
```

### JulesPlanStep
```python
# ANTES
step_id, description, action, parameters, dependencies

# DEPOIS (v1alpha)
step_id, index, title, description
```

### JulesActivity
```python
# DEPOIS - novos campos
originator: str = ""   # "user" | "agent" | "system"
description: str = ""  # activity summary from API
```

### JulesSession
```python
# DEPOIS - novo campo
url: str = ""  # web app session URL
```

### Resultado da Validação com API Real
```
Session State: AWAITING_USER_FEEDBACK  ✓ (novo estado reconhecido)
Activity Types: planGenerated, planApproved, progressUpdated, agentMessaged
All activities have originator: ✓
URL field parsed: https://jules.google.com/session/...
```

---

*Análise criada em 2026-01-04*
*Correções aplicadas e validadas com API real*
