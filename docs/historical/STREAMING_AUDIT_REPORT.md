# STREAMING AUDIT REPORT - MAESTRO UI v10.0

**Date**: 2025-11-24
**Auditor**: Claude Code (Constitutional Analysis Mode)
**Issue**: Agent streaming not displaying in real-time in MAESTRO UI
**Severity**: 🔴 **CRITICAL** - Core feature non-functional

---

## EXECUTIVE SUMMARY

**Problem Observed**: Screenshot shows MAESTRO UI with CODE EXECUTOR showing partial output, but PLANNER panel is **completely empty** despite agent execution.

**Root Cause Identified**: **12 out of 15 agents** (80%) are missing `execute_streaming()` method required for real-time UI updates.

**Impact**:
- ❌ No real-time streaming for PLANNER, EXPLORER, REVIEWER, etc.
- ❌ Users see empty panels during execution
- ❌ 30 FPS streaming architecture present but unused
- ❌ UI shows "Thinking..." but no actual LLM output

---

## SCREENSHOT ANALYSIS

### Observed Behavior (from provided screenshot)

**Top Section (Before Approval)**:
```
⚠️  APPROVAL REQUIRED
echo "1. Ferva água.\n2. Coloque o milho na água fervente por 3
minutos.\n3. Adicione o tempero.\n4. Misture bem e sirva."
```
✅ Approval system working

**Bottom Section (During Execution)**:

| Panel | Status | Content Observed |
|-------|--------|------------------|
| **CODE EXECUTOR ⚡** | 🟡 PARTIAL | Shows "🤔 Thinking..." + partial echo output |
| **PLANNER 🎯** | ❌ EMPTY | Completely blank (should show planning) |
| **FILE OPERATIONS 📁** | ❌ EMPTY | "No file operations yet" |

### Expected Behavior

| Panel | Should Show |
|-------|-------------|
| **CODE EXECUTOR** | Token-by-token streaming of command generation |
| **PLANNER** | Real-time plan steps as LLM generates them |
| **FILE OPERATIONS** | Live updates when files are read/written |

---

## ARCHITECTURAL ANALYSIS

### Current Architecture (What EXISTS)

```
┌─────────────────────────────────────────────────────────────┐
│                     MAESTRO UI v10.0                        │
│                  (maestro_shell_ui.py)                      │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ CODE EXECUTOR│  │   PLANNER    │  │ FILE OPS     │    │
│  │              │  │              │  │              │    │
│  │ update_agent_│  │ update_agent_│  │ add_file_    │    │
│  │ _stream()    │  │ _stream()    │  │ operation()  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                          ▲                                  │
│                          │                                  │
└──────────────────────────┼──────────────────────────────────┘
                           │
                    ✅ UI Layer: READY
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                     Orchestrator                            │
│               (maestro_v10_integrated.py)                   │
│                                                             │
│   async def execute_streaming(prompt, context):            │
│       agent_name = self.route(prompt)                      │
│       agent = self.agents[agent_name]                      │
│                                                             │
│       if hasattr(agent, 'execute_streaming'):              │
│           async for update in agent.execute_streaming():   │
│               yield update  ←─ STREAMS TO UI               │
│       else:                                                 │
│           result = await agent.execute()  ← FALLBACK       │
│           yield {"type": "result", "data": result}         │
│                                                             │
└──────────────────────────┼──────────────────────────────────┘
                           │
                    ✅ Orchestrator: READY
                           │
┌──────────────────────────┼──────────────────────────────────┐
│                      Agent Layer                            │
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │ NextGenExecutor  │  │  PlannerAgent    │               │
│  │                  │  │                  │               │
│  │ ✅ execute_     │  │ ❌ NO execute_  │               │
│  │    streaming()   │  │    streaming()   │               │
│  │                  │  │                  │               │
│  │ Yields:          │  │ Only has:        │               │
│  │ - thinking       │  │ - execute()      │               │
│  │ - command        │  │   (returns final)│               │
│  │ - executing      │  │                  │               │
│  │ - result         │  │                  │               │
│  └──────────────────┘  └──────────────────┘               │
│         ✅                      ❌                          │
└─────────────────────────────────────────────────────────────┘
```

### THE GAP

**The MISSING piece**: 12 agents don't implement `execute_streaming()`, so Orchestrator falls back to non-streaming execution, causing empty panels.

---

## DETAILED AGENT AUDIT

### ✅ Agents WITH Streaming (3/15 - 20%)

| Agent | File | Status | Streaming Quality |
|-------|------|--------|-------------------|
| **NextGenExecutor** | `executor_nextgen.py` | ✅ COMPLETE | Excellent (30 FPS ready) |
| **Executor (legacy)** | `executor.py` | ✅ PARTIAL | Basic streaming |
| **DataAgent** | `data_agent_production.py` | ✅ COMPLETE | Production-ready |

**NextGenExecutor Streaming Implementation** (Reference):
```python
async def execute_streaming(self, task: AgentTask) -> AsyncIterator[Dict[str, Any]]:
    """
    Streaming execution with real-time updates (30 FPS)
    Yields: {"type": "thinking"|"command"|"executing"|"result", "data": ...}
    """
    # 1. Stream thinking phase
    yield {"type": "status", "data": "🤔 Thinking..."}

    command_buffer = []
    async for token in self._stream_command_generation(task.request, task.context):
        command_buffer.append(token)
        yield {"type": "thinking", "data": token}  # ← Real-time tokens!

    command = ''.join(command_buffer).strip()
    yield {"type": "command", "data": command}

    # 2. Security validation
    yield {"type": "status", "data": "🔒 Validating..."}

    # 3. Execute command
    yield {"type": "executing", "data": "Running..."}
    result = await self._execute_command(command)

    # 4. Final result
    yield {"type": "result", "data": result}
```

### ❌ Agents WITHOUT Streaming (12/15 - 80%)

| Priority | Agent | File | Impact | Current Behavior |
|----------|-------|------|--------|------------------|
| 🔴 P0 | **PlannerAgent** | `planner.py` | CRITICAL | Empty panel in UI |
| 🔴 P0 | **ExplorerAgent** | `explorer.py` | CRITICAL | Empty panel in UI |
| 🟠 P1 | **ReviewerAgent** | `reviewer.py` | HIGH | No live review feedback |
| 🟠 P1 | **RefactorerAgent** | `refactorer.py` | HIGH | No live refactor progress |
| 🟡 P2 | **ArchitectAgent** | `architect.py` | MEDIUM | No feasibility analysis stream |
| 🟡 P2 | **SecurityAgent** | `security.py` | MEDIUM | No live security scan |
| 🟡 P2 | **PerformanceAgent** | `performance.py` | MEDIUM | No live benchmark stream |
| 🟡 P2 | **TestingAgent** | `testing.py` | MEDIUM | No live test execution |
| 🟢 P3 | **DocumentationAgent** | `documentation.py` | LOW | Docs generation not time-critical |
| 🟢 P3 | **DevOpsAgent** | `devops_agent.py` | LOW | CI/CD not time-critical |
| 🟢 P3 | **RefactorerV8** | `refactorer_v8.py` | LOW | Duplicate/legacy |
| 🟢 P3 | **LLMAdapter** | `llm_adapter.py` | LOW | Not a user-facing agent |

---

## IMPACT ANALYSIS

### User Experience Impact

**Current State** (as shown in screenshot):
1. User types: "me da uma receita de miojo"
2. Maestro routes to CODE EXECUTOR
3. CODE EXECUTOR streams tokens ✅ (shows "Thinking...")
4. User needs context from PLANNER
5. PLANNER panel is **completely empty** ❌
6. User doesn't know what plan is being created
7. FILE OPERATIONS shows "No file operations yet" ❌

**Result**: User sees 2/3 panels empty despite agent working.

### Performance Impact

- ❌ **30 FPS streaming architecture UNUSED** for 80% of agents
- ❌ **UI refresh working** but no data to display
- ❌ **Network bandwidth wasted** (full responses transmitted at once vs. streaming)
- ❌ **Perceived latency HIGH** (no intermediate feedback)

### Developer Impact

- ❌ **Inconsistent agent interfaces** (some stream, some don't)
- ❌ **UI code has dead pathways** (panels ready but agents don't feed them)
- ❌ **Debugging difficult** (can't see agent reasoning in real-time)

---

## ROOT CAUSE ANALYSIS

### Why This Happened

**Historical Context** (from codebase archaeology):

1. **Phase 1**: BaseAgent created with only `execute()` method
2. **Phase 2**: NextGenExecutor added `execute_streaming()` for performance
3. **Phase 3**: MAESTRO UI v10.0 built expecting all agents to stream
4. **Phase 4**: **GAP CREATED** - UI assumes streaming, but agents don't provide it

### The Mismatch

```python
# maestro_v10_integrated.py (Orchestrator)
async for update in self.orch.execute_streaming(q, context={'cwd': ...}):
    if update["type"] == "thinking":
        await self.maestro_ui.update_agent_stream(agent_name, token)
        #      ▲                                   ▲
        #      │                                   └─ UI READY to display
        #      └─ But most agents DON'T yield "thinking" updates!
```

```python
# planner.py (PlannerAgent)
async def execute(self, task: AgentTask) -> AgentResponse:
    # Thinks internally, NO streaming
    plan = await self._generate_plan(task)

    # Returns FINAL result only
    return AgentResponse(success=True, data={"plan": plan})
    # ❌ NO intermediate updates yielded
```

**Result**: Orchestrator calls `agent.execute()` (fallback), gets final result, UI panels stay empty until completion.

---

## SOLUTION ARCHITECTURE

### Overview

To fix streaming, we need to add `execute_streaming()` to all critical agents following the pattern established by NextGenExecutor.

### Streaming Contract (Interface)

```python
async def execute_streaming(
    self,
    task: AgentTask
) -> AsyncIterator[Dict[str, Any]]:
    """
    Stream agent execution with real-time updates.

    Yields dictionaries with structure:
        {
            "type": "thinking" | "status" | "command" | "executing" | "result",
            "data": <content>,
            "meta": {Optional metadata}
        }

    Update Types:
        - "thinking": LLM token-by-token generation
        - "status": Status messages (e.g., "Validating...", "Loading context...")
        - "command": Generated command/action
        - "executing": Execution in progress
        - "result": Final result (required, terminal event)

    Example Flow:
        yield {"type": "status", "data": "Loading files..."}
        yield {"type": "thinking", "data": "Based on"}
        yield {"type": "thinking", "data": " the code"}
        yield {"type": "command", "data": "refactor_function(...)"}
        yield {"type": "result", "data": AgentResponse(...)}
    """
```

### Implementation Pattern (Template)

```python
async def execute_streaming(
    self,
    task: AgentTask
) -> AsyncIterator[Dict[str, Any]]:
    """Streaming execution for [AgentName]"""

    # Phase 1: Context gathering (with status updates)
    yield {"type": "status", "data": "🔍 Gathering context..."}
    context = await self._gather_context(task)

    # Phase 2: LLM generation (with token streaming)
    yield {"type": "status", "data": "🤔 Analyzing..."}

    response_buffer = []
    async for token in self.llm.generate_stream(prompt, context):
        response_buffer.append(token)
        yield {"type": "thinking", "data": token}  # ← KEY: Stream tokens!

    response_text = ''.join(response_buffer)

    # Phase 3: Processing (with status updates)
    yield {"type": "status", "data": "⚙️  Processing..."}
    processed_data = await self._process_response(response_text, task)

    # Phase 4: Tool execution (if needed, with updates)
    if requires_tools:
        yield {"type": "status", "data": "🔧 Executing tools..."}
        tool_results = await self._execute_tools(processed_data)

    # Phase 5: Final result (required)
    final_result = AgentResponse(
        success=True,
        data=processed_data,
        reasoning=response_text
    )

    yield {"type": "result", "data": final_result}
```

### LLM Streaming Helper

**Problem**: Current LLMClient may not support streaming.

**Solution**: Add streaming method to LLMClient

```python
# qwen_dev_cli/core/llm.py

async def generate_stream(
    self,
    prompt: str,
    context: Optional[Dict] = None,
    **kwargs
) -> AsyncIterator[str]:
    """
    Stream LLM generation token-by-token.

    Yields individual tokens as they're generated.
    """
    if self.provider == "gemini":
        # Gemini streaming API
        response = await self.client.generate_content_async(
            prompt,
            stream=True,  # ← Enable streaming
            **kwargs
        )

        async for chunk in response:
            if chunk.text:
                yield chunk.text

    elif self.provider == "ollama":
        # Ollama streaming
        async for chunk in self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        ):
            yield chunk['message']['content']

    else:
        # Fallback: Simulate streaming by splitting response
        full_response = await self.generate(prompt, context, **kwargs)
        for token in full_response.split():
            yield token + " "
            await asyncio.sleep(0.01)  # Simulate streaming delay
```

---

## IMPLEMENTATION PLAN

### Phase 1: Critical Agents (P0) - Required for Basic Functionality

**Priority**: 🔴 CRITICAL
**Agents**: PlannerAgent, ExplorerAgent
**Timeline**: Implement first

#### 1.1 PlannerAgent Streaming

**File**: `qwen_dev_cli/agents/planner.py`

**Changes Required**:

```python
# ADD THIS METHOD

async def execute_streaming(
    self,
    task: AgentTask
) -> AsyncIterator[Dict[str, Any]]:
    """Stream plan generation with real-time updates"""

    # 1. Load context
    yield {"type": "status", "data": "📋 Loading project context..."}
    context = await self._gather_context(task)

    # 2. Stream plan generation
    yield {"type": "status", "data": "🎯 Generating plan..."}

    prompt = self._build_prompt(task, context)

    plan_buffer = []
    async for token in self.llm.generate_stream(prompt):
        plan_buffer.append(token)
        yield {"type": "thinking", "data": token}  # ← Stream to PLANNER panel

    plan_text = ''.join(plan_buffer)

    # 3. Parse plan into steps
    yield {"type": "status", "data": "⚙️  Parsing plan steps..."}
    parsed_plan = self._parse_plan(plan_text)

    # 4. Validate plan
    yield {"type": "status", "data": "✅ Validating plan..."}
    validated_plan = await self._validate_plan(parsed_plan, context)

    # 5. Final result
    result = AgentResponse(
        success=True,
        data={"plan": validated_plan, "raw_plan": plan_text},
        reasoning=f"Generated {len(validated_plan)} steps"
    )

    yield {"type": "result", "data": result}
```

**Dependencies**:
- Requires `LLMClient.generate_stream()` method
- No other breaking changes

**Testing**:
```python
# Test streaming works
planner = PlannerAgent(llm, mcp)
task = AgentTask(request="Create a login feature")

async for update in planner.execute_streaming(task):
    print(f"[{update['type']}] {update.get('data', '')[:50]}")
    # Should print:
    # [status] 📋 Loading project context...
    # [status] 🎯 Generating plan...
    # [thinking] Based on
    # [thinking]  the request
    # [thinking] , I will
    # ...
    # [result] AgentResponse(...)
```

#### 1.2 ExplorerAgent Streaming

**File**: `qwen_dev_cli/agents/explorer.py`

**Changes Required**:

```python
async def execute_streaming(
    self,
    task: AgentTask
) -> AsyncIterator[Dict[str, Any]]:
    """Stream code exploration with real-time updates"""

    # 1. Scan filesystem
    yield {"type": "status", "data": "🗺️  Scanning codebase..."}
    file_tree = await self._scan_directory(task.context.get('cwd', '.'))
    yield {"type": "status", "data": f"Found {len(file_tree)} files"}

    # 2. Build context
    yield {"type": "status", "data": "📖 Building context..."}
    context = await self._build_context(task, file_tree)

    # 3. Stream analysis
    yield {"type": "status", "data": "🔍 Analyzing code structure..."}

    prompt = self._build_exploration_prompt(task, context)

    analysis_buffer = []
    async for token in self.llm.generate_stream(prompt):
        analysis_buffer.append(token)
        yield {"type": "thinking", "data": token}  # ← Stream to EXPLORER panel

    analysis = ''.join(analysis_buffer)

    # 4. Extract findings
    yield {"type": "status", "data": "📊 Extracting insights..."}
    findings = self._extract_findings(analysis)

    # 5. Final result
    result = AgentResponse(
        success=True,
        data={"findings": findings, "file_tree": file_tree},
        reasoning=analysis
    )

    yield {"type": "result", "data": result}
```

### Phase 2: High-Impact Agents (P1)

**Priority**: 🟠 HIGH
**Agents**: ReviewerAgent, RefactorerAgent
**Timeline**: Implement after P0

Same pattern as above, adapted for each agent's specific workflow.

### Phase 3: Medium-Impact Agents (P2)

**Priority**: 🟡 MEDIUM
**Agents**: ArchitectAgent, SecurityAgent, PerformanceAgent, TestingAgent
**Timeline**: Implement incrementally

### Phase 4: Low-Priority Agents (P3)

**Priority**: 🟢 LOW
**Agents**: DocumentationAgent, DevOpsAgent
**Timeline**: Optional, nice-to-have

---

## FILE OPERATIONS STREAMING

**Separate Issue**: FILE OPERATIONS panel shows "No file operations yet"

### Root Cause

**File Tracker Integration Missing**

```python
# maestro_v10_integrated.py (line 817)
self.file_tracker = FileOperationTracker()
self.file_tracker.set_callback(self.maestro_ui.add_file_operation)
```

**Problem**: Agents don't call `file_tracker.track_operation()` when reading/writing files.

### Solution

**Option A: Automatic Tracking in Tool Execution**

Wrap MCP tool execution to automatically track file operations:

```python
# qwen_dev_cli/core/mcp.py

async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute tool with automatic file operation tracking"""

    # Execute tool
    result = await tool._execute_validated(**arguments)

    # Track file operations
    if tool_name in ['read_file', 'write_file', 'edit_file', 'move_file', 'copy_file']:
        self._track_file_operation(tool_name, arguments, result)

    return result

def _track_file_operation(self, tool_name, arguments, result):
    """Track file operation for UI display"""
    if hasattr(self, 'file_tracker') and self.file_tracker:
        operation = {
            'type': tool_name,
            'path': arguments.get('path') or arguments.get('file_path'),
            'success': result.success if hasattr(result, 'success') else True,
            'timestamp': datetime.now()
        }
        self.file_tracker.track_operation(operation)
```

**Option B: Explicit Tracking in Agents**

Each agent manually tracks file operations:

```python
# In agent's execute_streaming()
async for update in agent.execute_streaming(task):
    if update["type"] == "file_operation":
        self.file_tracker.track_operation(update["data"])

    yield update
```

**Recommendation**: Use Option A (automatic) for consistency and less agent code duplication.

---

## TESTING STRATEGY

### Unit Tests

```python
# tests/unit/test_planner_streaming.py

@pytest.mark.asyncio
async def test_planner_streams_thinking_tokens():
    """PlannerAgent should yield thinking tokens during execution"""
    planner = PlannerAgent(mock_llm, mock_mcp)
    task = AgentTask(request="Create feature X")

    thinking_tokens = []
    async for update in planner.execute_streaming(task):
        if update["type"] == "thinking":
            thinking_tokens.append(update["data"])

    # Should have received multiple tokens
    assert len(thinking_tokens) > 10

    # Tokens should form coherent text
    full_text = ''.join(thinking_tokens)
    assert len(full_text) > 100

@pytest.mark.asyncio
async def test_planner_yields_final_result():
    """PlannerAgent streaming must yield final result"""
    planner = PlannerAgent(mock_llm, mock_mcp)
    task = AgentTask(request="Create feature X")

    final_result = None
    async for update in planner.execute_streaming(task):
        if update["type"] == "result":
            final_result = update["data"]

    assert final_result is not None
    assert isinstance(final_result, AgentResponse)
    assert final_result.success
```

### Integration Tests

```python
# tests/integration/test_maestro_streaming.py

@pytest.mark.asyncio
async def test_maestro_ui_displays_planner_stream():
    """MAESTRO UI should display PlannerAgent streaming"""
    from maestro_v10_integrated import Shell

    shell = Shell()
    shell.init()

    # Capture UI updates
    ui_updates = []
    original_update = shell.maestro_ui.update_agent_stream

    async def capture_update(agent_name, text, *args, **kwargs):
        ui_updates.append((agent_name, text))
        await original_update(agent_name, text, *args, **kwargs)

    shell.maestro_ui.update_agent_stream = capture_update

    # Execute command that routes to PlannerAgent
    await shell.orch.execute_streaming(
        "Plan a refactoring for auth module",
        context={'cwd': '.'}
    )

    # Verify UI received updates
    assert len(ui_updates) > 0

    # Verify planner panel got updates
    planner_updates = [u for u in ui_updates if u[0] == 'planner']
    assert len(planner_updates) > 10  # Should have multiple tokens
```

### Manual Testing Checklist

```
□ Launch MAESTRO: ./maestro
□ Enter command: "Create a plan for implementing user auth"
□ Observe PLANNER panel during execution:
  □ Shows "📋 Loading project context..." status
  □ Shows "🎯 Generating plan..." status
  □ Shows LLM tokens streaming in real-time
  □ Text flows smoothly (30 FPS)
  □ Final plan appears formatted

□ Enter command: "Analyze the codebase structure"
□ Observe EXPLORER panel during execution:
  □ Shows "🗺️  Scanning codebase..." status
  □ Shows file count status
  □ Shows LLM analysis streaming
  □ Final findings appear

□ Enter command: "Write a simple hello world script"
□ Observe FILE OPERATIONS panel:
  □ Shows file write operation appear
  □ Shows file path and timestamp
  □ Status icon updates (success/failure)
```

---

## ROLLOUT STRATEGY

### Phase 1: Foundation (Week 1)

**Goal**: Enable streaming infrastructure

**Tasks**:
1. ✅ Add `LLMClient.generate_stream()` method
2. ✅ Test streaming with NextGenExecutor (already works)
3. ✅ Verify MAESTRO UI receives streams correctly
4. ✅ Add automatic file operation tracking to MCP

**Success Criteria**:
- NextGenExecutor streams visible in UI
- File operations tracked automatically
- No regressions

### Phase 2: Critical Agents (Week 2)

**Goal**: Fix P0 agents (PlannerAgent, ExplorerAgent)

**Tasks**:
1. ✅ Implement `PlannerAgent.execute_streaming()`
2. ✅ Implement `ExplorerAgent.execute_streaming()`
3. ✅ Write unit tests for both
4. ✅ Test in MAESTRO UI
5. ✅ Fix any issues found

**Success Criteria**:
- PLANNER panel shows real-time plan generation
- EXPLORER panel shows real-time analysis
- No empty panels during execution
- 30 FPS smooth streaming

### Phase 3: High-Impact Agents (Week 3-4)

**Goal**: Add streaming to ReviewerAgent, RefactorerAgent

**Tasks**:
1. Implement ReviewerAgent.execute_streaming()
2. Implement RefactorerAgent.execute_streaming()
3. Test and validate

**Success Criteria**:
- All P0 + P1 agents stream to UI
- User experience significantly improved

### Phase 4: Remaining Agents (Ongoing)

**Goal**: Add streaming to P2 and P3 agents incrementally

**Tasks**: Implement remaining agents as needed

---

## SUCCESS METRICS

### Technical Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Agents with streaming | 100% (15/15) | Audit script |
| UI panel usage | 100% | All panels show content |
| Streaming latency | < 50ms | Time from LLM token to UI |
| FPS during streaming | ≥ 25 FPS | PerformanceMonitor |
| Token throughput | > 50 tokens/sec | Measure in UI |

### User Experience Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Empty panel occurrences | 0 | Visual inspection |
| User can see progress | 100% of time | Observation |
| Perceived latency | Low | User feedback |

---

## KNOWN ISSUES & WORKAROUNDS

### Issue #1: LLMClient doesn't have generate_stream()

**Workaround**: Implement it (see Solution Architecture section)

### Issue #2: Some agents have complex multi-step workflows

**Workaround**: Stream each phase separately:
```python
# Phase 1
yield {"type": "status", "data": "Phase 1: Loading..."}
async for token in phase1_stream():
    yield {"type": "thinking", "data": token}

# Phase 2
yield {"type": "status", "data": "Phase 2: Analyzing..."}
async for token in phase2_stream():
    yield {"type": "thinking", "data": token}
```

### Issue #3: Streaming increases LLM API costs (slightly)

**Impact**: Minimal (streaming uses same tokens)
**Mitigation**: Streaming is more efficient (can cancel early)

---

## REFERENCES

### Code Files to Modify

| Priority | File | Changes Required |
|----------|------|------------------|
| P0 | `qwen_dev_cli/core/llm.py` | Add `generate_stream()` method |
| P0 | `qwen_dev_cli/agents/planner.py` | Add `execute_streaming()` |
| P0 | `qwen_dev_cli/agents/explorer.py` | Add `execute_streaming()` |
| P0 | `qwen_dev_cli/core/mcp.py` | Add file operation tracking |
| P1 | `qwen_dev_cli/agents/reviewer.py` | Add `execute_streaming()` |
| P1 | `qwen_dev_cli/agents/refactorer.py` | Add `execute_streaming()` |
| P2 | Other agents | Add `execute_streaming()` |

### Files Already Correct (No Changes)

- ✅ `maestro_v10_integrated.py` (Orchestrator handles streaming correctly)
- ✅ `qwen_dev_cli/tui/components/maestro_shell_ui.py` (UI ready for streaming)
- ✅ `qwen_dev_cli/agents/executor_nextgen.py` (Reference implementation)

### Architecture Diagram Files

```
docs/architecture/
├── streaming_flow.png (create: shows token flow)
├── agent_interface.md (create: documents execute_streaming contract)
└── maestro_ui_panels.md (create: documents panel update protocol)
```

---

## APPENDIX A: Streaming Update Types

| Type | Purpose | Data Format | Example |
|------|---------|-------------|---------|
| `thinking` | LLM token-by-token | String (single token or word) | "Based" |
| `status` | Status message | String (full message) | "🔍 Loading files..." |
| `command` | Generated command | String (command text) | "echo 'hello'" |
| `executing` | Tool execution | String (status message) | "Running command..." |
| `result` | Final result | AgentResponse or Dict | `AgentResponse(...)` |

---

## APPENDIX B: Quick Reference - Implement Streaming

**Copy-paste template for adding streaming to any agent**:

```python
async def execute_streaming(
    self,
    task: AgentTask
) -> AsyncIterator[Dict[str, Any]]:
    """Stream execution for [YOUR AGENT NAME]"""

    # 1. Pre-processing
    yield {"type": "status", "data": "🔄 Starting [agent name]..."}

    # 2. Main LLM generation (STREAMING!)
    yield {"type": "status", "data": "🤔 Analyzing..."}

    prompt = self._build_prompt(task)
    response_buffer = []

    async for token in self.llm.generate_stream(prompt):
        response_buffer.append(token)
        yield {"type": "thinking", "data": token}  # ← CRITICAL: Stream tokens!

    response_text = ''.join(response_buffer)

    # 3. Post-processing
    yield {"type": "status", "data": "⚙️  Processing..."}
    processed = self._process(response_text)

    # 4. Final result (REQUIRED!)
    result = AgentResponse(
        success=True,
        data=processed,
        reasoning=response_text
    )

    yield {"type": "result", "data": result}
```

---

**Report Version**: 1.0
**Last Updated**: 2025-11-24
**Next Review**: After Phase 1 implementation

**For Implementer**: This report contains EVERYTHING needed to fix streaming. Start with Phase 1 (LLMClient), then Phase 2 (PlannerAgent + ExplorerAgent). The architecture is sound, we just need to implement the streaming methods.

🎯 **Priority**: CRITICAL - This is core UX functionality
