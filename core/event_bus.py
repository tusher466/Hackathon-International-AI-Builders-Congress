"""In-process pub/sub used by websocket + pipeline."""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class EventBus:
    """Simple fan-out event bus with asyncio queues per subscriber."""

    def __init__(self):
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._global_subscribers: List[asyncio.Queue] = []
        self._lock = asyncio.Lock()

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish event with envelope {type, ts, payload}."""
        envelope = {
            "type": event_type,
            "ts": datetime.now(timezone.utc).isoformat(),
            "payload": payload,
        }
        # Put to global subscribers
        for q in list(self._global_subscribers):
            try:
                q.put_nowait(envelope)
            except asyncio.QueueFull:
                logger.warning(f"EventBus queue full, dropping {event_type}")
            except Exception as e:
                logger.warning(f"EventBus publish error: {e}")

        # Put to type-specific subscribers if any
        specific = self._subscribers.get(event_type, [])
        for q in list(specific):
            try:
                q.put_nowait(envelope)
            except Exception as e:
                logger.warning(f"EventBus specific publish error: {e}")

    def subscribe(self, event_type: Optional[str] = None, maxsize: int = 1000) -> asyncio.Queue:
        """Subscribe returns a queue that will receive events.

        If event_type is None, receives all events. Otherwise only that type.
        """
        q: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        if event_type is None:
            self._global_subscribers.append(q)
        else:
            self._subscribers.setdefault(event_type, []).append(q)
        return q

    def unsubscribe(self, queue: asyncio.Queue, event_type: Optional[str] = None) -> None:
        if event_type is None:
            if queue in self._global_subscribers:
                self._global_subscribers.remove(queue)
        else:
            lst = self._subscribers.get(event_type, [])
            if queue in lst:
                lst.remove(queue)

    def clear(self) -> None:
        self._subscribers.clear()
        self._global_subscribers.clear()


# Global singleton
_global_bus: Optional[EventBus] = None


def get_event_bus() -> EventBus:
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus
