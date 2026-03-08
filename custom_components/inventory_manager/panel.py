"""Panel for Inventory Manager."""
from __future__ import annotations

import json
from pathlib import Path

from aiohttp import web
from homeassistant.components import panel_custom
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

PANEL_TITLE = "Inventaire"
PANEL_ICON = "mdi:fridge-industrial-outline"

_WWW_PATH = Path(__file__).parent / "www"

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


class InventoryManagerJSView(HomeAssistantView):
    """Serve JS files with no-store headers to defeat aggressive WebView caching."""

    url = "/inventory_manager/{requested_file:.+}"
    name = "inventory_manager_js"
    requires_auth = False

    async def get(
        self, request: web.Request, requested_file: str
    ) -> web.Response:
        safe_path = Path(requested_file)
        if ".." in safe_path.parts:
            return web.Response(status=403)

        filepath = _WWW_PATH / safe_path
        if filepath.suffix != ".js" or not filepath.is_file():
            return web.Response(status=404)

        # Ensure resolved path stays within www/
        try:
            filepath.resolve().relative_to(_WWW_PATH.resolve())
        except ValueError:
            return web.Response(status=403)

        return web.Response(
            body=filepath.read_bytes(),
            content_type="application/javascript; charset=utf-8",
            headers=NO_CACHE_HEADERS,
        )


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Set up the Inventory Manager panel."""
    hass.http.register_view(InventoryManagerJSView())

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
