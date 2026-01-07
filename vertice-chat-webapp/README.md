# 🤖 Vertice Chat Web App

> **The Future of AI-Powered Development**

A revolutionary web application that combines conversational AI with direct code manipulation, enabling developers to interact with AI agents through natural language while building and editing code in real-time.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-100%25-blue)
![Next.js](https://img.shields.io/badge/Next.js-16.1.1-black)
![React](https://img.shields.io/badge/React-19.2.3-blue)
![Constitutional](https://img.shields.io/badge/Constitutional-100%25-green)

## 🌟 Features

### 🤖 Agentic Coding Experience
- **Natural Language Commands**: Speak or type commands to AI agents
- **Real-time Code Editing**: Monaco-powered code editor with syntax highlighting
- **Artifact Management**: Create, edit, and organize code files directly in chat
- **Multi-modal Interface**: Text, voice, and code editing in one seamless experience

### 🎙️ Voice Integration
- **OpenAI Whisper**: Real-time speech-to-text transcription
- **WebRTC Support**: Low-latency voice communication
- **Voice Commands**: Control the application with your voice
- **Multi-language Support**: Configurable language recognition

### 🔗 GitHub Integration
- **Repository Search**: Find and explore GitHub repositories
- **File Browsing**: Navigate repository contents
- **Clone Operations**: Import repositories as artifacts
- **Code Discovery**: Find inspiration and integrate existing code

### 🛡️ Enterprise Security
- **Clerk Authentication**: Secure user management with Passkeys
- **Rate Limiting**: Distributed protection against abuse
- **Input Validation**: OWASP-compliant sanitization
- **Audit Logging**: Complete activity tracking

### ⚡ Performance First
- **Next.js 15**: Latest App Router with Server Components
- **Partial Prerendering**: Hybrid static/dynamic rendering
- **Core Web Vitals**: Optimized for speed and UX
- **Edge Runtime**: Global CDN deployment ready

## 🚀 Quick Start

### Prerequisites
- Node.js 20+ with pnpm
- Python 3.11+ with pip
- GitHub account (for repository access)
- OpenAI API key (for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/vertice-chat-webapp.git
   cd vertice-chat-webapp
   ```

2. **Install dependencies**
   ```bash
   # Frontend
   cd frontend
   pnpm install

   # Backend
   cd ../backend
   pip install -r requirements.txt
   ```

3. **Environment Setup**
   ```bash
   # Copy environment templates
   cp frontend/.env.example frontend/.env.local
   cp backend/.env.example backend/.env

   # Edit with your API keys
   # Clerk, OpenAI, GitHub tokens, etc.
   ```

4. **Start Development Servers**
   ```bash
   # Terminal 1: Frontend
   cd frontend && pnpm dev

   # Terminal 2: Backend
   cd backend && uvicorn app.main:app --reload
   ```

5. **Open your browser**
   ```
   http://localhost:3000
   ```

## 📖 Usage

### Basic Chat
1. Sign in with your Clerk account
2. Start a conversation with the AI agent
3. Use slash commands for specific actions:
   - `/help` - Show available commands
   - `/run <code>` - Execute code
   - `/save [name]` - Save session
   - `/artifact new <file>` - Create code file

### Code Artifacts
1. Switch to "Artifacts" tab
2. Create new files or edit existing ones
3. Use the Monaco editor with full IDE features
4. Files are automatically saved and versioned

### Voice Commands
1. Click the microphone button in chat input
2. Grant microphone permissions
3. Speak naturally - your words are transcribed in real-time
4. Use voice to control the application

### GitHub Integration
1. Switch to "GitHub" tab
2. Search for repositories or browse your own
3. Explore file contents and clone repositories
4. Import code as artifacts for editing

## 🏗️ Architecture

### Frontend Architecture
```
frontend/
├── app/                    # Next.js App Router
│   ├── chat/              # Main chat interface
│   ├── sign-in/           # Authentication pages
│   ├── api/               # API routes
│   └── layout.tsx         # Root layout
├── components/            # React components
│   ├── chat/             # Chat-specific components
│   ├── artifacts/        # Code editing components
│   ├── github/           # Repository browser
│   ├── voice/            # Voice input components
│   └── ui/               # Reusable UI components
├── lib/                  # Business logic
│   ├── stores/           # Zustand state management
│   ├── commands/         # Slash command system
│   ├── github/           # GitHub API client
│   └── voice/            # Voice processing
└── hooks/                # Custom React hooks
```

### Backend Architecture
```
backend/
├── app/
│   ├── main.py           # FastAPI application
│   ├── core/             # Core functionality
│   │   ├── auth.py       # Clerk authentication
│   │   ├── config.py     # Settings management
│   │   ├── validation.py # Input validation
│   │   └── rate_limit.py # Rate limiting
│   ├── api/              # API endpoints
│   │   └── v1/           # Versioned endpoints
│   ├── llm/              # AI model integration
│   │   ├── router.py     # Model routing
│   │   └── cost_tracker.py # Usage tracking
│   ├── sandbox/          # Code execution
│   └── websocket/        # Real-time communication
├── tests/                # Test suites
└── alembic/              # Database migrations
```

## 🛠️ Technologies

### Frontend
- **Framework**: Next.js 15 with App Router
- **UI**: React 19.2.3 with TypeScript
- **Styling**: Tailwind CSS v4
- **State**: Zustand for global state
- **Editor**: Monaco Editor for code editing
- **Auth**: Clerk for authentication
- **Voice**: OpenAI Whisper + WebRTC
- **Git**: GitHub API integration

### Backend
- **Framework**: FastAPI with async support
- **Language**: Python 3.11+
- **Database**: PostgreSQL (Neon) + Redis (Upstash)
- **AI**: OpenAI, Anthropic, Google Vertex AI
- **Security**: Pydantic validation + rate limiting
- **Execution**: gVisor sandboxing
- **Real-time**: WebRTC + WebSocket support

### DevOps & Quality
- **Testing**: Vitest + Playwright + pytest
- **Linting**: ESLint + Ruff
- **Type Checking**: TypeScript + mypy
- **CI/CD**: GitHub Actions
- **Deployment**: Vercel (frontend) + Fly.io (backend)
- **Monitoring**: OpenTelemetry + Jaeger

## 🔧 Configuration

### Environment Variables

#### Frontend (.env.local)
```env
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...

# API Keys
NEXT_PUBLIC_OPENAI_API_KEY=sk-...
NEXT_PUBLIC_GOOGLE_API_KEY=...

# Backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Backend (.env)
```env
# Application
ENVIRONMENT=development
DEBUG=true

# Authentication
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...

# AI Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...

# Security
RATE_LIMIT_REQUESTS_PER_MINUTE=60
```

## 🧪 Testing

### Frontend Tests
```bash
cd frontend
pnpm test          # Unit tests
pnpm test:e2e      # End-to-end tests
pnpm test:ui       # Visual regression tests
```

### Backend Tests
```bash
cd backend
pytest tests/ -v                 # All tests
pytest tests/unit/ -v           # Unit tests only
pytest tests/integration/ -v    # Integration tests
```

### Accessibility Testing
```bash
cd frontend
pnpm test:a11y    # Automated accessibility tests
```

## 📊 Performance

### Core Web Vitals Targets
- **LCP** (Largest Contentful Paint): < 2.5s
- **FID** (First Input Delay): < 100ms
- **CLS** (Cumulative Layout Shift): < 0.1

### Bundle Analysis
```bash
cd frontend
pnpm build:analyze
```

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes following CODE_CONSTITUTION.md
4. Run tests: `pnpm test && cd ../backend && pytest`
5. Commit with conventional format: `feat: add new feature`
6. Push and create a Pull Request

### Code Standards
- **Constitutional Compliance**: 100% adherence to CODE_CONSTITUTION.md
- **Type Safety**: 100% TypeScript coverage
- **Testing**: Minimum 99% coverage
- **File Size**: Maximum 400 lines per file
- **Documentation**: JSDoc for all public APIs

### Commit Convention
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

## 📄 License

**Constitutional License** - Governed by Vértice values and CODE_CONSTITUTION.md

This project is built with integrity, transparency, and user sovereignty as core principles.

## 🙏 Acknowledgments

- **Constituição Vértice v3.0** - Philosophical foundation
- **CODE_CONSTITUTION.md** - Engineering standards
- **Google Engineering Practices** - Technical excellence
- **Open Source Community** - Building blocks

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/vertice-chat-webapp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/vertice-chat-webapp/discussions)
- **Documentation**: [Internal Wiki](https://wiki.vertice.ai)

---

**Built with ❤️ by the Vertice Team**

*Empowering developers with AI since 2026*