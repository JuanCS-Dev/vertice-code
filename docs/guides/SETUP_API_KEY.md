# 🔑 Configurar GEMINI_API_KEY no Hugging Face Space

## Passo a Passo (MANUAL - você precisa fazer)

### 1. Acesse as Configurações do Space
1. Vá para: https://huggingface.co/spaces/MCP-1st-Birthday/prometheus-mcp
2. Clique em **Settings** (⚙️ no canto superior direito)

### 2. Adicione o Secret
1. No menu lateral, clique em **Repository secrets**
2. Clique em **+ New secret**
3. Preencha:
   - **Name**: `GEMINI_API_KEY`
   - **Value**: Cole sua chave da API do Gemini (começa com `AIza...`)
4. Clique em **Add secret**

### 3. Reinicie o Space
O Space vai reiniciar automaticamente e a chave estará disponível via `os.getenv("GEMINI_API_KEY")`

---

## ✅ Como Saber se Funcionou
Após adicionar o secret e o Space reiniciar:
- O status deve mudar de "not-initialized" para "PROMETHEUS (gemini-default)"
- O erro "Failed to initialize Gemini client" deve desaparecer

---

## 🔄 Alternativa: Modo Demo (Sem API)
Se não quiser usar sua chave agora, eu posso configurar um modo demo que funciona sem API.
