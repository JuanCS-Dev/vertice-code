"""
Persistent Event Emitter with Outbox Pattern.

Wraps the event bus to provide reliable event delivery through
the outbox pattern. Events are persisted before emission.

Part of P0-3: Event Persistence Implementation
Created with love by: JuanCS Dev & Claude Opus 4.5
Date: 2026-01-06

Reference:
- bubus (https://github.com/browser-use/bubus) - Production event bus with WAL
"""

import logging

from vertice_core.messaging.events import Event
from .persistence import persistence

logger = logging.getLogger(__name__)


class PersistentEventEmitter:
    """
    Event emitter with outbox pattern for reliable delivery.

    Flow:
    1. Store event in outbox table (persisted)
    2. Emit event via event bus
    3. Mark as delivered in outbox
    4. On failure: event remains in outbox for replay
    """

    def __init__(self, event_bus):
        """
        Initialize persistent event emitter.

        Args:
            event_bus: Underlying event bus to use for emission
        """
        self.event_bus = event_bus
        self._initialized = False

    async def initialize(self):
        """Initialize persistence layer."""
        if self._initialized:
            return
        await persistence.initialize()
        self._initialized = True

    async def emit_persistent(self, event: Event) -> bool:
        """
        Emit event with persistence guarantee.

        Args:
            event: Event to emit (must be a dataclass Event)

        Returns:
            True if event was persisted and emitted successfully
        """
        if not self._initialized:
            await self.initialize()

        # Extract event data
        event_type = type(event).__name__
        event_data = event.data if hasattr(event, "data") else {}
        source = event.source if hasattr(event, "source") else "prometheus"

        try:
            # Step 1: Store in outbox (CRITICAL - persisted to disk)
            event_id = await persistence.store_event(event_type, event_data, source)

            # Step 2: Emit via event bus (best-effort)
            try:
                self.event_bus.emit_sync(event)
            except Exception as e:
                logger.warning(f"Event bus emission failed for {event_type}: {e}")
                # Event is in outbox, will be replayed later
                return False

            # Step 3: Mark as delivered (success)
            await persistence.mark_event_delivered(event_id)
            return True

        except Exception as e:
            logger.error(f"Failed to persist event {event_type}: {e}")
            return False

    async def replay_undelivered_events(self, max_events: int = 100) -> int:
        """
        Replay undelivered events from outbox.

        This should be called on initialization or periodically
        to ensure all events eventually get delivered.

        Args:
            max_events: Maximum number of events to replay

        Returns:
            Number of events successfully replayed
        """
        if not self._initialized:
            await self.initialize()

        undelivered = await persistence.get_undelivered_events(limit=max_events)
        replayed = 0

        for event_dict in undelivered:
            event_id = event_dict["id"]
            event_type = event_dict["event_type"]
            event_data = event_dict["event_data"]

            try:
                # Reconstruct event object
                # For now, we emit a generic Event since we don't have the class
                from vertice_core.messaging.events import Event

                event = Event(data=event_data, source=event_dict["source"])

                # Try to emit again
                self.event_bus.emit_sync(event)

                # Mark as delivered
                await persistence.mark_event_delivered(event_id)
                replayed += 1

            except Exception as e:
                logger.warning(f"Failed to replay event {event_id} ({event_type}): {e}")
                await persistence.increment_retry_count(event_id)

        if replayed > 0:
            logger.info(f"Replayed {replayed}/{len(undelivered)} undelivered events")

        return replayed

    async def cleanup_old_events(self, older_than_hours: int = 24) -> int:
        """
        Clean up old delivered events.

        Args:
            older_than_hours: Delete events delivered more than N hours ago

        Returns:
            Number of events deleted
        """
        if not self._initialized:
            await self.initialize()

        return await persistence.cleanup_delivered_events(older_than_hours)

    def emit_sync(self, event: Event) -> None:
        """
        Synchronous emission without persistence (legacy compatibility).

        For persistent emission, use emit_persistent() instead.

        Args:
            event: Event to emit
        """
        self.event_bus.emit_sync(event)
