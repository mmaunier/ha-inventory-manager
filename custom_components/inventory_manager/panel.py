"""Panel for Inventory Manager."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from aiohttp import web
from homeassistant.components import panel_custom
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import DOMAIN, STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY

PANEL_TITLE = "Inventaire"
PANEL_ICON = "mdi:fridge-industrial-outline"

_WWW_PATH = Path(__file__).parent / "www"

NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _get_version() -> str:
    """Read version from manifest.json."""
    manifest = Path(__file__).parent / "manifest.json"
    with open(manifest, encoding="utf-8") as fh:
        return json.load(fh).get("version", "0")


class InventoryManagerJSView(HomeAssistantView):
    """Serve JS files with versioned URL + no-store headers.

    URL pattern: /inventory_manager/v{version}/{file}
    The version segment is only used for cache-busting (forces service-worker
    and browser cache miss on every upgrade). The actual file is resolved from
    the www/ directory ignoring the version prefix.
    """

    url = "/inventory_manager/v{version}/{requested_file:.+}"
    name = "inventory_manager_js"
    requires_auth = False

    async def get(
        self, request: web.Request, version: str, requested_file: str
    ) -> web.Response:
        # version is intentionally ignored — only used for cache-busting
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


class InventoryManagerExportView(HomeAssistantView):
    """Serve inventory data as a downloadable JSON file.

    Content-Disposition: attachment triggers Android's download manager,
    which is the only reliable way to download files from a WebView.
    """

    url = "/inventory_manager/export"
    name = "inventory_manager_export"
    requires_auth = True

    async def get(self, request: web.Request) -> web.Response:
        hass = request.app["hass"]

        # Find the coordinator from hass.data
        coordinator = None
        for entry_data in hass.data.get(DOMAIN, {}).values():
            if isinstance(entry_data, dict) and "coordinator" in entry_data:
                coordinator = entry_data["coordinator"]
                break

        if coordinator is None:
            return web.Response(status=503, text="Coordinator not available")

        version = _get_version()
        locations = {
            STORAGE_FREEZER: "freezer",
            STORAGE_FRIDGE: "fridge",
            STORAGE_PANTRY: "pantry",
        }

        products_by_loc = {}
        categories_by_loc = {}
        zones_by_loc = {}
        for key, label in locations.items():
            products_by_loc[label] = coordinator.get_products_by_location(key)
            categories_by_loc[label] = coordinator.get_categories(key)
            zones_by_loc[label] = coordinator.get_zones(key)

        export_data = {
            "version": version,
            "export_date": datetime.now().isoformat(),
            "products": products_by_loc,
            "product_history": coordinator.product_history,
            "categories": categories_by_loc,
            "zones": zones_by_loc,
        }

        date = datetime.now().strftime("%Y-%m-%d")
        filename = f"inventory_backup_{date}.json"

        return web.Response(
            body=json.dumps(export_data, ensure_ascii=False, indent=2),
            content_type="application/json; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Set up the Inventory Manager panel."""
    version = _get_version()

    hass.http.register_view(InventoryManagerJSView())
    hass.http.register_view(InventoryManagerExportView())

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="inventory-manager-panel",
        frontend_url_path="inventory-manager",
        sidebar_title=PANEL_TITLE,
        sidebar_icon=PANEL_ICON,
        module_url=f"/inventory_manager/v{version}/panel.js",
        embed_iframe=False,
        require_admin=False,
    )


async def async_remove_panel(hass: HomeAssistant) -> None:
    """Remove the Inventory Manager panel."""
    hass.components.frontend.async_remove_panel("inventory-manager")
