"""
FastAPI Application Entry Point
Implements SSE streaming, CORS, and middleware stack
Reference: https://fastapi.tiangolo.com/advanced/
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Callable, Awaitable
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.core.observability import setup_telemetry
from app.api.v1 import chat, artifacts, teleport
from app.core.exceptions import AppException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
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
async def add_request_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Add unique request ID for distributed tracing"""
    import uuid

    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# 4. Exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Custom exception handler for application errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "request_id": getattr(request.state, "request_id", "unknown"),
        },
    )


# Include routers
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(artifacts.router, prefix="/api/v1/artifacts", tags=["artifacts"])
app.include_router(teleport.router, prefix="/api/v1/teleport", tags=["teleport"])


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


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
