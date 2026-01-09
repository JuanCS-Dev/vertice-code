# RELATÓRIO DE AUDITORIA PROFUNDA: INCONSISTÊNCIAS DE TOOLS NO SISTEMA
**Data:** 08/01/2026
**Auditor:** Sistema de Auditoria Automatizada
**Status:** CRÍTICO - MÚLTIPLAS INCONSISTÊNCIAS ENCONTRADAS

## 1. VISÃO GERAL DAS INCONSISTÊNCIAS

Durante auditoria profunda do sistema, foram identificadas **múltiplas inconsistências** na implementação de `tools` (function calling) através das diferentes camadas e provedores.

## 2. INCONSISTÊNCIA CRÍTICA: ASSINATURAS DE `stream_chat`

### Provedores que SUPORTAM tools customizados:
- ✅ `vertex_ai.py`: `tools: Optional[List[Any]] = None`
- ✅ `anthropic_vertex.py`: `tools: Optional[List[Any]] = None`
- ✅ `vertice_router.py`: `tools: Optional[List[Any]] = None`

### Provedores que NÃO SUPORTAM tools customizados:
- ❌ `gemini.py`: Sem parâmetro `tools`, usa hardcoded `["code_execution", "google_search_retrieval"]`
- ❌ `azure_openai.py`: Sem parâmetro `tools`
- ❌ `nebius.py`: Sem parâmetro `tools`
- ❌ `ollama.py`: Sem parâmetro `tools`
- ❌ `base.py`: Usa `**kwargs` mas não processa `tools`

### Impacto:
Quando `VerticeClient` seleciona um provedor que não suporta tools, elas são **ignoradas silenciosamente**, causando comportamento errático idêntico ao relatado anteriormente.

## 3. INCONSISTÊNCIA SECUNDÁRIA: ROTAS ALTERNATIVAS

### vertice_cli/core/llm.py
- ❌ Método `stream_chat` não aceita parâmetro `tools`
- ❌ Agentes CLI não podem usar function calling
- ✅ Usa VerticeClient internamente, mas descarta tools na interface pública

## 4. PROPAGAÇÃO DE **kwargs

### Problema Identificado:
`VerticeClient.stream_chat` propaga `**kwargs` para provedores, mas provedores sem parâmetro `tools` na assinatura ignoram o parâmetro silenciosamente.

### Exemplo:
```python
# VerticeClient faz:
provider.stream_chat(messages, max_tokens=..., temperature=..., tools=tools, **kwargs)

# Mas se provider declarar:
async def stream_chat(self, messages, max_tokens, temperature, **kwargs):
    # tools é ignorado!
```

## 5. CAMADAS DE ABSTRAÇÃO

### Fluxo Atual:
1. `Bridge` → configura tools no `LLMClient` via `set_tools()`
2. `StreamingManager` → passa tools para `client.stream(..., tools=...)`
3. `GeminiClient.stream` → aceita tools
4. `GeminiClient._stream_via_client` → (CORRIGIDO) passa tools para `VerticeClient`
5. `VerticeClient.stream_chat` → passa `tools=tools` via **kwargs
6. `Provider.stream_chat` → **INCONSISTENTE** - alguns aceitam, outros ignoram

## 6. RECOMENDAÇÕES PARA PADRONIZAÇÃO

### A. Padronizar Assinaturas de `stream_chat`
Todos os provedores devem declarar:
```python
async def stream_chat(
    self,
    messages: List[Dict[str, str]],
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    tools: Optional[List[Any]] = None,
    **kwargs
) -> AsyncGenerator[str, None]:
```

### B. Implementar Suporte a Tools nos Provedores Faltantes
- `gemini.py`: Aceitar `tools` e mesclar com hardcoded
- `azure_openai.py`: Implementar function calling
- `nebius.py`: Verificar se suporta e implementar
- `ollama.py`: Verificar se suporta e implementar

### C. Validação em Runtime
Adicionar em `VerticeClient`:
```python
if tools and not provider._supports_tools():
    logger.warning(f"Provider {name} ignoring {len(tools)} tools")
```

### D. Padronizar vertice_cli
Atualizar `vertice_cli/core/llm.py` para aceitar `tools`.

## 7. CORREÇÕES IMEDIATAS APLICADAS

- ✅ Corrigido `GeminiClient._stream_via_client` para aceitar e passar `tools`
- ✅ Adicionado logging para rastreamento

## 8. RISCO REMANESCENTE

Mesmo com correção, se `VerticeClient` escolher um provedor sem suporte a tools, elas serão perdidas. Sistema deve priorizar provedores com suporte a tools quando tools são solicitadas.

## 9. CONCLUSÃO

O sistema tem **inconsistências estruturais** que podem causar perda silenciosa de parâmetros críticos. Recomenda-se padronização completa das interfaces e implementação de validação em runtime para prevenir regressões.</content>
<parameter name="filePath">DEEP_AUDIT_TOOLS_INCONSISTENCIES.md