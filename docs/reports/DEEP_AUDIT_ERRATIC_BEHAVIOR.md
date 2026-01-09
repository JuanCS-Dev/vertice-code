# RELATÓRIO DE AUDITORIA PROFUNDA: COMPORTAMENTO ERRÁTICO DO VÉRTICE-CODE
**Data:** 08/01/2026
**Status:** CRÍTICO
**Auditor:** Gemini (Vertice-MAXIMUS)

## 1. O Problema (Sintomas Observados)
Com base nas evidências visuais (`print01.png`, `print02.png`, `print03.png`), o sistema apresenta o seguinte comportamento:
1.  **Falha na Execução de Ferramentas:** O modelo tenta usar ferramentas (ex: `bash_command`, `firebase projects:list`) mas falha em invocar a API nativa.
2.  **Vazamento de Abstração (Hallucination):** O modelo imprime "alucinações" de chamadas de ferramenta em texto plano (ex: `call:bash_command command: 'ls -l'`), misturando monólogo interno com a resposta do usuário.
3.  **Loop de Raciocínio (ReAct Loop):** O modelo entra em loops descrevendo o que vai fazer ("1 Tool Selection...", "2 Command Construction...") sem nunca executar a ação.
4.  **Diagnóstico Visual Crítico:** No `print03.png`, a saída de debug mostra explicitamente: `tools: []`.

## 2. A Causa Raiz (Análise de Código)
A auditoria do código revelou uma **falha lógica crítica** na delegação de chamadas entre o `GeminiClient` (Front-end client) e o `VerticeClient` (Unified Router).

### O Caminho da Falha:
1.  **Origem:** `VerticeBridge.chat` chama `self.llm.stream(..., tools=self.tools.get_schemas_for_llm())`. As ferramentas SÃO passadas corretamente aqui.
2.  **Ponto de Ruptura (`vertice_tui/core/llm_client.py`):**
    O método `GeminiClient.stream` tem uma lógica de roteamento preferencial (Route 1) para o `_vertice_client` (que gerencia múltiplos provedores).
    ```python
    # Route 1: Use VerticeClient if available
    if self._vertice_client:
        async for chunk in self._stream_via_client(prompt, system_prompt, context):
            yield chunk
        return
    ```
    Note que a variável `tools` (recebida nos argumentos de `stream`) **NÃO** é passada para `_stream_via_client`.

3.  **O Abismo (`GeminiClient._stream_via_client`):**
    ```python
    async def _stream_via_client(self, prompt, system_prompt, context):
        # ... constrói mensagens ...
        async for chunk in self._vertice_client.stream_chat(
            messages,
            system_prompt=system_prompt,
            # ERRO FATAL: tools e **kwargs são ignorados aqui!
        ):
            yield chunk
    ```
    O método chama o cliente unificado mas **descarta silenciosamente** a lista de ferramentas.

4.  **Consequência:**
    *   O `VerticeClient` recebe a requisição sem ferramentas.
    *   O Provedor (Vertex AI, Groq, etc.) é inicializado sem definições de função.
    *   O Prompt do Sistema (System Prompt) diz ao modelo: "Você tem acesso a ferramentas...".
    *   **Resultado:** O modelo, instruído a usar ferramentas mas privado da capacidade técnica de fazê-lo via API, tenta "simular" o uso escrevendo o texto que ele acha que o sistema espera (`call:bash_command...`), resultando no comportamento errático e texto vazado.

## 3. Fatores Contribuintes
1.  **Complexidade de Camadas:** A arquitetura possui múltiplas camadas de abstração (`Bridge` -> `GeminiClient` -> `VerticeClient` -> `Provider`). A informação se perdeu na transição entre a camada de Cliente de UI e o Roteador Unificado.
2.  **Validação Silenciosa:** O sistema não alerta se `tools` são passados mas ignorados.
3.  **Fallback Parcial:** A rota de fallback (`_stream_via_gemini`) implementa o uso de ferramentas corretamente, mas como a Rota 1 (`_vertice_client`) tem prioridade e "funciona" (retorna texto), o fallback nunca é acionado.

## 4. Plano de Correção (Recomendado)
Para corrigir isso, é necessário alterar `vertice_tui/core/llm_client.py`:

1.  Atualizar a assinatura de `_stream_via_client` para aceitar `tools` e `**kwargs`.
2.  Passar `tools` (e outros `kwargs`) na chamada para `self._vertice_client.stream_chat`.
3.  Garantir que `VerticeClient.stream_chat` propague esses argumentos para os provedores individuais.

**Ação Imediata:** Este relatório documenta o problema. Nenhuma correção foi aplicada conforme instrução.
