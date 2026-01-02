"""Sensor platform for Inventory Manager."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    STORAGE_FREEZER,
    STORAGE_LOCATIONS,
)
from .coordinator import InventoryCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Inventory Manager sensors."""
    coordinator: InventoryCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities = [
        InventoryTotalSensor(coordinator, entry),
        InventoryExpiringSensor(coordinator, entry),
        InventoryExpiredSensor(coordinator, entry),
    ]

    # Add location-specific sensors
    for location_key, location_name in STORAGE_LOCATIONS.items():
        entities.append(
            InventoryLocationSensor(coordinator, entry, location_key, location_name)
        )
        # Add expired sensor per location
        entities.append(
            InventoryLocationExpiredSensor(coordinator, entry, location_key, location_name)
        )

    async_add_entities(entities)


class InventoryBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for inventory."""

    def __init__(
        self,
        coordinator: InventoryCoordinator,
        entry: ConfigEntry,
        sensor_type: str,
        name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{sensor_type}"
        self._attr_has_entity_name = True

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Gestionnaire d'Inventaire",
            "manufacturer": "Home Assistant",
            "model": "Inventory Manager",
            "sw_version": "1.0.0",
        }


class InventoryTotalSensor(InventoryBaseSensor):
    """Sensor showing total products in inventory."""

    def __init__(
        self,
        coordinator: InventoryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            entry,
            "total_products",
            "Total Produits",
        )
        self._attr_icon = "mdi:package-variant"
        self._attr_native_unit_of_measurement = "produits"

    @property
    def native_value(self) -> int:
        """Return the total number of products."""
        return len(self.coordinator.products)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        products = self.coordinator.products
        return {
            "products": [
                {
                    "id": pid,
                    "name": p.get("name", "Inconnu"),
                    "location": STORAGE_LOCATIONS.get(p.get("location", ""), p.get("location", "")),
                    "expiry_date": p.get("expiry_date", ""),
                    "quantity": p.get("quantity", 1),
                }
                for pid, p in products.items()
            ],
        }


class InventoryLocationSensor(InventoryBaseSensor):
    """Sensor for a specific storage location."""

    def __init__(
        self,
        coordinator: InventoryCoordinator,
        entry: ConfigEntry,
        location_key: str,
        location_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            entry,
            f"location_{location_key}",
            location_name,
        )
        self._location_key = location_key
        self._attr_native_unit_of_measurement = "produits"
        
        # Set icon based on location
        icons = {
            "freezer": "mdi:fridge-industrial-outline",
            "fridge": "mdi:fridge-outline",
            "pantry": "mdi:cupboard-outline",
        }
        self._attr_icon = icons.get(location_key, "mdi:package-variant")

    @property
    def native_value(self) -> int:
        """Return the number of products in this location."""
        return len(self.coordinator.get_products_by_location(self._location_key))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        products = self.coordinator.get_products_by_location(self._location_key)
        now = dt_util.now().date()
        
        # Sort by expiry date
        sorted_products = []
        for p in products:
            expiry_str = p.get("expiry_date", "")
            try:
                expiry_date = datetime.fromisoformat(expiry_str).date()
                days_until = (expiry_date - now).days
            except ValueError:
                days_until = 999
            
            sorted_products.append({
                "id": p.get("id"),
                "name": p.get("name", "Inconnu"),
                "expiry_date": expiry_str,
                "days_until_expiry": days_until,
                "quantity": p.get("quantity", 1),
                "brand": p.get("brand", ""),
                "category": p.get("category", "Autre"),
                "zone": p.get("zone", "Zone 1"),
            })
        
        sorted_products.sort(key=lambda x: x["days_until_expiry"])
        
        return {
            "products": sorted_products,
            "location": self._location_key,
            "location_name": STORAGE_LOCATIONS.get(self._location_key, ""),
            "categories": self.coordinator.get_categories(self._location_key),
            "zones": self.coordinator.get_zones(self._location_key),
        }


class InventoryExpiringSensor(InventoryBaseSensor):
    """Sensor showing products expiring soon."""

    def __init__(
        self,
        coordinator: InventoryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            entry,
            "expiring_soon",
            "Produits Périmant Bientôt",
        )
        self._attr_icon = "mdi:clock-alert-outline"
        self._attr_native_unit_of_measurement = "produits"

    @property
    def native_value(self) -> int:
        """Return the number of products expiring soon."""
        return len(self.coordinator.get_expiring_products(days=7))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        expiring = self.coordinator.get_expiring_products(days=7)
        return {
            "products": [
                {
                    "id": p.get("id"),
                    "name": p.get("name", "Inconnu"),
                    "expiry_date": p.get("expiry_date", ""),
                    "days_until_expiry": p.get("days_until_expiry", 0),
                    "location": STORAGE_LOCATIONS.get(p.get("location", ""), p.get("location", "")),
                    "quantity": p.get("quantity", 1),
                }
                for p in expiring
            ],
        }


class InventoryExpiredSensor(InventoryBaseSensor):
    """Sensor showing expired products."""

    def __init__(
        self,
        coordinator: InventoryCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            entry,
            "expired",
            "Produits Périmés",
        )
        self._attr_icon = "mdi:alert-circle-outline"
        self._attr_native_unit_of_measurement = "produits"

    @property
    def native_value(self) -> int:
        """Return the number of expired products."""
        now = dt_util.now().date()
        count = 0
        
        for product in self.coordinator.products.values():
            expiry_str = product.get("expiry_date")
            if not expiry_str:
                continue
            try:
                expiry_date = datetime.fromisoformat(expiry_str).date()
                if expiry_date < now:
                    count += 1
            except ValueError:
                continue
        
        return count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        now = dt_util.now().date()
        expired = []
        
        for pid, product in self.coordinator.products.items():
            expiry_str = product.get("expiry_date")
            if not expiry_str:
                continue
            try:
                expiry_date = datetime.fromisoformat(expiry_str).date()
                if expiry_date < now:
                    days_expired = (now - expiry_date).days
                    expired.append({
                        "id": pid,
                        "name": product.get("name", "Inconnu"),
                        "expiry_date": expiry_str,
                        "days_expired": days_expired,
                        "location": STORAGE_LOCATIONS.get(product.get("location", ""), product.get("location", "")),
                        "quantity": product.get("quantity", 1),
                    })
            except ValueError:
                continue
        
        expired.sort(key=lambda x: x["days_expired"], reverse=True)
        
        return {"products": expired}


class InventoryLocationExpiredSensor(InventoryBaseSensor):
    """Sensor showing expired products for a specific location."""

    def __init__(
        self,
        coordinator: InventoryCoordinator,
        entry: ConfigEntry,
        location: str,
        location_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            entry,
            f"expired_{location}",
            f"Produits Périmés - {location_name}",
        )
        self._location = location
        self._location_name = location_name
        self._attr_icon = "mdi:alert-circle-outline"
        self._attr_native_unit_of_measurement = "produits"

    @property
    def native_value(self) -> int:
        """Return the number of expired products for this location."""
        now = dt_util.now().date()
        count = 0
        
        for product in self.coordinator.products.values():
            if product.get("location") != self._location:
                continue
            expiry_str = product.get("expiry_date")
            if not expiry_str:
                continue
            try:
                expiry_date = datetime.fromisoformat(expiry_str).date()
                if expiry_date < now:
                    count += 1
            except ValueError:
                continue
        
        return count

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        now = dt_util.now().date()
        expired = []
        
        for pid, product in self.coordinator.products.items():
            if product.get("location") != self._location:
                continue
            expiry_str = product.get("expiry_date")
            if not expiry_str:
                continue
            try:
                expiry_date = datetime.fromisoformat(expiry_str).date()
                if expiry_date < now:
                    days_expired = (now - expiry_date).days
                    expired.append({
                        "id": pid,
                        "name": product.get("name", "Inconnu"),
                        "expiry_date": expiry_str,
                        "days_expired": days_expired,
                        "location": self._location_name,
                        "quantity": product.get("quantity", 1),
                    })
            except ValueError:
                continue
        
        expired.sort(key=lambda x: x["days_expired"], reverse=True)
        
        return {"products": expired}

