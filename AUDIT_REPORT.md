# Relatório de Auditoria Técnica: Vertice-Code
**Data:** 2026-01-04
**Auditor:** Jules (AI Senior Software Engineer)
**Status:** 🚨 CRÍTICO

## 1. Resumo Executivo

O repositório `vertice-code` sofre de uma crise de identidade severa e dívida técnica acumulada ("bit rot"). O projeto tenta ser muitas coisas ao mesmo tempo (CLI, TUI, WebApp, Framework de Agentes) sem uma arquitetura unificada.

A falha mais crítica é o **"Split Brain" Arquitetural**: existem múltiplas definições de "Core", múltiplas implementações de backends web e uma mistura perigosa de código legado com código moderno que torna o sistema instável e impossível de testar confiavelmente.

---

## 2. Pontos Fracos Críticos (A Verdade Brutal)

### 2.1. Arquitetura "Split Brain" (Cérebro Dividido)
O código fonte sofre de uma duplicidade esquizofrênica.
*   **Problema:** Existem dois "núcleos" competindo: `src/core/` (Legado?) e `src/vertice_core/` (Moderno?).
*   **Evidência:** O `vertice_cli` importa de **ambos**.
    *   `from core.resilience import ...`
    *   `from vertice_core.protocols import ...`
*   **Impacto:** Risco altíssimo de bugs de estado, onde uma parte do sistema usa uma implementação de `resilience` e outra parte usa outra. Isso torna o debugging um pesadelo.

### 2.2. O Backend de Schrödinger (WebApp)
O diretório `vertice-chat-webapp/backend/` é uma alucinação técnica.
*   **Problema:** Ele contém arquivos para **dois** backends diferentes misturados no mesmo diretório.
    *   **Backend Python:** `requirements.txt` (FastAPI, SQLAlchemy), `Dockerfile` (usa Python), `app/main.py`.
    *   **Backend Node:** `package.json` (Express, VertexAI), `src/index.ts`.
*   **Impacto:** Um desenvolvedor novo não saberá qual backend é o "real". O Docker builda o Python, mas o código Node está lá, confundindo a IDE e a manutenção.

### 2.3. Colapso da Suite de Testes
A suite de testes está em estado de necrose.
*   **Problema:** O comando `pytest --collect-only` falhou com **91 erros**.
*   **Evidência:**
    *   Dependências fantasmas: O código de teste importa `prompt_toolkit`, `bs4`, `ddgs`, `yaml`, `hypothesis`, `async_lru`, `respx` — mas nenhuma delas está no `requirements.txt` principal ou devidamente instalada.
    *   Erros de Importação: Devido à arquitetura "Split Brain", os testes tentam importar módulos que não existem no caminho esperado.
*   **Impacto:** CI/CD inútil. Qualquer refatoração é um tiro no escuro.

### 2.4. Código Morto e Zumbi
O repositório é um cemitério de arquivos.
*   **Problema:** Arquivos de exemplo e experimentos estão misturados com código de produção.
*   **Evidências:**
    *   `src/app.py`: Um app Flask "Hello World" com uma função `failing_function` (divisão por zero) largado dentro da pasta de bibliotecas `src/`.
    *   `src/providers/`: Um diretório inteiro que parece legado (conflita com `vertice_cli/core/providers`), mas ainda contém chaves de API e lógica.
    *   `broken_loop.py` na raiz: O nome já diz tudo.

---

## 3. Análise de Componentes

### 3.1. CLI & TUI (`vertice_cli`, `vertice_tui`)
*   **Pontos Fortes:** A TUI usa `Textual`, que é moderno. A estrutura visual parece boa.
*   **Pontos Fracos:**
    *   **Async/Sync Hacking:** O `main.py` usa um wrapper `run_async` para tentar forçar código async a rodar dentro de loops existentes ou threads. Isso indica que a arquitetura não foi pensada como "Async-First", mas sim adaptada na força bruta.
    *   **Late Imports:** O código abusa de importações dentro de funções (`def ...: from ... import ...`). Isso melhora o tempo de boot, mas esconde erros de dependência (como visto nos testes) até o momento exato da execução.

### 3.2. Infraestrutura & Dependências
*   **Pontos Fracos:**
    *   `requirements.txt` incompleto. Faltam dezenas de bibliotecas usadas nos imports.
    *   Configuração do `pyproject.toml` exclui explicitamente `vertice_core.core`, admitindo a confusão estrutural.

---

## 4. Recomendações (O Plano de Recuperação)

Para salvar este projeto, é necessário uma intervenção cirúrgica imediata. Não adianta adicionar funcionalidades agora.

1.  **Unificação do Core (Prioridade 0):**
    *   Decidir entre `src/core` e `src/vertice_core`. Mover tudo para **um** lugar (sugiro `vertice_core`).
    *   Eliminar o diretório perdedor.
    *   Corrigir todos os imports no CLI e TUI.

2.  **Decisão do Backend Web:**
    *   Escolher Python (FastAPI) OU Node (Express). Não os dois.
    *   Deletar os arquivos da linguagem não escolhida.

3.  **Limpeza de Primavera:**
    *   Deletar `src/app.py`.
    *   Deletar `src/providers` (se `vertice_cli/core/providers` for o correto).
    *   Adicionar todas as dependências faltantes ao `requirements.txt`.

4.  **Ressuscitar os Testes:**
    *   Fazer o `pytest --collect-only` passar sem erros (mesmo que os testes falhem, a coleta deve funcionar).

**Conclusão:** O Vertice-Code tem potencial (bons frameworks escolhidos), mas está sufocado pela própria desorganização. Sem essa limpeza, o projeto irá falhar silenciosamente em produção.
