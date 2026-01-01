"""Config flow for Inventory Manager integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class InventoryManagerConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Inventory Manager."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id("inventory_manager")
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Gestionnaire d'Inventaire",
                data=user_input,
            )

        # Simplified form - just enable notifications
        data_schema = vol.Schema(
            {
                vol.Optional("notify_expiry", default=True): bool,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "InventoryManagerOptionsFlow":
        """Get the options flow for this handler."""
        return InventoryManagerOptionsFlow(config_entry)


class InventoryManagerOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Inventory Manager."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "notify_expiry",
                        default=self.config_entry.options.get("notify_expiry", True),
                    ): bool,
                }
            ),
        )
