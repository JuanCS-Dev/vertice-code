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

*Plan created: 2026-01-03*
*Research: Anthropic Claude, Google Gemini, Multilingual NLP 2025-2026*
*Author: Claude Opus 4.5*
