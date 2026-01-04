# NLU & Tool Orchestration Improvement Plan
## VERTICE - Natural Language Understanding Optimization

**Project:** Vertice-Code
**Date:** 2026-01-03
**Language Focus:** Brazilian Portuguese + English
**Goal:** Miraculous improvement in natural language understanding and automatic tool calling

---

## EXECUTIVE SUMMARY

This plan implements 7 phases to achieve excellent NLU for Brazilian Portuguese users, following 2025-2026 best practices from Anthropic (Claude) and Google (Gemini).

**Key Improvements:**
1. Portuguese keyword expansion (12 intents, 100+ keywords)
2. Anthropic's "think" tool for complex reasoning
3. Request amplification for vague inputs
4. Bilingual few-shot examples (PT-BR + EN)
5. Self-correction loops for tool execution
6. Localized error messages

---

## RESEARCH SOURCES (Web 2025-2026)

| Source | Key Insight |
|--------|-------------|
| [Anthropic Think Tool](https://www.anthropic.com/engineering/claude-think-tool) | "21.2 tool calls without human intervention (was 9.8)" |
| [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) | "Research and plan first improves performance" |
| [Gemini Function Calling](https://cloud.google.com/blog/products/ai-machine-learning/gemini-2-5-pro-flash-on-vertex-ai) | "tool_choice allow-list for injection resistance" |
| [Multilingual Prompt Engineering](https://arxiv.org/html/2505.11665v1) | "Crafted prompts extract knowledge across languages" |
| [Tool Calling Optimization](https://www.useparagon.com/learn/rag-best-practices-optimizing-tool-calling/) | "One-line reason before tool call boosts traceability" |

---

## CURRENT STATE ANALYSIS

### Files Identified

| Component | File | Lines | Issue |
|-----------|------|-------|-------|
| Intent Classifier | `vertice_cli/core/intent_classifier.py` | 122-167 | Only 14 PT keywords |
| Agent Router | `scripts/maestro/routing.py` | 1-83 | English-only |
| Semantic Router | `vertice_core/agents/router.py` | 121-282 | English examples only |
| Tool Search | `vertice_cli/tools/tool_search.py` | 65-106 | English keywords |
| Few-Shot Examples | `vertice_cli/prompts/few_shot_examples.py` | 1-100 | 13 EN examples, 0 PT |
| System Prompts | `vertice_cli/prompts/system_prompts.py` | 20-304 | No multilingual instruction |

### Current Limitations
- **No Portuguese support** in tool selection keywords
- **No "think" tool** for complex reasoning (Anthropic's key recommendation)
- **No request amplification** for vague inputs
- **Limited few-shot examples** (13 English, 0 Portuguese)
- **No self-correction loop** after tool execution

---

## PHASE 1: PORTUGUESE KEYWORD EXPANSION
**Priority:** CRITICAL | **Impact:** HIGH

### Task 1.1: Intent Classifier Keywords
**File:** `vertice_cli/core/intent_classifier.py`
**Lines:** 122-167 (HEURISTIC_PATTERNS)

Add Portuguese keywords to each intent:

```python
Intent.PLANNING: {
    "keywords": [
        # English (existing)
        "plan", "strategy", "roadmap", "goals", "design",
        # Portuguese (ADD)
        "plano", "planeja", "planejamento", "estrategia", "metas",
        "como fazer", "como implementar", "passo a passo", "etapas"
    ],
}

Intent.CODING: {
    "keywords": [
        "code", "implement", "create", "build", "write", "function",
        # Portuguese (ADD)
        "codigo", "implementar", "criar", "construir", "escrever",
        "funcao", "classe", "desenvolver", "programar", "fazer", "adicionar"
    ],
}

Intent.DEBUG: {
    "keywords": [
        "debug", "fix", "error", "bug", "issue", "problem",
        # Portuguese (ADD)
        "depurar", "corrigir", "erro", "problema", "falha",
        "consertar", "arrumar", "resolver", "nao funciona", "bugado"
    ],
}

# Continue for all 12 intents...
```

### Task 1.2: Maestro Routing Keywords
**File:** `scripts/maestro/routing.py`
**Function:** `route_to_agent()`

Add Portuguese patterns:

```python
# PRIORITY: Testing (ADD Portuguese)
if any(w in p for w in ['unit test', 'integration test', 'test case',
                         'teste unitario', 'teste de integracao', 'caso de teste']):
    return 'testing'

# PRIORITY: Code search (ADD Portuguese)
if any(w in p for w in ['find', 'search', 'locate', 'where',
                         'encontrar', 'buscar', 'localizar', 'onde', 'achar']):
    return 'explorer'
```

### Task 1.3: Tool Search Keywords
**File:** `vertice_cli/tools/tool_search.py`
**Lines:** 65-106 (CAPABILITY_KEYWORDS)

```python
"file_read": {
    "keywords": [
        "read", "view", "show", "display", "content",
        # Portuguese (ADD)
        "ler", "ver", "mostrar", "exibir", "conteudo", "abrir"
    ],
},
"file_write": {
    "keywords": [
        "write", "create", "save", "modify", "edit",
        # Portuguese (ADD)
        "escrever", "criar", "salvar", "modificar", "editar", "alterar"
    ],
},
```

---

## PHASE 2: THINK TOOL IMPLEMENTATION
**Priority:** HIGH | **Impact:** HIGH

Following Anthropic's 2025 recommendation for agentic workflows.

### Task 2.1: Create Think Tool
**New File:** `vertice_cli/tools/think_tool.py`

```python
"""
Think Tool - Extended Reasoning for Complex Tasks.
Implements Anthropic's 2025 "think" tool pattern.
"""

class ThinkTool(Tool):
    def __init__(self):
        super().__init__()
        self.name = "think"
        self.category = ToolCategory.SYSTEM
        self.description = (
            "Use this tool to think through complex problems step-by-step. "
            "Analyze the request, consider approaches, plan actions before executing."
        )
        self.parameters = {
            "thought": {
                "type": "string",
                "description": "Step-by-step reasoning: 1) Understanding, 2) Approaches, 3) Decision, 4) Risks",
                "required": True,
            }
        }

    async def _execute_validated(self, thought: str) -> ToolResult:
        return ToolResult(
            success=True,
            data="Thought recorded. Proceed with planned approach.",
            metadata={"thought_length": len(thought), "internal": True}
        )
```

### Task 2.2: Register Think Tool
**File:** `vertice_cli/tools/registry_setup.py`

```python
from .think_tool import ThinkTool
registry.register(ThinkTool())
```

### Task 2.3: System Prompt Integration
**File:** `vertice_cli/prompts/system_prompts.py`

Add think tool guidance:

```python
THINK_TOOL_GUIDANCE = """
## THINK TOOL - Extended Reasoning

For complex tasks, use the `think` tool BEFORE other tools:

WHEN TO THINK:
- Multi-step operations (3+ tools)
- Ambiguous requests needing interpretation
- Tasks with potential side effects
- When unsure about parameters

EXAMPLE:
User: "organize my project files"

Call think tool FIRST:
{"tool": "think", "args": {"thought": "User wants to organize files. Options: 1) Move by type, 2) Create directories, 3) Rename. I'll first list files to understand state."}}

THEN proceed with file operations.
"""
```

---

## PHASE 3: BILINGUAL FEW-SHOT EXAMPLES
**Priority:** HIGH | **Impact:** HIGH

### Task 3.1: Add Portuguese Examples
**File:** `vertice_cli/prompts/few_shot_examples.py`

```python
FEW_SHOT_EXAMPLES_PTBR = [
    # File reading
    {
        "user": "mostra o README",
        "assistant": '[{"tool": "readfile", "args": {"path": "README.md"}}]',
        "category": "file_reading"
    },
    {
        "user": "o que tem no config.py?",
        "assistant": '[{"tool": "readfile", "args": {"path": "config.py"}}]',
        "category": "file_reading"
    },
    # Search
    {
        "user": "encontre todos os TODO nos arquivos python",
        "assistant": '[{"tool": "searchfiles", "args": {"pattern": "TODO", "file_pattern": "*.py"}}]',
        "category": "search"
    },
    {
        "user": "onde esta a funcao calculate_total?",
        "assistant": '[{"tool": "grep", "args": {"pattern": "def calculate_total"}}]',
        "category": "search"
    },
    # Git
    {
        "user": "qual o status do git?",
        "assistant": '[{"tool": "gitstatus", "args": {}}]',
        "category": "git"
    },
    {
        "user": "commita as alteracoes com mensagem 'fix bug'",
        "assistant": '[{"tool": "bashcommand", "args": {"command": "git add -A && git commit -m \\"fix bug\\""}}]',
        "category": "git"
    },
    # File creation
    {
        "user": "crie um arquivo utils.py com hello world",
        "assistant": '[{"tool": "writefile", "args": {"path": "utils.py", "content": "def hello():\\n    print(\\"Hello!\\")\\n"}}]',
        "category": "file_writing"
    },
    # Questions (no tool)
    {
        "user": "como funciona o decorador @property?",
        "assistant": "O decorador `@property` transforma um metodo em atributo somente-leitura...",
        "category": "explanation"
    },
]

def get_bilingual_examples(user_input: str, max_examples: int = 5) -> list:
    """Get examples based on detected language."""
    # Simple Portuguese detection
    pt_indicators = ["que", "como", "para", "nao", "isso", "fazer", "qual"]
    is_portuguese = any(w in user_input.lower() for w in pt_indicators)

    if is_portuguese:
        return FEW_SHOT_EXAMPLES_PTBR[:max_examples]
    return FEW_SHOT_EXAMPLES[:max_examples]
```

---

## PHASE 4: REQUEST AMPLIFICATION
**Priority:** HIGH | **Impact:** MEDIUM

### Task 4.1: Create Request Amplifier
**New File:** `vertice_cli/core/request_amplifier.py`

```python
"""
Request Amplifier - Enriches vague requests with context.
"""

@dataclass
class AmplifiedRequest:
    original: str
    amplified: str
    detected_intent: str
    confidence: float
    missing_details: List[str]
    suggested_questions: List[str]

class RequestAmplifier:
    # Patterns indicating vague requests
    VAGUE_PATTERNS = [
        (r'^.{1,15}$', 'short_request'),
        (r'\b(isso|isto|this|that|it)\b', 'ambiguous_reference'),
        (r'^(faz|faca|do|make|fix)\s+', 'vague_verb'),
    ]

    def analyze(self, request: str) -> AmplifiedRequest:
        """Analyze and amplify a request."""
        vagueness = self._detect_vagueness(request)
        intent, confidence = self._infer_intent(request)
        missing = self._identify_missing_details(request, intent)
        questions = self._generate_questions(missing)
        amplified = self._amplify(request)

        return AmplifiedRequest(
            original=request,
            amplified=amplified,
            detected_intent=intent,
            confidence=confidence,
            missing_details=missing,
            suggested_questions=questions
        )

    def _generate_questions(self, missing: List[str]) -> List[str]:
        """Generate clarifying questions."""
        templates = {
            "file_target": "Em qual arquivo devo fazer isso?",
            "specific_change": "O que exatamente devo modificar?",
            "error_description": "Qual a mensagem de erro completa?",
        }
        return [templates.get(m, "") for m in missing[:3] if m in templates]
```

### Task 4.2: Integrate with Tool Handler
**File:** `vertice_cli/handlers/tool_execution_handler.py`

Add amplification step before tool execution.

---

## PHASE 5: ORCHESTRATION ENHANCEMENT
**Priority:** MEDIUM | **Impact:** MEDIUM

### Task 5.1: Self-Correction Loop
**File:** `vertice_cli/handlers/tool_execution_handler.py`

```python
async def execute_with_self_correction(
    self, tool_calls: List[Dict], max_corrections: int = 2
) -> str:
    """Execute tools with self-correction loop."""
    for attempt in range(max_corrections + 1):
        results = await self.execute_tool_calls(tool_calls)

        validation = self._validate_results(results)
        if validation.success:
            return results

        if attempt < max_corrections:
            corrective = await self._generate_correction(validation.issues)
            if corrective:
                tool_calls = corrective
                continue

        return f"{results}\n\n[Warning: {validation.issues}]"
```

### Task 5.2: Pre-Execution Planning
Add think step for complex tasks (3+ tools or low confidence).

---

## PHASE 6: MULTILINGUAL PROMPTS
**Priority:** MEDIUM | **Impact:** MEDIUM

### Task 6.1: System Prompt Multilingual Section
**File:** `vertice_cli/prompts/system_prompts.py`

```python
MULTILINGUAL_INSTRUCTION = """
## MULTILINGUAL SUPPORT

Respond in the user's language:
- Portuguese input -> Portuguese response
- English input -> English response
- Tool names always in English (API calls)

EXAMPLES:
- User: "mostra main.py" -> Portuguese response, use "readfile"
- User: "show main.py" -> English response, use "readfile"

Portuguese Command Patterns:
- "mostra/mostre" -> read/show
- "cria/crie" -> create
- "edita/edite" -> edit
- "busca/busque" -> search
- "roda/rode" -> execute
"""
```

---

## PHASE 7: ERROR LOCALIZATION
**Priority:** LOW | **Impact:** LOW

### Task 7.1: Localized Error Messages
**New File:** `vertice_cli/core/error_messages.py`

```python
ERROR_MESSAGES = {
    "file_not_found": {
        "en": "File not found: {path}. Search for similar files?",
        "pt": "Arquivo nao encontrado: {path}. Buscar arquivos similares?",
    },
    "tool_not_found": {
        "en": "Unknown tool: {tool}",
        "pt": "Ferramenta desconhecida: {tool}",
    },
    "ambiguous_request": {
        "en": "I'm not sure what you mean. Could you clarify?",
        "pt": "Nao tenho certeza do que voce quer. Pode esclarecer?",
    },
}
```

---

## IMPLEMENTATION SEQUENCE

| Phase | Task | Files | Priority | Est. Time |
|-------|------|-------|----------|-----------|
| 1.1 | Intent keywords PT | `intent_classifier.py` | CRITICAL | 1h |
| 1.2 | Routing keywords PT | `routing.py` | CRITICAL | 30min |
| 1.3 | Tool search keywords PT | `tool_search.py` | CRITICAL | 30min |
| 2.1 | Create think tool | `think_tool.py` (NEW) | HIGH | 1h |
| 2.2 | Register think tool | `registry_setup.py` | HIGH | 15min |
| 2.3 | Think prompt guidance | `system_prompts.py` | HIGH | 30min |
| 3.1 | PT-BR examples | `few_shot_examples.py` | HIGH | 1h |
| 4.1 | Request amplifier | `request_amplifier.py` (NEW) | HIGH | 2h |
| 4.2 | Integrate amplifier | `tool_execution_handler.py` | HIGH | 1h |
| 5.1 | Self-correction loop | `tool_execution_handler.py` | MEDIUM | 1h |
| 6.1 | Multilingual prompts | `system_prompts.py` | MEDIUM | 30min |
| 7.1 | Error localization | `error_messages.py` (NEW) | LOW | 1h |

**Total Estimated Time:** ~10 hours

---

## TESTING STRATEGY

### Portuguese NLU Test Cases

```python
PORTUGUESE_TEST_CASES = [
    ("mostra o arquivo main.py", "readfile", {"path": "main.py"}),
    ("o que tem no config.yaml?", "readfile", {"path": "config.yaml"}),
    ("onde esta a funcao calculate?", "grep", {"pattern": "def calculate"}),
    ("qual o status do git?", "gitstatus", {}),
    ("crie um arquivo test.py", "writefile", {"path": "test.py"}),
    ("busque todos os TODO", "searchfiles", {"pattern": "TODO"}),
]
```

### Target Metrics

| Metric | Target | Current (Est.) |
|--------|--------|----------------|
| PT Intent Accuracy | 95% | 60% |
| Tool Selection Accuracy | 90% | 75% |
| First-Attempt Success | 85% | 70% |
| Clarification Rate | <15% | 30% |

---

## CRITICAL FILES SUMMARY

1. **`vertice_cli/core/intent_classifier.py:122-167`** - Portuguese keywords
2. **`scripts/maestro/routing.py`** - Agent routing keywords
3. **`vertice_cli/tools/tool_search.py:65-106`** - Tool capability keywords
4. **`vertice_cli/prompts/few_shot_examples.py`** - Bilingual examples
5. **`vertice_cli/prompts/system_prompts.py`** - Multilingual instruction
6. **`vertice_cli/handlers/tool_execution_handler.py`** - Orchestration
7. **`vertice_cli/tools/think_tool.py`** (NEW) - Think tool
8. **`vertice_cli/core/request_amplifier.py`** (NEW) - Amplification
9. **`vertice_cli/core/error_messages.py`** (NEW) - Localization

---

# QUALITY AUDIT REPORT (2026-01-03)

## Audit Summary

| Component | Quality Score | Status |
|-----------|---------------|--------|
| **Keywords PT-BR** | 5.3/10 | ⚠️ Incomplete |
| **Think Tool** | 3/10 | 🔴 Placeholder |
| **Request Amplifier** | 3.5/10 | 🔴 Stub |
| **Few-Shot Examples** | 7/10 | ✅ OK |
| **Self-Correction** | 6/10 | ⚠️ Partial |
| **OVERALL** | **4.9/10** | 🔴 Needs Work |

## Critical Issues Found

### Issue 1: Think Tool is Placeholder (3/10)
- `_execute_validated()` returns static string
- NEVER auto-invoked for complex tasks
- Zero complexity detection
- Output not used for tool selection

### Issue 2: Request Amplifier is Stub (3.5/10)
- `_amplify()` returns original unchanged
- No context injection (cwd, git, files)
- Only 2/12 intents handled in `_identify_missing_details()`
- Clarifying questions generated but NEVER shown

### Issue 3: Keywords PT-BR Incomplete (5.3/10)
- Missing imperative forms (mostra, faz, busca)
- Missing accented versions (função, documentação)
- `routing.py` has only 5 PT words (needs 50+)
- No colloquialisms (dá uma olhada, roda isso)

---

## PHASE 8: REQUEST AMPLIFIER FIX
**Priority:** P0 CRITICAL | **Impact:** HIGH

### Task 8.1: Implement Real Amplification
**File:** `vertice_cli/core/request_amplifier.py`

**Current (BROKEN):**
```python
def _amplify(self, request: str) -> str:
    # Placeholder for more complex amplification logic
    return request  # RETURNS UNCHANGED!
```

**Fix - Full Implementation:**
```python
def __init__(self, context: Optional[Dict] = None):
    """Initialize with optional context."""
    self.classifier = SemanticIntentClassifier()
    self.context = context or {}

def _amplify(self, request: str) -> str:
    """
    Amplify request with contextual information.

    Adds:
    - Current working directory
    - Recently modified files
    - Git status hints
    - Inferred targets from context
    """
    parts = [request]

    # Add CWD context
    if cwd := self.context.get('cwd'):
        parts.append(f"[Context: Working in {cwd}]")

    # Add recent files if relevant
    if recent := self.context.get('recent_files', []):
        if self._mentions_file(request):
            candidates = ', '.join(recent[:3])
            parts.append(f"[Recent files: {candidates}]")

    # Add git context for git-related requests
    if self._is_git_request(request):
        if branch := self.context.get('git_branch'):
            parts.append(f"[Git branch: {branch}]")
        if modified := self.context.get('modified_files', []):
            files = ', '.join(modified[:5])
            parts.append(f"[Modified: {files}]")

    return ' '.join(parts)

def _mentions_file(self, request: str) -> bool:
    """Check if request mentions files."""
    file_words = ['file', 'arquivo', 'read', 'ler', 'show', 'mostra',
                  'edit', 'edita', 'write', 'escreve', '.py', '.js', '.ts']
    return any(w in request.lower() for w in file_words)

def _is_git_request(self, request: str) -> bool:
    """Check if request is git-related."""
    git_words = ['git', 'commit', 'push', 'pull', 'branch', 'merge',
                 'status', 'diff', 'log', 'commita', 'pusha']
    return any(w in request.lower() for w in git_words)
```

### Task 8.2: Inject Context into Amplifier
**File:** `vertice_cli/handlers/tool_execution_handler.py`

**Current (NO CONTEXT):**
```python
amplifier = RequestAmplifier()  # No context!
amplified_req = await amplifier.analyze(user_input)
```

**Fix:**
```python
# Build context from shell state
amplifier_context = {
    'cwd': self.context.cwd,
    'recent_files': list(self.context.read_files)[-5:],
    'modified_files': list(self.context.modified_files),
    'git_branch': self.context.git_branch,
}

amplifier = RequestAmplifier(context=amplifier_context)
amplified_req = await amplifier.analyze(user_input)

# Log amplification for debugging
if amplified_req.amplified != user_input:
    logger.debug(f"Amplified: {amplified_req.amplified}")
```

### Task 8.3: Expand Missing Details for All Intents
**File:** `vertice_cli/core/request_amplifier.py`

```python
# Intent-specific missing detail patterns
INTENT_REQUIREMENTS = {
    "coding": {
        "required": ["file_target"],
        "patterns": ["file", "arquivo", ".py", ".js", "module"],
    },
    "debug": {
        "required": ["error_description"],
        "patterns": ["error", "erro", "stack", "traceback"],
    },
    "refactor": {
        "required": ["refactor_scope", "file_target"],
        "patterns": ["class", "function", "module", "classe", "funcao"],
    },
    "test": {
        "required": ["test_target"],
        "patterns": ["test", "teste", "spec", "coverage"],
    },
    "planning": {
        "required": ["scope", "deliverables"],
        "patterns": ["goal", "objetivo", "milestone", "deadline"],
    },
    "review": {
        "required": ["review_target"],
        "patterns": ["file", "pr", "commit", "change"],
    },
    "docs": {
        "required": ["doc_target"],
        "patterns": ["readme", "docstring", "api", "guide"],
    },
    "explore": {
        "required": [],  # Exploration can be open-ended
        "patterns": [],
    },
    "architecture": {
        "required": ["component"],
        "patterns": ["system", "design", "module", "service"],
    },
    "performance": {
        "required": ["target_area"],
        "patterns": ["slow", "lento", "optimize", "profile"],
    },
    "security": {
        "required": ["security_scope"],
        "patterns": ["vulnerability", "auth", "injection", "xss"],
    },
    "general": {
        "required": [],
        "patterns": [],
    },
}

def _identify_missing_details(self, request: str, intent: str) -> List[str]:
    """Identify missing details based on intent requirements."""
    missing = []
    lower_req = request.lower()

    requirements = self.INTENT_REQUIREMENTS.get(intent, {})
    patterns = requirements.get("patterns", [])
    required = requirements.get("required", [])

    # Check if any required pattern is present
    has_specifics = any(p in lower_req for p in patterns)

    if not has_specifics and required:
        missing.extend(required)

    return missing
```

### Task 8.4: Show Clarifying Questions to User
**File:** `vertice_cli/handlers/tool_execution_handler.py`

```python
async def process_tool_calls(self, user_input: str) -> str:
    """Process with clarification support."""

    amplified_req = await amplifier.analyze(user_input)

    # If confidence is low and we have questions, ASK USER
    if amplified_req.confidence < 0.6 and amplified_req.suggested_questions:
        # Present questions to user
        self.console.print("[yellow]Preciso de mais detalhes:[/yellow]")
        for q in amplified_req.suggested_questions:
            self.console.print(f"  • {q}")

        # Return early - user needs to clarify
        return "Aguardando esclarecimento..."

    # Proceed with execution
    final_input = amplified_req.amplified
    # ... rest of execution
```

---

## PHASE 9: THINK TOOL ACTIVATION
**Priority:** P0 CRITICAL | **Impact:** HIGH

### Task 9.1: Create Complexity Analyzer
**New File:** `vertice_cli/core/complexity_analyzer.py`

```python
"""
Complexity Analyzer - Determines when to invoke think tool.

Based on Anthropic's 2025 research showing 21.2 vs 9.8 tool calls
with think-first approach.
"""

import re
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class ComplexityResult:
    score: float  # 0.0 to 1.0
    reasons: List[str]
    should_think: bool
    estimated_tools: int

class ComplexityAnalyzer:
    """Analyze request complexity to determine if think tool needed."""

    # Patterns indicating multi-step operations
    MULTI_STEP_PATTERNS = [
        (r'\b(and|e|then|depois|also|tambem)\b', 0.2, 'conjunction'),
        (r'\b(first|primeiro|next|proximo|finally|finalmente)\b', 0.3, 'sequence'),
        (r'\b(all|todos|every|cada|multiple|multiplos)\b', 0.2, 'plural_scope'),
        (r'\b(if|se|when|quando|unless|unless)\b', 0.15, 'conditional'),
    ]

    # Patterns indicating destructive/risky operations
    RISKY_PATTERNS = [
        (r'\b(delete|remove|apagar|deletar|rm)\b', 0.3, 'destructive'),
        (r'\b(push|deploy|publish|publicar)\b', 0.25, 'irreversible'),
        (r'\b(rename|renomear|move|mover)\b', 0.15, 'file_operation'),
        (r'\b(refactor|rewrite|restructure)\b', 0.2, 'large_change'),
    ]

    # Patterns indicating ambiguity
    AMBIGUITY_PATTERNS = [
        (r'^.{1,20}$', 0.2, 'short_request'),
        (r'\b(something|algo|stuff|coisa)\b', 0.25, 'vague_reference'),
        (r'\b(better|melhor|improve|melhorar)\b', 0.15, 'subjective'),
        (r'\?.*\?', 0.2, 'multiple_questions'),
    ]

    THINK_THRESHOLD = 0.5

    def analyze(self, request: str) -> ComplexityResult:
        """Analyze request and determine complexity."""
        score = 0.0
        reasons = []

        # Check multi-step patterns
        for pattern, weight, reason in self.MULTI_STEP_PATTERNS:
            if re.search(pattern, request, re.IGNORECASE):
                score += weight
                reasons.append(f"multi-step: {reason}")

        # Check risky patterns
        for pattern, weight, reason in self.RISKY_PATTERNS:
            if re.search(pattern, request, re.IGNORECASE):
                score += weight
                reasons.append(f"risky: {reason}")

        # Check ambiguity patterns
        for pattern, weight, reason in self.AMBIGUITY_PATTERNS:
            if re.search(pattern, request, re.IGNORECASE):
                score += weight
                reasons.append(f"ambiguous: {reason}")

        # Estimate tool count based on complexity
        estimated_tools = max(1, int(1 + score * 5))

        # Normalize score
        score = min(1.0, score)

        return ComplexityResult(
            score=score,
            reasons=reasons,
            should_think=score >= self.THINK_THRESHOLD,
            estimated_tools=estimated_tools
        )
```

### Task 9.2: Auto-Invoke Think for Complex Tasks
**File:** `vertice_cli/handlers/tool_execution_handler.py`

```python
from vertice_cli.core.complexity_analyzer import ComplexityAnalyzer

class ToolExecutionHandler:
    def __init__(self, shell):
        # ... existing init
        self.complexity_analyzer = ComplexityAnalyzer()

    async def process_tool_calls(self, user_input: str) -> str:
        """Process with automatic think invocation."""

        # Step 1: Analyze complexity
        complexity = self.complexity_analyzer.analyze(user_input)

        # Step 2: If complex, invoke think tool FIRST
        if complexity.should_think:
            self.console.print(
                f"[dim]Complex task detected (score={complexity.score:.2f}). "
                f"Thinking first...[/dim]"
            )

            # Generate thinking prompt
            think_prompt = self._generate_think_prompt(
                user_input,
                complexity.reasons,
                complexity.estimated_tools
            )

            # Execute think tool
            think_result = await self._execute_think(think_prompt)

            # Log the thought for debugging
            logger.info(f"Think result: {think_result}")

            # Include thinking in context for LLM
            enhanced_input = f"""
[THINKING COMPLETE]
{think_result}

[ORIGINAL REQUEST]
{user_input}

[INSTRUCTION]
Based on the thinking above, proceed with tool execution.
"""
            user_input = enhanced_input

        # Step 3: Continue with normal flow
        response = await self._get_llm_tool_response(user_input, turn)
        # ... rest of execution

    def _generate_think_prompt(
        self,
        request: str,
        reasons: List[str],
        estimated_tools: int
    ) -> str:
        """Generate structured thinking prompt."""
        return f"""
Analyze this request step-by-step:

REQUEST: {request}

COMPLEXITY SIGNALS: {', '.join(reasons)}
ESTIMATED TOOLS: {estimated_tools}

Think through:
1) UNDERSTANDING: What exactly is being asked?
2) APPROACH OPTIONS: What are 2-3 ways to accomplish this?
3) BEST APPROACH: Which approach is safest and most effective?
4) RISKS: What could go wrong? How to mitigate?
5) TOOL SEQUENCE: What tools in what order?

Provide concise analysis (max 200 words).
"""

    async def _execute_think(self, prompt: str) -> str:
        """Execute think tool and capture result."""
        from vertice_cli.tools.think_tool import ThinkTool

        think_tool = ThinkTool()
        result = await think_tool._execute_validated(thought=prompt)

        # For now, return the prompt as the "thought"
        # In future, this could involve LLM reasoning
        return prompt
```

### Task 9.3: Enhanced Think Tool with Structure
**File:** `vertice_cli/tools/think_tool.py`

```python
"""
Think Tool - Extended Reasoning for Complex Tasks.
Implements Anthropic's 2025 "think" tool pattern.

Enhanced version with structured output and validation.
"""

import re
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

from .base import Tool, ToolCategory, ToolResult

logger = logging.getLogger(__name__)

@dataclass
class ThoughtStructure:
    """Structured representation of thinking process."""
    understanding: str
    approaches: List[str]
    chosen_approach: str
    risks: List[str]
    tool_sequence: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "understanding": self.understanding,
            "approaches": self.approaches,
            "chosen_approach": self.chosen_approach,
            "risks": self.risks,
            "tool_sequence": self.tool_sequence,
        }

class ThinkTool(Tool):
    """
    Think Tool for extended reasoning before complex operations.

    Following Anthropic's 2025 research:
    - 21.2 tool calls without human intervention (was 9.8)
    - Significantly reduces errors on multi-step tasks
    """

    def __init__(self):
        super().__init__()
        self.name = "think"
        self.category = ToolCategory.SYSTEM
        self.description = (
            "Use this tool to think through complex problems step-by-step. "
            "Analyze the request, consider approaches, plan actions before executing. "
            "REQUIRED for: multi-file changes, destructive operations, ambiguous requests."
        )
        self.parameters = {
            "thought": {
                "type": "string",
                "description": (
                    "Step-by-step reasoning following structure: "
                    "1) UNDERSTANDING, 2) APPROACHES, 3) DECISION, 4) RISKS, 5) TOOL_SEQUENCE"
                ),
                "required": True,
            }
        }

        # Metrics tracking
        self._invocation_count = 0
        self._total_thought_length = 0

    async def _execute_validated(self, thought: str) -> ToolResult:
        """
        Process and validate thought structure.

        Returns structured result that can inform subsequent tool selection.
        """
        self._invocation_count += 1
        self._total_thought_length += len(thought)

        # Try to parse structured sections
        structure = self._parse_thought_structure(thought)

        # Log for observability
        logger.info(
            f"Think tool invoked (#{self._invocation_count}): "
            f"{len(thought)} chars, "
            f"tools planned: {structure.tool_sequence if structure else 'unstructured'}"
        )

        if structure:
            return ToolResult(
                success=True,
                data={
                    "status": "Structured thinking complete",
                    "understanding": structure.understanding[:200],
                    "chosen_approach": structure.chosen_approach,
                    "tool_count": len(structure.tool_sequence),
                    "risks_identified": len(structure.risks),
                },
                metadata={
                    "thought_length": len(thought),
                    "internal": True,
                    "structured": True,
                    "full_structure": structure.to_dict(),
                }
            )
        else:
            return ToolResult(
                success=True,
                data={
                    "status": "Thinking complete (unstructured)",
                    "summary": thought[:300],
                },
                metadata={
                    "thought_length": len(thought),
                    "internal": True,
                    "structured": False,
                }
            )

    def _parse_thought_structure(self, thought: str) -> Optional[ThoughtStructure]:
        """Attempt to parse structured thought format."""
        try:
            sections = {}

            # Try to extract numbered sections
            patterns = {
                "understanding": r"(?:1\)|UNDERSTANDING:?)\s*(.+?)(?=(?:2\)|APPROACH|$))",
                "approaches": r"(?:2\)|APPROACH(?:ES)?:?)\s*(.+?)(?=(?:3\)|BEST|DECISION|$))",
                "chosen": r"(?:3\)|BEST|DECISION:?)\s*(.+?)(?=(?:4\)|RISK|$))",
                "risks": r"(?:4\)|RISK(?:S)?:?)\s*(.+?)(?=(?:5\)|TOOL|SEQUENCE|$))",
                "tools": r"(?:5\)|TOOL(?:S)?|SEQUENCE:?)\s*(.+?)$",
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, thought, re.IGNORECASE | re.DOTALL)
                if match:
                    sections[key] = match.group(1).strip()

            if len(sections) >= 3:  # At least 3 sections found
                return ThoughtStructure(
                    understanding=sections.get("understanding", ""),
                    approaches=self._parse_list(sections.get("approaches", "")),
                    chosen_approach=sections.get("chosen", ""),
                    risks=self._parse_list(sections.get("risks", "")),
                    tool_sequence=self._parse_list(sections.get("tools", "")),
                )
        except Exception as e:
            logger.warning(f"Failed to parse thought structure: {e}")

        return None

    def _parse_list(self, text: str) -> List[str]:
        """Parse bullet points or numbered items from text."""
        items = []
        # Try bullet points
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith(('-', '*', '•')):
                items.append(line[1:].strip())
            elif re.match(r'^\d+[\.\)]\s*', line):
                items.append(re.sub(r'^\d+[\.\)]\s*', '', line))
        return items if items else [text.strip()]

    def get_stats(self) -> Dict[str, Any]:
        """Get think tool usage statistics."""
        return {
            "invocations": self._invocation_count,
            "total_chars": self._total_thought_length,
            "avg_length": (
                self._total_thought_length / self._invocation_count
                if self._invocation_count > 0 else 0
            ),
        }
```

---

## PHASE 10: PORTUGUESE KEYWORDS ENHANCEMENT
**Priority:** P1 HIGH | **Impact:** MEDIUM

### Task 10.1: Add Imperative Forms
**File:** `vertice_cli/core/intent_classifier.py`

```python
# ENHANCED: Add imperative verb forms for each intent
HEURISTIC_PATTERNS = {
    Intent.PLANNING: {
        "keywords": [
            # English
            "plan", "strategy", "roadmap", "goals", "design",
            # PT Infinitive
            "plano", "planejamento", "estrategia", "metas",
            # PT Imperative (ADD)
            "planeja", "planeje", "faz um plano", "me planeja",
            # PT Colloquial (ADD)
            "como fazer", "como implementar", "passo a passo", "me ajuda a planejar",
        ],
        "weight": 2,
    },
    Intent.CODING: {
        "keywords": [
            "code", "implement", "create", "build", "write", "function",
            # PT existing
            "codigo", "implementar", "criar", "construir", "escrever",
            "funcao", "classe", "desenvolver", "programar",
            # PT Imperative (ADD)
            "cria", "crie", "implementa", "implemente", "escreve", "escreva",
            "faz", "faca", "adiciona", "adicione", "desenvolve", "desenvolva",
            # PT Colloquial (ADD)
            "me faz", "faz pra mim", "coda isso", "programa isso",
        ],
        "weight": 2,
    },
    Intent.DEBUG: {
        "keywords": [
            "debug", "fix", "error", "bug", "issue", "problem", "broken",
            # PT existing
            "depurar", "corrigir", "erro", "problema", "falha",
            # PT Imperative (ADD)
            "corrige", "corrija", "conserta", "conserte", "arruma", "arrume",
            "resolve", "resolva", "debuga",
            # PT Colloquial (ADD)
            "nao funciona", "ta bugado", "ta quebrado", "da erro",
            "nao ta funcionando", "quebrou", "bugou",
        ],
        "weight": 3,
    },
    Intent.EXPLORE: {
        "keywords": [
            "explore", "find", "search", "where", "show", "navigate", "locate",
            # PT existing
            "explorar", "encontrar", "buscar", "onde", "mostrar", "navegar", "localizar",
            # PT Imperative (ADD)
            "mostra", "mostre", "busca", "busque", "encontra", "encontre",
            "acha", "ache", "procura", "procure", "localiza", "localize",
            # PT Colloquial (ADD)
            "me mostra", "da uma olhada", "ve ai", "acha pra mim",
            "onde fica", "onde ta", "cadê",
        ],
        "weight": 2,
    },
    Intent.TEST: {
        "keywords": [
            "test", "tests", "pytest", "unittest", "coverage", "spec",
            # PT existing
            "teste", "testes", "testar", "cobertura",
            # PT Imperative (ADD)
            "testa", "teste", "roda o teste", "roda os testes",
            "executa o teste", "verifica a cobertura",
            # PT Colloquial (ADD)
            "roda isso", "testa isso", "ve se funciona",
        ],
        "weight": 3,
    },
    # ... continue for all 12 intents
}
```

### Task 10.2: Add Accented Versions
**File:** `vertice_cli/core/intent_classifier.py`

Create accent normalizer utility:

```python
import unicodedata

def normalize_text(text: str) -> str:
    """Normalize text by removing accents for matching."""
    # NFD decomposes characters (é -> e + ´)
    # Then filter out combining marks
    normalized = unicodedata.normalize('NFD', text)
    return ''.join(c for c in normalized if not unicodedata.combining(c))

def matches_keyword(text: str, keyword: str) -> bool:
    """Check if text matches keyword (accent-insensitive)."""
    text_norm = normalize_text(text.lower())
    keyword_norm = normalize_text(keyword.lower())
    return keyword_norm in text_norm

# Update HEURISTIC_PATTERNS to include accented versions
# Keywords with accents will match both with and without
ACCENTED_KEYWORDS = {
    "funcao": "função",
    "documentacao": "documentação",
    "analise": "análise",
    "codigo": "código",
    "seguranca": "segurança",
    "vulnerabilidade": "vulnerabilidade",
    "desempenho": "desempenho",
    "padrao": "padrão",
    "diretorio": "diretório",
    "conteudo": "conteúdo",
}
```

### Task 10.3: Expand Routing Keywords
**File:** `scripts/maestro/routing.py`

```python
def route_to_agent(prompt: str) -> str:
    """Intelligent routing with full Portuguese support."""
    p = prompt.lower()

    # Normalize accents for matching
    p_norm = normalize_text(p)

    # PRIORITY 1: Testing
    if any(w in p_norm for w in [
        'unit test', 'integration test', 'test case', 'write test', 'generate test',
        # PT (EXPANDED)
        'teste unitario', 'teste de integracao', 'caso de teste',
        'escreve teste', 'cria teste', 'testa', 'roda teste', 'roda os testes',
    ]):
        return 'testing'

    # PRIORITY 2: Documentation
    if any(w in p_norm for w in [
        'write doc', 'api doc', 'docstring', 'readme', 'document',
        # PT (EXPANDED)
        'documenta', 'documentacao', 'escreve doc', 'cria readme',
        'adiciona docstring', 'explica o codigo',
    ]):
        return 'documentation'

    # PRIORITY 3: DevOps
    if any(w in p_norm for w in [
        'deploy', 'docker', 'kubernetes', 'k8s', 'pipeline', 'ci/cd',
        # PT (ADD)
        'faz deploy', 'deploya', 'sobe pra producao', 'cria container',
        'configura pipeline', 'automatiza',
    ]):
        return 'devops'

    # PRIORITY 4: Data
    if any(w in p_norm for w in [
        'database', 'schema', 'query', 'sql', 'migration', 'table',
        # PT (ADD)
        'banco de dados', 'esquema', 'consulta', 'migracao', 'tabela',
    ]):
        return 'data'

    # PRIORITY 5: Review
    if any(w in p_norm for w in [
        'review', 'audit', 'grade', 'lint', 'analyze',
        # PT (ADD)
        'revisa', 'revisao', 'audita', 'analisa', 'verifica qualidade',
        'da uma olhada', 'critica', 'avalia',
    ]):
        return 'reviewer'

    # PRIORITY 6: Refactor
    if any(w in p_norm for w in [
        'refactor', 'rename', 'extract', 'inline', 'modernize', 'clean up',
        # PT (ADD)
        'refatora', 'renomeia', 'extrai', 'limpa', 'moderniza',
        'melhora o codigo', 'simplifica', 'reestrutura',
    ]):
        return 'refactorer'

    # PRIORITY 7: Explorer
    if any(w in p_norm for w in [
        'explore', 'map', 'graph', 'blast radius', 'dependencies', 'structure',
        'find', 'search', 'locate', 'where',
        # PT (ADD)
        'encontrar', 'buscar', 'localizar', 'onde', 'achar',
        'mostra estrutura', 'mapeia', 'explora', 'procura',
        'onde fica', 'cade', 'acha',
    ]):
        return 'explorer'

    # PRIORITY 8: Architecture
    if any(w in p_norm for w in [
        'architecture', 'system design', 'architect', 'uml', 'diagram',
        # PT (ADD)
        'arquitetura', 'design de sistema', 'diagrama', 'componente',
        'estrutura do sistema',
    ]):
        return 'architect'

    # PRIORITY 9: Security
    if any(w in p_norm for w in [
        'security', 'vulnerability', 'exploit', 'cve', 'owasp', 'injection',
        # PT (ADD)
        'seguranca', 'vulnerabilidade', 'ataque', 'injecao',
        'verifica seguranca', 'acha vulnerabilidade',
    ]):
        return 'security'

    # PRIORITY 10: Performance
    if any(w in p_norm for w in [
        'performance', 'bottleneck', 'profil', 'benchmark', 'slow', 'latency',
        # PT (ADD)
        'desempenho', 'lento', 'otimiza', 'perfil', 'latencia',
        'ta lento', 'demora muito', 'melhora performance',
    ]):
        return 'performance'

    # PRIORITY 11: Planning
    if any(w in p_norm for w in [
        'plan', 'strategy', 'roadmap', 'break down', 'how to',
        # PT (ADD)
        'plano', 'estrategia', 'roteiro', 'como fazer', 'me ajuda a planejar',
    ]) and 'deploy' not in p:
        return 'planner'

    # Default: Executor
    return 'executor'
```

---

## PHASE 11: INTEGRATION TESTS
**Priority:** P2 MEDIUM | **Impact:** MEDIUM

### Task 11.1: NLU Quality Tests
**New File:** `tests/nlu/test_nlu_quality.py`

```python
"""
NLU Quality Tests - Validate Portuguese understanding.

Tests cover:
- Intent classification accuracy
- Tool selection accuracy
- Amplification effectiveness
- Think tool triggering
"""

import pytest
from vertice_cli.core.intent_classifier import SemanticIntentClassifier, Intent
from vertice_cli.core.request_amplifier import RequestAmplifier
from vertice_cli.core.complexity_analyzer import ComplexityAnalyzer

class TestPortugueseIntents:
    """Test Portuguese intent classification."""

    @pytest.fixture
    def classifier(self):
        return SemanticIntentClassifier()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("input_text,expected_intent", [
        # Explore
        ("mostra o arquivo main.py", Intent.EXPLORE),
        ("onde fica a funcao calculate?", Intent.EXPLORE),
        ("busca todos os TODO", Intent.EXPLORE),
        ("me mostra a estrutura do projeto", Intent.EXPLORE),

        # Coding
        ("cria uma funcao de validacao", Intent.CODING),
        ("implementa o endpoint de login", Intent.CODING),
        ("faz um componente de botao", Intent.CODING),
        ("adiciona um metodo na classe User", Intent.CODING),

        # Debug
        ("corrige o erro no login", Intent.DEBUG),
        ("ta bugado o formulario", Intent.DEBUG),
        ("nao ta funcionando o upload", Intent.DEBUG),
        ("resolve o problema de memoria", Intent.DEBUG),

        # Test
        ("roda os testes", Intent.TEST),
        ("cria teste unitario pro UserService", Intent.TEST),
        ("verifica a cobertura de testes", Intent.TEST),

        # Refactor
        ("refatora essa funcao", Intent.REFACTOR),
        ("limpa o codigo do modulo auth", Intent.REFACTOR),
        ("melhora a estrutura da classe", Intent.REFACTOR),
    ])
    async def test_portuguese_intent_classification(
        self, classifier, input_text, expected_intent
    ):
        result = await classifier.classify(input_text)
        assert result.intent == expected_intent, (
            f"Expected {expected_intent} for '{input_text}', "
            f"got {result.intent} (confidence: {result.confidence})"
        )


class TestComplexityAnalyzer:
    """Test complexity detection for think tool triggering."""

    @pytest.fixture
    def analyzer(self):
        return ComplexityAnalyzer()

    @pytest.mark.parametrize("input_text,should_think", [
        # Simple tasks - should NOT think
        ("mostra o README", False),
        ("qual o status do git?", False),
        ("ler config.py", False),

        # Complex tasks - SHOULD think
        ("refatora todos os arquivos e roda os testes", True),
        ("deleta os arquivos antigos e depois faz commit", True),
        ("primeiro busca os TODOs, depois cria issues pra cada um", True),
        ("se tiver erros, corrige. se nao, faz deploy", True),

        # Risky tasks - SHOULD think
        ("apaga todos os arquivos .pyc", True),
        ("faz push pro main", True),
        ("renomeia todas as funcoes que comecam com get_", True),
    ])
    def test_complexity_detection(self, analyzer, input_text, should_think):
        result = analyzer.analyze(input_text)
        assert result.should_think == should_think, (
            f"Expected should_think={should_think} for '{input_text}', "
            f"got {result.should_think} (score: {result.score})"
        )


class TestRequestAmplifier:
    """Test request amplification with context."""

    @pytest.fixture
    def amplifier_with_context(self):
        context = {
            'cwd': '/home/user/project',
            'recent_files': ['main.py', 'utils.py', 'config.py'],
            'modified_files': ['auth.py'],
            'git_branch': 'feature/login',
        }
        return RequestAmplifier(context=context)

    @pytest.mark.asyncio
    async def test_git_context_injection(self, amplifier_with_context):
        result = await amplifier_with_context.analyze("commita as alteracoes")

        assert "feature/login" in result.amplified
        assert "auth.py" in result.amplified

    @pytest.mark.asyncio
    async def test_file_context_injection(self, amplifier_with_context):
        result = await amplifier_with_context.analyze("mostra o arquivo")

        assert "main.py" in result.amplified or "Recent files" in result.amplified

    @pytest.mark.asyncio
    async def test_low_confidence_generates_questions(self, amplifier_with_context):
        result = await amplifier_with_context.analyze("faz isso")

        assert result.confidence < 0.7
        assert len(result.suggested_questions) > 0
```

---

## REVISED IMPLEMENTATION SEQUENCE

| Phase | Task | Files | Priority | Est. Time |
|-------|------|-------|----------|-----------|
| **8.1** | Implement _amplify() | `request_amplifier.py` | P0 | 2h |
| **8.2** | Inject context | `tool_execution_handler.py` | P0 | 1h |
| **8.3** | Expand missing details | `request_amplifier.py` | P0 | 1h |
| **8.4** | Show clarifying questions | `tool_execution_handler.py` | P0 | 1h |
| **9.1** | Complexity analyzer | `complexity_analyzer.py` (NEW) | P0 | 2h |
| **9.2** | Auto-invoke think | `tool_execution_handler.py` | P0 | 2h |
| **9.3** | Enhanced think tool | `think_tool.py` | P0 | 1h |
| **10.1** | Imperative forms | `intent_classifier.py` | P1 | 1h |
| **10.2** | Accent normalizer | `intent_classifier.py` | P1 | 30min |
| **10.3** | Routing keywords | `routing.py` | P1 | 1h |
| **11.1** | NLU quality tests | `test_nlu_quality.py` (NEW) | P2 | 2h |

**Total New Phases:** ~14.5 hours

---

## SUCCESS METRICS (Revised)

| Metric | Current | After Phase 8-11 | Target |
|--------|---------|------------------|--------|
| PT Intent Accuracy | 60% | 90% | 95% |
| Tool Selection Accuracy | 75% | 88% | 90% |
| Think Tool Trigger Rate | 0% | 80% | 85% |
| Amplification Value-Add | 0% | 70% | 80% |
| First-Attempt Success | 70% | 82% | 85% |

---

*Quality Audit: 2026-01-03*
*New Phases Added: 8, 9, 10, 11*
*Author: Claude Opus 4.5*
