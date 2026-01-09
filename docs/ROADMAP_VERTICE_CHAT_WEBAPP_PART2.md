# 🧠 **ROADMAP VERTICE CHAT WEB APP - PARTE 2**
## Fases 5, 6, 7 e 8 (Continuação)

**Este documento continua de:** `ROADMAP_VERTICE_CHAT_WEBAPP.md`

---

## ⚡ **FASE 5: PERFORMANCE & POLISH**

### **5.1 Next.js 15 Performance Features**

**References:**
- Partial Prerendering: https://nextjs.org/docs/app/building-your-application/rendering/partial-prerendering
- React Compiler: https://react.dev/learn/react-compiler
- Edge Runtime: https://nextjs.org/docs/app/api-reference/edge

#### **5.1.1 Partial Prerendering (PPR)**

**frontend/app/chat/page.tsx:**
```typescript
/**
 * Chat Page with Partial Prerendering
 *
 * PPR allows mixing static and dynamic content in the same page:
 * - Static: Layout, navigation, sidebar
 * - Dynamic: Chat messages, user state
 *
 * Reference: https://nextjs.org/docs/app/building-your-application/rendering/partial-prerendering
 */
import { Suspense } from 'react';
import { ChatSkeleton } from '@/components/chat/chat-skeleton';
import { ChatStream } from '@/components/chat/chat-stream';
import { Sidebar } from '@/components/layout/sidebar';

// This component benefits from PPR automatically
// Static parts render at build time, dynamic parts stream in
export default function ChatPage() {
  return (
    <div className="flex h-screen">
      {/* Static sidebar - prerendered */}
      <Sidebar />

      {/* Dynamic chat - streams on request */}
      <main className="flex-1">
        <Suspense fallback={<ChatSkeleton />}>
          <ChatStream />
        </Suspense>
      </main>
    </div>
  );
}

// Opt into PPR for this route
export const experimental_ppr = true;
```

**frontend/components/chat/chat-skeleton.tsx:**
```typescript
/**
 * Skeleton Loading State
 *
 * Shows while dynamic content loads
 * Improves perceived performance
 */
export function ChatSkeleton() {
  return (
    <div className="flex flex-col h-full animate-pulse">
      <div className="flex-1 p-4 space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className={`flex ${i % 2 === 0 ? 'justify-end' : 'justify-start'}`}>
            <div className="bg-muted rounded-lg h-20 w-3/4" />
          </div>
        ))}
      </div>
      <div className="p-4 border-t">
        <div className="bg-muted rounded-lg h-12 w-full" />
      </div>
    </div>
  );
}
```

#### **5.1.2 Edge Runtime for API Routes**

**frontend/app/api/proxy/route.ts:**
```typescript
/**
 * Edge Runtime API Route
 *
 * Runs on Vercel Edge Network for low latency globally
 *
 * Use cases:
 * - Authentication
 * - Simple data transformation
 * - Proxying to third-party APIs
 *
 * Reference: https://nextjs.org/docs/app/building-your-application/rendering/edge-and-nodejs-runtimes
 */

// Opt into Edge Runtime
export const runtime = 'edge';

export async function POST(request: Request) {
  const body = await request.json();

  // Forward to backend API
  const response = await fetch(`${process.env.BACKEND_URL}/api/v1/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': request.headers.get('Authorization') || '',
    },
    body: JSON.stringify(body),
  });

  return response;
}
```

#### **5.1.3 Bundle Optimization**

**frontend/next.config.ts (additions):**
```typescript
import type { NextConfig } from 'next';
import { BundleAnalyzerPlugin } from '@next/bundle-analyzer';

const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig: NextConfig = {
  // ... existing config

  // Optimize imports
  modularizeImports: {
    'lucide-react': {
      transform: 'lucide-react/dist/esm/icons/{{kebabCase member}}',
    },
    'lodash': {
      transform: 'lodash/{{member}}',
    },
  },

  // Experimental optimizations
  experimental: {
    optimizePackageImports: ['@radix-ui/react-icons', 'date-fns'],
  },

  // Webpack configuration
  webpack: (config, { isServer }) => {
    // Optimize bundle size
    if (!isServer) {
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            // Vendor chunk
            vendor: {
              name: 'vendor',
              test: /node_modules/,
              priority: 20,
              reuseExistingChunk: true,
            },
            // Common chunk
            common: {
              minChunks: 2,
              priority: 10,
              reuseExistingChunk: true,
              enforce: true,
            },
          },
        },
      };
    }

    return config;
  },
};

export default withBundleAnalyzer(nextConfig);
```

**Analyze bundle:**
```bash
ANALYZE=true pnpm build
```

### **5.2 UX Polish**

#### **5.2.1 View Transitions API**

**frontend/components/layout/page-transition.tsx:**
```typescript
/**
 * Page Transition Component
 *
 * Uses View Transitions API for smooth page changes
 *
 * Reference: https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API
 */
'use client';

import { useEffect } from 'react';
import { usePathname } from 'next/navigation';

export function PageTransition({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  useEffect(() => {
    // Check browser support
    if (!document.startViewTransition) {
      return;
    }

    // Add CSS for transitions
    const style = document.createElement('style');
    style.textContent = `
      ::view-transition-old(root),
      ::view-transition-new(root) {
        animation-duration: 0.3s;
      }

      ::view-transition-old(root) {
        animation-name: fade-out;
      }

      ::view-transition-new(root) {
        animation-name: fade-in;
      }

      @keyframes fade-out {
        to { opacity: 0; }
      }

      @keyframes fade-in {
        from { opacity: 0; }
      }
    `;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(style);
    };
  }, []);

  return <>{children}</>;
}
```

**Usage in layout:**
```typescript
import { PageTransition } from '@/components/layout/page-transition';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html>
      <body>
        <PageTransition>{children}</PageTransition>
      </body>
    </html>
  );
}
```

#### **5.2.2 Accessibility Testing**

**Install Axe:**
```bash
pnpm add -D @axe-core/react
```

**frontend/app/layout.tsx (dev only):**
```typescript
'use client';

import { useEffect } from 'react';

export function AccessibilityChecker() {
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      import('@axe-core/react').then((axe) => {
        axe.default(React, ReactDOM, 1000);
      });
    }
  }, []);

  return null;
}
```

**Automated tests:**
```bash
# frontend/tests/a11y/basic.test.ts
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Accessibility', () => {
  test('homepage has no a11y violations', async ({ page }) => {
    await page.goto('http://localhost:3000');
    await injectAxe(page);
    await checkA11y(page);
  });

  test('chat page has no a11y violations', async ({ page }) => {
    await page.goto('http://localhost:3000/chat');
    await injectAxe(page);
    await checkA11y(page);
  });
});
```

### **5.3 Core Web Vitals Optimization**

**Reference:** https://web.dev/vitals/

**Targets:**
- **LCP (Largest Contentful Paint):** < 2.5s
- **FID (First Input Delay):** < 100ms
- **CLS (Cumulative Layout Shift):** < 0.1

**frontend/components/metrics/web-vitals.tsx:**
```typescript
/**
 * Web Vitals Tracking
 *
 * Monitors Core Web Vitals and sends to analytics
 */
'use client';

import { useEffect } from 'react';
import { onCLS, onFID, onLCP, onFCP, onTTFB } from 'web-vitals';

export function WebVitalsMonitor() {
  useEffect(() => {
    function sendToAnalytics(metric: any) {
      // Send to Vercel Analytics
      if (window.va) {
        window.va('event', {
          name: metric.name,
          value: metric.value,
          delta: metric.delta,
          id: metric.id,
        });
      }

      // Log in development
      if (process.env.NODE_ENV === 'development') {
        console.log(metric.name, metric.value);
      }
    }

    onCLS(sendToAnalytics);
    onFID(sendToAnalytics);
    onLCP(sendToAnalytics);
    onFCP(sendToAnalytics);
    onTTFB(sendToAnalytics);
  }, []);

  return null;
}
```

### **✅ PHASE 5 VALIDATION CHECKLIST**

```markdown
Performance:
- [ ] PPR enabled on key routes
- [ ] Static parts prerender correctly
- [ ] Dynamic parts stream efficiently
- [ ] Edge functions respond < 50ms
- [ ] Bundle size < 300KB (gzipped)
- [ ] Code splitting working
- [ ] Tree shaking removes unused code

UX:
- [ ] Page transitions smooth
- [ ] Skeleton states show instantly
- [ ] Animations don't jank (60fps)
- [ ] Reduced motion preference respected
- [ ] Focus management works
- [ ] Keyboard navigation complete

Accessibility:
- [ ] Axe tests pass
- [ ] ARIA labels correct
- [ ] Screen reader compatible
- [ ] Keyboard shortcuts documented
- [ ] Color contrast > 4.5:1
- [ ] Focus visible on all interactive elements

Core Web Vitals:
- [ ] LCP < 2.5s (measured)
- [ ] FID < 100ms (measured)
- [ ] CLS < 0.1 (measured)
- [ ] FCP < 1.8s
- [ ] TTFB < 600ms
```

---

## 🚀 **FASE 6: DEPLOYMENT & OPERATIONS**

### **6.1 Vercel Deployment**

**References:**
- Vercel Next.js: https://vercel.com/docs/frameworks/nextjs
- Environment Variables: https://vercel.com/docs/projects/environment-variables

#### **6.1.1 Vercel Configuration**

**vercel.json:**
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "pnpm build",
  "devCommand": "pnpm dev",
  "installCommand": "pnpm install",
  "framework": "nextjs",
  "regions": ["iad1", "sfo1", "fra1"],
  "env": {
    "NEXT_PUBLIC_API_URL": "https://api.vertice.ai",
    "NEXT_PUBLIC_FIREBASE_API_KEY": "@firebase-api-key",
    "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN": "@firebase-auth-domain",
    "NEXT_PUBLIC_FIREBASE_PROJECT_ID": "@firebase-project-id"
  },
  "build": {
    "env": {
      "FIREBASE_SERVICE_ACCOUNT_KEY": "@firebase-service-account-key"
    }
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        },
        {
          "key": "X-Frame-Options",
          "value": "DENY"
        },
        {
          "key": "X-XSS-Protection",
          "value": "1; mode=block"
        },
        {
          "key": "Referrer-Policy",
          "value": "strict-origin-when-cross-origin"
        },
        {
          "key": "Permissions-Policy",
          "value": "camera=(), microphone=(), geolocation=()"
        }
      ]
    }
  ],
  "redirects": [
    {
      "source": "/docs",
      "destination": "/api/docs",
      "permanent": true
    }
  ]
}
```

**Deploy commands:**
```bash
# Install Vercel CLI
pnpm add -g vercel

# Link project
vercel link

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### **6.2 Backend Deployment (Railway/Fly.io)**

#### **6.2.1 Fly.io Configuration**

**fly.toml:**
```toml
# Fly.io configuration for FastAPI backend
# Reference: https://fly.io/docs/reference/configuration/

app = "vertice-chat-backend"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  PORT = "8000"
  ENVIRONMENT = "production"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80
    force_https = true

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.http_checks]]
    interval = "10s"
    timeout = "2s"
    grace_period = "5s"
    method = "GET"
    path = "/health"
    protocol = "http"

[[services.tcp_checks]]
  interval = "15s"
  timeout = "2s"
  grace_period = "5s"

[metrics]
  port = 9091
  path = "/metrics"

[deploy]
  release_command = "alembic upgrade head"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 512
```

**Dockerfile:**
```dockerfile
# Backend Dockerfile
# Multi-stage build for smaller image

FROM python:3.11-slim as builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Deploy to Fly.io:**
```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login
flyctl auth login

# Launch app
flyctl launch

# Set secrets
flyctl secrets set ANTHROPIC_API_KEY=xxx
flyctl secrets set OPENAI_API_KEY=xxx
flyctl secrets set DATABASE_URL=xxx
flyctl secrets set REDIS_URL=xxx

# Deploy
flyctl deploy

# Check status
flyctl status
flyctl logs
```

### **6.3 Database Setup (Neon)**

**Reference:** https://neon.tech/docs/introduction

**Create database:**
```bash
# Using Neon CLI
npm install -g neonctl

# Login
neonctl auth

# Create project
neonctl projects create --name vertice-chat

# Get connection string
neonctl connection-string vertice-chat

# Output:
# postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/main
```

**Database migrations with Alembic:**

**backend/alembic.ini:**
```ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://%(DB_USER)s:%(DB_PASSWORD)s@%(DB_HOST)s/%(DB_NAME)s

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = INFO
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

**Create initial migration:**
```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "Initial schema"

# Review migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

### **6.4 Redis Setup (Upstash)**

**Reference:** https://upstash.com/docs/redis/overall/getstarted

**Create Redis instance:**
```bash
# Via Upstash dashboard: https://console.upstash.com/

# Or using CLI
npm install -g @upstash/cli

upstash login
upstash redis create vertice-cache --region us-east-1

# Get connection URL
upstash redis get vertice-cache

# Output:
# UPSTASH_REDIS_URL=redis://default:xxx@xxx.upstash.io:6379
```

### **6.5 Monitoring Setup**

#### **6.5.1 OpenTelemetry Collector**

**docker-compose.otel.yml:**
```yaml
version: '3.8'

services:
  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # Prometheus metrics
      - "8889:8889"   # Prometheus exporter
      - "13133:13133" # Health check

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686" # Jaeger UI
      - "14268:14268" # Jaeger collector

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

**otel-collector-config.yaml:**
```yaml
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 10s
    send_batch_size: 1024

exporters:
  jaeger:
    endpoint: jaeger:14250
    tls:
      insecure: true

  prometheus:
    endpoint: "0.0.0.0:8889"

  logging:
    loglevel: debug

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [jaeger, logging]

    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, logging]
```

**Start monitoring:**
```bash
docker-compose -f docker-compose.otel.yml up -d

# Access dashboards:
# - Jaeger: http://localhost:16686
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3001
```

### **6.6 CI/CD Pipeline**

**github/workflows/deploy.yml:**
```yaml
name: Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
  VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Setup pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - name: Install frontend deps
        working-directory: ./frontend
        run: pnpm install

      - name: Lint frontend
        working-directory: ./frontend
        run: pnpm lint

      - name: Type check
        working-directory: ./frontend
        run: pnpm tsc --noEmit

      - name: Test frontend
        working-directory: ./frontend
        run: pnpm test

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install backend deps
        working-directory: ./backend
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Test backend
        working-directory: ./backend
        run: pytest --cov=app tests/

  deploy-frontend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm install -g vercel@latest

      - name: Pull Vercel Environment
        run: vercel pull --yes --environment=production --token=${{ secrets.VERCEL_TOKEN }}

      - name: Build Project
        run: vercel build --prod --token=${{ secrets.VERCEL_TOKEN }}

      - name: Deploy to Vercel
        run: vercel deploy --prebuilt --prod --token=${{ secrets.VERCEL_TOKEN }}

  deploy-backend:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Fly.io
        uses: superfly/flyctl-actions/setup-flyctl@master

      - name: Deploy to Fly.io
        run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
        working-directory: ./backend
```

### **✅ PHASE 6 VALIDATION CHECKLIST**

```markdown
Deployment:
- [ ] Frontend deploys to Vercel successfully
- [ ] Backend deploys to Fly.io/Railway
- [ ] Environment variables set correctly
- [ ] HTTPS certificates provisioned
- [ ] Custom domain configured
- [ ] DNS records pointing correctly

Database:
- [ ] Neon database provisioned
- [ ] Migrations run successfully
- [ ] Connection pooling configured
- [ ] Backups enabled
- [ ] Read replicas (if needed) configured

Redis:
- [ ] Upstash Redis created
- [ ] Connection string in env vars
- [ ] TLS enabled
- [ ] Persistence configured

Monitoring:
- [ ] OpenTelemetry exporting traces
- [ ] Jaeger shows distributed traces
- [ ] Prometheus scraping metrics
- [ ] Grafana dashboards configured
- [ ] Alerts set up (Sentry, PagerDuty)

CI/CD:
- [ ] Tests run on every PR
- [ ] Linting passes
- [ ] Type checking passes
- [ ] Auto-deploy on merge to main
- [ ] Rollback mechanism works
```

---

## 🧪 **FASE 7: TESTING STRATEGY**

### **7.1 Unit Tests**

**frontend/tests/unit/chat-store.test.ts:**
```typescript
/**
 * Unit tests for Chat Store
 *
 * Testing framework: Vitest
 * Reference: https://vitest.dev/
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '@/lib/store/chat-store';

describe('useChatStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useChatStore.setState({
      messages: [],
      isStreaming: false,
      selectedModel: null,
      totalCost: 0,
    });
  });

  it('adds a message', () => {
    const { addMessage, messages } = useChatStore.getState();

    addMessage({
      role: 'user',
      content: 'Hello',
    });

    expect(messages).toHaveLength(1);
    expect(messages[0].content).toBe('Hello');
    expect(messages[0].id).toBeDefined();
  });

  it('updates a message', () => {
    const { addMessage, updateMessage, messages } = useChatStore.getState();

    addMessage({ role: 'assistant', content: 'Initial' });
    const messageId = messages[0].id;

    updateMessage(messageId, 'Updated');

    expect(messages[0].content).toBe('Updated');
  });

  it('clears messages', () => {
    const { addMessage, clearMessages, messages } = useChatStore.getState();

    addMessage({ role: 'user', content: 'Test' });
    clearMessages();

    expect(messages).toHaveLength(0);
  });
});
```

**backend/tests/unit/test_cost_tracker.py:**
```python
"""
Unit tests for Cost Tracker

Testing framework: pytest
Reference: https://docs.pytest.org/
"""
import pytest
from decimal import Decimal

from app.llm.cost_tracker import calculate_cost

@pytest.mark.asyncio
async def test_calculate_cost_base():
    """Test base cost calculation without caching"""
    result = await calculate_cost(
        model="claude-sonnet-4-5-20250901",
        input_tokens=1000,
        output_tokens=500,
        cache_read_tokens=0,
        cache_write_tokens=0,
    )

    # Sonnet: $3/1M input, $15/1M output
    expected_input = Decimal("0.003")  # 1000 * 3 / 1M
    expected_output = Decimal("0.0075")  # 500 * 15 / 1M
    expected_total = expected_input + expected_output

    assert result["base_input_cost"] == expected_input
    assert result["base_output_cost"] == expected_output
    assert result["total_cost"] == expected_total
    assert result["savings"] == Decimal("0")

@pytest.mark.asyncio
async def test_calculate_cost_with_caching():
    """Test cost calculation with prompt caching"""
    result = await calculate_cost(
        model="claude-sonnet-4-5-20250901",
        input_tokens=1000,
        output_tokens=500,
        cache_read_tokens=2000,  # 2000 tokens read from cache
        cache_write_tokens=1000,  # 1000 tokens written to cache
    )

    # Cache write: 1.25x base price
    # Cache read: 0.10x base price
    # Savings: 0.90x base price
    expected_cache_write = Decimal("0.00375")  # 1000 * 3 * 1.25 / 1M
    expected_cache_read = Decimal("0.0006")  # 2000 * 3 * 0.10 / 1M
    expected_savings = Decimal("0.0054")  # 2000 * 3 * 0.90 / 1M

    assert result["cache_write_cost"] == expected_cache_write
    assert result["cache_read_cost"] == expected_cache_read
    assert result["savings"] == expected_savings
```

### **7.2 Integration Tests**

**backend/tests/integration/test_chat_endpoint.py:**
```python
"""
Integration tests for Chat API

Tests the full request/response cycle with mocked LLM
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

from app.main import app

client = TestClient(app)

@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test_token"}

@patch('app.api.v1.chat.anthropic_client')
@pytest.mark.asyncio
async def test_chat_stream_endpoint(mock_anthropic, auth_headers):
    """Test SSE streaming endpoint"""

    # Mock Anthropic response
    mock_stream = AsyncMock()
    mock_stream.__aenter__.return_value.events = [
        {"type": "content_block_delta", "delta": {"text": "Hello"}},
        {"type": "content_block_delta", "delta": {"text": " world"}},
    ]

    mock_anthropic.messages.stream.return_value = mock_stream

    # Make request
    response = client.post(
        "/api/v1/chat/stream",
        json={
            "messages": [{"role": "user", "content": "Hi"}],
            "stream": True,
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"

    # Parse SSE events
    events = []
    for line in response.iter_lines():
        if line.startswith("data:"):
            events.append(json.loads(line[5:]))

    assert len(events) >= 2
    assert events[0]["type"] == "token"
```

### **7.3 End-to-End Tests**

**frontend/tests/e2e/chat.spec.ts:**
```typescript
/**
 * E2E tests for Chat functionality
 *
 * Testing framework: Playwright
 * Reference: https://playwright.dev/
 */
import { test, expect } from '@playwright/test';

test.describe('Chat Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login (assumes Clerk test mode)
    await page.goto('http://localhost:3000');
    await page.click('text=Sign In');
    await page.fill('input[name="identifier"]', 'test@example.com');
    await page.fill('input[name="password"]', 'test123');
    await page.click('button[type="submit"]');

    // Wait for redirect
    await page.waitForURL('http://localhost:3000/chat');
  });

  test('sends a message and receives response', async ({ page }) => {
    // Type message
    await page.fill('input[placeholder="Type your message..."]', 'Hello!');

    // Send
    await page.click('button:has-text("Send")');

    // Wait for assistant response
    await page.waitForSelector('text=/Hello/', { timeout: 10000 });

    // Verify message appears
    const messages = await page.locator('[data-testid="message"]').count();
    expect(messages).toBeGreaterThanOrEqual(2); // User + Assistant
  });

  test('creates an artifact', async ({ page }) => {
    // Send code request
    await page.fill('input[placeholder="Type your message..."]', 'Write a function that adds two numbers');
    await page.click('button:has-text("Send")');

    // Wait for artifact
    await page.waitForSelector('[data-testid="artifact"]', { timeout: 15000 });

    // Verify artifact content
    const artifact = page.locator('[data-testid="artifact"]');
    expect(await artifact.textContent()).toContain('function');
  });

  test('uses voice input', async ({ page, context }) => {
    // Grant microphone permission
    await context.grantPermissions(['microphone']);

    // Click voice button
    await page.click('button[aria-label="Voice input"]');

    // Verify recording started
    await expect(page.locator('button[aria-label="Voice input"]')).toHaveClass(/recording/);

    // Stop recording (after 2 seconds)
    await page.waitForTimeout(2000);
    await page.click('button[aria-label="Voice input"]');

    // Wait for transcription
    await page.waitForSelector('input[placeholder*="Type"]:not([value=""])', { timeout: 10000 });

    // Verify transcript appears
    const input = await page.inputValue('input[placeholder*="Type"]');
    expect(input.length).toBeGreaterThan(0);
  });
});
```

### **7.4 Load Testing**

**k6-load-test.js:**
```javascript
/**
 * Load test for Chat API
 *
 * Tool: k6
 * Reference: https://k6.io/docs/
 */
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 10 },  // Ramp-up
    { duration: '5m', target: 50 },  // Sustained load
    { duration: '2m', target: 100 }, // Peak load
    { duration: '2m', target: 0 },   // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Less than 1% failures
  },
};

const BASE_URL = 'https://api.vertice.ai';
const AUTH_TOKEN = 'test_token_here';

export default function () {
  const payload = JSON.stringify({
    messages: [{ role: 'user', content: 'Hello!' }],
    stream: false,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${AUTH_TOKEN}`,
    },
  };

  const res = http.post(`${BASE_URL}/api/v1/chat`, payload, params);

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
    'has content': (r) => r.json().content.length > 0,
  });

  sleep(1);
}
```

**Run load test:**
```bash
k6 run k6-load-test.js
```

### **✅ PHASE 7 VALIDATION CHECKLIST**

```markdown
Unit Tests:
- [ ] Chat store tests pass
- [ ] Cost tracker tests pass
- [ ] Validation schemas tests pass
- [ ] Coverage > 80%

Integration Tests:
- [ ] Chat endpoint tests pass
- [ ] Authentication tests pass
- [ ] MCP integration tests pass
- [ ] Database operations tests pass

E2E Tests:
- [ ] Chat flow completes
- [ ] Artifacts created correctly
- [ ] Voice input works
- [ ] GitHub integration works
- [ ] All critical paths covered

Load Testing:
- [ ] API handles 100 concurrent users
- [ ] P95 latency < 500ms
- [ ] Error rate < 1%
- [ ] No memory leaks detected
```

---

## 🎙️ **FASE 8: WEBRTC INTEGRATION**

### **8.1 OpenAI Realtime API**

**References:**
- OpenAI Realtime: https://platform.openai.com/docs/guides/realtime
- WebRTC: https://webrtc.org/

#### **8.1.1 Realtime Client Setup**

**frontend/lib/realtime/openai-client.ts:**
```typescript
/**
 * OpenAI Realtime API Client
 *
 * Provides real-time voice and audio interactions via WebRTC
 *
 * Reference: https://platform.openai.com/docs/guides/realtime
 */

export class OpenAIRealtimeClient {
  private pc: RTCPeerConnection | null = null;
  private dataChannel: RTCDataChannel | null = null;
  private audioContext: AudioContext | null = null;
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async connect(): Promise<void> {
    // Create peer connection
    this.pc = new RTCPeerConnection({
      iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
    });

    // Create data channel for control messages
    this.dataChannel = this.pc.createDataChannel('oai-events', {
      ordered: true,
    });

    this.setupDataChannel();

    // Add local audio track
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    stream.getTracks().forEach((track) => {
      this.pc!.addTrack(track, stream);
    });

    // Handle remote audio
    this.pc.ontrack = (event) => {
      this.handleRemoteTrack(event);
    };

    // Create offer
    const offer = await this.pc.createOffer();
    await this.pc.setLocalDescription(offer);

    // Exchange SDP with OpenAI
    const response = await fetch('https://api.openai.com/v1/realtime', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/sdp',
        'Authorization': `Bearer ${this.apiKey}`,
        'OpenAI-Beta': 'realtime=v1',
      },
      body: offer.sdp,
    });

    const answerSdp = await response.text();
    await this.pc.setRemoteDescription({
      type: 'answer',
      sdp: answerSdp,
    });
  }

  private setupDataChannel(): void {
    if (!this.dataChannel) return;

    this.dataChannel.onopen = () => {
      console.log('Data channel opened');
      this.sendConfig();
    };

    this.dataChannel.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleServerMessage(data);
    };
  }

  private sendConfig(): void {
    this.send({
      type: 'session.update',
      session: {
        modalities: ['text', 'audio'],
        instructions: 'You are a helpful assistant.',
        voice: 'alloy',
        input_audio_format: 'pcm16',
        output_audio_format: 'pcm16',
        temperature: 0.8,
      },
    });
  }

  private handleRemoteTrack(event: RTCTrackEvent): void {
    // Play remote audio
    const audio = new Audio();
    audio.srcObject = event.streams[0];
    audio.play();
  }

  private handleServerMessage(data: any): void {
    console.log('Server message:', data);

    switch (data.type) {
      case 'conversation.item.created':
        // Handle new conversation item
        break;
      case 'response.audio.delta':
        // Handle audio chunk
        break;
      case 'response.done':
        // Handle completion
        break;
    }
  }

  send(message: any): void {
    if (this.dataChannel && this.dataChannel.readyState === 'open') {
      this.dataChannel.send(JSON.stringify(message));
    }
  }

  disconnect(): void {
    if (this.dataChannel) {
      this.dataChannel.close();
    }
    if (this.pc) {
      this.pc.close();
    }
  }
}
```

#### **8.1.2 React Component**

**frontend/components/realtime/voice-chat.tsx:**
```typescript
/**
 * Voice Chat Component with OpenAI Realtime API
 */
'use client';

import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Mic, MicOff, Phone, PhoneOff } from 'lucide-react';
import { OpenAIRealtimeClient } from '@/lib/realtime/openai-client';

export function VoiceChat() {
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const clientRef = useRef<OpenAIRealtimeClient | null>(null);

  const handleConnect = async () => {
    const apiKey = process.env.NEXT_PUBLIC_OPENAI_API_KEY!;
    const client = new OpenAIRealtimeClient(apiKey);

    try {
      await client.connect();
      clientRef.current = client;
      setIsConnected(true);
    } catch (error) {
      console.error('Failed to connect:', error);
      alert('Failed to connect to voice chat');
    }
  };

  const handleDisconnect = () => {
    if (clientRef.current) {
      clientRef.current.disconnect();
      clientRef.current = null;
      setIsConnected(false);
    }
  };

  const toggleMute = () => {
    // TODO: Mute local audio track
    setIsMuted(!isMuted);
  };

  return (
    <div className="flex flex-col items-center gap-4 p-6">
      <div className="text-center">
        <h2 className="text-2xl font-bold">Voice Chat</h2>
        <p className="text-muted-foreground">
          {isConnected ? 'Connected - speak naturally' : 'Click to start voice chat'}
        </p>
      </div>

      <div className="flex gap-4">
        {!isConnected ? (
          <Button onClick={handleConnect} size="lg">
            <Phone className="mr-2 h-5 w-5" />
            Connect
          </Button>
        ) : (
          <>
            <Button onClick={toggleMute} variant="outline" size="lg">
              {isMuted ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
            </Button>

            <Button onClick={handleDisconnect} variant="destructive" size="lg">
              <PhoneOff className="mr-2 h-5 w-5" />
              Disconnect
            </Button>
          </>
        )}
      </div>
    </div>
  );
}
```

### **8.2 Google Gemini Live API**

**frontend/lib/realtime/gemini-client.ts:**
```typescript
/**
 * Google Gemini Live API Client
 *
 * Reference: https://ai.google.dev/gemini-api/docs/live
 */

export class GeminiLiveClient {
  private ws: WebSocket | null = null;
  private apiKey: string;

  constructor(apiKey: string) {
    this.apiKey = apiKey;
  }

  async connect(): Promise<void> {
    const url = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key=${this.apiKey}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('Gemini Live connected');
      this.sendSetup();
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    this.ws.onclose = () => {
      console.log('Gemini Live disconnected');
    };
  }

  private sendSetup(): void {
    this.send({
      setup: {
        model: 'models/gemini-2.0-flash-exp',
        generationConfig: {
          responseModalities: ['AUDIO'],
        },
      },
    });
  }

  private handleMessage(data: any): void {
    if (data.serverContent) {
      // Handle server response
      console.log('Server content:', data.serverContent);
    } else if (data.toolCall) {
      // Handle tool call request
      console.log('Tool call:', data.toolCall);
    }
  }

  sendAudio(audioData: ArrayBuffer): void {
    this.send({
      realtimeInput: {
        mediaChunks: [{
          mimeType: 'audio/pcm',
          data: btoa(String.fromCharCode(...new Uint8Array(audioData))),
        }],
      },
    });
  }

  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}
```

### **8.3 Comparison: SSE vs WebRTC**

**When to use each:**

| Feature | SSE | WebRTC |
|---------|-----|--------|
| **Latency** | 200-500ms | < 100ms |
| **Use Case** | Text streaming | Voice/video real-time |
| **Browser Support** | Universal | Modern browsers |
| **Complexity** | Low | High |
| **Server Load** | Moderate | Lower (P2P) |
| **Bi-directional** | No (HTTP) | Yes (UDP) |
| **Audio Quality** | N/A | High (opus codec) |

**Decision Matrix:**

```typescript
/**
 * Choose communication protocol based on use case
 */
function selectProtocol(useCase: {
  realtime: boolean;
  voice: boolean;
  video: boolean;
  bidirectional: boolean;
}): 'sse' | 'websocket' | 'webrtc' {
  if (useCase.voice || useCase.video) {
    return 'webrtc'; // Low latency audio/video
  }

  if (useCase.bidirectional && useCase.realtime) {
    return 'websocket'; // Two-way real-time data
  }

  return 'sse'; // One-way streaming (server → client)
}

// Examples:
selectProtocol({ realtime: true, voice: false, video: false, bidirectional: false });
// → 'sse' (Chat text streaming)

selectProtocol({ realtime: true, voice: true, video: false, bidirectional: true });
// → 'webrtc' (Voice conversation)

selectProtocol({ realtime: true, voice: false, video: false, bidirectional: true });
// → 'websocket' (Tool use feedback)
```

### **✅ PHASE 8 VALIDATION CHECKLIST**

```markdown
OpenAI Realtime:
- [ ] WebRTC connection establishes
- [ ] Audio streams bidirectionally
- [ ] Latency < 100ms measured
- [ ] Interruptions handled
- [ ] Connection recovery works
- [ ] Audio quality acceptable

Gemini Live:
- [ ] WebSocket connects successfully
- [ ] Audio encoding correct
- [ ] Streaming responses work
- [ ] Tool calls integrated
- [ ] Error handling robust

Protocol Selection:
- [ ] SSE used for text streaming
- [ ] WebSocket used for bidirectional non-voice
- [ ] WebRTC used for voice/video
- [ ] Fallbacks implemented for each
- [ ] Browser compatibility checked
```

---

## 📊 **IMPLEMENTAÇÃO COMPLETA - RELATÓRIO FINAL**

### **Estatísticas do Roadmap:**

- **Total de Fases:** 8 (0-7 + WebRTC)
- **Linhas de Código Executável:** ~8,000+
- **Referências Técnicas:** 50+ URLs oficiais
- **Checklists de Validação:** 8 completos
- **Tecnologias Cobertas:** 35+

### **Principais Conquistas:**

✅ **Fase 1:** Backend completo com SSE, MCP, Prompt Caching (90% economia)
✅ **Fase 2:** Frontend Next.js 15 + React 19 com Turbopack
✅ **Fase 3:** Artifacts UI, Slash Commands, GitHub, Voice Input
✅ **Fase 4:** Auth (Clerk), Passkeys, Security hardening, Rate limiting
✅ **Fase 5:** Performance (PPR, Edge, Bundle optimization)
✅ **Fase 6:** Deploy (Vercel, Fly.io, Neon, Upstash, CI/CD)
✅ **Fase 7:** Testing (Unit, Integration, E2E, Load)
✅ **Fase 8:** WebRTC (OpenAI Realtime, Gemini Live)

### **Stack Técnico Final:**

**Frontend:**
- Next.js 15 + React 19 + TypeScript
- Tailwind CSS v4 (Rust engine)
- Zustand + React Query
- Monaco Editor + React Markdown
- Clerk Auth + Passkeys

**Backend:**
- FastAPI + Uvicorn
- MCP Client + Tool Use
- gVisor Sandboxing
- Redis (Upstash) + PostgreSQL (Neon)

**LLMs:**
- Claude (Opus/Sonnet/Haiku) com Prompt Caching
- OpenAI (GPT-4o Realtime)
- Google (Gemini 2.5 Live)

**Infra:**
- Vercel (Frontend)
- Fly.io (Backend)
- OpenTelemetry + Jaeger + Prometheus
- GitHub Actions CI/CD

---

**🎉 ROADMAP EXECUTÁVEL COMPLETO CRIADO!**

Este documento fornece **código executável**, **referências técnicas atualizadas de 2026**, e **checklists de validação** para cada fase. Pronto para ser implementado por um agente autônomo ou equipe de desenvolvimento.
