"""Inventory Manager integration for Home Assistant."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN
from .coordinator import InventoryCoordinator
from .services import async_setup_services, async_unload_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# This integration is config entry only
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Inventory Manager component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Inventory Manager from a config entry."""
    _LOGGER.info("Setting up Inventory Manager integration")

    # Create coordinator
    coordinator = InventoryCoordinator(hass, entry)
    
    # Load existing data
    await coordinator.async_load_data()
    
    # Store coordinator
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up services
    await async_setup_services(hass, coordinator)

    # Register panel (web interface)
    await _async_register_panel(hass)

    _LOGGER.info("Inventory Manager integration setup complete")
    return True


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the Inventory Manager panel."""
    www_path = Path(__file__).parent / "www"
    
    # Register static path for panel files
    await hass.http.async_register_static_paths([
        StaticPathConfig("/inventory_manager", str(www_path), cache_headers=False)
    ])
    
    # Register the panel in sidebar
    frontend.async_register_built_in_panel(
        hass,
        component_name="custom",
        sidebar_title="Inventaire",
        sidebar_icon="mdi:fridge-industrial-outline",
        frontend_url_path="inventory-manager",
        config={
            "_panel_custom": {
                "name": "inventory-manager-panel",
                "module_url": "/inventory_manager/panel.js",
            }
        },
        require_admin=False,
    )


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        # Unload services
        await async_unload_services(hass)
        
        # Remove panel
        frontend.async_remove_panel(hass, "inventory-manager")
        
        # Remove data
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
