# 📚 TEXTUAL (2026) — CONSOLIDAÇÃO DE PADRÕES OFICIAIS (FASE 1)

> **Escopo:** somente consolidação de documentação oficial + checklist de conformidade.
> **Fora de escopo (por enquanto):** declarar “✅ conforme” vs nosso código. Isso será feito na **Fase 2 (auditoria)**.

## 0) Baseline do ambiente (para evitar “doc drift”)

**Motivo:** a documentação “atual” do Textual pode evoluir; esta fase fixa um baseline para validar padrões no código depois.

```bash
python -c "import textual, pytest_asyncio; print('textual', textual.__version__); print('pytest-asyncio', pytest_asyncio.__version__)"
```

- Textual (instalado): `6.2.1`
- pytest-asyncio (instalado): `0.24.0`
- Config pytest do repo (já presente): `pytest.ini` define `asyncio_mode=auto` e `asyncio_default_fixture_loop_scope=function`

## 1) App lifecycle, mounting e shutdown (padrões 2026)

**Source:** https://textual.textualize.io/guide/app/
**Seções (âncoras):**
- `#mounting` (montagem / lifecycle prático)
- `#awaiting-mount` (aguardar mount para evitar race conditions)
- `#async-events` (handlers async)
- `#exiting` (saída correta do app)

**Pattern (adaptado dos exemplos oficiais):**
```python
from textual.app import App, ComposeResult
from textual.widgets import Static


class MyApp(App[None]):
    def compose(self) -> ComposeResult:
        yield Static("Hello")

    async def on_mount(self) -> None:
        # Se precisar garantir que o mount terminou:
        await self.mount(Static("mounted later"))
        self.query_one(Static).focus()  # após mount, pode consultar com segurança
```

**Notas práticas (guideline):**
- Preferir `compose()` para definir a árvore inicial; evitar montar widgets em `__init__`.
- Se o handler precisa do widget já montado, use o padrão de “await mount” (evita depender de internals).
- Para encerrar, use `self.exit(...)` / fluxo de saída do Textual; evitar `sys.exit()` dentro do app.

## 2) Eventos e handlers (padrões 2026)

**Source:** https://textual.textualize.io/guide/events/
**Source (API do decorator):** https://textual.textualize.io/api/on/

**Pattern 1 — `on_*` handlers (simples):**
```python
class MyApp(App[None]):
    async def on_key(self, event) -> None:
        # handler pode ser async conforme guia de eventos
        if event.key == "escape":
            self.exit()
```

**Pattern 2 — `@on(...)` com selector (declarativo):**
```python
from textual import on
from textual.widgets import Button


class MyView:
    @on(Button.Pressed, "#quit")
    def _quit(self) -> None:
        self.app.exit()
```

**Checklist de eventos (para Fase 2):**
- Evitar handlers fazendo I/O bloqueante (mover para worker).
- Preferir seleção por CSS selectors quando apropriado (melhora legibilidade e reduz “if cascata”).
- Evitar acessar internals do message pump / loop em handlers.

## 3) Workers (padrões 2026)

**Source:** https://textual.textualize.io/guide/workers/
**Source (API do decorator):** https://textual.textualize.io/api/work/

**Pattern 1 — `@work(...)` (recomendado para tarefas associadas a handlers):**
```python
from textual import work


class MyApp(App[None]):
    @work(exclusive=True, group="chat")
    async def do_background(self) -> None:
        ...
```

**Pattern 2 — `run_worker(...)` (útil para disparo dinâmico):**
```python
class MyApp(App[None]):
    def start_job(self) -> None:
        self.run_worker(self._job(), group="jobs", exclusive=False)

    async def _job(self) -> None:
        ...
```

**Pontos “2026” para auditoria:**
- Usar `group`/`exclusive` para garantir cancelamento determinístico (evitar workers órfãos em teardown).
- Usar `thread=True` (thread worker) apenas para código bloqueante/CPU-bound que não pode ser async.
- Cancelamento/exit: garantir que o app não termina com workers ainda executando.

## 4) Reactivity (padrões 2026)

**Source:** https://textual.textualize.io/guide/reactivity/

**Pattern:**
```python
from textual.reactive import reactive


class MyWidget:
    is_processing: reactive[bool] = reactive(False)

    def watch_is_processing(self, value: bool) -> None:
        # watcher deve ser leve; sem computação pesada
        self.set_class(value, "-busy")
```

**Performance checklist (do guia de reatividade):**
- Watchers: pequenos e sem I/O.
- Atualizações: reduzir churn de refresh (evitar `refresh()` em loop apertado).
- Preferir atualizar o modelo (state) e deixar reatividade atualizar UI, não o contrário.

## 5) Widgets, composição e “growth control” (padrões 2026)

**Source:** https://textual.textualize.io/guide/widgets/

**Guideline:** para listas longas (ex.: chat), a UI deve evitar crescimento infinito de widgets sem estratégia de descarte/compactação.

**Padrões que o Textual fornece para ajudar:**
- Containers e scroll nativos (usar widgets adequados ao caso).
- Lazy instantiation (próxima seção) para widgets caros.

## 6) Lazy mounting / lazy instantiation (padrões 2026)

**Source:** https://textual.textualize.io/api/lazy/

**Pattern:**
```python
from textual.app import ComposeResult
from textual.lazy import Lazy
from textual.widgets import Markdown


class MyApp(App[None]):
    def compose(self) -> ComposeResult:
        # Widget pesado só será materializado quando necessário
        yield Lazy(Markdown("..."))
```

## 7) Testing do Textual (padrões 2026)

**Source:** https://textual.textualize.io/guide/testing/
**Seções (âncoras):**
- `#testing-apps` (run_test / Pilot)
- `#pausing-the-pilot` (sincronizar com timers/refresh)

**Pattern:**
```python
import pytest


@pytest.mark.asyncio
async def test_app_basic():
    app = MyApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()
        ...
```

**Guidelines relevantes ao bug “ContextVar / message pump”:**
- Use `async with app.run_test()` para garantir startup/teardown do Textual no mesmo fluxo.
- Evite tocar em internals do Textual (ex.: message pump privado) no teste; prefira `Pilot`.
- Evite “spawn” de tasks fora do controle do app durante o teste sem cancelar/aguardar corretamente.

## 8) Screens / Modes (padrões 2026)

**Source:** https://textual.textualize.io/guide/screens/

**Guideline:** para múltiplas “views”, use screens/modes ao invés de esconder/mostrar widgets manualmente e acumular árvore.

---

# ✅ CHECKLIST DE CONFORMIDADE (para preencher na Fase 2)

> Este checklist é a “grade” de auditoria: **sem marcar** até auditar os arquivos do TUI.

## App lifecycle
- [ ] `compose()` define árvore inicial (ou justificativa clara se não).
- [ ] `on_mount()` faz apenas setup leve (sem I/O bloqueante).
- [ ] Onde há dependência de mount, usa padrão de “awaiting mount”: https://textual.textualize.io/guide/app/#awaiting-mount
- [ ] Saída limpa via `exit(...)`: https://textual.textualize.io/guide/app/#exiting

## Eventos
- [ ] Handlers sem I/O bloqueante; delegam para workers quando necessário.
- [ ] Uso consistente de `@on(...)`/selectors quando reduz complexidade: https://textual.textualize.io/guide/events/

## Workers
- [ ] Long tasks sempre em worker (`@work` / `run_worker`): https://textual.textualize.io/guide/workers/
- [ ] `group`/`exclusive` usados para evitar workers órfãos: https://textual.textualize.io/api/work/
- [ ] Cancelamento / teardown garante zero workers ativos no fim do teste.

## Reactivity
- [ ] State UI é `reactive` quando dirige renderização: https://textual.textualize.io/guide/reactivity/
- [ ] Watchers leves; sem loop/IO; sem “refresh storm”.

## Testing
- [ ] Testes TUI usam `run_test()` + `Pilot` (sem internals): https://textual.textualize.io/guide/testing/#testing-apps
- [ ] Uso de `pilot.pause()` quando necessário: https://textual.textualize.io/guide/testing/#pausing-the-pilot

## Performance & memória
- [ ] Listas longas têm estratégia para limitar crescimento de widgets (janela, descarte, compactação).
- [ ] Widgets caros usam `Lazy(...)`: https://textual.textualize.io/api/lazy/

---

# 🧩 PROBLEMAS CONHECIDOS — BASE OFICIAL (FASE 1)

## A) DeprecationWarning do pytest-asyncio: `event_loop fixture has been redefined`

**Base oficial (warning do plugin):** o próprio warning recomenda **não** substituir `event_loop` e aponta alternativas (`loop_scope` e `event_loop_policy`).
**Source (exemplo de warning reproduzido):** https://bugs.debian.org/1099275
**Source (changelog 0.24.0):** https://pytest-asyncio.readthedocs.io/en/v0.24.0/reference/changelog.html (seção “0.22.0”)

**Padrão recomendado (direção):**
- Remover fixtures customizadas de `event_loop` (salvo caso muito específico).
- Usar marcação/parametrização oficial (ex.: scope via mark) e/ou `event_loop_policy`.

> **Nota:** o repo já configura `asyncio_mode=auto` e `asyncio_default_fixture_loop_scope=function` em `pytest.ini`.

## B) `ValueError: Token ... was created in a different Context` (ContextVar)

**Semântica oficial do Python:** `ContextVar.reset(token)` só aceita tokens criados no **mesmo** `Context`.
**Source:** https://docs.python.org/3/library/contextvars.html

**Relação com Textual:** o Textual mantém `active_message_pump` como `ContextVar` (ligado ao message pump do app).
**Source (API):** https://textual.textualize.io/api/message_pump/

**Implicação prática (para Fase 2):**
- Qualquer teardown que tente “resetar” token criado em outro contexto (ex.: tasks criadas fora do lifecycle do app / loop trocado / fixture de loop customizada) pode disparar esse erro.

---

# 🧭 DOC DRIFT / LINKS DO PROMPT QUE NÃO BATEM (registrado na Fase 1)

- `https://textual.textualize.io/how-to/test-your-app/` → não acessível via crawler; usar `guide/testing/`.
- `https://textual.textualize.io/blog/2023/09/18/things-i-wish-id-known/` → não acessível via crawler; opcional.
- `guide/reactivity/#performance` e `guide/widgets/#lazy-loading` → âncoras não encontradas; usar:
  - Reactivity: https://textual.textualize.io/guide/reactivity/
  - Lazy: https://textual.textualize.io/api/lazy/
  - Workers performance: https://textual.textualize.io/guide/workers/

---

# ➡️ PRÓXIMO PASSO (FASE 2)

Auditar (contra o checklist acima) os arquivos TUI e testes E2E, com foco em:
- Lifecycle / message pump / workers em teardown (para curar o ContextVar ValueError).
- Fixtures e configuração pytest-asyncio (para eliminar o DeprecationWarning).
