# VERTICE Context Architecture

## Component Overview

```
┌─────────────────────────────────────────────────────────┐
│                      TUI Layer                          │
│  ┌───────────────┐  ┌───────────┐  ┌────────────────┐   │
│  │ TokenDashboard │  │ StatusBar │  │ ResponseView   │   │
│  └───────┬───────┘  └─────┬─────┘  └───────┬────────┘   │
└──────────┼────────────────┼────────────────┼────────────┘
           │                │                │
┌──────────┴────────────────┴────────────────┴────────────┐
│                    Core Layer                            │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────┐   │
│  │ObservationMasker│  │SlidingWindow  │  │Thought    │   │
│  │                │  │Compressor     │  │Signatures │   │
│  └───────┬────────┘  └───────┬───────┘  └─────┬─────┘   │
└──────────┼───────────────────┼────────────────┼─────────┘
           │                   │                │
┌──────────┴───────────────────┴────────────────┴─────────┐
│                   Handler Layer                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │             ClaudeParityHandler                  │    │
│  │  /compact, /context, /tokens                     │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
           │
┌──────────┴──────────────────────────────────────────────┐
│                   Chat Controller                        │
│  ┌─────────────────────────────────────────────────┐    │
│  │  _execute_single_tool() -> uses masking          │    │
│  │  _run_agentic_loop() -> uses thought signatures  │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Tool Execution Flow

```
User Request
     │
     ▼
[ChatController._execute_single_tool]
     │
     ├──► Execute tool
     │
     ▼
[mask_tool_output(output)]
     │
     ├──► Returns ToolMaskingResult
     │    - content: compressed output
     │    - compression_ratio: 3.5x
     │    - tokens_saved: 500
     │
     ▼
Add to history with masked content
```

### 2. Context Compression Flow

```
User types /compact
     │
     ▼
[ClaudeParityHandler._handle_compact]
     │
     ├──► Check utilization (64% threshold)
     │
     ▼
[SlidingWindowCompressor.compress(strategy)]
     │
     ├──► Apply strategy (FIFO/PRIORITY/HIERARCHICAL)
     ├──► Remove low-priority messages
     ├──► Preserve bookends (first + last)
     │
     ▼
Return CompressionResult
     │
     ▼
Update TokenDashboard
```

### 3. Reasoning Chain Flow

```
User sends complex request
     │
     ▼
[ChatController._run_agentic_loop]
     │
     ├──► _determine_thinking_level(message)
     │    Returns: "high" for architecture tasks
     │
     ▼
[ThoughtSignatureManager.create_signature]
     │
     ├──► Creates parent signature
     │
     ▼
For each tool iteration:
     │
     ├──► Execute tool
     ├──► Create child signature (fork)
     ├──► Add observations
     │
     ▼
Complete chain with conclusion
```

## File Structure

```
tui/
├── core/
│   ├── context/
│   │   ├── __init__.py           # Exports
│   │   ├── masking.py            # ObservationMasker
│   │   ├── sliding_window.py     # SlidingWindowCompressor
│   │   └── thought_signatures.py # ThoughtSignatures
│   └── chat/
│       └── controller.py         # Uses all components
├── handlers/
│   └── claude_parity.py          # /compact, /context commands
├── widgets/
│   ├── token_meter.py            # TokenDashboard, MiniTokenMeter
│   └── status_bar.py             # Uses MiniTokenMeter
└── app.py                        # Mounts TokenDashboard
```

## Key Classes

### ObservationMasker (`masking.py`)

```python
class ObservationMasker:
    def mask_content(self, content: str) -> MaskedContent
    def get_stats(self) -> Dict[str, Any]
    def reset_stats(self) -> None

@dataclass
class ToolMaskingResult:
    content: str
    original_tokens: int
    masked_tokens: int
    was_masked: bool
    compression_ratio: float
    tokens_saved: int
```

### SlidingWindowCompressor (`sliding_window.py`)

```python
class SlidingWindowCompressor:
    def add_message(self, role: str, content: str, priority: float = 0.5)
    def needs_compression(self) -> bool
    def compress(self, strategy: WindowStrategy, force: bool = False) -> CompressionResult
    def get_context_string(self) -> str
    def get_stats(self) -> Dict[str, Any]

    @property
    def utilization(self) -> float
    @property
    def total_tokens(self) -> int
    @property
    def message_count(self) -> int
```

### ThoughtSignatureManager (`thought_signatures.py`)

```python
class ThoughtSignatureManager:
    def create_signature(
        self,
        hypothesis: str,
        thinking_level: ThinkingLevel,
        parent_id: Optional[str] = None,
    ) -> ThoughtSignature

    def get_chain(self, signature_id: str) -> List[ThoughtSignature]
    def get_active_signature(self) -> Optional[ThoughtSignature]
    def get_reasoning_context(self) -> str
```

## Configuration

### WindowConfig

```python
@dataclass
class WindowConfig:
    max_tokens: int = 32_000
    target_tokens: int = 24_000
    min_tokens: int = 4_000
    trigger_percent: float = 0.85
    emergency_percent: float = 0.95
    keep_recent: int = 5
    keep_system: bool = True
```

### Masking Strategies

```python
class MaskingStrategy(Enum):
    AGGRESSIVE = "aggressive"  # Maximum compression
    MODERATE = "moderate"      # Balanced
    CONSERVATIVE = "conservative"  # Preserve more
```

## Test Coverage

| Component | Tests | Location |
|-----------|-------|----------|
| ObservationMasker | 15 | `test_context_sprint4.py` |
| SlidingWindowCompressor | 15 | `test_context_sprint4.py` |
| ThoughtSignatures | 17 | `test_context_sprint4.py` |
| Integration | 8 | `test_context_sprint4.py` |
| E2E | 34 | `test_context_sprint5.py` |
| **Total** | **89** | |

---

*Soli Deo Gloria*
