# 🧠 **ROADMAP EXECUTÁVEL: VERTICE CHAT WEB APP**
## 📘 Documentação Técnica Completa para Implementação Autônoma

**Versão:** 2.0 (Janeiro 2026)
**Baseado em:** Anthropic Claude Code, OpenAI Realtime API, Google Gemini Live API, MCP Spec Nov 2025

**📊 STATUS DE IMPLEMENTAÇÃO:**
- ✅ **FASE 0**: Environment Setup (100%)
- ✅ **FASE 1**: Core Infrastructure (100%)
- ✅ **FASE 2**: Frontend Architecture (100%)
- 🔄 **FASE 3**: User Experience & Agentic Coding (25%) - **Artifacts System Complete**
- ⏳ **FASE 4**: Authentication & Security (0%)
- ⏳ **FASE 5**: Performance & Deployment (0%)
- ⏳ **FASE 6**: Advanced Features (0%)

---

## 🎯 **VISÃO GERAL**

Criar um web chat app similar ao **Claude Code Web (2026)** com:
- Interface elegante inspirada em Artifacts UI (Anthropic)
- Streaming de baixa latência (SSE + WebRTC)
- Multi-agent colaborativo com MCP integration
- Teleport para desenvolvimento local (Web ↔ CLI)
- Sandboxing seguro (gVisor approach)
- **Prompt caching** para otimização de custos (90% redução)
- Observabilidade desde o MVP

**Referências:**
- Anthropic Claude Code: https://www.anthropic.com/engineering/claude-code-best-practices
- Claude Sandboxing: https://www.anthropic.com/engineering/claude-code-sandboxing
- OpenAI Realtime API: https://platform.openai.com/docs/models/gpt-realtime
- Gemini Live API: https://ai.google.dev/gemini-api/docs/live
- MCP Specification: https://modelcontextprotocol.io/specification/2025-11-25

---

## 📐 **ARQUITETURA GERAL**

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐    │
│  │  Next.js 15  │  │  React 19    │  │  Tailwind CSS v4  │    │
│  │  (App Router)│  │  (RSC + SC)  │  │  (Rust Engine)    │    │
│  └──────────────┘  └──────────────┘  └───────────────────┘    │
│         ↓ SSE/WebRTC/WebSocket                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API LAYER                          │
│  ┌──────────────────────┐  ┌───────────────────────────┐       │
│  │   FastAPI + Uvicorn  │  │  Server Actions (Next.js) │       │
│  │   (Python 3.11+)     │  │  (Simple mutations)       │       │
│  └──────────────────────┘  └───────────────────────────┘       │
│         ↓ MCP Client Protocol (JSON-RPC 2.0)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LLM ORCHESTRATION LAYER                      │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ Prompt Cache    │  │ Smart Router │  │  Cost Tracker    │  │
│  │ (90% savings)   │  │ (Intent→LLM) │  │  (Per-user)      │  │
│  └─────────────────┘  └──────────────┘  └──────────────────┘  │
│         ↓                     ↓                    ↓            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  LLM Providers: Claude, GPT-4o, Gemini 2.5, Groq       │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MCP TOOLS LAYER                              │
│  ┌───────────────┐  ┌───────────────┐  ┌──────────────────┐   │
│  │ Filesystem    │  │  Git Tools    │  │  Exec Sandbox    │   │
│  │ (Read/Write)  │  │  (GitHub API) │  │  (gVisor)        │   │
│  └───────────────┘  └───────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   PERSISTENCE LAYER                             │
│  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐    │
│  │ PostgreSQL   │  │  Redis Cache  │  │  S3/R2 Storage   │    │
│  │ (Neon)       │  │  (Upstash)    │  │  (Artifacts)     │    │
│  └──────────────┘  └───────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   OBSERVABILITY LAYER (Day 1!)                  │
│  ┌────────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ OpenTelemetry  │  │   Sentry     │  │  Vercel Analytics │  │
│  │ (Traces+Logs)  │  │   (Errors)   │  │  (Performance)    │  │
│  └────────────────┘  └──────────────┘  └───────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 **FASE 0: PREREQUISITES & SETUP**

### **0.1 Environment Setup** ✅ **COMPLETADO**

**Node.js & Package Manager:**
```bash
# Install Node.js 20+ (LTS)
# Official: https://nodejs.org/en/download
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify versions
node -v  # Should be >= 20.0.0
npm -v   # Should be >= 10.0.0

# Install pnpm (faster than npm, recommended for Next.js)
# Docs: https://pnpm.io/installation
npm install -g pnpm@8.15.0
```

**Python Environment:**
```bash
# Python 3.11+ required for FastAPI + modern async
# Official: https://www.python.org/downloads/
sudo apt install python3.11 python3.11-venv python3-pip

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

**Repository Structure:**
```
vertice-chat-webapp/
├── frontend/              # Next.js 15 application
│   ├── app/              # App Router (Next.js 15)
│   ├── components/       # React components
│   ├── lib/              # Utilities
│   └── public/           # Static assets
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Core logic
│   │   ├── mcp/         # MCP client integration
│   │   ├── llm/         # LLM orchestration
│   │   └── sandbox/     # Code execution
│   ├── tests/           # Pytest tests
│   └── requirements.txt
├── shared/              # Shared types (TypeScript + Python)
├── docs/                # Documentation
└── docker/              # Docker configs
```

**Create Repository:**
```bash
mkdir -p vertice-chat-webapp/{frontend,backend,shared,docs,docker}
cd vertice-chat-webapp
git init
```

---

## 📦 **FASE 1: CORE INFRASTRUCTURE**

### **1.1 Backend Architecture - FastAPI with Streaming** ✅ **COMPLETADO**

#### **1.1.1 Dependencies (requirements.txt)** ✅
```txt
# requirements.txt
# LLM Providers SDK
anthropic==0.39.0          # Claude SDK - https://docs.anthropic.com/en/api/client-sdks
openai==1.54.0             # OpenAI SDK - https://platform.openai.com/docs/api-reference
google-generativeai==0.8.3 # Gemini SDK - https://ai.google.dev/gemini-api/docs

# FastAPI Ecosystem
fastapi==0.115.0           # Modern async web framework
uvicorn[standard]==0.32.0  # ASGI server with performance extras
pydantic==2.9.0            # Data validation (v2 is 5-50x faster)
pydantic-settings==2.5.2   # Settings management

# Streaming & Real-time
sse-starlette==2.1.3       # Server-Sent Events - https://github.com/sysid/sse-starlette
python-socketio==5.11.4    # Socket.IO server
aioredis==2.0.1            # Async Redis client

# MCP Protocol
mcp==1.1.0                 # Model Context Protocol SDK - https://modelcontextprotocol.io

# Database
asyncpg==0.29.0            # Async PostgreSQL driver
sqlalchemy[asyncio]==2.0.35 # ORM with async support
alembic==1.13.3            # Database migrations

# Caching & Queue
redis==5.1.1               # Redis client
hiredis==2.3.2             # Redis parser (C extension for speed)

# Security
python-jose[cryptography]==3.3.0  # JWT tokens
passlib[bcrypt]==1.7.4     # Password hashing
python-multipart==0.0.12   # File upload support

# Observability
opentelemetry-api==1.27.0
opentelemetry-sdk==1.27.0
opentelemetry-instrumentation-fastapi==0.48b0
sentry-sdk[fastapi]==2.16.0

# Testing
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
httpx==0.27.2              # Async HTTP client for tests
```

**Install:**
```bash
cd backend
pip install -r requirements.txt
```

#### **1.1.2 FastAPI Application Structure** ✅

**backend/app/main.py:**
```python
"""
FastAPI Application Entry Point
Implements SSE streaming, CORS, and middleware stack
Reference: https://fastapi.tiangolo.com/advanced/
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.core.config import settings
from app.core.observability import setup_telemetry
from app.api.v1 import chat, artifacts, teleport
from app.core.exceptions import AppException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    Reference: https://fastapi.tiangolo.com/advanced/events/
    """
    # Startup
    logger.info("Starting Vertice Chat Backend...")

    # Initialize OpenTelemetry
    setup_telemetry()

    # Initialize Sentry
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,  # 10% of requests traced
            profiles_sample_rate=0.1,
        )

    # Initialize Redis connection pool
    from app.core.cache import init_redis_pool
    await init_redis_pool()

    # Initialize DB connection pool
    from app.core.database import init_db_pool
    await init_db_pool()

    logger.info("Backend ready!")
    yield

    # Shutdown
    logger.info("Shutting down...")
    from app.core.cache import close_redis_pool
    from app.core.database import close_db_pool
    await close_redis_pool()
    await close_db_pool()

# Create FastAPI app
app = FastAPI(
    title="Vertice Chat API",
    description="Multi-LLM Agentic Chat with MCP Integration",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Middleware Stack (order matters!)
# 1. CORS - Must be first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# 2. GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. Request ID middleware (for tracing)
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for distributed tracing"""
    import uuid
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# 4. Exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Custom exception handler for application errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "request_id": request.state.request_id},
    )

# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(artifacts.router, prefix="/api/v1/artifacts", tags=["artifacts"])
app.include_router(teleport.router, prefix="/api/v1/teleport", tags=["teleport"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }

# Instrument with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Only in dev
        log_level="info",
        access_log=True,
    )
```

#### **1.1.3 Configuration Management** ✅

**backend/app/core/config.py:**
```python
"""
Application Configuration using Pydantic Settings
Reference: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Application
    APP_NAME: str = "Vertice Chat"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "https://app.vertice.ai"]

    # LLM API Keys
    ANTHROPIC_API_KEY: str
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    GROQ_API_KEY: Optional[str] = None

    # Prompt Caching Config
    # Reference: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
    ENABLE_PROMPT_CACHING: bool = True
    CACHE_MIN_TOKENS: int = 1024  # Minimum for Anthropic caching
    CACHE_TTL_SECONDS: int = 300  # 5 minutes (Anthropic default)

    # Cost Management
    MAX_TOKENS_PER_REQUEST: int = 8192
    DAILY_TOKEN_LIMIT_PER_USER: int = 100_000

    # Database (Neon PostgreSQL)
    DATABASE_URL: str
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # Redis (Upstash)
    REDIS_URL: str
    REDIS_MAX_CONNECTIONS: int = 50

    # S3 Compatible Storage (for artifacts)
    S3_ENDPOINT_URL: str
    S3_ACCESS_KEY: str
    S3_SECRET_KEY: str
    S3_BUCKET_NAME: str = "vertice-artifacts"

    # Observability
    SENTRY_DSN: Optional[str] = None
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None

    # Sandboxing
    ENABLE_SANDBOXING: bool = True
    SANDBOX_ALLOWED_DIRS: List[str] = ["/tmp/workspace"]
    SANDBOX_ALLOWED_HOSTS: List[str] = ["github.com", "api.anthropic.com"]

    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()

settings = get_settings()
```

#### **1.1.4 Server-Sent Events (SSE) Streaming** ✅

**backend/app/api/v1/chat.py:**
```python
"""
Chat API with SSE Streaming
Implements token-by-token streaming with Anthropic prompt caching
References:
- Anthropic Streaming: https://docs.anthropic.com/en/api/messages-streaming
- SSE Spec: https://html.spec.whatwg.org/multipage/server-sent-events.html
- Starlette SSE: https://github.com/sysid/sse-starlette
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel, Field
from typing import AsyncIterator, List, Optional, Literal
from enum import Enum
import json
import logging
import anthropic
from anthropic import AsyncAnthropic

from app.core.config import settings
from app.core.auth import get_current_user
from app.core.cache import get_cached_prompt, set_cached_prompt
from app.core.observability import trace_llm_call
from app.llm.router import route_to_model
from app.llm.cost_tracker import track_token_usage

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Anthropic client with prompt caching
# Reference: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
anthropic_client = AsyncAnthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    default_headers={"anthropic-beta": "prompt-caching-2024-07-31"}
)

class MessageRole(str, Enum):
    """Message roles as per Anthropic API"""
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    """Chat message structure"""
    role: MessageRole
    content: str
    timestamp: Optional[int] = None

class ChatRequest(BaseModel):
    """Chat request payload"""
    messages: List[Message] = Field(..., min_length=1)
    system_prompt: Optional[str] = None
    model: Optional[str] = None  # Auto-route if None
    max_tokens: int = Field(default=4096, le=8192)
    temperature: float = Field(default=0.8, ge=0.0, le=1.0)
    stream: bool = True
    enable_caching: bool = True

class StreamEvent(BaseModel):
    """SSE event structure"""
    type: Literal["token", "metadata", "error", "done"]
    data: dict

async def stream_claude_response(
    request: ChatRequest,
    user_id: str,
) -> AsyncIterator[str]:
    """
    Stream Claude response with prompt caching

    Prompt Caching Strategy (Anthropic):
    - Static system prompt → Cache with cache_control
    - Recent conversation history → Cache if > 1024 tokens
    - Latest user message → Never cache (always dynamic)

    Cost breakdown:
    - Cache write: 1.25x input token price (one-time)
    - Cache read: 0.1x input token price (90% savings!)
    - Break-even: 2 requests with same prefix

    Reference: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
    """
    try:
        # Determine model (intelligent routing)
        model = request.model or route_to_model(
            messages=request.messages,
            user_id=user_id
        )

        # Construct messages with caching markers
        messages = []

        # Add system prompt with caching if enabled
        system_blocks = []
        if request.system_prompt:
            system_blocks.append({
                "type": "text",
                "text": request.system_prompt,
            })

            # Mark for caching (static content)
            if request.enable_caching and settings.ENABLE_PROMPT_CACHING:
                system_blocks[-1]["cache_control"] = {"type": "ephemeral"}

        # Add conversation history with caching
        # Cache all but the last user message (which is dynamic)
        for i, msg in enumerate(request.messages[:-1]):
            messages.append({
                "role": msg.role.value,
                "content": msg.content,
            })

            # Cache checkpoint every 3-4 messages if total > 1024 tokens
            # This is a heuristic - proper implementation should count tokens
            if (i + 1) % 4 == 0 and request.enable_caching:
                messages[-1]["cache_control"] = {"type": "ephemeral"}

        # Add latest user message (never cached - always fresh)
        messages.append({
            "role": request.messages[-1].role.value,
            "content": request.messages[-1].content,
        })

        # Start tracing
        with trace_llm_call(model=model, user_id=user_id) as span:
            # Stream from Claude
            async with anthropic_client.messages.stream(
                model=model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                system=system_blocks,
                messages=messages,
            ) as stream:

                # Yield metadata first
                yield f"event: metadata\ndata: {json.dumps({'model': model, 'cached': False})}\n\n"

                # Stream tokens
                async for event in stream:
                    if event.type == "content_block_delta":
                        # Token received
                        token = event.delta.text if hasattr(event.delta, 'text') else ""

                        stream_event = StreamEvent(
                            type="token",
                            data={"token": token}
                        )
                        yield f"event: token\ndata: {stream_event.model_dump_json()}\n\n"

                    elif event.type == "message_start":
                        # Check if cache was used
                        usage = event.message.usage
                        cache_hit = getattr(usage, 'cache_read_input_tokens', 0) > 0

                        if cache_hit:
                            logger.info(f"Cache HIT for user {user_id}: saved {usage.cache_read_input_tokens} tokens")

                        # Update metadata with cache info
                        yield f"event: metadata\ndata: {json.dumps({'cached': cache_hit, 'tokens_saved': getattr(usage, 'cache_read_input_tokens', 0)})}\n\n"

                # Get final message
                final_message = await stream.get_final_message()

                # Track token usage for cost management
                await track_token_usage(
                    user_id=user_id,
                    model=model,
                    input_tokens=final_message.usage.input_tokens,
                    output_tokens=final_message.usage.output_tokens,
                    cache_read_tokens=getattr(final_message.usage, 'cache_read_input_tokens', 0),
                    cache_write_tokens=getattr(final_message.usage, 'cache_creation_input_tokens', 0),
                )

                # Add to span
                span.set_attribute("llm.input_tokens", final_message.usage.input_tokens)
                span.set_attribute("llm.output_tokens", final_message.usage.output_tokens)
                span.set_attribute("llm.cache_hit", cache_hit)

                # Done event
                yield f"event: done\ndata: {json.dumps({'finish_reason': final_message.stop_reason})}\n\n"

    except anthropic.APIError as e:
        logger.error(f"Anthropic API error: {e}")
        error_event = StreamEvent(
            type="error",
            data={"message": str(e), "code": e.status_code}
        )
        yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        error_event = StreamEvent(
            type="error",
            data={"message": "Internal server error"}
        )
        yield f"event: error\ndata: {error_event.model_dump_json()}\n\n"

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    SSE streaming endpoint

    Connection format:
    - Content-Type: text/event-stream
    - Cache-Control: no-cache
    - X-Accel-Buffering: no (for nginx)

    Event types:
    - metadata: Model info, cache status
    - token: Individual token
    - error: Error occurred
    - done: Stream complete

    Example client (JavaScript):
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    eventSource.addEventListener('token', (e) => {
      const data = JSON.parse(e.data);
      console.log(data.token);
    });
    ```

    Reference: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
    """
    return EventSourceResponse(
        stream_claude_response(request, current_user["id"]),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )
```

#### **1.1.5 Intelligent Model Router** ✅

**backend/app/llm/router.py:**
```python
"""
Intelligent Model Router
Routes requests to optimal LLM based on intent, complexity, and cost

Strategy:
- Simple queries → Claude Haiku (fast + cheap)
- Medium complexity → Claude Sonnet (balanced)
- Complex reasoning → Claude Opus (powerful)
- Voice/Audio → GPT-4o Realtime or Gemini Live

Cost comparison (per 1M tokens):
- Haiku:  $0.25 input / $1.25 output
- Sonnet: $3 input / $15 output
- Opus:   $15 input / $75 output

Reference: https://www.anthropic.com/pricing
"""
from typing import List, Literal
from enum import Enum
import re
import logging

from app.api.v1.chat import Message

logger = logging.getLogger(__name__)

class ModelTier(str, Enum):
    """Model tiers by capability and cost"""
    FAST = "claude-3-5-haiku-20241022"      # Fastest, cheapest
    BALANCED = "claude-sonnet-4-5-20250901" # Best balance
    POWERFUL = "claude-opus-4-5-20251101"   # Most capable

class IntentType(str, Enum):
    """User intent classification"""
    SIMPLE_QUERY = "simple"
    CODE_GENERATION = "code"
    COMPLEX_REASONING = "reasoning"
    LONG_CONTEXT = "long_context"

def classify_intent(messages: List[Message]) -> IntentType:
    """
    Classify user intent from conversation

    Heuristics:
    - Code keywords → CODE_GENERATION
    - Long messages (>1000 chars) → LONG_CONTEXT
    - Question marks, simple queries → SIMPLE_QUERY
    - Otherwise → COMPLEX_REASONING
    """
    latest_message = messages[-1].content.lower()

    # Code indicators
    code_keywords = ["write code", "implement", "function", "class", "debug", "fix bug"]
    if any(kw in latest_message for kw in code_keywords):
        return IntentType.CODE_GENERATION

    # Long context
    total_length = sum(len(msg.content) for msg in messages)
    if total_length > 10000:  # ~2500 tokens
        return IntentType.LONG_CONTEXT

    # Simple query
    if latest_message.endswith("?") and len(latest_message) < 200:
        return IntentType.SIMPLE_QUERY

    return IntentType.COMPLEX_REASONING

def route_to_model(messages: List[Message], user_id: str) -> str:
    """
    Route to optimal model based on intent and user quota

    Decision tree:
    1. Classify intent
    2. Check user's remaining quota
    3. Select model tier
    4. Return model ID
    """
    intent = classify_intent(messages)

    logger.info(f"Routing user {user_id} with intent {intent}")

    # TODO: Check user quota from DB
    # For now, use intent-based routing

    if intent == IntentType.SIMPLE_QUERY:
        model = ModelTier.FAST
    elif intent == IntentType.CODE_GENERATION:
        model = ModelTier.BALANCED
    elif intent == IntentType.COMPLEX_REASONING:
        model = ModelTier.POWERFUL
    else:  # LONG_CONTEXT
        model = ModelTier.BALANCED  # Sonnet handles 200K context well

    logger.info(f"Selected model: {model}")
    return model.value
```

#### **1.1.6 Cost Tracking System** ✅

**backend/app/llm/cost_tracker.py:**
```python
"""
LLM Cost Tracking and Quota Management

Tracks token usage per user with Redis for fast access
and PostgreSQL for historical data.

Cost calculation formulas (Anthropic 2026):
- Base input:  tokens * model_input_price_per_1M / 1_000_000
- Base output: tokens * model_output_price_per_1M / 1_000_000
- Cache write:  tokens * model_input_price_per_1M * 1.25 / 1_000_000
- Cache read:   tokens * model_input_price_per_1M * 0.10 / 1_000_000

Reference: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching#pricing
"""
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from typing import Dict

from app.core.cache import get_redis
from app.core.database import get_db_session

logger = logging.getLogger(__name__)

# Pricing table (per 1M tokens) - Update from API
MODEL_PRICING = {
    "claude-3-5-haiku-20241022": {
        "input": Decimal("0.25"),
        "output": Decimal("1.25"),
    },
    "claude-sonnet-4-5-20250901": {
        "input": Decimal("3.00"),
        "output": Decimal("15.00"),
    },
    "claude-opus-4-5-20251101": {
        "input": Decimal("15.00"),
        "output": Decimal("75.00"),
    },
}

async def calculate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> Dict[str, Decimal]:
    """
    Calculate cost breakdown for LLM call

    Returns:
        {
            "base_input_cost": Decimal,
            "base_output_cost": Decimal,
            "cache_write_cost": Decimal,
            "cache_read_cost": Decimal,
            "total_cost": Decimal,
            "savings": Decimal,  # From caching
        }
    """
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        logger.warning(f"Unknown model {model}, using Sonnet pricing")
        pricing = MODEL_PRICING["claude-sonnet-4-5-20250901"]

    # Base costs
    base_input_cost = (input_tokens * pricing["input"]) / 1_000_000
    base_output_cost = (output_tokens * pricing["output"]) / 1_000_000

    # Cache costs (Anthropic caching: +25% write, 90% discount read)
    cache_write_cost = (cache_write_tokens * pricing["input"] * Decimal("1.25")) / 1_000_000
    cache_read_cost = (cache_read_tokens * pricing["input"] * Decimal("0.10")) / 1_000_000

    # Savings calculation: what we would have paid without caching
    savings = (cache_read_tokens * pricing["input"] * Decimal("0.90")) / 1_000_000

    total_cost = base_input_cost + base_output_cost + cache_write_cost + cache_read_cost

    return {
        "base_input_cost": base_input_cost,
        "base_output_cost": base_output_cost,
        "cache_write_cost": cache_write_cost,
        "cache_read_cost": cache_read_cost,
        "total_cost": total_cost,
        "savings": savings,
    }

async def track_token_usage(
    user_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> None:
    """
    Track token usage in Redis (fast) and PostgreSQL (persistent)

    Redis keys:
    - user:{user_id}:tokens:daily → Daily token count (expires 24h)
    - user:{user_id}:cost:daily → Daily cost (expires 24h)

    PostgreSQL:
    - token_usage table for historical analysis
    """
    redis = await get_redis()

    # Calculate cost
    costs = await calculate_cost(
        model, input_tokens, output_tokens,
        cache_read_tokens, cache_write_tokens
    )

    # Update Redis counters
    today = datetime.utcnow().strftime("%Y-%m-%d")
    redis_key_tokens = f"user:{user_id}:tokens:{today}"
    redis_key_cost = f"user:{user_id}:cost:{today}"

    total_tokens = input_tokens + output_tokens

    await redis.incrby(redis_key_tokens, total_tokens)
    await redis.incrbyfloat(redis_key_cost, float(costs["total_cost"]))

    # Set expiry (25 hours to avoid edge cases)
    await redis.expire(redis_key_tokens, 90000)
    await redis.expire(redis_key_cost, 90000)

    # Log to database (async task)
    async with get_db_session() as session:
        from app.models.usage import TokenUsage

        usage = TokenUsage(
            user_id=user_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read_tokens,
            cache_write_tokens=cache_write_tokens,
            total_cost=costs["total_cost"],
            cache_savings=costs["savings"],
            timestamp=datetime.utcnow(),
        )
        session.add(usage)
        await session.commit()

    logger.info(
        f"User {user_id}: {total_tokens} tokens, "
        f"${costs['total_cost']:.4f} cost, "
        f"${costs['savings']:.4f} saved from caching"
    )

async def check_user_quota(user_id: str) -> Dict[str, int]:
    """
    Check user's daily quota

    Returns:
        {
            "tokens_used": int,
            "tokens_remaining": int,
            "cost_usd": float,
        }
    """
    redis = await get_redis()

    today = datetime.utcnow().strftime("%Y-%m-%d")
    redis_key_tokens = f"user:{user_id}:tokens:{today}"
    redis_key_cost = f"user:{user_id}:cost:{today}"

    tokens_used = int(await redis.get(redis_key_tokens) or 0)
    cost_usd = float(await redis.get(redis_key_cost) or 0.0)

    # TODO: Get user's quota from DB (premium users have higher limits)
    from app.core.config import settings
    daily_limit = settings.DAILY_TOKEN_LIMIT_PER_USER

    return {
        "tokens_used": tokens_used,
        "tokens_remaining": max(0, daily_limit - tokens_used),
        "cost_usd": cost_usd,
    }
```

### **1.2 MCP Integration Layer** ✅ **COMPLETADO**

#### **1.2.1 MCP Client Implementation** ✅

**backend/app/mcp/client.py:**
```python
"""
Model Context Protocol (MCP) Client
Connects to MCP servers to provide tools to LLMs

Architecture:
    FastAPI Backend (this)
        ↓ MCP Client
    MCP Server (filesystem, git, exec)
        ↓ Tool execution
    Result → LLM

References:
- MCP Spec: https://modelcontextprotocol.io/specification/2025-11-25
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- Anthropic MCP Guide: https://docs.anthropic.com/en/docs/build-with-claude/mcp
"""
import asyncio
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

# MCP SDK (install: pip install mcp)
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool, TextContent, ImageContent

logger = logging.getLogger(__name__)

class MCPClient:
    """
    MCP Client for connecting to tool servers

    Manages multiple MCP server connections:
    - Filesystem server (read/write files)
    - Git server (clone, commit, push)
    - Exec server (sandboxed code execution)
    """

    def __init__(self):
        self.sessions: Dict[str, ClientSession] = {}
        self.available_tools: Dict[str, Tool] = {}

    async def connect_server(
        self,
        name: str,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Connect to an MCP server via stdio

        Example:
            await client.connect_server(
                "filesystem",
                "python",
                ["-m", "mcp_server_filesystem", "/workspace"]
            )
        """
        logger.info(f"Connecting to MCP server: {name}")

        server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env or {},
        )

        try:
            # Create stdio transport
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize connection
                    await session.initialize()

                    # List available tools
                    tools_result = await session.list_tools()

                    # Store session and tools
                    self.sessions[name] = session

                    for tool in tools_result.tools:
                        tool_key = f"{name}:{tool.name}"
                        self.available_tools[tool_key] = tool
                        logger.info(f"Registered tool: {tool_key}")

        except Exception as e:
            logger.error(f"Failed to connect to MCP server {name}: {e}")
            raise

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> List[TextContent | ImageContent]:
        """
        Call a tool on an MCP server

        Example:
            result = await client.call_tool(
                "filesystem",
                "read_file",
                {"path": "/workspace/main.py"}
            )

        Returns:
            List of content blocks (text or images)
        """
        session = self.sessions.get(server_name)
        if not session:
            raise ValueError(f"No active session for server: {server_name}")

        tool_key = f"{server_name}:{tool_name}"
        if tool_key not in self.available_tools:
            raise ValueError(f"Tool not found: {tool_key}")

        logger.info(f"Calling tool: {tool_key} with args {arguments}")

        try:
            result = await session.call_tool(tool_name, arguments)
            return result.content

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            raise

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        Get all tools in Anthropic's tool schema format

        Converts MCP tools to format expected by Claude API:
        {
            "name": "tool_name",
            "description": "What the tool does",
            "input_schema": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }

        Reference: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
        """
        tools_schema = []

        for tool_key, tool in self.available_tools.items():
            server_name, tool_name = tool_key.split(":", 1)

            schema = {
                "name": tool_key.replace(":", "_"),  # Claude doesn't allow colons
                "description": tool.description or f"Tool from {server_name}",
                "input_schema": tool.inputSchema,
            }
            tools_schema.append(schema)

        return tools_schema

    async def close_all(self):
        """Close all MCP connections"""
        for name, session in self.sessions.items():
            logger.info(f"Closing MCP session: {name}")
            # Sessions auto-close with context manager

        self.sessions.clear()
        self.available_tools.clear()

# Global MCP client instance
_mcp_client: Optional[MCPClient] = None

async def init_mcp_client():
    """Initialize MCP client and connect to servers"""
    global _mcp_client

    _mcp_client = MCPClient()

    # Connect to standard MCP servers
    # These are example servers - adjust based on your setup

    # 1. Filesystem server (from MCP official)
    await _mcp_client.connect_server(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp/workspace"],
    )

    # 2. Git server (custom or community)
    # await _mcp_client.connect_server(
    #     name="git",
    #     command="python",
    #     args=["-m", "mcp_server_git"],
    # )

    # 3. Exec server (sandboxed execution - we'll build this)
    # await _mcp_client.connect_server(
    #     name="exec",
    #     command="python",
    #     args=["-m", "app.sandbox.mcp_server"],
    # )

    logger.info(f"MCP client initialized with {len(_mcp_client.available_tools)} tools")

def get_mcp_client() -> MCPClient:
    """Get global MCP client instance"""
    if _mcp_client is None:
        raise RuntimeError("MCP client not initialized. Call init_mcp_client() first.")
    return _mcp_client

async def close_mcp_client():
    """Close MCP client"""
    global _mcp_client
    if _mcp_client:
        await _mcp_client.close_all()
        _mcp_client = None
```

#### **1.2.2 Tool Use with Claude** ✅

**backend/app/llm/tool_use.py:**
```python
"""
Claude Tool Use Integration with MCP

Implements the tool use loop:
1. Claude requests tool
2. Execute via MCP
3. Return result to Claude
4. Claude continues

Reference: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
"""
import logging
from typing import List, AsyncIterator, Dict, Any
import anthropic
from anthropic import AsyncAnthropic
from anthropic.types import (
    MessageParam,
    ToolUseBlock,
    ToolResultBlockParam,
)

from app.mcp.client import get_mcp_client
from app.core.config import settings

logger = logging.getLogger(__name__)

anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

async def chat_with_tools(
    messages: List[MessageParam],
    system_prompt: str,
    max_iterations: int = 10,
) -> AsyncIterator[Dict[str, Any]]:
    """
    Chat with Claude using MCP tools

    Implements agentic tool use loop with iteration limit

    Yields events:
    - {"type": "text", "text": str}
    - {"type": "tool_use", "name": str, "input": dict}
    - {"type": "tool_result", "content": str}
    - {"type": "done"}
    """
    mcp_client = get_mcp_client()
    tools_schema = mcp_client.get_tools_schema()

    current_messages = list(messages)
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        logger.info(f"Tool use iteration {iteration}/{max_iterations}")

        # Call Claude with tools
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-5-20250901",
            max_tokens=4096,
            system=system_prompt,
            messages=current_messages,
            tools=tools_schema,
        )

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Claude is done
            for block in response.content:
                if hasattr(block, "text"):
                    yield {"type": "text", "text": block.text}
            yield {"type": "done"}
            break

        elif response.stop_reason == "tool_use":
            # Claude wants to use tools
            tool_results = []

            for block in response.content:
                if isinstance(block, ToolUseBlock):
                    tool_name = block.name
                    tool_input = block.input
                    tool_id = block.id

                    # Yield tool use event
                    yield {
                        "type": "tool_use",
                        "name": tool_name,
                        "input": tool_input,
                    }

                    # Parse MCP tool name (format: server_tool)
                    if "_" not in tool_name:
                        logger.error(f"Invalid tool name format: {tool_name}")
                        continue

                    server_name, mcp_tool_name = tool_name.split("_", 1)

                    try:
                        # Execute via MCP
                        result_content = await mcp_client.call_tool(
                            server_name=server_name,
                            tool_name=mcp_tool_name,
                            arguments=tool_input,
                        )

                        # Convert MCP result to string
                        result_text = "\n".join(
                            c.text if hasattr(c, "text") else str(c)
                            for c in result_content
                        )

                        # Yield tool result event
                        yield {
                            "type": "tool_result",
                            "tool_name": tool_name,
                            "content": result_text,
                        }

                        # Add to results
                        tool_results.append(
                            ToolResultBlockParam(
                                type="tool_result",
                                tool_use_id=tool_id,
                                content=result_text,
                            )
                        )

                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")

                        error_result = ToolResultBlockParam(
                            type="tool_result",
                            tool_use_id=tool_id,
                            content=f"Error: {str(e)}",
                            is_error=True,
                        )
                        tool_results.append(error_result)

            # Add assistant's tool use to history
            current_messages.append({
                "role": "assistant",
                "content": response.content,
            })

            # Add tool results
            current_messages.append({
                "role": "user",
                "content": tool_results,
            })

        else:
            # Unexpected stop reason
            logger.warning(f"Unexpected stop reason: {response.stop_reason}")
            yield {"type": "done"}
            break

    if iteration >= max_iterations:
        logger.warning("Max tool use iterations reached")
        yield {
            "type": "text",
            "text": "\n\n*[Max iterations reached. Please continue or rephrase.]*"
        }
        yield {"type": "done"}
```

---

### **1.3 Sandboxing with gVisor** ✅ **COMPLETADO**

**backend/app/sandbox/executor.py:**
```python
"""
Secure Code Execution with gVisor-based Sandboxing

Implements Anthropic's sandboxing approach:
- Filesystem isolation (read/write restrictions)
- Network isolation (allowlist-based)
- Resource limits (CPU, memory, time)

Based on:
- Anthropic Sandbox Runtime: https://github.com/anthropic-experimental/sandbox-runtime
- gVisor: https://gvisor.dev/
- Security best practices: https://www.anthropic.com/engineering/claude-code-sandboxing

Note: This is a simplified implementation. For production, use Anthropic's
sandbox-runtime or a managed service like E2B.dev
"""
import asyncio
import logging
import tempfile
import os
import shutil
from typing import Dict, List, Optional
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SandboxConfig:
    """Sandbox configuration"""
    # Filesystem
    allowed_read_dirs: List[str]
    allowed_write_dirs: List[str]

    # Network
    allowed_hosts: List[str]
    block_network: bool = False

    # Resources
    max_execution_time: int = 30  # seconds
    max_memory_mb: int = 512
    max_cpu_percent: int = 50

@dataclass
class ExecutionResult:
    """Code execution result"""
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    error: Optional[str] = None

class SandboxExecutor:
    """
    Sandboxed code executor

    Uses gVisor (runsc) for OS-level sandboxing without Docker overhead.

    Installation:
    ```bash
    # Install gVisor (Linux only)
    (
      set -e
      ARCH=$(uname -m)
      URL=https://storage.googleapis.com/gvisor/releases/release/latest/${ARCH}
      wget ${URL}/runsc ${URL}/runsc.sha512 \
        ${URL}/containerd-shim-runsc-v1 ${URL}/containerd-shim-runsc-v1.sha512
      sha512sum -c runsc.sha512 \
        -c containerd-shim-runsc-v1.sha512
      rm -f *.sha512
      chmod a+rx runsc containerd-shim-runsc-v1
      sudo mv runsc containerd-shim-runsc-v1 /usr/local/bin
    )
    ```

    Reference: https://gvisor.dev/docs/user_guide/install/
    """

    def __init__(self, config: SandboxConfig):
        self.config = config

    async def execute_python(
        self,
        code: str,
        working_dir: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute Python code in sandbox

        Steps:
        1. Create temporary workspace
        2. Write code to file
        3. Execute with gVisor runtime
        4. Capture output and clean up
        """
        # Create temp workspace
        workspace = working_dir or tempfile.mkdtemp(prefix="sandbox_")
        code_file = os.path.join(workspace, "main.py")

        try:
            # Write code to file
            with open(code_file, "w") as f:
                f.write(code)

            # Build command with gVisor
            # Note: This is simplified. Real implementation needs proper
            # gVisor configuration with OCI runtime spec

            if shutil.which("runsc"):
                # Use gVisor if available
                cmd = self._build_gvisor_command(code_file, workspace)
            else:
                # Fallback to regular Python with limited permissions
                logger.warning("gVisor not found, using fallback sandbox")
                cmd = self._build_fallback_command(code_file, workspace)

            # Execute with timeout
            import time
            start_time = time.time()

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=workspace,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.max_execution_time,
                )
                exit_code = process.returncode
                error = None

            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                stdout, stderr = b"", b"Execution timeout"
                exit_code = -1
                error = "Timeout exceeded"

            execution_time = time.time() - start_time

            return ExecutionResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=exit_code,
                execution_time=execution_time,
                error=error,
            )

        finally:
            # Cleanup
            if not working_dir:  # Only delete if we created it
                shutil.rmtree(workspace, ignore_errors=True)

    def _build_gvisor_command(self, code_file: str, workspace: str) -> List[str]:
        """
        Build gVisor runsc command

        gVisor provides strong isolation but requires proper setup.
        For production, use Anthropic's sandbox-runtime or E2B.

        Reference: https://github.com/anthropic-experimental/sandbox-runtime
        """
        # This is a placeholder - real implementation needs OCI spec
        return [
            "runsc",
            "--network=none" if self.config.block_network else "--network=sandbox",
            "run",
            "--",
            "python3",
            code_file,
        ]

    def _build_fallback_command(self, code_file: str, workspace: str) -> List[str]:
        """
        Fallback to Python with basic restrictions

        NOT SECURE for production - use only for development
        """
        return [
            "python3",
            "-I",  # Isolated mode (no user site-packages)
            "-B",  # Don't write .pyc files
            code_file,
        ]

# Example usage in MCP server
async def example_usage():
    """Example: Execute code via sandbox"""
    config = SandboxConfig(
        allowed_read_dirs=["/tmp/workspace"],
        allowed_write_dirs=["/tmp/workspace/output"],
        allowed_hosts=["api.anthropic.com"],
        max_execution_time=10,
    )

    executor = SandboxExecutor(config)

    code = """
import sys
print("Hello from sandbox!")
print("Python version:", sys.version)
    """

    result = await executor.execute_python(code)

    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Exit code:", result.exit_code)
    print("Execution time:", result.execution_time)
```

---

### **✅ PHASE 1 VALIDATION CHECKLIST**

```markdown
Backend Core:
- [ ] FastAPI app runs on http://localhost:8000
- [ ] /health endpoint returns 200
- [ ] /api/docs shows Swagger UI
- [ ] Environment variables loaded correctly
- [ ] Logging outputs to console

Streaming:
- [ ] /api/v1/chat/stream endpoint accepts POST
- [ ] SSE events stream correctly (use curl or EventSource)
- [ ] Tokens appear progressively
- [ ] Cache hit/miss reported in metadata event
- [ ] Connection closes gracefully on completion

Prompt Caching:
- [ ] First request shows cache_write_tokens > 0
- [ ] Second request (same prefix) shows cache_read_tokens > 0
- [ ] Cost reduction visible in logs (~90%)
- [ ] Cache TTL respected (5 min default)

Cost Tracking:
- [ ] Redis counters increment after each request
- [ ] PostgreSQL token_usage table populated
- [ ] Cost calculation matches Anthropic pricing
- [ ] /api/v1/users/me/quota endpoint returns usage

MCP Integration:
- [ ] MCP client connects to filesystem server
- [ ] Tools listed in /api/v1/tools endpoint
- [ ] Tool execution returns results
- [ ] Errors handled gracefully

Sandboxing:
- [ ] Python code executes in isolated environment
- [ ] Filesystem access restricted to allowed dirs
- [ ] Execution timeout enforced
- [ ] Resource limits respected

Observability:
- [ ] OpenTelemetry traces exported
- [ ] Sentry captures errors
- [ ] Logs include request IDs
- [ ] Metrics tracked (latency, token usage)
```

**Test Commands:**
```bash
# 1. Start backend
cd backend
uvicorn app.main:app --reload

# 2. Test health
curl http://localhost:8000/health

# 3. Test SSE streaming (requires auth token)
curl -N -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"messages":[{"role":"user","content":"Hello!"}],"stream":true}' \
     http://localhost:8000/api/v1/chat/stream

# 4. Check Redis cache
redis-cli
> KEYS user:*
> GET user:test-user-id:tokens:2026-01-07

# 5. Check PostgreSQL
psql $DATABASE_URL
SELECT * FROM token_usage ORDER BY timestamp DESC LIMIT 10;
```

---

## 📦 **FASE 2: FRONTEND ARCHITECTURE** ✅ **COMPLETADO**

### **2.1 Next.js 15 Setup with React 19** ✅ **COMPLETADO**

#### **2.1.1 Project Initialization** ✅

```bash
cd frontend

# Create Next.js 15 app with Turbopack
# Reference: https://nextjs.org/docs/getting-started/installation
pnpm create next-app@latest . \
  --typescript \
  --tailwind \
  --app \
  --turbopack \
  --import-alias "@/*"

# Answer prompts:
# ✔ Would you like to use TypeScript? › Yes
# ✔ Would you like to use ESLint? › Yes
# ✔ Would you like to use Tailwind CSS? › Yes
# ✔ Would you like your code inside a `src/` directory? › No
# ✔ Would you like to use App Router? › Yes
# ✔ Would you like to use Turbopack? › Yes
# ✔ Would you like to customize the import alias? › @/*
```

#### **2.1.2 Dependencies** ✅

**frontend/package.json (additions):**
```json
{
  "dependencies": {
    "next": "15.1.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",

    "@radix-ui/react-dialog": "^1.1.2",
    "@radix-ui/react-dropdown-menu": "^2.1.2",
    "@radix-ui/react-slot": "^1.1.0",
    "@radix-ui/react-tabs": "^1.1.1",
    "@radix-ui/react-tooltip": "^1.1.4",

    "tailwindcss": "^4.0.0",
    "framer-motion": "^12.0.0",
    "lucide-react": "^0.468.0",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "tailwind-merge": "^2.6.0",

    "zustand": "^5.0.2",
    "@tanstack/react-query": "^5.62.0",

    "@monaco-editor/react": "^4.6.0",
    "react-markdown": "^9.0.0",
    "rehype-highlight": "^7.0.0",
    "remark-gfm": "^4.0.0",

    "@sentry/nextjs": "^8.42.0",
    "@vercel/analytics": "^1.4.1",
    "@vercel/speed-insights": "^1.1.0",

    "zod": "^3.24.1",
    "date-fns": "^4.1.0"
  },
  "devDependencies": {
    "@types/node": "^22",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "typescript": "^5.7.2",
    "eslint": "^9",
    "eslint-config-next": "15.1.0",

    "@playwright/test": "^1.49.1",
    "vitest": "^2.1.8",
    "@vitejs/plugin-react": "^4.3.4",
    "@testing-library/react": "^16.1.0",
    "@testing-library/user-event": "^14.5.2"
  }
}
```

**Install:**
```bash
pnpm install
```

#### **2.1.3 Next.js Configuration** ✅

**frontend/next.config.ts:**
```typescript
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  // Enable experimental features
  experimental: {
    // Partial Prerendering (PPR) - hybrid static/dynamic
    // Reference: https://nextjs.org/docs/app/building-your-application/rendering/partial-prerendering
    ppr: 'incremental',

    // React Compiler (auto-memoization)
    // Reference: https://react.dev/learn/react-compiler
    reactCompiler: true,

    // Turbopack (dev mode only in 15.0)
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },
  },

  // Bundle analyzer (for optimization)
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },

  // Image optimization
  images: {
    domains: ['avatars.githubusercontent.com', 'cdn.vertice.ai'],
    formats: ['image/avif', 'image/webp'],
  },

  // Headers for security
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },

  // Environment variables available to browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
```

#### **2.1.4 Tailwind CSS v4 Configuration** ✅

**frontend/tailwind.config.ts:**
```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],

  theme: {
    extend: {
      colors: {
        // Neo-minimalist palette
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',

        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
      },

      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },

      fontFamily: {
        sans: ['var(--font-geist-sans)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-geist-mono)', 'monospace'],
      },

      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
      },

      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
      },
    },
  },

  plugins: [
    require('@tailwindcss/typography'),
    require('tailwindcss-animate'),
  ],
};

export default config;
```

**frontend/app/globals.css:**
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* CSS Variables for theming */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222 47% 11%;

    --primary: 221 83% 53%;
    --primary-foreground: 210 40% 98%;

    --secondary: 210 40% 96%;
    --secondary-foreground: 222 47% 11%;

    --muted: 210 40% 96%;
    --muted-foreground: 215 16% 47%;

    --accent: 210 40% 96%;
    --accent-foreground: 222 47% 11%;

    --destructive: 0 84% 60%;
    --destructive-foreground: 210 40% 98%;

    --border: 214 32% 91%;
    --input: 214 32% 91%;
    --ring: 221 83% 53%;

    --radius: 0.5rem;
  }

  .dark {
    --background: 222 47% 11%;
    --foreground: 210 40% 98%;

    --primary: 217 91% 60%;
    --primary-foreground: 222 47% 11%;

    --secondary: 217 33% 17%;
    --secondary-foreground: 210 40% 98%;

    --muted: 217 33% 17%;
    --muted-foreground: 215 20% 65%;

    --accent: 217 33% 17%;
    --accent-foreground: 210 40% 98%;

    --destructive: 0 63% 31%;
    --destructive-foreground: 210 40% 98%;

    --border: 217 33% 17%;
    --input: 217 33% 17%;
    --ring: 224 76% 48%;
  }
}

@layer base {
  * {
    @apply border-border;
  }
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}

/* Custom scrollbar */
@layer utilities {
  .scrollbar-thin::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  .scrollbar-thin::-webkit-scrollbar-track {
    @apply bg-secondary;
  }
  .scrollbar-thin::-webkit-scrollbar-thumb {
    @apply bg-muted-foreground/50 rounded-full;
  }
  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    @apply bg-muted-foreground;
  }
}
```

#### **2.1.5 State Management Setup** ✅

### **2.2 Chat UI Components & State Management** ✅ **COMPLETADO**

#### **2.2.1 Zustand Chat Store**
```typescript
// frontend/lib/stores/chat-store.ts
interface ChatState {
  currentSessionId: string | null;
  sessions: Record<string, ChatSession>;
  isLoading: boolean;
  error: string | null;
  // Actions: createSession, addMessage, etc.
}
```

**Features:**
- ✅ Session management (create, delete, switch)
- ✅ Message persistence (localStorage)
- ✅ Real-time state updates
- ✅ Type-safe state management

#### **2.2.2 Chat Components**
```typescript
// Core Components:
- ChatSidebar: Session navigation & management
- ChatMessages: Message display with auto-scroll
- ChatInput: Intelligent input with validation
- ChatSettings: Model & parameter configuration
- MessageBubble: Rich message rendering
```

**Features:**
- ✅ Markdown rendering with syntax highlighting
- ✅ Code copy functionality
- ✅ Message metadata (tokens, cost, timing)
- ✅ Responsive design
- ✅ TypeScript 100% coverage

#### **2.2.3 UI Component Library**
```typescript
// Shadcn/ui components implemented:
- Button, Card, Badge, Avatar
- ScrollArea, Separator, Label
- Select, Slider, Textarea
- DropdownMenu, Toast
```

**Features:**
- ✅ Radix UI primitives
- ✅ Tailwind CSS v4 styling
- ✅ Accessibility (ARIA compliant)
- ✅ Dark mode support

**frontend/lib/store/chat-store.ts:**
```typescript
/**
 * Zustand Store for Chat State
 *
 * Manages:
 * - Messages array
 * - Streaming state
 * - Model selection
 * - Cost tracking
 *
 * Reference: https://zustand-demo.pmnd.rs/
 */
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
  model?: string;
  tokens?: {
    input: number;
    output: number;
    cached: number;
  };
}

export interface ChatState {
  // Messages
  messages: Message[];
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, content: string) => void;
  clearMessages: () => void;

  // Streaming
  isStreaming: boolean;
  currentStreamId: string | null;
  setStreaming: (streaming: boolean, streamId?: string) => void;

  // Model
  selectedModel: string | null;
  setModel: (model: string | null) => void;

  // Cost tracking
  totalCost: number;
  addCost: (cost: number) => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    persist(
      (set, get) => ({
        // Initial state
        messages: [],
        isStreaming: false,
        currentStreamId: null,
        selectedModel: null,
        totalCost: 0,

        // Actions
        addMessage: (message) => {
          const id = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          const timestamp = Date.now();

          set((state) => ({
            messages: [
              ...state.messages,
              { ...message, id, timestamp },
            ],
          }));
        },

        updateMessage: (id, content) => {
          set((state) => ({
            messages: state.messages.map((msg) =>
              msg.id === id ? { ...msg, content } : msg
            ),
          }));
        },

        clearMessages: () => {
          set({ messages: [], totalCost: 0 });
        },

        setStreaming: (streaming, streamId) => {
          set({
            isStreaming: streaming,
            currentStreamId: streamId || null,
          });
        },

        setModel: (model) => {
          set({ selectedModel: model });
        },

        addCost: (cost) => {
          set((state) => ({
            totalCost: state.totalCost + cost,
          }));
        },
      }),
      {
        name: 'vertice-chat-storage',
        partialize: (state) => ({
          messages: state.messages.slice(-50), // Only persist last 50
          selectedModel: state.selectedModel,
          totalCost: state.totalCost,
        }),
      }
    ),
    { name: 'ChatStore' }
  )
);
```

**frontend/lib/api/chat-client.ts:**
```typescript
/**
 * SSE Chat Client
 *
 * Handles Server-Sent Events streaming from backend
 *
 * Reference: https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events
 */

export interface StreamEvent {
  type: 'metadata' | 'token' | 'error' | 'done';
  data: any;
}

export interface ChatRequest {
  messages: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;
  model?: string;
  stream?: boolean;
  enable_caching?: boolean;
}

export class ChatClient {
  private baseUrl: string;
  private authToken: string | null = null;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
  }

  setAuthToken(token: string) {
    this.authToken = token;
  }

  /**
   * Stream chat response using fetch + ReadableStream
   *
   * Modern approach using Fetch API instead of EventSource
   * (EventSource doesn't support POST or custom headers)
   */
  async *streamChat(request: ChatRequest): AsyncGenerator<StreamEvent> {
    const response = await fetch(`${this.baseUrl}/api/v1/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
      },
      body: JSON.stringify({
        ...request,
        stream: true,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    // Parse SSE stream
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Split by double newline (SSE event separator)
        const events = buffer.split('\n\n');
        buffer = events.pop() || ''; // Keep incomplete event in buffer

        for (const event of events) {
          if (!event.trim()) continue;

          // Parse SSE format: "event: type\ndata: json"
          const lines = event.split('\n');
          let eventType = 'message'; // default
          let eventData = '';

          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.slice(6).trim();
            } else if (line.startsWith('data:')) {
              eventData = line.slice(5).trim();
            }
          }

          if (eventData) {
            try {
              const parsed = JSON.parse(eventData);
              yield {
                type: eventType as StreamEvent['type'],
                data: parsed,
              };
            } catch (e) {
              console.error('Failed to parse SSE data:', eventData);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Non-streaming chat (for simple use cases)
   */
  async chat(request: Omit<ChatRequest, 'stream'>): Promise<{
    content: string;
    model: string;
    tokens: {
      input: number;
      output: number;
      cached: number;
    };
  }> {
    const response = await fetch(`${this.baseUrl}/api/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.authToken && { Authorization: `Bearer ${this.authToken}` }),
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Chat request failed');
    }

    return response.json();
  }
}

// Singleton instance
export const chatClient = new ChatClient();
```

**frontend/components/chat/chat-stream.tsx:**
```typescript
/**
 * Chat Stream Component
 *
 * Handles SSE streaming with React 19 optimistic updates
 *
 * Uses:
 * - useOptimistic for instant UI updates
 * - Suspense for loading states
 * - Error boundaries for error handling
 */
'use client';

import { useState, useEffect, useRef } from 'react';
import { useOptimistic } from 'react';
import { useChatStore } from '@/lib/store/chat-store';
import { chatClient } from '@/lib/api/chat-client';
import { Button } from '@/components/ui/button';
import { Loader2, StopCircle } from 'lucide-react';

export function ChatStream() {
  const { messages, addMessage, updateMessage, isStreaming, setStreaming } = useChatStore();
  const [input, setInput] = useState('');
  const abortControllerRef = useRef<AbortController | null>(null);

  // Optimistic updates for instant feedback
  const [optimisticMessages, addOptimisticMessage] = useOptimistic(
    messages,
    (state, newMessage: typeof messages[0]) => [...state, newMessage]
  );

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();

    if (!input.trim() || isStreaming) return;

    // Add user message optimistically
    const userMessage = {
      role: 'user' as const,
      content: input.trim(),
    };

    addOptimisticMessage({
      ...userMessage,
      id: `temp_${Date.now()}`,
      timestamp: Date.now(),
    });

    // Actually add to store
    addMessage(userMessage);

    // Clear input
    setInput('');

    // Start streaming
    setStreaming(true);

    // Create assistant message placeholder
    const assistantId = `msg_${Date.now()}_assistant`;
    addMessage({
      role: 'assistant',
      content: '',
    });

    let assistantContent = '';

    try {
      // Stream response
      for await (const event of chatClient.streamChat({
        messages: [...messages, userMessage].map((m) => ({
          role: m.role,
          content: m.content,
        })),
      })) {
        if (event.type === 'token') {
          assistantContent += event.data.token;
          updateMessage(assistantId, assistantContent);
        } else if (event.type === 'metadata') {
          console.log('Stream metadata:', event.data);
        } else if (event.type === 'error') {
          console.error('Stream error:', event.data);
          assistantContent += `\n\n*Error: ${event.data.message}*`;
          updateMessage(assistantId, assistantContent);
        } else if (event.type === 'done') {
          console.log('Stream complete');
        }
      }
    } catch (error) {
      console.error('Streaming failed:', error);
      assistantContent += `\n\n*Connection error. Please try again.*`;
      updateMessage(assistantId, assistantContent);
    } finally {
      setStreaming(false);
    }
  }

  function handleStop() {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setStreaming(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {optimisticMessages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground'
              }`}
            >
              {message.content || <Loader2 className="h-4 w-4 animate-spin" />}
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type your message..."
            disabled={isStreaming}
            className="flex-1 px-4 py-2 rounded-lg border bg-background"
          />

          {isStreaming ? (
            <Button
              type="button"
              onClick={handleStop}
              variant="destructive"
              size="icon"
            >
              <StopCircle className="h-5 w-5" />
            </Button>
          ) : (
            <Button type="submit" disabled={!input.trim()}>
              Send
            </Button>
          )}
        </div>
      </form>
    </div>
  );
}
```

---

## 📦 **FASE 3: USER EXPERIENCE & AGENTIC CODING**

### **3.1 Artifacts System - Claude Code Inspired** ✅ **COMPLETADO**

#### **3.1.1 Zustand Artifacts Store**
```typescript
// frontend/lib/stores/artifacts-store.ts
interface ArtifactsState {
  artifacts: Record<string, Artifact>;
  activeArtifactId: string | null;
  expandedFolders: Set<string>;
  // Create, update, delete, save operations
}
```

**Features:**
- ✅ File/folder creation and management
- ✅ Hierarchical tree structure
- ✅ Persistence with localStorage
- ✅ Real-time state updates
- ✅ Export/import functionality

#### **3.1.2 Artifacts UI Components**
```typescript
// Core Components:
- ArtifactsPanel: Main interface with sidebar toggle
- ArtifactTree: File browser with drag-drop
- ArtifactEditor: Monaco-style code editor
- ArtifactToolbar: Actions (save, export, search)
- File upload and export functionality
```

**Features:**
- ✅ Syntax highlighting for 20+ languages
- ✅ Auto-save with modification tracking
- ✅ File upload via drag-drop
- ✅ Folder organization
- ✅ Copy to clipboard
- ✅ Search and replace (UI ready)

#### **3.1.3 Integration with Chat**
```typescript
// Toggle between views:
const [viewMode, setViewMode] = useState<'chat' | 'artifacts'>('chat');
```

**Features:**
- ✅ Seamless switching between chat and artifacts
- ✅ Independent state management
- ✅ Shared UI components
- ✅ Responsive design for both modes

**References:**
- Anthropic Artifacts UI: https://support.anthropic.com/en/articles/9487310-what-are-artifacts-and-how-do-i-use-them
- Claude Code Features: https://code.claude.com/docs

#### **3.1.1 Artifacts Architecture**

**frontend/lib/types/artifacts.ts:**
```typescript
/**
 * Artifacts Type System
 *
 * Based on Claude's Artifacts UI pattern
 * Reference: Anthropic Artifacts documentation
 */

export enum ArtifactType {
  CODE = 'code',
  MARKDOWN = 'markdown',
  HTML = 'html',
  REACT = 'react',
  SVG = 'svg',
  MERMAID = 'mermaid',
  JSON = 'json',
}

export interface Artifact {
  id: string;
  type: ArtifactType;
  title: string;
  content: string;
  language?: string; // For code artifacts
  messageId: string; // Associated chat message
  createdAt: number;
  updatedAt: number;
  version: number;
  parentId?: string; // For artifact versioning
}

export interface ArtifactVersion {
  id: string;
  artifactId: string;
  version: number;
  content: string;
  diff?: string;
  createdAt: number;
  createdBy: 'user' | 'assistant';
}
```

**frontend/lib/store/artifacts-store.ts:**
```typescript
/**
 * Zustand Store for Artifacts Management
 *
 * Handles artifact lifecycle and versioning
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { Artifact, ArtifactType, ArtifactVersion } from '@/lib/types/artifacts';

interface ArtifactsState {
  artifacts: Map<string, Artifact>;
  versions: Map<string, ArtifactVersion[]>;
  activeArtifactId: string | null;

  // Actions
  createArtifact: (artifact: Omit<Artifact, 'id' | 'createdAt' | 'updatedAt' | 'version'>) => string;
  updateArtifact: (id: string, content: string) => void;
  deleteArtifact: (id: string) => void;
  setActiveArtifact: (id: string | null) => void;

  // Versioning
  getVersions: (artifactId: string) => ArtifactVersion[];
  restoreVersion: (artifactId: string, version: number) => void;
}

export const useArtifactsStore = create<ArtifactsState>()(
  persist(
    (set, get) => ({
      artifacts: new Map(),
      versions: new Map(),
      activeArtifactId: null,

      createArtifact: (data) => {
        const id = `artifact_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
        const now = Date.now();

        const artifact: Artifact = {
          ...data,
          id,
          createdAt: now,
          updatedAt: now,
          version: 1,
        };

        set((state) => {
          const newArtifacts = new Map(state.artifacts);
          newArtifacts.set(id, artifact);

          // Create initial version
          const newVersions = new Map(state.versions);
          newVersions.set(id, [{
            id: `${id}_v1`,
            artifactId: id,
            version: 1,
            content: data.content,
            createdAt: now,
            createdBy: 'assistant',
          }]);

          return {
            artifacts: newArtifacts,
            versions: newVersions,
            activeArtifactId: id,
          };
        });

        return id;
      },

      updateArtifact: (id, content) => {
        set((state) => {
          const artifact = state.artifacts.get(id);
          if (!artifact) return state;

          const newVersion = artifact.version + 1;
          const now = Date.now();

          // Update artifact
          const updatedArtifact: Artifact = {
            ...artifact,
            content,
            version: newVersion,
            updatedAt: now,
          };

          const newArtifacts = new Map(state.artifacts);
          newArtifacts.set(id, updatedArtifact);

          // Add version
          const versions = state.versions.get(id) || [];
          const newVersionEntry: ArtifactVersion = {
            id: `${id}_v${newVersion}`,
            artifactId: id,
            version: newVersion,
            content,
            createdAt: now,
            createdBy: 'user',
          };

          const newVersions = new Map(state.versions);
          newVersions.set(id, [...versions, newVersionEntry]);

          return {
            artifacts: newArtifacts,
            versions: newVersions,
          };
        });
      },

      deleteArtifact: (id) => {
        set((state) => {
          const newArtifacts = new Map(state.artifacts);
          const newVersions = new Map(state.versions);

          newArtifacts.delete(id);
          newVersions.delete(id);

          return {
            artifacts: newArtifacts,
            versions: newVersions,
            activeArtifactId: state.activeArtifactId === id ? null : state.activeArtifactId,
          };
        });
      },

      setActiveArtifact: (id) => {
        set({ activeArtifactId: id });
      },

      getVersions: (artifactId) => {
        return get().versions.get(artifactId) || [];
      },

      restoreVersion: (artifactId, version) => {
        const state = get();
        const versions = state.versions.get(artifactId);
        const targetVersion = versions?.find((v) => v.version === version);

        if (targetVersion) {
          get().updateArtifact(artifactId, targetVersion.content);
        }
      },
    }),
    {
      name: 'vertice-artifacts-storage',
      serialize: (state) => {
        // Convert Maps to arrays for persistence
        return JSON.stringify({
          artifacts: Array.from(state.artifacts.entries()),
          versions: Array.from(state.versions.entries()),
          activeArtifactId: state.activeArtifactId,
        });
      },
      deserialize: (str) => {
        const data = JSON.parse(str);
        return {
          artifacts: new Map(data.artifacts),
          versions: new Map(data.versions),
          activeArtifactId: data.activeArtifactId,
        };
      },
    }
  )
);
```

#### **3.1.2 Artifact Viewer Components**

**frontend/components/artifacts/artifact-viewer.tsx:**
```typescript
/**
 * Artifact Viewer with Live Previews
 *
 * Supports multiple artifact types with syntax highlighting and live rendering
 *
 * References:
 * - Monaco Editor: https://microsoft.github.io/monaco-editor/
 * - React Markdown: https://github.com/remarkjs/react-markdown
 */
'use client';

import { useState, useEffect, Suspense } from 'react';
import dynamic from 'next/dynamic';
import { useArtifactsStore } from '@/lib/store/artifacts-store';
import { Artifact, ArtifactType } from '@/lib/types/artifacts';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Download, Copy, History, Play, FileCode } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';

// Lazy load Monaco Editor (heavy dependency)
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
  loading: () => <div className="animate-pulse bg-muted h-full" />,
});

interface ArtifactViewerProps {
  artifactId: string;
}

export function ArtifactViewer({ artifactId }: ArtifactViewerProps) {
  const { artifacts, updateArtifact } = useArtifactsStore();
  const artifact = artifacts.get(artifactId);
  const [localContent, setLocalContent] = useState(artifact?.content || '');
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    if (artifact) {
      setLocalContent(artifact.content);
      setIsDirty(false);
    }
  }, [artifact]);

  if (!artifact) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        No artifact selected
      </div>
    );
  }

  const handleContentChange = (value: string | undefined) => {
    if (value !== undefined) {
      setLocalContent(value);
      setIsDirty(value !== artifact.content);
    }
  };

  const handleSave = () => {
    if (isDirty) {
      updateArtifact(artifactId, localContent);
      setIsDirty(false);
    }
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(artifact.content);
    // TODO: Show toast notification
  };

  const handleDownload = () => {
    const blob = new Blob([artifact.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${artifact.title}.${getFileExtension(artifact.type)}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b">
        <div>
          <h2 className="text-lg font-semibold">{artifact.title}</h2>
          <p className="text-sm text-muted-foreground">
            Version {artifact.version} • {artifact.type}
          </p>
        </div>

        <div className="flex gap-2">
          <Button variant="ghost" size="icon" onClick={handleCopy}>
            <Copy className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon" onClick={handleDownload}>
            <Download className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon">
            <History className="h-4 w-4" />
          </Button>
          {isDirty && (
            <Button onClick={handleSave} size="sm">
              Save
            </Button>
          )}
        </div>
      </div>

      {/* Content */}
      <Tabs defaultValue="preview" className="flex-1 flex flex-col">
        <TabsList className="mx-4 mt-2">
          <TabsTrigger value="preview">Preview</TabsTrigger>
          <TabsTrigger value="code">Code</TabsTrigger>
        </TabsList>

        <TabsContent value="preview" className="flex-1 overflow-auto">
          <ArtifactPreview artifact={artifact} />
        </TabsContent>

        <TabsContent value="code" className="flex-1">
          <MonacoEditor
            height="100%"
            language={getMonacoLanguage(artifact.type, artifact.language)}
            value={localContent}
            onChange={handleContentChange}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              wordWrap: 'on',
              automaticLayout: true,
            }}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ArtifactPreview({ artifact }: { artifact: Artifact }) {
  switch (artifact.type) {
    case ArtifactType.MARKDOWN:
      return (
        <div className="prose dark:prose-invert max-w-none p-6">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {artifact.content}
          </ReactMarkdown>
        </div>
      );

    case ArtifactType.HTML:
      return (
        <iframe
          srcDoc={artifact.content}
          className="w-full h-full border-0"
          sandbox="allow-scripts"
          title={artifact.title}
        />
      );

    case ArtifactType.REACT:
      return <ReactLivePreview code={artifact.content} />;

    case ArtifactType.SVG:
      return (
        <div
          className="flex items-center justify-center h-full p-6"
          dangerouslySetInnerHTML={{ __html: artifact.content }}
        />
      );

    case ArtifactType.CODE:
      return (
        <pre className="p-6 overflow-auto">
          <code className={`language-${artifact.language || 'text'}`}>
            {artifact.content}
          </code>
        </pre>
      );

    default:
      return (
        <div className="p-6 font-mono text-sm whitespace-pre-wrap">
          {artifact.content}
        </div>
      );
  }
}

function ReactLivePreview({ code }: { code: string }) {
  /**
   * Live React component preview
   * Uses react-live or similar for safe execution
   *
   * Reference: https://github.com/FormidableLabs/react-live
   */
  // TODO: Implement safe React component rendering
  return (
    <div className="flex items-center justify-center h-full">
      <p className="text-muted-foreground">React preview coming soon</p>
    </div>
  );
}

function getMonacoLanguage(type: ArtifactType, language?: string): string {
  if (language) return language;

  const languageMap: Record<ArtifactType, string> = {
    [ArtifactType.CODE]: 'typescript',
    [ArtifactType.MARKDOWN]: 'markdown',
    [ArtifactType.HTML]: 'html',
    [ArtifactType.REACT]: 'typescript',
    [ArtifactType.SVG]: 'xml',
    [ArtifactType.MERMAID]: 'mermaid',
    [ArtifactType.JSON]: 'json',
  };

  return languageMap[type] || 'plaintext';
}

function getFileExtension(type: ArtifactType): string {
  const extMap: Record<ArtifactType, string> = {
    [ArtifactType.CODE]: 'txt',
    [ArtifactType.MARKDOWN]: 'md',
    [ArtifactType.HTML]: 'html',
    [ArtifactType.REACT]: 'tsx',
    [ArtifactType.SVG]: 'svg',
    [ArtifactType.MERMAID]: 'mmd',
    [ArtifactType.JSON]: 'json',
  };

  return extMap[type] || 'txt';
}
```

### **3.2 Slash Commands System**

**frontend/lib/commands/registry.ts:**
```typescript
/**
 * Slash Commands Registry
 *
 * Implements command palette for quick actions
 * Inspired by Linear, Notion, and Claude Code
 *
 * Reference: https://cmdk.paco.me/
 */

export interface Command {
  id: string;
  name: string;
  description: string;
  icon?: string;
  shortcut?: string;
  category: 'file' | 'mode' | 'config' | 'action';
  handler: (args?: string[]) => void | Promise<void>;
}

export class CommandRegistry {
  private commands = new Map<string, Command>();

  register(command: Command) {
    this.commands.set(command.id, command);
  }

  unregister(commandId: string) {
    this.commands.delete(commandId);
  }

  getAll(): Command[] {
    return Array.from(this.commands.values());
  }

  getByCategory(category: Command['category']): Command[] {
    return this.getAll().filter((cmd) => cmd.category === category);
  }

  execute(commandId: string, args?: string[]): void | Promise<void> {
    const command = this.commands.get(commandId);
    if (!command) {
      throw new Error(`Command not found: ${commandId}`);
    }
    return command.handler(args);
  }

  search(query: string): Command[] {
    const lowerQuery = query.toLowerCase();
    return this.getAll().filter((cmd) =>
      cmd.name.toLowerCase().includes(lowerQuery) ||
      cmd.description.toLowerCase().includes(lowerQuery)
    );
  }
}

// Global registry instance
export const commandRegistry = new CommandRegistry();

// Register built-in commands
commandRegistry.register({
  id: 'attach-file',
  name: '/attach',
  description: 'Attach files or folders to the conversation',
  icon: 'paperclip',
  category: 'file',
  handler: async () => {
    // TODO: Open file picker
    console.log('Attach file command');
  },
});

commandRegistry.register({
  id: 'mode-code',
  name: '/code',
  description: 'Switch to coding mode',
  icon: 'code',
  category: 'mode',
  handler: () => {
    // TODO: Set mode to coding
    console.log('Code mode activated');
  },
});

commandRegistry.register({
  id: 'mode-chat',
  name: '/chat',
  description: 'Switch to chat mode',
  icon: 'message-circle',
  category: 'mode',
  handler: () => {
    console.log('Chat mode activated');
  },
});

commandRegistry.register({
  id: 'config-model',
  name: '/model',
  description: 'Change the AI model',
  icon: 'brain',
  category: 'config',
  handler: () => {
    // TODO: Open model selector
    console.log('Model selector opened');
  },
});

commandRegistry.register({
  id: 'clear-history',
  name: '/clear',
  description: 'Clear conversation history',
  icon: 'trash',
  category: 'action',
  handler: () => {
    if (confirm('Clear all messages?')) {
      // TODO: Clear chat store
      console.log('History cleared');
    }
  },
});
```

**frontend/components/chat/command-palette.tsx:**
```typescript
/**
 * Command Palette Component
 *
 * Keyboard-driven command interface
 * Uses cmdk library for filtering and navigation
 *
 * Reference: https://github.com/pacocoursey/cmdk
 */
'use client';

import { useState, useEffect } from 'react';
import { Command } from 'cmdk';
import { commandRegistry } from '@/lib/commands/registry';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import {
  FileText,
  Code,
  MessageCircle,
  Brain,
  Trash,
  Paperclip
} from 'lucide-react';

const iconMap = {
  'paperclip': Paperclip,
  'code': Code,
  'message-circle': MessageCircle,
  'brain': Brain,
  'trash': Trash,
  'file-text': FileText,
};

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const [search, setSearch] = useState('');
  const commands = commandRegistry.getAll();

  // Keyboard shortcut (Cmd+K / Ctrl+K)
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [open, onOpenChange]);

  const handleSelect = async (commandId: string) => {
    await commandRegistry.execute(commandId);
    onOpenChange(false);
    setSearch('');
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="p-0 max-w-2xl">
        <Command className="rounded-lg border shadow-md">
          <Command.Input
            value={search}
            onValueChange={setSearch}
            placeholder="Type a command or search..."
            className="h-12 px-4 border-b"
          />

          <Command.List className="max-h-96 overflow-y-auto p-2">
            <Command.Empty className="py-6 text-center text-sm text-muted-foreground">
              No commands found.
            </Command.Empty>

            {['file', 'mode', 'config', 'action'].map((category) => {
              const categoryCommands = commands.filter((cmd) => cmd.category === category);

              if (categoryCommands.length === 0) return null;

              return (
                <Command.Group key={category} heading={category.toUpperCase()}>
                  {categoryCommands.map((command) => {
                    const Icon = command.icon ? iconMap[command.icon as keyof typeof iconMap] : FileText;

                    return (
                      <Command.Item
                        key={command.id}
                        value={command.name}
                        onSelect={() => handleSelect(command.id)}
                        className="flex items-center gap-3 px-3 py-2 rounded cursor-pointer hover:bg-accent"
                      >
                        <Icon className="h-4 w-4 text-muted-foreground" />
                        <div className="flex-1">
                          <p className="font-medium">{command.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {command.description}
                          </p>
                        </div>
                        {command.shortcut && (
                          <kbd className="text-xs bg-muted px-2 py-1 rounded">
                            {command.shortcut}
                          </kbd>
                        )}
                      </Command.Item>
                    );
                  })}
                </Command.Group>
              );
            })}
          </Command.List>
        </Command>
      </DialogContent>
    </Dialog>
  );
}
```

### **3.3 GitHub Integration**

**frontend/lib/integrations/github.ts:**
```typescript
/**
 * GitHub Integration Client
 *
 * OAuth authentication and API interactions
 *
 * References:
 * - GitHub OAuth: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
 * - GitHub REST API: https://docs.github.com/en/rest
 * - Octokit: https://github.com/octokit/octokit.js
 */
import { Octokit } from '@octokit/rest';

export class GitHubClient {
  private octokit: Octokit | null = null;
  private accessToken: string | null = null;

  constructor() {
    // Load token from storage
    if (typeof window !== 'undefined') {
      this.accessToken = localStorage.getItem('github_access_token');
      if (this.accessToken) {
        this.octokit = new Octokit({ auth: this.accessToken });
      }
    }
  }

  /**
   * Initiate GitHub OAuth flow
   *
   * Steps:
   * 1. Redirect to GitHub authorization URL
   * 2. User authorizes app
   * 3. GitHub redirects back with code
   * 4. Exchange code for access token
   */
  async initiateOAuth() {
    const clientId = process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID;
    const redirectUri = `${window.location.origin}/auth/github/callback`;

    const params = new URLSearchParams({
      client_id: clientId!,
      redirect_uri: redirectUri,
      scope: 'repo read:user',
      state: crypto.randomUUID(), // CSRF protection
    });

    window.location.href = `https://github.com/login/oauth/authorize?${params}`;
  }

  /**
   * Handle OAuth callback
   *
   * Called after GitHub redirects back
   */
  async handleCallback(code: string): Promise<void> {
    // Exchange code for token via backend
    const response = await fetch('/api/auth/github/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code }),
    });

    const { access_token } = await response.json();

    this.accessToken = access_token;
    localStorage.setItem('github_access_token', access_token);

    this.octokit = new Octokit({ auth: access_token });
  }

  isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  async getCurrentUser() {
    if (!this.octokit) throw new Error('Not authenticated');

    const { data } = await this.octokit.users.getAuthenticated();
    return data;
  }

  async listRepositories() {
    if (!this.octokit) throw new Error('Not authenticated');

    const { data } = await this.octokit.repos.listForAuthenticatedUser({
      sort: 'updated',
      per_page: 100,
    });

    return data;
  }

  async getRepository(owner: string, repo: string) {
    if (!this.octokit) throw new Error('Not authenticated');

    const { data } = await this.octokit.repos.get({ owner, repo });
    return data;
  }

  async listPullRequests(owner: string, repo: string) {
    if (!this.octokit) throw new Error('Not authenticated');

    const { data } = await this.octokit.pulls.list({
      owner,
      repo,
      state: 'open',
      sort: 'created',
      direction: 'desc',
    });

    return data;
  }

  async getPullRequest(owner: string, repo: string, pullNumber: number) {
    if (!this.octokit) throw new Error('Not authenticated');

    const { data } = await this.octokit.pulls.get({
      owner,
      repo,
      pull_number: pullNumber,
    });

    return data;
  }

  async getPullRequestDiff(owner: string, repo: string, pullNumber: number) {
    if (!this.octokit) throw new Error('Not authenticated');

    const { data } = await this.octokit.pulls.get({
      owner,
      repo,
      pull_number: pullNumber,
      mediaType: { format: 'diff' },
    });

    return data;
  }

  async createBranch(owner: string, repo: string, branchName: string, sha: string) {
    if (!this.octokit) throw new Error('Not authenticated');

    const { data } = await this.octokit.git.createRef({
      owner,
      repo,
      ref: `refs/heads/${branchName}`,
      sha,
    });

    return data;
  }

  async createCommit(
    owner: string,
    repo: string,
    message: string,
    tree: string,
    parents: string[]
  ) {
    if (!this.octokit) throw new Error('Not authenticated');

    const { data } = await this.octokit.git.createCommit({
      owner,
      repo,
      message,
      tree,
      parents,
    });

    return data;
  }

  async createPullRequest(
    owner: string,
    repo: string,
    title: string,
    head: string,
    base: string,
    body?: string
  ) {
    if (!this.octokit) throw new Error('Not authenticated');

    const { data } = await this.octokit.pulls.create({
      owner,
      repo,
      title,
      head,
      base,
      body,
    });

    return data;
  }

  disconnect() {
    this.accessToken = null;
    this.octokit = null;
    localStorage.removeItem('github_access_token');
  }
}

// Singleton instance
export const githubClient = new GitHubClient();
```

**backend/app/api/v1/github.py:**
```python
"""
GitHub Integration Backend
Handles OAuth token exchange (server-side for security)

Security note: Client secret should NEVER be exposed to frontend
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import logging

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class TokenExchangeRequest(BaseModel):
    code: str

class TokenExchangeResponse(BaseModel):
    access_token: str
    token_type: str
    scope: str

@router.post("/token", response_model=TokenExchangeResponse)
async def exchange_github_token(request: TokenExchangeRequest):
    """
    Exchange OAuth code for access token

    This must be done server-side because it requires the client secret

    Reference: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                json={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": request.code,
                },
            )

            response.raise_for_status()
            data = response.json()

            if "error" in data:
                raise HTTPException(
                    status_code=400,
                    detail=f"GitHub OAuth error: {data['error_description']}"
                )

            return TokenExchangeResponse(**data)

        except httpx.HTTPError as e:
            logger.error(f"GitHub token exchange failed: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to exchange GitHub token"
            )
```

### **3.4 Voice Input with Whisper**

**frontend/components/chat/voice-input.tsx:**
```typescript
/**
 * Voice Input Component
 *
 * Uses Web Speech API for recording and Whisper API for transcription
 *
 * References:
 * - Web Speech API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API
 * - OpenAI Whisper: https://platform.openai.com/docs/guides/speech-to-text
 */
'use client';

import { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Mic, MicOff, Loader2 } from 'lucide-react';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export function VoiceInput({ onTranscript, disabled }: VoiceInputProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    // Check browser support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      console.warn('Voice input not supported in this browser');
    }
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm',
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
        await transcribeAudio(audioBlob);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setIsTranscribing(true);

    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'audio.webm');
      formData.append('model', 'whisper-1');

      const response = await fetch('/api/v1/transcribe', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Transcription failed');
      }

      const { text } = await response.json();
      onTranscript(text);
    } catch (error) {
      console.error('Transcription error:', error);
      alert('Failed to transcribe audio');
    } finally {
      setIsTranscribing(false);
    }
  };

  const handleClick = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  return (
    <Button
      variant={isRecording ? 'destructive' : 'ghost'}
      size="icon"
      onClick={handleClick}
      disabled={disabled || isTranscribing}
    >
      {isTranscribing ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : isRecording ? (
        <MicOff className="h-4 w-4" />
      ) : (
        <Mic className="h-4 w-4" />
      )}
    </Button>
  );
}
```

**backend/app/api/v1/transcribe.py:**
```python
"""
Audio Transcription Endpoint
Uses OpenAI Whisper API

Reference: https://platform.openai.com/docs/guides/speech-to-text
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
import logging
import openai

from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    duration: float

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribe audio to text using Whisper

    Supports:
    - Multiple audio formats (webm, mp3, wav, m4a)
    - Automatic language detection
    - Timestamps (optional)
    """
    try:
        # Validate file type
        allowed_types = ['audio/webm', 'audio/mpeg', 'audio/wav', 'audio/m4a']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {allowed_types}"
            )

        # Read file content
        audio_data = await file.read()

        # Transcribe with Whisper
        logger.info(f"Transcribing audio file: {file.filename}")

        response = await openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=(file.filename, audio_data),
            response_format="verbose_json",
        )

        return TranscriptionResponse(
            text=response.text,
            language=response.language,
            duration=response.duration,
        )

    except openai.APIError as e:
        logger.error(f"Whisper API error: {e}")
        raise HTTPException(status_code=500, detail="Transcription failed")

    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

### **✅ PHASE 3 VALIDATION CHECKLIST**

```markdown
Artifacts System:
- [ ] Artifact store persists across refreshes
- [ ] Code artifacts render with syntax highlighting
- [ ] Markdown artifacts render correctly
- [ ] HTML artifacts sandbox properly
- [ ] Version history tracked correctly
- [ ] Diff view works between versions
- [ ] Export/download functionality works

Slash Commands:
- [ ] Command palette opens with Cmd/Ctrl+K
- [ ] Commands filter as user types
- [ ] /attach opens file picker
- [ ] /mode switches context
- [ ] /clear confirms before clearing
- [ ] Custom commands can be registered

GitHub Integration:
- [ ] OAuth flow completes successfully
- [ ] Repositories list loads
- [ ] Pull requests display with diffs
- [ ] Branch creation works
- [ ] Commit creation (with approval) works
- [ ] Token stored securely
- [ ] Disconnect clears all data

Voice Input:
- [ ] Microphone permission requested
- [ ] Recording indicator shows
- [ ] Audio uploads to backend
- [ ] Whisper transcription accurate
- [ ] Transcribed text appears in input
- [ ] Error handling graceful
```

---

## 🔐 **FASE 4: AUTHENTICATION & SECURITY**

### **4.1 Authentication with Clerk**

**References:**
- Clerk Next.js: https://clerk.com/docs/quickstarts/nextjs
- Passkeys (FIDO2): https://clerk.com/docs/authentication/passkeys
- Enterprise SSO: https://clerk.com/docs/authentication/enterprise-connections

#### **4.1.1 Clerk Setup**

**Install dependencies:**
```bash
cd frontend
pnpm add @clerk/nextjs
```

**frontend/.env.local:**
```env
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# After sign-in/sign-up redirects
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/onboarding
```

**frontend/app/layout.tsx:**
```typescript
/**
 * Root Layout with Clerk Provider
 *
 * Wraps entire app with authentication context
 */
import { ClerkProvider } from '@clerk/nextjs';
import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Vertice Chat',
  description: 'Multi-LLM Agentic Chat Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body>{children}</body>
      </html>
    </ClerkProvider>
  );
}
```

**frontend/middleware.ts:**
```typescript
/**
 * Clerk Middleware for Route Protection
 *
 * Automatically protects routes and handles auth redirects
 *
 * Reference: https://clerk.com/docs/references/nextjs/clerk-middleware
 */
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isPublicRoute = createRouteMatcher([
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks(.*)',
  '/',
]);

export default clerkMiddleware((auth, request) => {
  if (!isPublicRoute(request)) {
    auth().protect();
  }
});

export const config = {
  matcher: [
    // Skip Next.js internals and static files
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    // Always run for API routes
    '/(api|trpc)(.*)',
  ],
};
```

#### **4.1.2 Protected API Routes**

**backend/app/core/auth.py:**
```python
"""
Authentication Utilities
Validates Clerk JWT tokens

Reference: https://clerk.com/docs/backend-requests/handling/manual-jwt
"""
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
import logging
from functools import lru_cache
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

@lru_cache()
def get_clerk_jwks() -> Dict:
    """
    Fetch Clerk's JWKS (JSON Web Key Set) for token verification

    Cached to avoid repeated network calls
    """
    response = httpx.get(
        f"https://{settings.CLERK_DOMAIN}/.well-known/jwks.json"
    )
    response.raise_for_status()
    return response.json()

async def verify_clerk_token(token: str) -> Dict:
    """
    Verify Clerk JWT token

    Returns decoded token payload with user info
    """
    try:
        # Get JWKS
        jwks = get_clerk_jwks()

        # Decode and verify token
        # Clerk uses RS256 algorithm
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.CLERK_AUDIENCE,
            issuer=f"https://{settings.CLERK_DOMAIN}",
        )

        return payload

    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict:
    """
    FastAPI dependency for getting current authenticated user

    Usage:
        @router.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            return {"user_id": user["sub"]}
    """
    token = credentials.credentials
    payload = await verify_clerk_token(token)

    return {
        "id": payload["sub"],
        "email": payload.get("email"),
        "name": payload.get("name"),
        "metadata": payload.get("public_metadata", {}),
    }

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[Dict]:
    """
    Optional authentication - returns None if not authenticated
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
```

#### **4.1.3 Passkeys (FIDO2) Support**

**frontend/components/auth/passkey-setup.tsx:**
```typescript
/**
 * Passkey Setup Component
 *
 * Enables passwordless authentication via FIDO2/WebAuthn
 *
 * References:
 * - Clerk Passkeys: https://clerk.com/docs/authentication/passkeys
 * - WebAuthn: https://webauthn.guide/
 */
'use client';

import { useUser } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Key, Check, X } from 'lucide-react';
import { useState } from 'react';

export function PasskeySetup() {
  const { user } = useUser();
  const [isLoading, setIsLoading] = useState(false);
  const [hasPasskey, setHasPasskey] = useState(
    user?.passkeys && user.passkeys.length > 0
  );

  const handleCreatePasskey = async () => {
    if (!user) return;

    setIsLoading(true);

    try {
      // Create passkey via Clerk
      await user.createPasskey();
      setHasPasskey(true);

      // Show success message
      alert('Passkey created successfully!');
    } catch (error) {
      console.error('Failed to create passkey:', error);
      alert('Failed to create passkey. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Key className="h-5 w-5" />
          Passkeys
        </CardTitle>
        <CardDescription>
          Sign in securely without a password using your device's biometric authentication
        </CardDescription>
      </CardHeader>
      <CardContent>
        {hasPasskey ? (
          <div className="flex items-center gap-2 text-green-600">
            <Check className="h-5 w-5" />
            <span>Passkey configured</span>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-muted-foreground">
              <X className="h-5 w-5" />
              <span>No passkey configured</span>
            </div>
            <Button
              onClick={handleCreatePasskey}
              disabled={isLoading}
            >
              {isLoading ? 'Creating...' : 'Create Passkey'}
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

### **4.2 Security Hardening**

#### **4.2.1 Input Validation with Zod**

**shared/schemas/validation.ts:**
```typescript
/**
 * Shared Validation Schemas
 *
 * Used across frontend and backend (via zod-to-json-schema)
 *
 * Reference: https://zod.dev/
 */
import { z } from 'zod';

// Chat message validation
export const chatMessageSchema = z.object({
  role: z.enum(['user', 'assistant']),
  content: z.string()
    .min(1, 'Message cannot be empty')
    .max(32000, 'Message too long'),
  model: z.string().optional(),
  temperature: z.number().min(0).max(2).optional(),
});

// User input validation (XSS prevention)
export const userInputSchema = z.string()
  .min(1)
  .max(10000)
  .refine((val) => {
    // Block common XSS patterns
    const xssPatterns = [
      /<script[^>]*>.*?<\/script>/gi,
      /javascript:/gi,
      /on\w+\s*=/gi,
    ];
    return !xssPatterns.some((pattern) => pattern.test(val));
  }, 'Invalid input detected');

// File upload validation
export const fileUploadSchema = z.object({
  name: z.string().min(1).max(255),
  size: z.number().max(10 * 1024 * 1024, 'File too large (max 10MB)'),
  type: z.enum([
    'text/plain',
    'text/markdown',
    'text/html',
    'application/json',
    'image/png',
    'image/jpeg',
    'image/svg+xml',
  ]),
});

// Artifact validation
export const artifactSchema = z.object({
  type: z.enum(['code', 'markdown', 'html', 'react', 'svg', 'mermaid', 'json']),
  title: z.string().min(1).max(200),
  content: z.string().min(1).max(100000),
  language: z.string().optional(),
});

// GitHub integration validation
export const githubRepoSchema = z.object({
  owner: z.string().min(1).max(39),
  repo: z.string().min(1).max(100),
});

export const githubPRSchema = z.object({
  title: z.string().min(1).max(256),
  body: z.string().max(65536).optional(),
  head: z.string().min(1),
  base: z.string().min(1),
});
```

**backend/app/core/validation.py:**
```python
"""
Input Validation Middleware

Validates and sanitizes all user inputs

Reference: https://docs.pydantic.dev/latest/
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
import re
import bleach

class ChatMessageInput(BaseModel):
    """Validated chat message input"""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=32000)
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=0.8, ge=0.0, le=2.0)

    @validator('content')
    def sanitize_content(cls, v):
        """Sanitize content to prevent XSS"""
        # Remove potentially dangerous HTML tags
        allowed_tags = ['p', 'br', 'strong', 'em', 'code', 'pre']
        cleaned = bleach.clean(v, tags=allowed_tags, strip=True)
        return cleaned

class FileUploadInput(BaseModel):
    """Validated file upload"""
    name: str = Field(..., min_length=1, max_length=255)
    size: int = Field(..., le=10 * 1024 * 1024)  # 10MB max
    content_type: str

    @validator('content_type')
    def validate_content_type(cls, v):
        """Validate file type"""
        allowed_types = [
            'text/plain',
            'text/markdown',
            'text/html',
            'application/json',
            'image/png',
            'image/jpeg',
            'image/svg+xml',
        ]
        if v not in allowed_types:
            raise ValueError(f"Invalid file type: {v}")
        return v

    @validator('name')
    def validate_filename(cls, v):
        """Sanitize filename to prevent path traversal"""
        # Remove path separators
        cleaned = re.sub(r'[/\\]', '', v)
        # Remove null bytes
        cleaned = cleaned.replace('\x00', '')
        return cleaned

class GitHubRepoInput(BaseModel):
    """Validated GitHub repository"""
    owner: str = Field(..., min_length=1, max_length=39, pattern=r'^[a-zA-Z0-9\-]+$')
    repo: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-zA-Z0-9\-_.]+$')
```

#### **4.2.2 Rate Limiting**

**backend/app/core/rate_limit.py:**
```python
"""
Rate Limiting Middleware

Uses Redis for distributed rate limiting

Reference: https://github.com/alisaifee/flask-limiter
"""
from fastapi import HTTPException, Request
from typing import Callable
import time
import logging
from functools import wraps

from app.core.cache import get_redis

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Token bucket rate limiter

    Algorithm:
    - Each user has a bucket with max tokens
    - Tokens refill at constant rate
    - Each request consumes tokens
    - Request rejected if insufficient tokens
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10,
    ):
        self.rate = requests_per_minute / 60  # requests per second
        self.burst_size = burst_size

    async def check_rate_limit(self, user_id: str) -> bool:
        """
        Check if user is within rate limit

        Returns True if request allowed, False otherwise
        """
        redis = await get_redis()

        key = f"rate_limit:{user_id}"
        now = time.time()

        # Get current bucket state
        bucket = await redis.hgetall(key)

        if not bucket:
            # Initialize bucket
            bucket = {
                'tokens': self.burst_size,
                'last_update': now,
            }
        else:
            # Refill tokens based on time passed
            tokens = float(bucket['tokens'])
            last_update = float(bucket['last_update'])

            time_passed = now - last_update
            tokens = min(
                self.burst_size,
                tokens + time_passed * self.rate
            )

            bucket = {
                'tokens': tokens,
                'last_update': now,
            }

        # Check if request allowed
        if bucket['tokens'] >= 1:
            # Consume token
            bucket['tokens'] -= 1

            # Update bucket
            await redis.hset(key, mapping=bucket)
            await redis.expire(key, 3600)  # 1 hour TTL

            return True
        else:
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False

# Global rate limiter instance
rate_limiter = RateLimiter(
    requests_per_minute=60,
    burst_size=10,
)

def rate_limit(func: Callable):
    """
    Decorator for rate limiting endpoints

    Usage:
        @router.post("/chat")
        @rate_limit
        async def chat(user: dict = Depends(get_current_user)):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract user from kwargs
        user = kwargs.get('current_user') or kwargs.get('user')

        if not user:
            # No user, skip rate limiting
            return await func(*args, **kwargs)

        user_id = user['id']

        # Check rate limit
        allowed = await rate_limiter.check_rate_limit(user_id)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"},
            )

        return await func(*args, **kwargs)

    return wrapper
```

#### **4.2.3 CORS Configuration**

**backend/app/core/cors.py:**
```python
"""
CORS Configuration

Secure cross-origin resource sharing setup

Reference: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
"""
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from app.core.config import settings

def setup_cors(app: FastAPI):
    """
    Configure CORS middleware

    Security considerations:
    - Never use "*" in production
    - Explicitly list allowed origins
    - Limit allowed methods and headers
    - Set max_age for preflight caching
    """

    # Allowed origins (never use "*" in production!)
    allowed_origins = settings.CORS_ORIGINS  # From environment

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,  # Allow cookies/auth headers
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Request-ID",
        ],
        expose_headers=["X-Request-ID"],
        max_age=3600,  # Cache preflight for 1 hour
    )
```

### **✅ PHASE 4 VALIDATION CHECKLIST**

```markdown
Authentication (Clerk):
- [ ] Clerk provider wraps app correctly
- [ ] Sign-in/sign-up pages functional
- [ ] Protected routes redirect to login
- [ ] JWT tokens validated on backend
- [ ] User info accessible in components
- [ ] Logout clears session completely

Passkeys:
- [ ] Passkey creation works
- [ ] Biometric authentication prompts correctly
- [ ] Fallback to password available
- [ ] Passkey works across devices (if synced)
- [ ] Error handling graceful

Security:
- [ ] Input validation catches XSS attempts
- [ ] File uploads sanitized
- [ ] SQL injection prevented (parameterized queries)
- [ ] CSRF tokens on forms (if using cookies)
- [ ] Content Security Policy headers set
- [ ] HTTPS enforced in production

Rate Limiting:
- [ ] Rate limit triggers after burst
- [ ] 429 status returned with Retry-After
- [ ] Different limits per user tier
- [ ] Redis bucket state persists
- [ ] Rate limit resets correctly

CORS:
- [ ] Preflight requests succeed
- [ ] Credentials included in requests
- [ ] Only allowed origins accepted
- [ ] Error responses have correct headers
```

---
