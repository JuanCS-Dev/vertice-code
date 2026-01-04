# P2 Tool Optimization Research
## Date: 2026-01-03
## Model: Gemini 2.5 Pro

---

# PART 1: CURRENT STATE ANALYSIS

## Issue #1: Git Diff Truncation Without Indicator
**File**: `vertice_cli/tools/git/inspect_tools.py:391`
```python
"diff": result.data[:10000] if not stat_only else None,  # NO INDICATOR
```
**Problem**: Silently truncates to 10KB, user doesn't know diff is incomplete

## Issue #2: AskUserQuestion No Response Mechanism
**File**: `vertice_cli/tools/parity/interaction_tools.py:34-202`
- `answer_question()` is class method (line 188), NOT a tool
- `get_pending_questions()` is class method (line 180), NOT a tool
- LLM can ASK but cannot RETRIEVE answers programmatically

## Issue #3: Todo State Not Persisted
**File**: `vertice_cli/tools/parity/todo_tools.py:30-82`
```python
cls._instance._todos: List[Dict[str, Any]] = []  # LINE 45 - IN MEMORY ONLY
```
**Problem**: No save/load, lost on restart

## Issue #4: Memory Tools Not Registered
**File**: `vertice_cli/tools/parity/__init__.py:1-112`
- `get_claude_parity_tools()` missing memory tools
- `prometheus_tools.py` has `PrometheusMemoryQueryTool` but NOT in parity registry

## Issue #5: Schema Validation Too Lenient
**File**: `vertice_cli/tools/validated.py:101-127`
- `get_validators()` defaults to `{}` (line 33)
- Invalid status silently becomes "pending" (todo_tools.py:201)
- `self.parameters` schema NEVER validated against inputs

---

# PART 2: WEB 2026 BEST PRACTICES RESEARCH

## Input Validation (2025-2026 Standards)

### Source: [Scalify AI - Function Calling Best Practices](https://www.scalifiai.com/blog/function-calling-tool-call-best%20practices)
> "All inputs must be validated before processing. Bad data should never enter the system - garbage in, garbage out."

### Source: [Agenta - Structured Outputs Guide](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms)
> "Use jsonschema validation to catch ValidationErrors before execution."

### Source: [Martin Fowler - Function Calling LLMs](https://martinfowler.com/articles/function-call-LLM.html)
> "Type checking confirms every argument matches its required data type before execution."

## Output Validation

### Source: [Agenta](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms)
> "Output validators check the final response and ensure the answer follows a logical chain. If error found, system can self-correct by re-asking LLM with more context."

## Error Handling

### Source: [AI SDK - Tool Calling](https://ai-sdk.dev/docs/ai-sdk-core/tools-and-tool-calling)
> "When tool execution fails, add errors as tool-error content parts to enable automated LLM roundtrips."

### Source: [Vellum - LLM Agent Build Guide](https://www.vellum.ai/blog/the-ultimate-llm-agent-build-guide)
> "Use experimental_repairToolCall function to attempt repairs, including sending schema to stronger model."

## Schema Enforcement

### Source: [Agenta](https://agenta.ai/blog/the-guide-to-structured-outputs-and-function-calling-with-llms)
> "JSON parser breaks on unexpected field types. Application crashes because LLM renamed 'status' to 'current_state'. Solution: structured outputs that enforce consistent data formats from start."

## Security

### Source: [Runloop - Mastering LLM Function Calling](https://runloop.ai/blog/mastering-llm-function-calling-a-guide-to-enhancing-ai-capabilities)
> "Implement guardrails: validate all inputs/outputs, use execution safeguards like timeouts and security allowlists."

---

# PART 3: GEMINI 2.5 PRO SPECIFIC

## Source: [Spark Co - Mastering Google Gemini Function Calling 2025](https://sparkco.ai/blog/mastering-google-gemini-function-calling-in-2025)
> "Use structured schemas for tool calling patterns. Essential practices: detailed function names, parameter descriptions, automated function execution."

## Source: [Google Developers Blog - Gemini 2.5 Pro](https://developers.googleblog.com/en/gemini-2-5-pro-io-improved-coding-performance/)
> "New versions addressed: reducing errors in function calling, improving function calling trigger rates."

## Source: [Google AI - Function Calling](https://ai.google.dev/gemini-api/docs/function-calling)
> "Gemini 2.5 Pro uses internal 'thinking' process to reason through requests. Significantly improves function calling performance."

## Source: [Google Developers Blog - Building Agents](https://developers.googleblog.com/en/building-agents-google-gemini-open-source-frameworks/)
> "Advanced agentic patterns: self-correction, dynamic planning, and memory for more robust agents."

---

# PART 4: ACTIONABLE P2 FIXES

## Fix 1: Git Diff Truncation Indicator
**File**: `vertice_cli/tools/git/inspect_tools.py:388-398`
**Action**: Add `is_truncated`, `original_size` to response
```python
diff_content = result.data
is_truncated = len(diff_content) > 10000
return ToolResult(
    success=True,
    data={
        "diff": diff_content[:10000] if not stat_only else None,
        "is_truncated": is_truncated if not stat_only else False,
        "original_size": len(diff_content) if is_truncated else None,
        ...
    }
)
```

## Fix 2: Todo Persistence
**File**: `vertice_cli/tools/parity/todo_tools.py:30-82`
**Action**: Add save/load to session directory
- Add `_save_to_session()` method
- Add `_load_from_session()` method
- Call save on every update
- Call load on initialization

## Fix 3: Schema Validation Enforcement
**File**: `vertice_cli/tools/validated.py`
**Action**: Validate inputs against `self.parameters` schema
- Use jsonschema or manual validation
- Reject invalid types, don't silent-fix
- Log validation failures

## Fix 4: Memory Tools Registration
**File**: `vertice_cli/tools/parity/__init__.py`
**Action**: Import and register memory tools
```python
from vertice_cli.tools.prometheus_tools import PrometheusMemoryQueryTool
# Add to get_claude_parity_tools()
```

## Fix 5: AskUserQuestion Response (DEFER)
**Complexity**: HIGH - Requires async response mechanism
**Action**: Document limitation, defer to later phase

---

# EXECUTION PRIORITY

| Priority | Issue | Complexity | Impact | STATUS |
|----------|-------|------------|--------|--------|
| P2.1 | Git diff truncation | LOW | HIGH | ✅ DONE |
| P2.2 | Todo persistence | MEDIUM | HIGH | ✅ DONE |
| P2.3 | Schema validation | MEDIUM | MEDIUM | ✅ DONE |
| P2.4 | Memory tools registration | LOW | MEDIUM | ✅ DONE |
| P2.5 | AskUserQuestion response | HIGH | DEFER | DEFERRED |

---

# PART 5: IMPLEMENTATION LOG

## P2.1 - Git Diff Truncation (COMPLETED)
- **File**: `vertice_cli/tools/git/inspect_tools.py:388-415`
- **Change**: Added `is_truncated`, `original_size`, `truncated_at` to response
- **Test**: GitDiffEnhancedTool imports successfully

## P2.2 - Todo Persistence (COMPLETED)
- **File**: `vertice_cli/tools/parity/todo_tools.py:30-141`
- **Change**: Added `_save()`, `_load()`, `_ensure_loaded()` methods to TodoState
- **Persistence**: `.vertice/todos.json` with atomic write pattern
- **Test**: TodoState persists to `/media/juan/DATA/Vertice-Code/.vertice/todos.json`

## P2.3 - Schema Validation (COMPLETED)
- **File**: `vertice_cli/tools/validated.py:101-198`
- **Change**: Added `_validate_against_schema()` and `_check_type()` methods
- **Validates**: Required fields, type checking, enum validation
- **Test**: ValidatedTool._validate_against_schema method exists

## P2.4 - Memory Tools Registration (COMPLETED)
- **File**: `vertice_cli/tools/parity/__init__.py:57-114`
- **Change**: Added `get_memory_tools()`, `PROMETHEUS_AVAILABLE` flag
- **Conditional**: Memory tools added when prometheus_provider is passed
- **Test**: PROMETHEUS_AVAILABLE=True, 16 parity tools registered

---

# PART 6: VERIFICATION RESULTS

## Test Results (2026-01-03)

### P2.1 Git Diff Truncation
```
✓ diff present: True
✓ is_truncated field: True
✓ is_truncated value: True
✓ metadata has original_size: True
✓ metadata has truncated_at: True
✓ P2.1 PASS - Truncation indicator present
```

### P2.2 Todo Persistence
```
✓ todos.json created
✓ Contains 2 todos
✓ Has version field: True
✓ Loaded 2 todos from disk
✓ P2.2 PASS - Persistence working
```

### P2.3 Schema Validation
```
✓ Required field validation works
✓ Type validation works
✓ Enum validation works
✓ Valid inputs pass
✓ P2.3 PASS - Schema validation working
11/11 test_validated_tools.py tests PASS
```

### P2.4 Memory Tools Registration
```
✓ PROMETHEUS_AVAILABLE: True
✓ Tools without provider: 16
✓ Memory tools without provider: 0
✓ Tools with provider: 18
✓ Memory tools added when provider present
✓ P2.4 PASS - Memory registration working
```

---

*Research saved: 2026-01-03*
*Implementation completed: 2026-01-03*
*Verification completed: 2026-01-03*
*Sources: Scalify AI, Agenta, Martin Fowler, AI SDK, Vellum, Runloop, Google Developers*
