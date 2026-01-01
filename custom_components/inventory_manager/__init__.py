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
from .const import DEFAULT_CATEGORIES, DEFAULT_ZONES, STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY
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

    # Initialize categories and zones by location in options if not present (for new installations)
    # Also migrate from old list format to new dict format
    needs_update = False
    new_options = {**entry.options}
    
    # Migrate or initialize categories
    if "categories" not in new_options:
        new_options["categories"] = DEFAULT_CATEGORIES
        needs_update = True
    elif isinstance(new_options["categories"], list):
        # Migration: old list format → new dict format (all locations get the same categories)
        old_categories = new_options["categories"]
        new_options["categories"] = {
            STORAGE_FREEZER: old_categories,
            STORAGE_FRIDGE: list(DEFAULT_CATEGORIES[STORAGE_FRIDGE]),
            STORAGE_PANTRY: list(DEFAULT_CATEGORIES[STORAGE_PANTRY]),
        }
        needs_update = True
        _LOGGER.info("Migrated categories from list to dict format")
    
    # Migrate or initialize zones
    if "zones" not in new_options:
        new_options["zones"] = DEFAULT_ZONES
        needs_update = True
    elif isinstance(new_options["zones"], list):
        # Migration: old list format → new dict format (all locations get the same zones)
        old_zones = new_options["zones"]
        new_options["zones"] = {
            STORAGE_FREEZER: old_zones,
            STORAGE_FRIDGE: old_zones[:],
            STORAGE_PANTRY: old_zones[:],
        }
        needs_update = True
        _LOGGER.info("Migrated zones from list to dict format")
    
    if needs_update:
        hass.config_entries.async_update_entry(entry, options=new_options)
        _LOGGER.info("Updated entry options with migrated/initialized data")

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
