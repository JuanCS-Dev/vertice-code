# PROMETHEUS TUI Integration Plan
## VERTICE - Meta-Agent Exposure & Toggle System

**Project:** Vertice-Code
**Date:** 2026-01-04
**Goal:** Integrate PROMETHEUS meta-agent into TUI with toggle, status bar indicator, and persistence

---

## Executive Summary

PROMETHEUS is an 8,000+ line meta-agent system that integrates 6 research breakthroughs (Agent0, SimuRA, MIRIX, Reflexion, AutoTools, Tree of Thoughts). Currently it's "invisible" - commands exist but:
1. Bridge class is missing required attributes (`_provider_mode`)
2. No visual indicator in status bar
3. No keyboard shortcut for quick toggle
4. No persistence of user preference

This plan follows the **Tribunal Mode pattern** (Ctrl+M) as reference implementation.

---

## Research Insights (2026)

| Source | Pattern |
|--------|---------|
| [Windsurf Flow](https://www.builder.io/blog/agentic-ide) | Granular automation controls |
| [Adaptive Orchestrator](https://www.getdynamiq.ai/post/agent-orchestration-patterns-in-multi-agent-systems-linear-and-adaptive-approaches-with-dynamiq) | Status Monitoring, Dynamic Flow |
| [Meta-Agents](https://medium.com/@varunharsha1992/meta-agents-towards-scalable-ai-agent-development-e380737efdbb) | Interaction Configurator, feedback loops |

---

## Current State

### Existing Commands (vertice_tui/handlers/basic.py:198-250)
- `/prometheus status` - Show system status
- `/prometheus evolve N` - Run evolution iterations
- `/prometheus memory` - Show memory status
- `/prometheus enable` - Enable mode
- `/prometheus disable` - Disable mode

### Issues Found
1. **Bridge missing `_provider_mode`** - Referenced in app.py:420-436 but not initialized
2. **No status bar indicator** - Tribunal has badge, PROMETHEUS doesn't
3. **No keyboard shortcut** - Ctrl+M for Tribunal, nothing for PROMETHEUS
4. **Auto-detection exists** - ProviderManager routes complex tasks but no visual feedback

---

## Implementation Plan

### Phase 1: Fix Bridge Initialization

**File:** `vertice_tui/core/bridge.py`
**Location:** After line 137 (after `_a2a_manager`)

```python
# PROMETHEUS state
self._provider_mode: str = "auto"  # Synced with _provider_manager.mode
```

Add property after `status_line` (line 168):

```python
@property
def prometheus_mode(self) -> bool:
    """Check if PROMETHEUS mode is enabled."""
    return self._provider_manager.mode == "prometheus"

@prometheus_mode.setter
def prometheus_mode(self, enabled: bool) -> None:
    """Enable or disable PROMETHEUS mode."""
    self._provider_manager.mode = "prometheus" if enabled else "auto"
    self._provider_mode = self._provider_manager.mode
```

---

### Phase 2: Add StatusBar Reactive

**File:** `vertice_tui/widgets/status_bar.py`

Add reactive after line 85 (`tribunal_mode`):
```python
prometheus_mode: reactive[bool] = reactive(False)
```

Update `_format_model()` at line 112:
```python
def _format_model(self) -> str:
    """Format model name with mode indicators."""
    if self.prometheus_mode:
        return "[bold #FF6B00]PROMETHEUS[/bold #FF6B00]"  # Orange/Fire
    if self.tribunal_mode:
        return "[bold #EF4444]TRIBUNAL[/bold #EF4444]"
    if not self.llm_connected:
        return "[dim]No Model[/dim]"
    return f"[bold]{self.model_name}[/bold]"
```

Add watcher after `watch_tribunal_mode`:
```python
def watch_prometheus_mode(self, value: bool) -> None:
    """Update display when PROMETHEUS mode changes."""
    self._update_element("#model", self._format_model())
```

---

### Phase 3: Add Keyboard Binding

**File:** `vertice_tui/app.py`

Add binding after line 66 (after `ctrl+m`):
```python
Binding("ctrl+shift+p", "toggle_prometheus", "Prometheus", show=True),
```

Add action method (after `action_toggle_tribunal`):
```python
def action_toggle_prometheus(self) -> None:
    """Toggle PROMETHEUS mode - self-evolving meta-agent."""
    status = self.query_one(StatusBar)
    status.prometheus_mode = not status.prometheus_mode

    # Update bridge
    self.bridge.prometheus_mode = status.prometheus_mode

    # Persist preference
    ThemeManager.save_prometheus_preference(status.prometheus_mode)

    # User feedback
    response = self.query_one("#response", ResponseView)
    if status.prometheus_mode:
        mode_text = (
            "**PROMETHEUS MODE ENABLED**\n\n"
            "Self-evolving meta-agent activated:\n"
            "- World Model simulation (SimuRA)\n"
            "- 6-type memory system (MIRIX)\n"
            "- Self-reflection engine (Reflexion)\n"
            "- Co-evolution learning (Agent0)\n\n"
            "*Complex tasks will use enhanced reasoning.*"
        )
    else:
        mode_text = "**PROMETHEUS MODE DISABLED**\n\nReturned to standard mode."

    response.add_system_message(mode_text)
```

---

### Phase 4: Add Persistence

**File:** `vertice_tui/themes/theme_manager.py`

Add methods after `get_auto_theme()` (line 421):

```python
@classmethod
def get_prometheus_preference(cls) -> bool:
    """Load saved prometheus preference."""
    try:
        if cls.CONFIG_FILE.exists():
            config = json.loads(cls.CONFIG_FILE.read_text())
            return config.get("prometheus_mode", False)
    except (json.JSONDecodeError, IOError):
        pass
    return False

@classmethod
def save_prometheus_preference(cls, enabled: bool) -> None:
    """Save prometheus preference to config file."""
    try:
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        config = {}
        if cls.CONFIG_FILE.exists():
            try:
                config = json.loads(cls.CONFIG_FILE.read_text())
            except json.JSONDecodeError:
                pass
        config["prometheus_mode"] = enabled
        cls.CONFIG_FILE.write_text(json.dumps(config, indent=2))
    except IOError:
        pass
```

---

### Phase 5: Restore State on Startup

**File:** `vertice_tui/app.py`

In `on_mount()` method, add after theme restoration:
```python
# Restore PROMETHEUS mode preference
prometheus_enabled = ThemeManager.get_prometheus_preference()
if prometheus_enabled:
    status = self.query_one(StatusBar)
    status.prometheus_mode = True
    self.bridge.prometheus_mode = True
```

---

### Phase 6: Fix /prometheus Commands

**File:** `vertice_tui/handlers/basic.py`

Update `_handle_prometheus` to sync with StatusBar:

```python
elif subcommand == "enable":
    self.bridge.prometheus_mode = True
    try:
        from vertice_tui.widgets.status_bar import StatusBar
        status = self.app.query_one(StatusBar)
        status.prometheus_mode = True
    except Exception:
        pass
    ThemeManager.save_prometheus_preference(True)
    view.add_success("PROMETHEUS mode enabled.")

elif subcommand == "disable":
    self.bridge.prometheus_mode = False
    try:
        from vertice_tui.widgets.status_bar import StatusBar
        status = self.app.query_one(StatusBar)
        status.prometheus_mode = False
    except Exception:
        pass
    ThemeManager.save_prometheus_preference(False)
    view.add_success("PROMETHEUS mode disabled.")
```

---

## Files to Modify

| File | Changes | Lines |
|------|---------|-------|
| `vertice_tui/core/bridge.py` | Add `_provider_mode`, `prometheus_mode` property | ~138, ~170 |
| `vertice_tui/widgets/status_bar.py` | Add `prometheus_mode` reactive, update `_format_model()`, add watcher | ~86, ~112 |
| `vertice_tui/app.py` | Add `Ctrl+Shift+P` binding, add `action_toggle_prometheus()` | ~67, ~450 |
| `vertice_tui/themes/theme_manager.py` | Add `get_prometheus_preference()`, `save_prometheus_preference()` | ~422 |
| `vertice_tui/handlers/basic.py` | Sync `/prometheus enable/disable` with StatusBar | ~232-240 |

---

## Testing Checklist

- [ ] `Ctrl+Shift+P` toggles PROMETHEUS mode
- [ ] Status bar shows orange "PROMETHEUS" badge when enabled
- [ ] `/prometheus enable` syncs with status bar
- [ ] `/prometheus disable` syncs with status bar
- [ ] Preference persists in `~/.vertice_tui/config.json`
- [ ] PROMETHEUS state restores on app startup
- [ ] Tribunal and PROMETHEUS modes are independent

---

## Visual Result

**Status bar when PROMETHEUS enabled:**
```
▸ READY │ PROMETHEUS │ ◆ Coder │ ▰▰▱▱▱ 15k/32k │ $0.05 │ ✓
         ^^^^^^^^^^^
         Orange badge
```

**Status bar when TRIBUNAL enabled:**
```
▸ READY │ TRIBUNAL │ ◆ Coder │ ▰▰▱▱▱ 15k/32k │ $0.05 │ ✓
         ^^^^^^^^
         Red badge
```

---

*Plan created: 2026-01-04*
*Reference: Tribunal Mode pattern (Ctrl+M)*
*Author: Claude Opus 4.5*
