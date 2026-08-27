"""Ulanzi Renderer integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    ATTR_PAYLOAD,
    ATTR_PRIORITY,
    ATTR_SLOT_ID,
    ATTR_TTL_SECONDS,
    CONF_BROKER_HOST,
    CONF_BROKER_PORT,
    CONF_PREFIX,
    DATA_COORDINATOR,
    DEFAULT_PREFIX,
    DOMAIN,
    SERVICE_PUBLISH,
    SERVICE_RETRACT,
)
from .coordinator import UlanziRendererCoordinator
from .mqtt_publisher import MqttPublisher

PUBLISH_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_SLOT_ID): cv.string,
        vol.Required(ATTR_PRIORITY): vol.Coerce(int),
        vol.Required(ATTR_PAYLOAD): dict,
        vol.Optional(ATTR_TTL_SECONDS): vol.All(
            vol.Coerce(float), vol.Range(min=0, min_included=False)
        ),
    }
)

RETRACT_SCHEMA = vol.Schema({vol.Required(ATTR_SLOT_ID): cv.string})


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration namespace."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ulanzi Renderer from a config entry."""
    prefix = entry.data.get(CONF_PREFIX, DEFAULT_PREFIX).strip("/")
    topic = f"{prefix}/custom/test"
    publisher = MqttPublisher(hass, topic)
    coordinator = UlanziRendererCoordinator(hass, publisher)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        CONF_HOST: entry.data.get(CONF_BROKER_HOST),
        CONF_PORT: entry.data.get(CONF_BROKER_PORT),
    }

    async def async_handle_publish(call: ServiceCall) -> None:
        coordinator.upsert(
            call.data[ATTR_SLOT_ID],
            call.data[ATTR_PRIORITY],
            call.data[ATTR_PAYLOAD],
            call.data.get(ATTR_TTL_SECONDS),
        )
        await coordinator.async_tick()

    async def async_handle_retract(call: ServiceCall) -> None:
        coordinator.retract(call.data[ATTR_SLOT_ID])
        await coordinator.async_tick()

    hass.services.async_register(
        DOMAIN,
        SERVICE_PUBLISH,
        async_handle_publish,
        schema=PUBLISH_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_RETRACT,
        async_handle_retract,
        schema=RETRACT_SCHEMA,
    )
    await coordinator.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and release services and timers."""
    data = hass.data[DOMAIN].pop(entry.entry_id)
    coordinator: UlanziRendererCoordinator = data[DATA_COORDINATOR]
    await coordinator.async_stop()
    hass.services.async_remove(DOMAIN, SERVICE_PUBLISH)
    hass.services.async_remove(DOMAIN, SERVICE_RETRACT)
    return True
