# Testes Manuais - MAESTRO + DataAgent
## Guia para testar no seu terminal

---

## 🚀 SETUP

```bash
# 1. Ativar ambiente (se necessário)
source venv/bin/activate  # ou seu virtualenv

# 2. Verificar que Gemini está configurado
cat .env | grep GEMINI
# Deve mostrar: GEMINI_API_KEY=...
```

---

## 📋 TESTE 1: Iniciar MAESTRO

```bash
# Rodar MAESTRO
python3 maestro_v10_integrated.py
```

**Esperado:**
```
╔══════════════════════════════════════════════════════════════╗
║                    MAESTRO v10.0                            ║
║              Agent-Powered Terminal @ 30 FPS                ║
╚══════════════════════════════════════════════════════════════╝

maestro>
```

---

## 📋 TESTE 2: Verificar Agentes Disponíveis

```bash
# No prompt do MAESTRO, digite:
/agents
```

**Esperado:**
```
🤖 Available Agents (v6.0)
  ├─ 💻 SimpleExecutor
  ├─ ⚡ Planner v5.0
  ├─ 🔍 Reviewer v5.0
  ├─ 🔧 Refactorer v8.0
  ├─ 🗺️ Explorer
  └─ 🗄️ DataAgent v1.0          ← NOVO!
      ├─ Schema analysis & optimization
      ├─ Query optimization (70%+ improvements)
      ├─ Migration planning with rollback
      └─ Extended thinking (5000 token budget)
```

---

## 📋 TESTE 3: Help do DataAgent

```bash
# No prompt do MAESTRO:
/data
```

**Esperado:**
```
╭─────────── 🗄️  DataAgent Quick Reference ───────────╮
│ 🗄️  DataAgent v1.0 - Database Operations           │
│                                                     │
│ Capabilities:                                       │
│   • Schema Analysis (detect issues, recommend fixes)│
│   • Query Optimization (70%+ improvements)          │
│   • Migration Planning (risk assessment + rollback) │
│   • Extended Thinking (5000 token budget)           │
│                                                     │
│ Usage Examples:                                     │
│   analyze schema for users table                    │
│   optimize query SELECT * FROM orders WHERE...      │
│   plan migration to add email_verified column       │
╰─────────────────────────────────────────────────────╯
```

---

## 📋 TESTE 4: Schema Analysis

```bash
# No prompt do MAESTRO:
analyze schema for users table with id, name, email and 3 jsonb columns
```

**Esperado:**
```
🗄️  DATABASE ANALYSIS

[Gemini vai analisar e retornar algo como:]

Schema Analysis Results:

⚠️  Schema Issues Found:
  🔴 Table 'users' has no primary key
     💡 Add a primary key (UUID or BIGSERIAL)

  🟡 Table 'users' lacks audit timestamps
     💡 Add created_at, updated_at columns

  🟠 Table 'users' has 3 JSON columns
     💡 Consider normalizing frequently-queried JSON fields

💭 Reasoning:
[Thinking trace aparece aqui...]
```

---

## 📋 TESTE 5: Query Optimization

```bash
# No prompt do MAESTRO:
optimize query SELECT * FROM users WHERE email LIKE '%gmail%'
```

**Esperado:**
```
🗄️  DATABASE ANALYSIS

[Gemini vai otimizar:]

⚡ Query Optimization:
  Improvement: 60-80%
  Confidence: 85%
  Indexes needed: users(email), ...

Recommendations:
- Avoid leading wildcard in LIKE (kills index usage)
- Consider full-text search for email patterns
- Add index on email column
```

---

## 📋 TESTE 6: Migration Planning

```bash
# No prompt do MAESTRO:
plan migration to add email_verified boolean column to users table
```

**Esperado:**
```
🗄️  DATABASE ANALYSIS

🏗️  Migration Plan:
  🟢 Risk: LOW
  ⏱️  Downtime: 0s
  ✅ Can run online: True

Up Commands:
  • ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE

Down Commands:
  • ALTER TABLE users DROP COLUMN email_verified

💭 Reasoning:
[Risk assessment thinking...]
```

---

## 📋 TESTE 7: Roteamento Inteligente

### 7.1 - Deve chamar DataAgent:
```bash
database help
schema issues
query performance
table optimization
sql performance
```

### 7.2 - Deve chamar outros agentes (sem conflito):
```bash
review base.py                    # → Reviewer
plan implement user auth          # → Planner
refactor extract method           # → Refactorer
```

---

## 📋 TESTE 8: Help Geral

```bash
# No prompt do MAESTRO:
/help
```

**Esperado:**
```
Agent Triggers:
  "review..."      → Reviewer v5.0
  "plan..."        → Planner v5.0
  "refactor..."    → Refactorer v8.0
  "explore..."     → Explorer
  "database..."    → DataAgent v1.0  ← NOVO!
  "run/exec..."    → Executor

Examples:
  analyze schema for users table   ← NOVO!
  optimize query SELECT * FROM...  ← NOVO!
```

---

## 📋 TESTE 9: Teste de Stress

```bash
# Teste complexo com query grande:
optimize this query: SELECT u.id, u.name, u.email, o.order_id, o.amount, o.created_at FROM users u LEFT JOIN orders o ON u.id = o.user_id WHERE u.email LIKE '%@gmail.com' AND o.status = 'pending' AND o.created_at > NOW() - INTERVAL '7 days' ORDER BY o.created_at DESC LIMIT 100
```

**Esperado:**
- DataAgent deve processar com Extended Thinking
- Deve retornar análise detalhada
- Sugerir múltiplos indexes
- Mostrar % de melhoria

---

## ✅ CHECKLIST DE VALIDAÇÃO

Marque conforme testa:

- [ ] MAESTRO inicia corretamente
- [ ] `/agents` mostra DataAgent v1.0
- [ ] `/data` mostra quick reference
- [ ] `/help` menciona DataAgent
- [ ] "analyze schema" chama DataAgent
- [ ] "optimize query" chama DataAgent
- [ ] "plan migration" chama DataAgent
- [ ] "database ..." chama DataAgent
- [ ] "review ..." ainda chama Reviewer (sem conflito)
- [ ] "plan ..." para coisas não-DB chama Planner (sem conflito)
- [ ] Output tem ícones coloridos (🔴🟠🟡🟢)
- [ ] Output mostra thinking trace
- [ ] Gemini responde corretamente
- [ ] Nenhum erro ou exception

---

## 🐛 SE ALGO DER ERRADO

### Erro: "ModuleNotFoundError"
```bash
# Verificar imports
python3 -c "from qwen_dev_cli.agents.data_agent_production import create_data_agent; print('OK')"
```

### Erro: "LLM call failed"
```bash
# Verificar Gemini
python3 -c "from qwen_dev_cli.core.llm import LLMClient; import asyncio; asyncio.run(LLMClient().generate('test'))"
```

### DataAgent não aparece em /agents
```bash
# Verificar se está registrado
python3 -c "from maestro_v10_integrated import Orchestrator; from qwen_dev_cli.core.llm import LLMClient; o = Orchestrator(LLMClient(), None); print('data' in o.agents)"
# Deve printar: True
```

### Routing errado
```bash
# Testar routing direto
python3 -c "from maestro_v10_integrated import Orchestrator; from qwen_dev_cli.core.llm import LLMClient; o = Orchestrator(LLMClient(), None); print(o.route('analyze schema'))"
# Deve printar: data
```

---

## 📸 SCREENSHOTS ESPERADOS

Quando tudo funcionar, você deve ver:

1. **DataAgent em /agents** - Tree com 🗄️ DataAgent v1.0
2. **Output colorido** - 🔴🟠🟡🟢 para severidade
3. **Thinking trace** - "💭 Reasoning: ..."
4. **Métricas** - "Improvement: 70%", "Confidence: 85%"
5. **Migration plan** - Risk levels com ícones

---

## 🎯 PRÓXIMOS PASSOS

Se tudo passar:
1. ✅ Marcar todos os itens do checklist
2. ✅ Tirar screenshot do /agents
3. ✅ Testar com query SQL real (se tiver banco)
4. ✅ Compartilhar feedback

---

**Boa sorte! 🚀**
