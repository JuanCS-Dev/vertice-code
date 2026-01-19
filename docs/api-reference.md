# VERTICE Context API Reference

## Masking Module

### mask_tool_output()

Mask tool output for context efficiency.

```python
from tui.core.context import mask_tool_output

result = mask_tool_output(
    output: str,           # Raw tool output
    tool_name: str = "tool",  # Tool identifier
    preserve_errors: bool = True,  # Keep errors intact
) -> ToolMaskingResult
```

**Returns:** `ToolMaskingResult`
- `content: str` - Masked content
- `original_tokens: int` - Original token count
- `masked_tokens: int` - After masking
- `was_masked: bool` - Whether masking occurred
- `compression_ratio: float` - Compression ratio
- `tokens_saved: int` - Tokens saved

### ObservationMasker

```python
from tui.core.context import ObservationMasker

masker = ObservationMasker()

# Mask content
result: MaskedContent = masker.mask_content(content: str)

# Get statistics
stats: Dict[str, Any] = masker.get_stats()

# Reset statistics
masker.reset_stats()
```

---

## Sliding Window Module

### get_sliding_window()

Get singleton compressor instance.

```python
from tui.core.context import get_sliding_window

compressor = get_sliding_window()
```

### SlidingWindowCompressor

```python
from tui.core.context import SlidingWindowCompressor, WindowConfig

# Create with custom config
config = WindowConfig(
    max_tokens=32_000,
    target_tokens=24_000,
    trigger_percent=0.64,
)
compressor = SlidingWindowCompressor(config=config)

# Add messages
compressor.add_message(
    role: str,              # "user", "assistant", "system", "tool"
    content: str,           # Message content
    priority: float = 0.5,  # 0.0-1.0 (higher = keep longer)
)

# Check compression need
needs: bool = compressor.needs_compression()

# Compress
from tui.core.context import WindowStrategy

result: CompressionResult = compressor.compress(
    strategy: WindowStrategy = WindowStrategy.PRIORITY,
    force: bool = False,
)

# Properties
utilization: float = compressor.utilization  # 0.0-1.0
total_tokens: int = compressor.total_tokens
message_count: int = compressor.message_count

# Get context
context: str = compressor.get_context_string()

# Get stats
stats: Dict[str, Any] = compressor.get_stats()

# Clear
compressor.clear()

# Get compression history
history: List[CompressionResult] = compressor.get_compression_history()
```

### WindowStrategy

```python
from tui.core.context import WindowStrategy

WindowStrategy.FIFO          # Remove oldest first
WindowStrategy.PRIORITY      # Remove low-priority first
WindowStrategy.HIERARCHICAL  # Tiered compression
WindowStrategy.ADAPTIVE      # Auto-select best
```

### CompressionResult

```python
@dataclass
class CompressionResult:
    strategy_used: WindowStrategy
    tokens_before: int
    tokens_after: int
    tokens_saved: int
    messages_before: int
    messages_after: int
    compression_ratio: float
    duration_ms: float
```

---

## Thought Signatures Module

### get_thought_manager()

Get singleton manager instance.

```python
from tui.core.context import get_thought_manager

manager = get_thought_manager()
```

### ThoughtSignatureManager

```python
from tui.core.context import ThoughtSignatureManager, ThinkingLevel

manager = ThoughtSignatureManager()

# Create signature
sig: ThoughtSignature = manager.create_signature(
    hypothesis: str,          # Current reasoning
    thinking_level: ThinkingLevel,
    parent_id: Optional[str] = None,
    key_observations: List[str] = [],
)

# Get chain
chain: List[ThoughtSignature] = manager.get_chain(signature_id: str)

# Get active signature
active: Optional[ThoughtSignature] = manager.get_active_signature()

# Get reasoning context
context: str = manager.get_reasoning_context()

# Set thinking level
manager.set_thinking_level(level: ThinkingLevel)

# Clear chain
manager.clear_chain()

# Get stats
stats: Dict[str, Any] = manager.get_stats()
```

### ThinkingLevel

```python
from tui.core.context import ThinkingLevel

ThinkingLevel.MINIMAL  # Trivial operations
ThinkingLevel.LOW      # Simple fixes
ThinkingLevel.MEDIUM   # Standard tasks
ThinkingLevel.HIGH     # Complex architecture
```

### ThoughtSignature

```python
@dataclass
class ThoughtSignature:
    signature_id: str
    thinking_level: ThinkingLevel
    hypothesis: str
    key_observations: List[str]
    parent_id: Optional[str]
    created_at: datetime
    status: SignatureStatus

    def encode(self) -> str
    @classmethod
    def decode(cls, encoded: str) -> "ThoughtSignature"
    def is_expired(self, ttl_seconds: int = 300) -> bool
```

---

## Widget Module

### TokenDashboard

```python
from tui.widgets import TokenDashboard

dashboard = TokenDashboard(id="token-dashboard")

# Update usage
dashboard.update_usage(
    used: int,
    limit: Optional[int] = None,
)

# Update breakdown
dashboard.update_breakdown(
    messages: int = 0,
    files: int = 0,
    summary: int = 0,
    system: int = 0,
    tools: int = 0,
)

# Update compression
dashboard.update_compression(
    ratio: float,
    is_compacting: bool = False,
    count: int = 0,
)

# Update thinking level
dashboard.update_thinking_level(level: str)

# Toggle collapsed
dashboard.toggle_collapsed()

# Get stats
stats: Dict[str, Any] = dashboard.get_stats()
```

### MiniTokenMeter

```python
from tui.widgets import MiniTokenMeter

meter = MiniTokenMeter(id="mini-meter")

# Reactive properties
meter.used = 8000
meter.limit = 32000

# Render
rendered: str = meter.render()  # "▰▰▰▱▱ 8k/32k"
```

### TokenMeter

```python
from tui.widgets import TokenMeter

meter = TokenMeter(id="meter")
meter.used = 16000
meter.limit = 32000

rendered: str = meter.render()
# "[████████░░] 16k/32k (50%)"
```

---

## Convenience Exports

All components are available from `tui.core.context`:

```python
from tui.core.context import (
    # Masking
    MaskingStrategy,
    ContentType,
    MaskedContent,
    MaskingResult,
    ToolMaskingResult,
    ObservationMasker,
    mask_observation,
    mask_tool_output,

    # Sliding Window
    WindowStrategy,
    WindowConfig,
    Message,
    CompressionResult,
    SlidingWindowCompressor,
    get_sliding_window,

    # Thought Signatures
    ThinkingLevel,
    SignatureStatus,
    ThoughtSignature,
    ThoughtSignatureManager,
    get_thought_manager,
    create_thought_signature,
)
```

---

*Soli Deo Gloria*
