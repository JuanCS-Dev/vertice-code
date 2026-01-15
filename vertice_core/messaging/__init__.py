"""
Messaging module stub for vertice_core.

This forwards to the real implementation in src/vertice_core/messaging.
"""

from typing import Optional

# Minimal EventBus implementation for compatibility
class EventBus:
    """Minimal event bus for compatibility."""
    
    def __init__(self):
        self._handlers = {}
    
    def emit(self, event):
        """Emit an event."""
        event_type = type(event).__name__
        for handler in self._handlers.get(event_type, []):
            handler(event)
    
    def subscribe(self, event_type, handler):
        """Subscribe to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

# Global event bus
_global_bus: Optional[EventBus] = None

def get_event_bus() -> EventBus:
    """Get or create the global event bus."""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus

__all__ = ["EventBus", "get_event_bus"]
