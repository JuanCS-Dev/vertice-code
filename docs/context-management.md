# VERTICE Context Management Guide

## Overview

VERTICE provides intelligent context management inspired by Claude Code and Cursor patterns.
This guide covers the context optimization system implemented in Sprint 4-5.

## Components

### 1. ObservationMasker

Zero-cost context compression for tool outputs.

**Usage:**
```python
from tui.core.context import mask_tool_output, ToolMaskingResult

result = mask_tool_output(
    output="...",  # Tool output
    tool_name="grep",
    preserve_errors=True
)

print(result.content)  # Masked content
print(result.compression_ratio)  # e.g., 3.5x
print(result.tokens_saved)  # Tokens saved
```

**Benefits:**
- 60-80% context reduction for verbose outputs
- Preserves errors and important information
- Zero quality loss (research-backed)

### 2. SlidingWindowCompressor

Gemini-style progressive context truncation.

**Strategies:**
- `FIFO`: Remove oldest messages first
- `PRIORITY`: Keep high-priority messages
- `HIERARCHICAL`: Tiered compression (summary > recent > old)
- `ADAPTIVE`: Auto-select best strategy

**Usage:**
```python
from tui.core.context import get_sliding_window, WindowStrategy

compressor = get_sliding_window()

# Add messages
compressor.add_message("user", "Hello!")
compressor.add_message("assistant", "Hi there!")

# Check if compression needed (64% threshold)
if compressor.needs_compression():
    result = compressor.compress(strategy=WindowStrategy.PRIORITY)
    print(f"Saved {result.tokens_saved} tokens")
```

### 3. ThoughtSignatures

Gemini 3-style reasoning continuity across API calls.

**Thinking Levels:**
- `MINIMAL`: Trivial operations (hello, help)
- `LOW`: Simple fixes, small changes
- `MEDIUM`: Standard coding tasks
- `HIGH`: Complex architecture, design decisions

**Usage:**
```python
from tui.core.context import get_thought_manager, ThinkingLevel

manager = get_thought_manager()

sig = manager.create_signature(
    hypothesis="Designing authentication system",
    thinking_level=ThinkingLevel.HIGH,
)

# Fork for subtask
child = manager.create_signature(
    hypothesis="Implementing JWT validation",
    parent_id=sig.signature_id,
)
```

## TUI Commands

| Command | Description |
|---------|-------------|
| `/context` | Show full context breakdown |
| `/compact` | Compress context (auto-strategy) |
| `/compact fifo` | FIFO compression |
| `/compact priority` | Priority-based compression |
| `/tokens` | Quick token count |
| `Ctrl+D` | Toggle TokenDashboard |

## TokenDashboard Widget

Visual context usage indicator:

```
┌─ Context Usage ──────────────────────────┐
│ [████████░░░░░░░░] 8.5k/32k (27%)        │
│ Messages: 4.2k | Files: 2.1k | Sum: 1.5k │
│ ◆ 2.5x compressed | Auto: 64%           │
│ ◇◇◆◇ Medium                              │
└──────────────────────────────────────────┘
```

**Color Coding:**
- Green (< 60%): Healthy
- Yellow (60-85%): Elevated
- Orange (85-95%): Warning
- Red (> 95%): Critical

## Best Practices

1. **Auto-compact at 64%** (Claude Code pattern)
2. **Use PRIORITY strategy** for most cases
3. **Monitor thinking level** for complex tasks
4. **Check `/context`** before long sessions

## Configuration

```python
from tui.core.context import WindowConfig

config = WindowConfig(
    max_tokens=32_000,      # Max context size
    target_tokens=24_000,   # Target after compression
    trigger_percent=0.64,   # Auto-compact threshold
)
```

---

*Soli Deo Gloria*
