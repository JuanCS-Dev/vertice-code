# VERTICE Hardening & Polish Plan
## Comprehensive Codebase Quality Improvement

**Project:** Vertice-Code
**Date:** 2026-01-04
**Goal:** Address 500+ identified issues across error handling, resilience, accessibility, performance, and testing

---

## Executive Summary

14 exploratory agents analyzed the entire codebase and identified **500+ polish opportunities** across 8 categories:

| Category | Issues | Severity |
|----------|--------|----------|
| Error Handling & Resilience | 80+ | CRITICAL |
| CLI Tools Validation | 50+ | HIGH |
| Agent System Consistency | 50+ | HIGH |
| PROMETHEUS Core Stability | 50+ | HIGH |
| Test Coverage Gaps | 100+ | MEDIUM |
| Accessibility & UX | 30+ | MEDIUM |
| Performance Bottlenecks | 14+ | MEDIUM |
| Domain Kernel Types | 40+ | LOW |

---

## Phase 1: CRITICAL - Error Handling (Week 1)

### 1.1 Fix Bare Except Clauses (8 locations)

| File | Line | Fix |
|------|------|-----|
| `prometheus/agents/executor_agent.py` | 312 | Replace `except:` with `except Exception as e:` + logging |
| `prometheus/tools/tool_factory.py` | 505, 522, 530 | Add specific exception types |
| `vertice_tui/handlers/basic.py` | 241, 254 | Log exceptions instead of silencing |

### 1.2 Fix Silent Background Task Failures

**File:** `vertice_tui/core/streaming/production_stream.py`

```python
# Line 343-346: Add exception callback
self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
self._heartbeat_task.add_done_callback(self._handle_task_exception)

def _handle_task_exception(self, task: asyncio.Task) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc:
        logger.error(f"Background task failed: {exc}", exc_info=exc)
```

### 1.3 Add Missing Confirmation Dialogs

| File | Command | Action |
|------|---------|--------|
| `vertice_tui/handlers/basic.py:77` | `/clear` | Add "Clear all context?" confirmation |
| `vertice_tui/handlers/operations.py:217` | `/restore` | Add "Overwrite current session?" confirmation |
| `vertice_tui/core/custom_commands.py:297` | `delete_command()` | Add confirmation before `unlink()` |

---

## Phase 2: HIGH - Validation & Consistency (Week 2)

### 2.1 CLI Tools Missing Validators (8 tools)

**Files to update:**

| Tool File | Missing Validators |
|-----------|-------------------|
| `vertice_cli/tools/context.py:75,154` | `SaveSessionTool`, `RestoreBackupTool` |
| `vertice_cli/tools/search.py:52,236` | `SearchFilesTool`, `GetDirectoryTreeTool` |
| `vertice_cli/tools/web_access.py:36,160,297,424` | `PackageSearchTool`, `FetchURLTool`, `DownloadFileTool`, `HTTPRequestTool` |

**Pattern to add:**
```python
def get_validators(self) -> Dict[str, Callable]:
    return {
        "required_param": lambda v: v is not None and len(v) > 0,
        "timeout": lambda v: v is None or (isinstance(v, (int, float)) and v > 0),
    }
```

### 2.2 Agent Interface Standardization

**Issue:** Two incompatible base agent classes:
- `agents/base.py` (simple, observability)
- `vertice_cli/agents/base.py` (complex, OODA loop)

**Fix:** Create unified `vertice_core/agents/base_protocol.py`:
```python
class AgentProtocol(Protocol):
    async def execute(self, request: AgentTask) -> AsyncIterator[str]: ...
    async def validate_input(self, request: AgentTask) -> bool: ...
    def get_status(self) -> Dict[str, Any]: ...
```

### 2.3 Timeout Handling (5 tools)

**Add configurable timeout parameter to:**
- `vertice_cli/tools/search.py:84` - SearchFilesTool (hardcoded 10s)
- `vertice_cli/tools/web_access.py:70,192,338,493` - All web tools

---

## Phase 3: HIGH - PROMETHEUS Stability (Week 3)

### 3.1 Memory Leak Fixes (5 unbounded lists)

| File | Line | Fix |
|------|------|-----|
| `prometheus/core/orchestrator.py` | 108 | Add `maxlen=500` to execution_history |
| `prometheus/core/llm_client.py` | 65 | Add `maxlen=100` to conversation_history |
| `prometheus/core/reflection.py` | 100 | Add `maxlen=200` to reflection_history |
| `prometheus/sandbox/executor.py` | 76 | Add `maxlen=100` to execution_history |

**Pattern:**
```python
from collections import deque
self.execution_history: deque = deque(maxlen=500)
```

### 3.2 Thread Safety (8 locations)

**File:** `prometheus/memory/system.py`
```python
# Add lock to all memory operations
import threading
self._memory_lock = threading.RLock()

def remember_experience(self, exp):
    with self._memory_lock:
        self.episodic.append(exp)
```

### 3.3 Add Logging Throughout

**No logging imports in PROMETHEUS core.** Add to all files:
```python
import logging
logger = logging.getLogger(__name__)
```

---

## Phase 4: MEDIUM - Performance (Week 4)

### 4.1 O(n) → O(1) Cache Lookups

**File:** `core/caching/semantic.py:122-145`
```python
# Replace linear search with approximate nearest neighbor
from sklearn.neighbors import BallTree
# Or use faiss for larger scale
```

**File:** `core/caching/exact.py:147-165`
```python
# Replace O(n) eviction with heap
import heapq
self._access_heap = []  # (timestamp, key)
```

### 4.2 Rate Limiter Optimization

**File:** `core/resilience/rate_limiter.py:100-120`
```python
# Replace polling with asyncio.Event
self._refill_event = asyncio.Event()
await self._refill_event.wait()  # Instead of sleep loop
```

### 4.3 Message Queue Sort Optimization

**File:** `vertice_core/messaging/memory.py:54-56`
```python
# Replace sort-on-insert with heap
import heapq
heapq.heappush(self._delayed, (visible_at, message))
```

---

## Phase 5: MEDIUM - Accessibility (Week 5)

### 5.1 Missing ARIA Labels

**File:** `vertice_tui/widgets/modal.py`
- Add `role="dialog"` to all modal classes
- Add `aria-label` to ConfirmDialog, AlertDialog, InputDialog
- Add `aria-busy="true"` to ProgressDialog

### 5.2 Connect Unused Accessibility Code

**File:** `vertice_cli/tui/accessibility.py`
- `KeyboardNavigation` class (178-206) defined but unused
- `ScreenReaderText` class (143-173) defined but unused
- `AccessibilityValidator` (87-104) never called

**Action:** Wire these into actual widgets.

### 5.3 Keyboard Shortcuts

**File:** `vertice_tui/widgets/input_area.py:41-43`
Add missing shortcuts:
- `Tab` - completion
- `Shift+Tab` - reverse completion
- `Ctrl+A` - select all
- `Ctrl+U` - clear line

---

## Phase 6: Test Coverage (Week 6)

### 6.1 Fix Skipped Tests (15+)

| File | Issue |
|------|-------|
| `tests/agents/test_refactor_comprehensive.py` | 12 tests skipped - implement inline analysis |
| `tests/agents/test_explorer_edge_cases.py` | All skipped - rewrite for v8.0 API |

### 6.2 Add Missing Error Path Tests

**Priority areas:**
- Connection timeout/refused scenarios
- Permission denied errors
- LLM failure scenarios (partial responses, rate limiting)

### 6.3 Fix Flaky Tests (20+)

Replace `time.sleep()` with proper async waiting:
```python
# Before
time.sleep(0.1)

# After
await asyncio.wait_for(condition.wait(), timeout=1.0)
```

---

## Phase 7: Domain Kernel Polish (Week 7)

### 7.1 Add Missing `__repr__` Methods

**Files needing `__repr__`:**
- `vertice_core/types/agents.py:118` - AgentIdentity
- `vertice_core/multitenancy/tenant.py:118` - Tenant
- `vertice_core/messaging/events.py:19` - Event
- `vertice_core/types/models.py:28,90,124` - AgentTask, AgentResponse, TaskResult
- `vertice_core/code/ast/types.py:23,43,63` - CodeLocation, CodeMatch, CodeSymbol

### 7.2 Add Serialization Methods

**Add `to_dict()`/`from_dict()` to:**
- `vertice_core/types/circuit.py:38,51` - CircuitBreakerStats, SimpleCircuitBreaker
- `vertice_core/interfaces/llm.py:45,62` - LLMResponse, ChatMessage

### 7.3 Fix Exception Duplication

**Issue:** `CapabilityViolationError` defined in two places with different signatures:
- `vertice_core/types/exceptions.py:45`
- `vertice_core/exceptions.py:385`

**Fix:** Deprecate `types/exceptions.py` version, use unified hierarchy.

---

## Edge Case Tests

### E1. Streaming Edge Cases
```python
def test_empty_chunk_handling():
    """LLM returns empty chunk mid-stream."""

def test_malformed_json_in_stream():
    """SSE event contains invalid JSON."""

def test_connection_drop_recovery():
    """Network drops during streaming, verify reconnect."""
```

### E2. Rate Limiting Edge Cases
```python
def test_429_with_retry_after_header():
    """Respect Retry-After header from provider."""

def test_529_anthropic_overloaded():
    """Handle Anthropic 529 overloaded error."""

def test_concurrent_rate_limit_exhaustion():
    """Multiple requests exhaust quota simultaneously."""
```

### E3. Context Window Edge Cases
```python
def test_context_exactly_at_limit():
    """Request exactly at context window limit."""

def test_context_overflow_graceful():
    """Request exceeds limit, verify truncation."""

def test_token_count_accuracy():
    """Verify token counting matches provider."""
```

### E4. File Operation Edge Cases
```python
def test_binary_file_read():
    """Read binary file, verify proper error."""

def test_file_locked_by_process():
    """File locked, verify timeout and error."""

def test_symlink_loop():
    """Symlink creates loop, verify detection."""
```

### E5. Agent Failure Edge Cases
```python
def test_agent_timeout_partial_result():
    """Agent times out, verify partial results saved."""

def test_agent_cascade_failure():
    """One agent fails, verify others continue."""

def test_agent_memory_exhaustion():
    """Agent uses too much memory, verify kill."""
```

---

## Files Summary

### Critical (Phase 1)
- `vertice_tui/core/streaming/production_stream.py`
- `prometheus/tools/tool_factory.py`
- `vertice_tui/handlers/basic.py`
- `vertice_tui/handlers/operations.py`

### High Priority (Phase 2-3)
- `vertice_cli/tools/context.py`
- `vertice_cli/tools/search.py`
- `vertice_cli/tools/web_access.py`
- `prometheus/core/orchestrator.py`
- `prometheus/core/llm_client.py`
- `prometheus/memory/system.py`

### Medium Priority (Phase 4-5)
- `core/caching/semantic.py`
- `core/caching/exact.py`
- `core/resilience/rate_limiter.py`
- `vertice_tui/widgets/modal.py`
- `vertice_cli/tui/accessibility.py`

---

## Success Metrics

- [ ] 0 bare except clauses in production code
- [ ] All destructive actions have confirmation dialogs
- [ ] All CLI tools have validators
- [ ] PROMETHEUS memory bounded to <500MB
- [ ] O(n) lookups replaced with O(1) or O(log n)
- [ ] 90%+ test coverage on error paths
- [ ] All accessibility code wired to UI

---

*Plan created: 2026-01-04*
*Based on: 14 exploratory agents, 500+ findings*
*Author: Claude Opus 4.5*
