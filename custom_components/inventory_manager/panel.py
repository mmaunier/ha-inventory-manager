"""Panel for Inventory Manager."""
from __future__ import annotations

import os
from pathlib import Path

from homeassistant.components import panel_custom
from homeassistant.core import HomeAssistant

PANEL_URL = "/api/panel_custom/inventory_manager"
PANEL_TITLE = "Inventaire"
PANEL_ICON = "mdi:fridge-industrial-outline"
PANEL_NAME = "inventory-manager-panel"


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Set up the Inventory Manager panel."""
    # Register the panel
    hass.http.register_static_path(
        "/inventory_manager",
        str(Path(__file__).parent / "www"),
        cache_headers=False,
    )

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="inventory-manager-panel",
        frontend_url_path="inventory-manager",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        module_url="/inventory_manager/panel.js",
        embed_iframe=False,
        require_admin=False,
    )


async def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the Inventory Manager panel."""
    hass.components.frontend.async_remove_panel("inventory-manager")
