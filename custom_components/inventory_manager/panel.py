"""Panel for Inventory Manager."""
from __future__ import annotations

import json
import os
from pathlib import Path

from homeassistant.components import panel_custom
from homeassistant.core import HomeAssistant

PANEL_URL = "/api/panel_custom/inventory_manager"
PANEL_TITLE = "Inventaire"
PANEL_ICON = "mdi:fridge-industrial-outline"
PANEL_NAME = "inventory-manager-panel"


def _get_version() -> str:
    """Read version from manifest.json for cache-busting."""
    manifest_path = Path(__file__).parent / "manifest.json"
    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f).get("version", "0")


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Set up the Inventory Manager panel."""
    version = _get_version()

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
        module_url=f"/inventory_manager/panel.js?v={version}",
        embed_iframe=False,
        require_admin=False,
    )


async def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the Inventory Manager panel."""
    hass.components.frontend.async_remove_panel("inventory-manager")
