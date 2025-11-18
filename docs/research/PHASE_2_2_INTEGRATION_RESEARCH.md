# 🔬 PHASE 2.2 RESEARCH: Tool Registry & Execution Patterns (2025)

**Research Date:** 2025-11-17 23:15 UTC  
**Focus:** GitHub Copilot CLI, Cursor AI, Claude Code  
**Objective:** Learn production patterns for tool registry and execution

---

## 🎯 KEY DISCOVERIES

### **1. GitHub Copilot CLI (2024-2025)**

#### **Tool Execution Architecture:**
```
User Input → AI Analysis → Tool Selection → Permission Check → Execute → Feedback
```

**Key Features:**
- ✅ **Defense-in-depth permission model**
  - Multi-layer allow/deny lists
  - `--allow-tool` and `--deny-tool` flags
  - Glob pattern matching (e.g., `--deny-tool "shell (rm -rf *)"`)
  - Explicit user approval for destructive operations

- ✅ **Shell Integration:**
  - Runs in native shell environment (bash, PowerShell, etc.)
  - Direct execution with `!` prefix (bypasses AI)
  - `ghcs` alias for seamless integration
  - Environment-specific compatibility

- ✅ **Custom Agents (NEW 2025):**
  - Project/org/global level configuration
  - Domain-specific assistants (e.g., Kubernetes agent)
  - Context-aware automation
  - Tool-specific permissions per agent

- ✅ **Session State:**
  - Maintains permissions during session
  - Prompts again in new sessions (unless trusted)
  - Command history tracking
  - Timeline view of operations

**Security Model:**
```python
# Copilot CLI pattern
def execute_tool(tool_call, session):
    # 1. Check permissions
    if not is_allowed(tool_call, session.permissions):
        return request_approval(tool_call)
    
    # 2. Validate safety
    if is_dangerous(tool_call):
        return request_explicit_confirmation(tool_call)
    
    # 3. Execute with timeout
    result = run_with_sandbox(tool_call, timeout=30)
    
    # 4. Track in session
    session.add_to_history(tool_call, result)
    
    return result
```

---

### **2. Cursor AI (2024-2025)**

#### **Dynamic Tool Registry:**

**NOT static registry! Context-driven approach:**

```typescript
// Cursor pattern (conceptual)
class CursorToolRegistry {
    // NO upfront loading of all tools
    // Tools discovered dynamically based on:
    // - Project structure (package.json, Dockerfile, CI scripts)
    // - Available extensions
    // - Current context
    
    async discoverTools(context: ProjectContext): Promise<Tool[]> {
        const tools = [];
        
        // Dynamic discovery
        if (context.hasFile('package.json')) {
            tools.push(npmTools);
        }
        if (context.hasFile('Dockerfile')) {
            tools.push(dockerTools);
        }
        // etc.
        
        return tools;
    }
    
    // Tools loaded on-demand during execution
    async executeTool(toolName: string, args: any) {
        const tool = await this.loadTool(toolName); // Lazy loading
        return tool.execute(args);
    }
}
```

**Key Features:**
- ✅ **Context-Aware Discovery:** Tools found based on project files
- ✅ **Lazy Loading:** Only load tools when needed
- ✅ **VS Code Integration:** Imports settings, extensions, keybindings
- ✅ **Real-time Execution:** Agent generates and runs code dynamically
- ✅ **MCP-Style Approach:** Dynamic import/call pattern

**Security:**
- ⚠️ **Workspace Trust Required:** Prevents auto-execution from malicious tasks.json
- ✅ **Sandboxed Execution:** Limits tool access to safe operations

---

### **3. Claude Code (2025)**

#### **NEW: MCP Code Execution Model**

**Revolutionary Change (Nov 2025):**

**OLD MODEL (Pre-2025):**
```python
# Tools passed via prompt
prompt = f"""
Available tools:
{tool_schema_1}
{tool_schema_2}
...
{tool_schema_50}  # Limit: ~50 tools max

Choose and invoke tools...
"""
# Problem: Prompt bloat, limited scalability
```

**NEW MODEL (2025):**
```python
# Agent writes code to dynamically import tools
prompt = f"""
You have access to a code executor.
Write Python/Bash to import and call tools as needed.

Example:
```python
from tools import read_file, git_commit

content = read_file("/path/to/file")
result = git_commit("feat: " + content)
```
"""

# Benefits:
# - Supports 100s of tools (no prompt bloat)
# - Composable (loops, conditionals, error handling)
# - Debuggable (code is visible)
# - Scalable
```

**Tool Registry Pattern:**
```python
# Claude Code approach
class MCPToolRegistry:
    """
    Minimal context approach:
    - Only code_executor API in prompt
    - Tools imported dynamically by agent
    """
    
    def __init__(self):
        self.tools = {}  # Available tools
        self.session = None
    
    async def execute_code(self, code: str, session: Session):
        """Execute agent-generated code."""
        # 1. Sandbox setup
        sandbox = create_sandbox(session)
        
        # 2. Make tools importable
        sandbox.make_available(self.tools)
        
        # 3. Execute with safety
        result = await sandbox.run(code, timeout=60)
        
        # 4. Track in session
        session.add_history("code_exec", code, result)
        
        return result
```

**Session Management Best Practices:**
- ✅ **CLAUDE.md File:** Project memory, conventions, commands
- ✅ **Context Management:** `/status`, `/clear` at 80% tokens
- ✅ **Feature Branch Isolation:** `git checkout -b feature/X`
- ✅ **Permission Modes:** Plan mode vs AcceptEdits mode
- ✅ **Sub-Agents:** Logical module separation
- ✅ **Custom Commands:** `.claude/commands` for reusables
- ✅ **Automated Testing:** CI gates for AI-generated code
- ✅ **Sandbox Security:** Filesystem & network restrictions

---

## 🏆 BEST PRACTICES (SYNTHESIZED FROM ALL 3)

### **1. Tool Registry Architecture:**

**✅ HYBRID APPROACH (Best of all 3):**

```python
class HybridToolRegistry:
    """
    Combines:
    - Static core tools (always loaded)
    - Dynamic discovery (Cursor pattern)
    - On-demand execution (Claude pattern)
    """
    
    def __init__(self):
        # Core tools (always available)
        self.core_tools = {
            "read_file": ReadFileTool(),
            "write_file": WriteFileTool(),
            "bash_command": BashCommandTool(),
        }
        
        # Discovered tools (context-dependent)
        self.discovered_tools = {}
        
        # Lazy-loaded tools (heavy dependencies)
        self.lazy_tools = {}
    
    def register_core(self, tool: Tool):
        """Register core tool (always available)."""
        self.core_tools[tool.name] = tool
    
    async def discover_tools(self, context: ProjectContext):
        """Discover tools based on project (Cursor pattern)."""
        if context.has_git():
            self.discovered_tools["git_commit"] = GitCommitTool()
        
        if context.has_node():
            self.discovered_tools["npm_install"] = NpmInstallTool()
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get tool by name (with lazy loading)."""
        # Check core first
        if name in self.core_tools:
            return self.core_tools[name]
        
        # Check discovered
        if name in self.discovered_tools:
            return self.discovered_tools[name]
        
        # Lazy load if needed
        if name in self.lazy_tools:
            return self._lazy_load(name)
        
        return None
    
    def get_available_tools(self, context: Optional[str] = None) -> List[Tool]:
        """Get all available tools for current context."""
        tools = list(self.core_tools.values())
        
        if context:
            # Filter by context
            tools.extend([
                t for t in self.discovered_tools.values()
                if t.is_relevant(context)
            ])
        
        return tools
```

---

### **2. Execution Pipeline:**

**✅ MULTI-LAYER SECURITY (Copilot pattern):**

```python
async def execute_tool_call(
    tool_call: Dict[str, Any],
    session: Session,
    registry: ToolRegistry,
    safety: SafetyValidator
) -> ExecutionResult:
    """
    Execution pipeline with multi-layer checks.
    
    Flow:
    1. Parse tool call
    2. Validate safety (blacklist + whitelist)
    3. Check permissions (session-based)
    4. Get tool from registry
    5. Execute with timeout
    6. Track in session
    7. Return result
    """
    
    # 1. Parse
    tool_name = tool_call.get("tool")
    arguments = tool_call.get("arguments", {})
    
    # 2. Safety check (CRITICAL)
    is_safe, reason = safety.is_safe(tool_call)
    if not is_safe:
        logger.warning(f"Blocked: {reason}")
        return ExecutionResult(
            success=False,
            blocked=True,
            block_reason=reason
        )
    
    # 3. Permission check (Copilot pattern)
    if not session.has_permission(tool_name):
        approval = await request_user_approval(tool_call)
        if not approval:
            return ExecutionResult(success=False, error="User denied")
        session.grant_permission(tool_name)
    
    # 4. Get tool
    tool = registry.get_tool(tool_name)
    if not tool:
        return ExecutionResult(
            success=False,
            error=f"Tool not found: {tool_name}"
        )
    
    # 5. Execute with timeout
    try:
        result = await asyncio.wait_for(
            tool.execute(**arguments),
            timeout=30.0
        )
    except asyncio.TimeoutError:
        return ExecutionResult(
            success=False,
            error="Tool execution timed out"
        )
    except Exception as e:
        logger.error(f"Tool failed: {e}")
        return ExecutionResult(success=False, error=str(e))
    
    # 6. Track in session
    session.add_history("tool_call", {
        "tool": tool_name,
        "args": arguments,
        "result": result
    })
    
    # 7. Return
    return ExecutionResult(success=True, result=result)
```

---

### **3. Session Management:**

**✅ PERSISTENT STATE (Claude pattern):**

```python
class ProductionSession:
    """
    Best practices from Claude Code + Copilot.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.cwd = os.getcwd()
        
        # Context (Claude pattern)
        self.context_tokens = 0
        self.max_tokens = 200_000  # Claude Sonnet limit
        
        # Permissions (Copilot pattern)
        self.granted_permissions = set()
        self.denied_permissions = set()
        
        # History
        self.history = []
        self.checkpoints = []
        
        # File tracking (Cursor pattern)
        self.read_files = set()
        self.modified_files = set()
    
    def should_clear_context(self) -> bool:
        """Check if context should be cleared (Claude pattern)."""
        return self.context_tokens > (self.max_tokens * 0.8)
    
    def create_checkpoint(self):
        """Save current state (Claude pattern)."""
        self.checkpoints.append({
            "timestamp": datetime.now(),
            "history": self.history[-50:],
            "permissions": self.granted_permissions.copy(),
        })
    
    def has_permission(self, tool_name: str) -> bool:
        """Check if tool is allowed (Copilot pattern)."""
        if tool_name in self.denied_permissions:
            return False
        return tool_name in self.granted_permissions
```

---

## 🔥 OUR IMPLEMENTATION STRATEGY

### **Phase 2.2 Actions:**

1. **✅ Implement Hybrid Registry:**
   - Core tools (always loaded)
   - Dynamic discovery based on project
   - Lazy loading for heavy tools

2. **✅ Multi-Layer Execution:**
   - Safety validation (blacklist/whitelist)
   - Permission system (session-based)
   - Timeout enforcement
   - Session tracking

3. **✅ Session Management:**
   - Persistent state
   - Context monitoring
   - Checkpoint system
   - Permission caching

4. **✅ Security First:**
   - Copilot-style defense-in-depth
   - Claude-style sandboxing
   - Cursor-style workspace trust

---

## 📊 COMPARISON TABLE

| Feature | Copilot CLI | Cursor AI | Claude Code | **OUR IMPL** |
|---------|-------------|-----------|-------------|--------------|
| Tool Registry | Static | Dynamic | MCP Code | **Hybrid** ✅ |
| Execution | Permission-based | Context-aware | Code-based | **Multi-layer** ✅ |
| Session State | Yes | Limited | Yes (CLAUDE.md) | **Yes + checkpoints** ✅ |
| Security | Defense-in-depth | Workspace Trust | Sandbox | **All 3** ✅ |
| Permission Model | Explicit approval | Trust-based | Mode-based | **Hybrid** ✅ |
| Context Management | Timeline | N/A | Token tracking | **Token + timeline** ✅ |
| Tool Discovery | No | Yes | No | **Yes** ✅ |

---

## 🎯 IMPLEMENTATION CHECKLIST

**Phase 2.2 (Today):**
- [x] Research complete
- [ ] Implement hybrid registry
- [ ] Add tool registration in ShellBridge
- [ ] Fix 3 failing tests
- [ ] Add permission system
- [ ] Session checkpoint support
- [ ] End-to-end test with real LLM

**Success Criteria:**
- 20/20 tests passing
- <200ms execution latency
- 100% dangerous ops blocked
- Session persistence working

---

**Research Complete!** Now implementing...

**Sources:**
- GitHub Copilot CLI Documentation (2024-2025)
- Cursor AI Engineering Blog + Forums
- Anthropic Claude Code Best Practices (Nov 2025)
- MCP Code Execution Whitepaper

**Next:** Implement hybrid registry + multi-layer execution pipeline!

---

_"Copy from one, it's plagiarism; copy from three, it's research."_  
— Unknown

**Let's build the best of all 3! 🚀**
