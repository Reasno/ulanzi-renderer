"""MQTT output adapter for Ulanzi Renderer."""

from __future__ import annotations
import hashlib
import json
from typing import Any
from homeassistant.components import mqtt
from homeassistant.core import HomeAssistant

class MqttPublisher:
    """Publish stable JSON payloads through Home Assistant MQTT."""
    def __init__(self, hass: HomeAssistant, topic: str) -> None:
        self._hass = hass
        self.topic = topic
        self.last_payload_hash: str | None = None

    @staticmethod
    def serialize(payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    async def async_publish_if_changed(self, payload: dict[str, Any], *, force: bool = False) -> bool:
        serialized = self.serialize(payload)
        payload_hash = hashlib.sha256(serialized.encode()).hexdigest()
        if not force and payload_hash == self.last_payload_hash:
            return False
        await mqtt.async_publish(self._hass, self.topic, serialized, qos=0, retain=False)
        self.last_payload_hash = payload_hash
        return True
