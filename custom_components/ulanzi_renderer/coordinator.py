"""Tick coordinator for Ulanzi Renderer."""

from __future__ import annotations

from datetime import timedelta
import hashlib
import json
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DEFAULT_TICK_INTERVAL,
    ENABLE_ENTITY_ID,
    SHADOW_HEAD_ENTITY_ID,
    STATUS_ENTITY_ID,
)
from .mqtt_publisher import MqttPublisher
from .renderer import DisplaySlot, Renderer

_LOGGER = logging.getLogger(__name__)


class UlanziRendererCoordinator:
    """Own renderer state, the one-second tick, and the single output path."""

    def __init__(self, hass: HomeAssistant, publisher: MqttPublisher) -> None:
        self.hass = hass
        self.renderer = Renderer()
        self.publisher = publisher
        self._remove_tick = None
        self._last_head_request_id: str | None = None

    async def async_start(self) -> None:
        """Start periodic rendering."""
        self._remove_tick = async_track_time_interval(
            self.hass,
            self.async_tick,
            timedelta(seconds=DEFAULT_TICK_INTERVAL),
        )
        await self.async_tick()

    async def async_stop(self) -> None:
        """Stop periodic rendering."""
        if self._remove_tick is not None:
            self._remove_tick()
            self._remove_tick = None

    def upsert(
        self,
        slot_id: str,
        priority: int,
        payload: dict[str, Any],
        ttl_seconds: float | None,
    ) -> DisplaySlot:
        """Submit a display intent."""
        return self.renderer.upsert(slot_id, priority, payload, ttl_seconds)

    def retract(self, slot_id: str) -> None:
        """Retract a display intent idempotently."""
        self.renderer.retract(slot_id)

    async def async_tick(self, _now: Any = None) -> None:
        """Choose the current head and publish only when active mode is enabled."""
        slot = self.renderer.peek_active()
        enabled = self.hass.states.is_state(ENABLE_ENTITY_ID, "on")
        mode = "active" if enabled else "shadow"

        payload_hash = None
        if slot is not None:
            serialized = json.dumps(
                slot.payload,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            payload_hash = hashlib.sha256(serialized.encode()).hexdigest()

        attributes = {
            "mode": mode,
            "head": slot.slot_id if slot else None,
            "head_priority": slot.priority if slot else None,
            "slot_count": len(self.renderer.slots),
            "heap_size": self.renderer.heap_size,
            "payload_hash": payload_hash,
        }
        self.hass.states.async_set(STATUS_ENTITY_ID, mode, attributes)
        self.hass.states.async_set(
            SHADOW_HEAD_ENTITY_ID,
            slot.slot_id if slot else "none",
            attributes,
        )

        request_id = slot.request_id if slot else None
        if request_id != self._last_head_request_id:
            _LOGGER.info(
                "Renderer head changed to %s (priority=%s, mode=%s)",
                slot.slot_id if slot else None,
                slot.priority if slot else None,
                mode,
            )
            self._last_head_request_id = request_id

        if enabled and slot is not None:
            await self.publisher.async_publish_if_changed(slot.payload)
