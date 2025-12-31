# VERTICE Open Source Release Plan (Investment-Ready)

## Objetivo
Preparar VERTICE para lançamento open source profissional com estratégia Open Core para atrair investimento.

## Configurações Confirmadas
- **Stripe Donation Link**: https://buy.stripe.com/aFa6oJ1mY7KU1fW4LF33W01
- **Licença**: MIT (confirmado)
- **GitHub URL**: github.com/JuanCS-Dev/vertice-code
- **Autor**: Juan Carlos de Souza
- **Escopo**: Completo (todos os 14 arquivos)

---

## Estado Atual (75% pronto)

### Já Existe
- [x] README.md completo (483 linhas)
- [x] LICENSE (MIT)
- [x] CONTRIBUTING.md
- [x] SECURITY.md
- [x] CHANGELOG.md
- [x] .github/workflows/tests.yml
- [x] .github/workflows/lint.yml
- [x] .github/ISSUE_TEMPLATE/ (bug, feature)
- [x] .github/PULL_REQUEST_TEMPLATE/
- [x] 732+ testes
- [x] docs/ com 100+ arquivos

### Falta Criar
- [ ] CODE_OF_CONDUCT.md
- [ ] .github/FUNDING.yml (Stripe link)
- [ ] .github/CODEOWNERS
- [ ] .github/dependabot.yml
- [ ] .github/workflows/publish.yml (PyPI)
- [ ] Package READMEs (8 pacotes)
- [ ] docs/GETTING_STARTED.md
- [ ] examples/README.md

---

## Sprint 1: GitHub Community Standards

### 1.1 CODE_OF_CONDUCT.md
- Contributor Covenant v2.1
- Enforcement contact: juancs.dev@gmail.com

### 1.2 .github/FUNDING.yml
```yaml
custom: ["https://buy.stripe.com/aFa6oJ1mY7KU1fW4LF33W01"]
```

### 1.3 .github/CODEOWNERS
```
* @JuanCS-Dev
/vertice_cli/ @JuanCS-Dev
/vertice_tui/ @JuanCS-Dev
/vertice_governance/ @JuanCS-Dev
```

### 1.4 .github/dependabot.yml
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

---

## Sprint 2: README & Branding

### 2.1 Atualizar README.md
- Adicionar badges (PyPI, Tests, License, Python)
- Adicionar botão "Sponsor this project"
- Adicionar screenshot do TUI (se existir)
- Manter estrutura atual (já está excelente)

### 2.2 Corrigir URLs no pyproject.toml
```toml
[project.urls]
Homepage = "https://github.com/JuanCS-Dev/vertice-code"
Repository = "https://github.com/JuanCS-Dev/vertice-code"
Issues = "https://github.com/JuanCS-Dev/vertice-code/issues"
Funding = "https://buy.stripe.com/aFa6oJ1mY7KU1fW4LF33W01"
```

---

## Sprint 3: Package Documentation (8 READMEs)

Criar README.md para cada pacote principal:

| Pacote | Descrição | Prioridade |
|--------|-----------|------------|
| `vertice_cli/README.md` | CLI interface docs | HIGH |
| `vertice_tui/README.md` | TUI interface docs | HIGH |
| `vertice_core/README.md` | Domain kernel | HIGH |
| `agents/README.md` | Agent system | HIGH |
| `core/README.md` | Framework foundation | MEDIUM |
| `vertice_governance/README.md` | Constitutional AI | MEDIUM |
| `prometheus/README.md` | Já existe (915 linhas) | SKIP |
| `tools/README.md` | Tools system | MEDIUM |

### Template para cada README:
```markdown
# Package Name

Brief description.

## Installation
## Quick Start
## API Reference
## Examples
```

---

## Sprint 4: PyPI Publishing

### 4.1 Atualizar pyproject.toml
- Versão: 0.8.0 (alinhar com commits)
- Nome PyPI: `vertice` (simples)
- Adicionar URL de Funding

### 4.2 Criar .github/workflows/publish.yml
- Trigger: git tag (v*)
- Build: python -m build
- Publish: twine upload to PyPI

---

## Sprint 5: Extras

### 5.1 docs/GETTING_STARTED.md
- Guia de 5 minutos
- Instalação simplificada
- Primeiro uso

### 5.2 examples/README.md
- Índice dos 13 exemplos existentes

---

## Arquivos a Criar

| Arquivo | Linhas Est. | Sprint |
|---------|-------------|--------|
| `CODE_OF_CONDUCT.md` | ~130 | 1 |
| `.github/FUNDING.yml` | ~3 | 1 |
| `.github/CODEOWNERS` | ~5 | 1 |
| `.github/dependabot.yml` | ~10 | 1 |
| `.github/workflows/publish.yml` | ~50 | 4 |
| `vertice_cli/README.md` | ~80 | 3 |
| `vertice_tui/README.md` | ~80 | 3 |
| `vertice_core/README.md` | ~60 | 3 |
| `agents/README.md` | ~100 | 3 |
| `core/README.md` | ~60 | 3 |
| `vertice_governance/README.md` | ~80 | 3 |
| `tools/README.md` | ~60 | 3 |
| `docs/GETTING_STARTED.md` | ~100 | 5 |
| `examples/README.md` | ~50 | 5 |

## Arquivos a Modificar

| Arquivo | Mudança |
|---------|---------|
| `README.md` | Adicionar badges + sponsor button |
| `pyproject.toml` | URLs (vertice-code) + funding URL |

---

## Ordem de Execução

1. **CODE_OF_CONDUCT.md** - obrigatório para community profile
2. **.github/FUNDING.yml** - ativa botão Sponsor
3. **.github/CODEOWNERS** - define ownership
4. **.github/dependabot.yml** - security updates
5. **README.md updates** - badges + sponsor
6. **pyproject.toml updates** - URLs corretas
7. **Package READMEs** (8 arquivos)
8. **.github/workflows/publish.yml** - PyPI automation
9. **docs/GETTING_STARTED.md**
10. **examples/README.md**

---

## Próximos Passos Pós-Release

1. Publicar no PyPI
2. Post no Hacker News
3. Post no Reddit r/programming
4. Criar Discord server
5. Buscar primeiros 100 stars
