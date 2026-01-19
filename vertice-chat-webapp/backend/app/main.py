"""
FastAPI Application Entry Point
Implements SSE streaming, CORS, and middleware stack
Reference: https://fastapi.tiangolo.com/advanced/
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Callable, Awaitable
import logging
import time
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.core.observability import setup_telemetry
from app.api.v1 import chat, artifacts, teleport, agents, billing, admin

try:
    from app.api.v1 import terminal
except ImportError as e:
    print(f"Warning: Terminal API not available: {e}")
    terminal = None

try:
    from app.api.v1 import executor
except ImportError as e:
    print(f"Warning: Executor API not available: {e}")
    executor = None
from app.core.exceptions import AppException

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers[
            "Content-Security-Policy"
        ] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]

        # Add custom headers
        response.headers["X-Vertice-Version"] = "1.0.0"
        response.headers["X-Security-Enabled"] = "true"

        return response


# Rate Limiting Middleware (Simple in-memory implementation)
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}  # Simple in-memory storage (not for production)

    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Clean old requests
        current_time = time.time()
        if client_ip in self.requests:
            self.requests[client_ip] = [
                req_time
                for req_time in self.requests[client_ip]
                if current_time - req_time < self.window_seconds
            ]

        # Check rate limit
        if client_ip in self.requests and len(self.requests[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "retry_after": self.window_seconds},
            )

        # Record request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        self.requests[client_ip].append(current_time)

        # Continue with request
        response = await call_next(request)
        return response


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

    # Initialize Cache (Firestore)
    from app.core.cache import init_cache_pool

    await init_cache_pool()

    # Initialize DB connection pool
    from app.core.database import init_db_pool

    await init_db_pool()

    logger.info("Backend ready!")
    yield

    # Shutdown
    logger.info("Shutting down...")
    from app.core.cache import close_cache_pool
    # from app.core.database import close_db_pool

    await close_cache_pool()
    # await close_db_pool()


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
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# 2. GZip compression for responses > 1KB
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 3. Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# 4. Rate limiting middleware (100 requests per minute per IP)
app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)


# 5. Authentication middleware (Next-Gen Identity 3.0)
@app.middleware("http")
async def authentication_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Mandatory authentication middleware - Next-Gen Identity 3.0"""
    from app.core.auth import authenticate_request

    # Public endpoints that don't require authentication
    public_paths = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/docs",
        "/api/redoc",
        "/api/openapi.json",
    ]

    # Skip authentication for public endpoints
    if request.url.path in public_paths:
        response = await call_next(request)
        return response

    # Extract authentication tokens
    authorization = request.headers.get("Authorization")
    api_key = request.headers.get("X-API-Key")

    # Authenticate request (human or agent)

    # DEBUG: Pervasive Logging
    logger.info(f"[Middleware] Processing {request.method} {request.url.path}")
    if authorization:
        logger.info(f"[Middleware] Auth Header Present. Length: {len(authorization)}")
        if authorization.startswith("Bearer "):
            logger.info(f"[Middleware] Token Prefix Valid. Sample: {authorization[:15]}...")
    else:
        logger.warning(f"[Middleware] NO AUTH HEADER RECEIVED for {request.url.path}")

    auth_result = await authenticate_request(token=authorization, api_key=api_key)

    if not auth_result:
        logger.warning(f"[Middleware] Auth Result is None. Rejecting {request.url.path}")
        # Return 401 for unauthenticated requests
        return JSONResponse(
            status_code=401,
            content={
                "error": "Authentication required",
                "message": "Please provide Authorization header (for humans) or X-API-Key header (for agents)",
                "docs": "https://docs.vertice.ai/authentication",
            },
        )

    # Store authentication context in request state
    request.state.auth = auth_result

    # Continue with authenticated request
    response = await call_next(request)
    return response


# 6. Request ID middleware (for tracing)
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
app.include_router(agents.router, prefix="/api/v1", tags=["agents"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["billing"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])

if terminal:
    app.include_router(terminal.router, prefix="/api/v1/terminal", tags=["terminal"])

if executor:
    app.include_router(executor.router, prefix="/api/v1/agents", tags=["agents"])


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
