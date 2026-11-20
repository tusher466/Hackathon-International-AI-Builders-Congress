"""Bounded in-memory ring buffer for fast dashboard queries."""
from __future__ import annotations

import threading
from collections import defaultdict, deque
from typing import Deque, Dict, List, Optional

from ingestion.schemas import SensorReading


class RingBuffer:
    """Thread-safe bounded ring buffer per machine."""

    def __init__(self, maxlen: int = 500):
        self.maxlen = maxlen
        self._buffers: Dict[str, Deque[SensorReading]] = defaultdict(lambda: deque(maxlen=self.maxlen))
        self._lock = threading.RLock()

    def add(self, reading: SensorReading) -> None:
        with self._lock:
            self._buffers[reading.machine_id].append(reading)

    def get_recent(self, machine_id: str, limit: int = 100) -> List[SensorReading]:
        with self._lock:
            buf = self._buffers.get(machine_id)
            if not buf:
                return []
            # deque stores oldest first, newest at right
            items = list(buf)
            if limit:
                items = items[-limit:]
            return items

    def get_all_machines(self) -> List[str]:
        with self._lock:
            return list(self._buffers.keys())

    def clear(self, machine_id: Optional[str] = None) -> None:
        with self._lock:
            if machine_id:
                self._buffers.pop(machine_id, None)
            else:
                self._buffers.clear()

    def count(self, machine_id: str) -> int:
        with self._lock:
            buf = self._buffers.get(machine_id)
            return len(buf) if buf else 0

    def last_sequence(self, machine_id: str) -> Optional[int]:
        with self._lock:
            buf = self._buffers.get(machine_id)
            if buf and len(buf) > 0:
                return buf[-1].sequence
            return None


# Global singleton
_global_buffer: Optional[RingBuffer] = None


def get_ring_buffer() -> RingBuffer:
    global _global_buffer
    if _global_buffer is None:
        from config.settings import get_settings
        settings = get_settings()
        _global_buffer = RingBuffer(maxlen=settings.RING_BUFFER_SIZE)
    return _global_buffer
