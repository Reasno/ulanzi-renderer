"""Config flow for Ulanzi Renderer."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_BROKER_HOST,
    CONF_BROKER_PORT,
    CONF_PREFIX,
    DEFAULT_BROKER_HOST,
    DEFAULT_BROKER_PORT,
    DEFAULT_PREFIX,
    DOMAIN,
)


class UlanziRendererConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle UI setup for Ulanzi Renderer."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Collect broker metadata and the Ulanzi MQTT prefix."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Ulanzi Renderer", data=user_input)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_BROKER_HOST, default=DEFAULT_BROKER_HOST
                ): str,
                vol.Required(
                    CONF_BROKER_PORT, default=DEFAULT_BROKER_PORT
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=65535)),
                vol.Required(CONF_PREFIX, default=DEFAULT_PREFIX): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)
