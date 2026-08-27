"""Priority queue used by Ulanzi Renderer."""

from __future__ import annotations
from dataclasses import dataclass, field
import heapq
import time
from typing import Any
import uuid

@dataclass(slots=True)
class DisplaySlot:
    """A display intent participating in priority arbitration."""
    slot_id: str
    priority: int
    payload: dict[str, Any]
    request_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    expires_at: float | None = None
    updated_at: float = field(default_factory=time.time)

class Renderer:
    """Maintain display slots with heapq and lazy deletion."""
    def __init__(self) -> None:
        self.slots: dict[str, DisplaySlot] = {}
        self._heap: list[tuple[int, float, str, str]] = []

    def upsert(self, slot_id: str, priority: int, payload: dict[str, Any], ttl_seconds: float | None = None, *, now: float | None = None) -> DisplaySlot:
        """Insert or replace a slot; stale heap entries are deleted lazily."""
        updated_at = time.time() if now is None else now
        expires_at = updated_at + ttl_seconds if ttl_seconds is not None else None
        slot = DisplaySlot(slot_id=slot_id, priority=priority, payload=dict(payload), expires_at=expires_at, updated_at=updated_at)
        self.slots[slot_id] = slot
        heapq.heappush(self._heap, (slot.priority, slot.updated_at, slot.request_id, slot.slot_id))
        return slot

    def retract(self, slot_id: str) -> None:
        """Remove from the truth store; heap cleanup is deferred."""
        self.slots.pop(slot_id, None)

    def peek_active(self, now: float | None = None) -> DisplaySlot | None:
        """Return the highest-priority live slot after lazy cleanup."""
        timestamp = time.time() if now is None else now
        while self._heap:
            _, _, request_id, slot_id = self._heap[0]
            slot = self.slots.get(slot_id)
            if slot is None or slot.request_id != request_id:
                heapq.heappop(self._heap)
                continue
            if slot.expires_at is not None and slot.expires_at <= timestamp:
                self.slots.pop(slot_id, None)
                heapq.heappop(self._heap)
                continue
            return slot
        return None

    @property
    def heap_size(self) -> int:
        return len(self._heap)
