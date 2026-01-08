# Prometheus MCP Server Dockerfile
# Multi-stage build for optimal image size
# Supports: File, Git, Execution, Web, Media, Context, Notebook, Agent tools

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY prometheus/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim

LABEL maintainer="Juan Carlos <juancs.d3v@gmail.com>"
LABEL description="Prometheus MCP Server - Universal Gateway for 58+ Tools"
LABEL version="1.0.0"

WORKDIR /app

# Install runtime system dependencies
# - git: Required for git_tools.py (git operations)
# - ripgrep: Required for search_tools.py (fast file search)
# - curl: For health checks
RUN apt-get update && apt-get install -y \
    git \
    ripgrep \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
# Note: Copy ALL necessary directories for Prometheus to work
COPY prometheus/ ./prometheus/
COPY vertice_core/ ./vertice_core/
COPY vertice_cli/ ./vertice_cli/
COPY core/ ./core/
COPY providers/ ./providers/
COPY agents/ ./agents/
COPY vertice_governance/ ./vertice_governance/

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app:$PYTHONPATH

# Environment variables with defaults
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=3000
ENV MCP_LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Expose MCP server port
EXPOSE 3000

# Health check endpoint
# Checks if server responds to HTTP health check within 3s
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# Run MCP Server via standalone runner (no prometheus/__init__.py dependencies)
CMD ["python", "prometheus/mcp_server/run_server.py", "--host", "0.0.0.0", "--port", "3000"]
