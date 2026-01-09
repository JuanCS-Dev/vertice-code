# 🚀 VERTICE-CODE ROADMAP PARA LANÇAMENTO PÚBLICO (MASTER TECHNICAL PLAN)

**Data:** Janeiro 2026
**Versão:** 2.1.0 (Constitution Compliant)
**Status:** EXECUÇÃO IMEDIATA
**Contexto:** Este documento serve como a **Fonte Única da Verdade (SSOT)** para a implementação offline. Contém especificações técnicas, snippets de configuração e checklists de compliance baseados nas tecnologias de 2026 e estritamente alinhados à **CODE_CONSTITUTION.md**.

---

## 📚 **ÍNDICE TÉCNICO**

1.  [Fase 1: Next-Gen Identity (Auth 3.0)](#fase-1-next-gen-identity-auth-30)
2.  [Fase 2: User & Agent Management](#fase-2-user--agent-management)
3.  [Fase 3: Global Commerce (Merchant of Record)](#fase-3-global-commerce-merchant-of-record)
4.  [Fase 4: Infraestrutura Híbrida (Wasm/K8s)](#fase-4-infraestrutura-híbrida-wasmk8s)
5.  [Fase 5: AI Safety & ISO 42001](#fase-5-ai-safety--iso-42001)
6.  [Fase 6: Evaluation-Driven CI/CD](#fase-6-evaluation-driven-cicd)

---

## 🔥 **FASE 1: NEXT-GEN IDENTITY (Auth 3.0)**

**Objetivo:** Implementar autenticação "Phishing-Resistant" por padrão para humanos e máquinas.

### **1.1 Human Authentication (Clerk.com)**
*Padrão 2026: Senhas são consideradas "Legacy". O fluxo primário deve ser Passkeys.*

**Especificação de Implementação:**
1.  **Configuração do Clerk (Dashboard):**
    *   Habilitar **Passkeys** como método primário.
    *   Configurar **"Passwordless"** mode (Email Magic Links como fallback).
    *   Desabilitar criação de senhas para novos usuários.
    *   **Session Management:** Configurar *Continuous Access Evaluation (CAE)* para revogação de tokens em tempo real em caso de risco detectado.

2.  **Frontend (React/Vite) - Componente `SignIn`:**
    *Compliance: Código claro, sem lógica implícita.*

    ```tsx
    // src/components/auth/SignIn.tsx
    import { signInWithEmailAndPassword, signInWithPasskey } from '@/lib/auth';
    import React, { useState } from "react";

    /**
     * Componente de Login principal.
     * Força o uso de Passkeys/Passwordless conforme Diretriz de Segurança 2026.
     */
    export default function SignInPage(): React.JSX.Element {
      const [email, setEmail] = useState('');
      const [password, setPassword] = useState('');

      const handleEmailSignIn = async () => {
        try {
          await signInWithEmailAndPassword(email, password);
        } catch (error) {
          console.error('Sign in failed:', error);
        }
      };

      const handlePasskeySignIn = async () => {
        try {
          await signInWithPasskey();
        } catch (error) {
          console.error('Passkey sign in failed:', error);
        }
      };

      return (
        <div className="auth-wrapper">
          <button onClick={handlePasskeySignIn}>Sign in with Passkey</button>
          <form onSubmit={handleEmailSignIn}>
              elements: {
                footerAction: { display: "none" } // Remove opção de senha (Legacy)
              }
            }}
          />
        </div>
      );
    }
    ```

3.  **Verificação de Dispositivo (Device Trust):**
    *   Utilizar headers do Clerk para validar se o dispositivo é "conhecido" antes de permitir ações sensíveis (ex: deletar workspace).

### **1.2 Agentic Identity (Machine-to-Machine)**
*Agentes autônomos precisam de identidade própria para acessar APIs externas e gastar créditos.*

**Arquitetura "Agent Wallet":**
1.  **Modelo de Dados (PostgreSQL):**
    *Compliance: Nomes explícitos (snake_case), tipos seguros.*

    ```sql
    CREATE TABLE agent_identities (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        workspace_id UUID REFERENCES workspaces(id) NOT NULL,
        agent_name VARCHAR(255) NOT NULL,
        api_key_hash VARCHAR(255) NOT NULL, -- Armazenamento seguro SHA-256
        scopes JSONB DEFAULT '["read:memory", "write:logs"]'::jsonb,
        daily_budget_cents INTEGER DEFAULT 1000 CHECK (daily_budget_cents > 0), -- Circuit breaker financeiro
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
    );
    ```
2.  **Autenticação (FastAPI Middleware):**
    *   Validar header `X-Agent-Key`.
    *   Verificar se o agente não excedeu o `daily_budget_cents`.
    *   **Rotação de Chaves:** Implementar rotação automática de chaves a cada 30 dias para agentes de longa duração.

---

## 🔥 **FASE 2: USER & AGENT MANAGEMENT**

**Objetivo:** Isolamento total de dados entre tenants (Multi-tenancy RAG) e compliance GDPR.

### **2.1 RAG Multi-tenancy (Vector Database)**
*Padrão 2026: Metadata Filtering Obrigatório.*

**Estratégia de Isolamento:**
*   **NÃO** criar uma collection por cliente (ineficiente para milhares de usuários).
*   **SIM** usar "Partitioning" ou "Metadata Filtering" estrito.

**Exemplo de Implementação (Qdrant/Pinecone):**
*Compliance: Type hints completos, Docstrings Google-style.*

```python
from typing import List, Dict, Any
from uuid import uuid4
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

def upsert_knowledge(
    client: QdrantClient,
    user_id: str,
    text_content: str,
    embedding: List[float]
) -> None:
    """
    Insere conhecimento vetorial com isolamento de tenant obrigatório.

    Args:
        client: Cliente Qdrant autenticado.
        user_id: ID do workspace/usuário para isolamento (Tenant ID).
        text_content: Texto original a ser armazenado.
        embedding: Vetor gerado pelo modelo de embedding.

    Raises:
        ValueError: Se o user_id for inválido ou vazio.
    """
    if not user_id:
        raise ValueError("user_id (tenant) is mandatory for data isolation.")

    client.upsert(
        collection_name="vertice_knowledge",
        points=[
            PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload={
                    "workspace_id": user_id, # <--- MANDATORY TENANT TAG
                    "content": text_content,
                    "access_level": "admin"
                }
            )
        ]
    )

def search_knowledge(
    client: QdrantClient,
    user_id: str,
    query_vector: List[float]
) -> List[Dict[str, Any]]:
    """
    Busca conhecimento respeitando o isolamento do tenant.
    """
    results = client.search(
        collection_name="vertice_knowledge",
        query_vector=query_vector,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="workspace_id",
                    match=MatchValue(value=user_id) # <--- ENFORCED FILTER
                )
            ]
        )
    )
    return [hit.payload for hit in results if hit.payload]
```

### **2.2 GDPR & "Crypto-Shredding"**
*Como deletar dados de um usuário em backups imutáveis? Deletando a chave de criptografia.*

**Fluxo Técnico:**
1.  Cada `workspace` possui uma `data_encryption_key` (DEK) única, criptografada por uma `master_key` (KEK).
2.  Dados sensíveis (prompts, logs) são criptografados com a DEK do workspace antes de ir para o banco (Application-Level Encryption).
3.  **Right to be Forgotten:** Para "apagar" o usuário, basta deletar a DEK do banco. Os dados restantes tornam-se lixo criptográfico irrecuperável, satisfazendo GDPR/LGPD sem precisar reescrever backups de fita.

---

## 🔥 **FASE 3: GLOBAL COMMERCE (Merchant of Record)**

**Objetivo:** Vender em 100+ países sem abrir filiais locais.
**Solução:** **Stripe Managed Payments** (Preview 2025/2026).

### **3.1 Integração Usage-Based Billing (Metered)**
*Cobrança por tokens de LLM e tempo de computação.*

**Workflow de Implementação:**
1.  **Stripe Dashboard:**
    *   Criar Produto: "Vertice Compute Credits".
    *   Preço: "Metered usage", "Aggregate usage: Sum".

2.  **Código de Report (Python Worker):**
    *Compliance: Tratamento de erros explícito, Logging estruturado, Type Hints.*

    ```python
    import stripe
    import redis
    import time
    import logging
    from typing import List, Optional

    logger = logging.getLogger(__name__)

    # Configuração de Retry/Circuit Breaker implícita na arquitetura
    
    def report_usage_to_stripe(active_users: List[str], redis_client: redis.Redis) -> None:
        """
        Reporta uso agregado ao Stripe para evitar Rate Limits.
        Executado via Celery/Bull a cada 15 min.

        Args:
            active_users: Lista de IDs de usuários ativos.
            redis_client: Conexão Redis para buscar métricas.
        """
        for user_id in active_users:
            # Pega consumo acumulado e reseta atomicamente (GETDEL)
            token_key = f"usage:{user_id}:tokens"
            tokens_str: Optional[str] = redis_client.getdel(token_key)
            
            if not tokens_str:
                continue

            try:
                subscription_item_id = _get_sub_item_id(user_id) # Helper function
                
                stripe.SubscriptionItem.create_usage_record(
                    subscription_item_id=subscription_item_id,
                    quantity=int(tokens_str),
                    timestamp=int(time.time()),
                    action="increment"
                )
                logger.info(f"Reported {tokens_str} tokens for user {user_id}")

            except stripe.error.StripeError as e:
                # Falha ruidosa para monitoramento
                logger.error(f"Stripe Billing Error for user {user_id}: {e}")
                # Re-adiciona os tokens ao Redis para não perder cobrança
                redis_client.incrby(token_key, int(tokens_str))
                raise # Permite que o worker do Celery faça o retry
    
    def _get_sub_item_id(user_id: str) -> str:
        """Helper para recuperar ID da subscription no banco."""
        # Implementação simulada
        return "si_12345"
    ```

3.  **Webhooks Críticos:**
    *   `invoice.created`: Verificar se o saldo do usuário cobre a fatura.
    *   `customer.subscription.deleted`: Bloquear acesso imediato dos agentes.

---

## 🔥 **FASE 4: INFRAESTRUTURA HÍBRIDA (Wasm/K8s)**

**Objetivo:** Rodar código Python de agentes de forma segura e barata (Cold-start < 10ms).
**Tecnologia:** **Spin Framework** (Serverless Wasm).

### **4.1 Configuração do Componente Wasm (Python)**
*Permite que o agente execute scripts Python gerados dinamicamente em uma sandbox segura, sem acesso ao host.*

**Arquivo `spin.toml`:**
```toml
spin_manifest_version = 2

[application]
name = "vertice-agent-executor"
version = "1.0.0"
authors = ["Vertice AI"]

[[component]]
id = "python-agent"
source = "agent.wasm" # Compilado via componentize-py
allowed_outbound_hosts = ["https://api.openai.com", "https://google.com"] # Allowlist estrita (Security First)
files = [{ source = "Lib", destination = "/Lib" }]
[component.build]
command = "componentize-py -w spin-http componentize app -o agent.wasm"
```

**Código do Agente (`app.py`):**
*Compliance: Spin SDK types.*

```python
from spin_sdk import http
from spin_sdk.http import Request, Response

class IncomingHandler(http.IncomingHandler):
    def handle_request(self, request: Request) -> Response:
        """
        Executa a lógica do agente dentro da Sandbox Wasm.
        
        Args:
            request: Objeto de requisição HTTP do Spin.
            
        Returns:
            Response: Resposta HTTP processada.
        """
        # Isolamento total de memória garantido pelo Runtime Wasm
        # TODO(implementação): Adicionar lógica de inferência aqui
        # Nota: Placeholder permitido neste documento de planejamento, proibido no código final.
        
        return Response(
            200,
            {"content-type": "text/plain"},
            bytes("Agent Active and Secure", "utf-8")
        )
```

### **4.2 Orquestração**
*   **K8s (Control Plane):** Gerencia API, Banco de Dados e filas.
*   **SpinKube:** Operador Kubernetes para rodar os Wasm apps nos mesmos nós, mas com densidade muito maior que Docker.

---

## 🔥 **FASE 5: AI SAFETY & ISO 42001**

**Objetivo:** Compliance técnico para certificação ISO 42001 (AI Management System).

### **5.1 Checklist Técnico ISO 42001 (Anexo A)**

| Controle ISO | Implementação Técnica no Vertice-Code |
| :--- | :--- |
| **A.2 Bias Mitigation** | Pipeline de CI que roda prompts de teste contra grupos demográficos protegidos (Fairness Evals). |
| **A.4 Audit Trails** | Tabela `audit_logs` imutável registrando: Input Prompt, Output Gerado, Modelo Usado, Latência, Custo. |
| **A.6 Data Governance** | Tagging de dados de treino/RAG com origem e licença. Bloqueio de ingestão de dados não licenciados. |
| **A.7 Security** | Proteção contra **Prompt Injection** (via Guardrails) e **Model Theft**. |
| **A.10 User Info** | Disclaimer automático na UI: "AI generated content can be inaccurate". Link para o "System Card". |

### **5.2 Guardrails de Entrada/Saída (Lakera / Custom)**
*Bloquear ataques antes que cheguem ao LLM.*

**Exemplo de Integração (Python):**
*Compliance: Tratamento de exceção de segurança explícito.*

```python
import requests
import os
from typing import Dict, Any

class SecurityException(Exception):
    """Raised when a security guardrail is triggered."""
    pass

def check_prompt_safety(prompt: str) -> None:
    """
    Verifica se o prompt contém injeções ou conteúdo malicioso usando Lakera Guard.
    
    Args:
        prompt: O texto do usuário.
    
    Raises:
        SecurityException: Se o prompt for sinalizado como inseguro.
        RuntimeError: Se a API de segurança falhar.
    """
    api_key = os.getenv("LAKERA_GUARD_API_KEY")
    if not api_key:
        raise RuntimeError("Missing LAKERA_GUARD_API_KEY configuration.")

    url = "https://api.lakera.ai/v2/guard"
    
    try:
        response = requests.post(
            url, 
            json={"messages": [{"role": "user", "content": prompt}]},
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=2.0 # Fail fast
        )
        response.raise_for_status()
        data: Dict[str, Any] = response.json()
        
        if data.get("flagged", False):
            raise SecurityException(f"Prompt Injection Detected: {data.get('category')}")
            
    except requests.RequestException as e:
        # Fail safe: Se o guardrail cair, bloqueamos o acesso por precaução?
        # Ou permitimos com log? Política: Bloquear em alta segurança.
        raise RuntimeError(f"Security Check Failed: {e}")
```

---

## 🔥 **FASE 6: EVALUATION-DRIVEN CI/CD**

**Objetivo:** Deploy seguro. Se a IA ficar "mais burra", o deploy é cancelado.

### **6.1 Pipeline GitHub Actions**

```yaml
name: AI Evaluation & Deploy

on: [push]

jobs:
  evaluate-model:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run Evals (Promptfoo/DeepEval)
        run: |
          # Executa 500 prompts de teste (Golden Dataset)
          # Compara performance com a versão anterior (Baseline)
          # Quality Gate: 99% rule apply here too
          npx promptfoo eval -c promptfooconfig.yaml --output report.json
          
      - name: Check Quality Gate
        run: |
          # Falha se a acurácia cair mais que 2%
          python scripts/check_quality_gate.py report.json --threshold 0.95

  deploy:
    needs: evaluate-model
    if: success()
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: ./deploy.sh
```

### **6.2 Monitoramento em Produção (Observability)**
*   Integrar SDK do **LangSmith** ou **Arize Phoenix** para rastrear traces de execução.
*   **Métrica Chave:** "% de Feedback Negativo (Thumbs down)" dos usuários. Alerta no Slack se > 5% em 1h.

---

**Nota Final:** Este documento deve ser seguido rigorosamente. Qualquer desvio arquitetural requer aprovação do Arquiteto-Chefe e atualização deste roadmap. O código gerado a partir deste plano DEVE passar pelos validadores automáticos do Code Constitution.
