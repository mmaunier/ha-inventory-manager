"""Data coordinator for Inventory Manager."""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    OPENFOODFACTS_API_URL,
    STORAGE_FILE,
    STORAGE_FREEZER,
    STORAGE_FRIDGE,
    STORAGE_PANTRY,
    STORAGE_LOCATIONS,
    SCAN_INTERVAL,
    EXPIRY_THRESHOLD_URGENT,
    EXPIRY_THRESHOLD_SOON,
    EXPIRY_THRESHOLD_NORMAL,
    EVENT_PRODUCT_ADDED,
    EVENT_PRODUCT_REMOVED,
    EVENT_PRODUCT_EXPIRING,
    CATEGORY_MAPPING,
    DEFAULT_CATEGORIES,
    DEFAULT_ZONES,
)

_LOGGER = logging.getLogger(__name__)


class InventoryCoordinator(DataUpdateCoordinator):
    """Coordinator for managing inventory data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.entry = entry
        self._storage_path = Path(hass.config.path(STORAGE_FILE))
        self._products: dict[str, dict[str, Any]] = {}
        self._last_notification_check: datetime | None = None

    @property
    def products(self) -> dict[str, dict[str, Any]]:
        """Return all products."""
        return self._products

    async def async_load_data(self) -> None:
        """Load inventory data from storage."""
        try:
            if self._storage_path.exists():
                data = await self.hass.async_add_executor_job(
                    self._read_storage_file
                )
                self._products = data.get("products", {})
                _LOGGER.info("Loaded %d products from storage", len(self._products))
            else:
                _LOGGER.info("No existing inventory file, starting fresh")
                self._products = {}
        except Exception as err:
            _LOGGER.error("Error loading inventory data: %s", err)
            self._products = {}

    def _read_storage_file(self) -> dict:
        """Read storage file (blocking)."""
        with open(self._storage_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def async_save_data(self) -> None:
        """Save inventory data to storage."""
        try:
            data = {
                "products": self._products,
                "last_updated": datetime.now().isoformat(),
            }
            await self.hass.async_add_executor_job(
                self._write_storage_file, data
            )
            _LOGGER.debug("Saved %d products to storage", len(self._products))
        except Exception as err:
            _LOGGER.error("Error saving inventory data: %s", err)

    def _write_storage_file(self, data: dict) -> None:
        """Write storage file (blocking)."""
        with open(self._storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data and check for expiring products."""
        await self._check_expiring_products()
        return self._get_summary()

    def _get_summary(self) -> dict[str, Any]:
        """Get inventory summary."""
        now = dt_util.now().date()
        summary = {
            "total_products": len(self._products),
            "locations": {},
            "expired": [],
            "expiring_today": [],
            "expiring_soon": [],
        }

        for location in STORAGE_LOCATIONS:
            location_products = [
                p for p in self._products.values() 
                if p.get("location") == location
            ]
            summary["locations"][location] = {
                "count": len(location_products),
                "products": location_products,
            }

        # Check expiry dates
        for product_id, product in self._products.items():
            expiry_str = product.get("expiry_date")
            if not expiry_str:
                continue

            try:
                expiry_date = datetime.fromisoformat(expiry_str).date()
                days_until_expiry = (expiry_date - now).days

                product_info = {
                    "id": product_id,
                    "name": product.get("name", "Inconnu"),
                    "expiry_date": expiry_str,
                    "days_until_expiry": days_until_expiry,
                    "location": product.get("location"),
                }

                if days_until_expiry < 0:
                    summary["expired"].append(product_info)
                elif days_until_expiry == 0:
                    summary["expiring_today"].append(product_info)
                elif days_until_expiry <= EXPIRY_THRESHOLD_SOON:
                    summary["expiring_soon"].append(product_info)
            except ValueError:
                _LOGGER.warning("Invalid expiry date for product %s", product_id)

        return summary

    async def _check_expiring_products(self) -> None:
        """Check for expiring products and send notifications."""
        now = dt_util.now()
        today = now.date()

        # Only check once per 6 hours
        if (
            self._last_notification_check
            and (now - self._last_notification_check).total_seconds() < 21600  # 6h
        ):
            return

        self._last_notification_check = now
        _LOGGER.info("Checking for expiring products...")

        for product_id, product in self._products.items():
            expiry_str = product.get("expiry_date")
            if not expiry_str:
                continue

            try:
                expiry_date = datetime.fromisoformat(expiry_str).date()
                days_until_expiry = (expiry_date - today).days
                
                notification_type = None

                # Logique simplifiée
                if days_until_expiry < 0:
                    notification_type = "expired"
                elif days_until_expiry == 0:
                    notification_type = "expires_today"
                elif days_until_expiry <= 3:
                    notification_type = "expires_soon"

                if notification_type:
                    _LOGGER.info(
                        "Sending expiry event for %s (%s, %d days)",
                        product.get("name"),
                        notification_type,
                        days_until_expiry
                    )
                    self.hass.bus.async_fire(
                        EVENT_PRODUCT_EXPIRING,
                        {
                            "product_id": product_id,
                            "name": product.get("name", "Inconnu"),
                            "expiry_date": expiry_str,
                            "days_until_expiry": days_until_expiry,
                            "location": product.get("location"),
                            "notification_type": notification_type,
                        },
                    )

            except ValueError:
                continue

    async def async_fetch_product_info(self, barcode: str) -> dict[str, Any] | None:
        """Fetch product information from Open Food Facts."""
        url = OPENFOODFACTS_API_URL.format(barcode=barcode)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status != 200:
                        _LOGGER.warning("Open Food Facts returned status %d", response.status)
                        return None

                    data = await response.json()
                    
                    if data.get("status") != 1:
                        _LOGGER.info("Product not found in Open Food Facts: %s", barcode)
                        return None

                    product = data.get("product", {})
                    
                    return {
                        "barcode": barcode,
                        "name": product.get("product_name", product.get("product_name_fr", "Produit inconnu")),
                        "brand": product.get("brands", ""),
                        "categories": product.get("categories", ""),
                        "categories_tags": product.get("categories_tags", []),
                        "image_url": product.get("image_url", ""),
                        "quantity_info": product.get("quantity", ""),
                        "nutriscore": product.get("nutriscore_grade", ""),
                    }

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching product info from Open Food Facts")
            return None
        except Exception as err:
            _LOGGER.error("Error fetching product info: %s", err)
            return None

    def _map_category(self, categories_tags: list[str], location: str = STORAGE_FREEZER) -> str:
        """Map Open Food Facts categories to our simplified categories for a specific location."""
        if not categories_tags:
            return "Autre"
        
        # Convert tags to lowercase for matching
        tags_lower = [tag.lower() for tag in categories_tags]
        tags_str = " ".join(tags_lower)
        
        # Get custom categories from config for the specific location
        all_categories = self.entry.options.get("categories", DEFAULT_CATEGORIES)
        if isinstance(all_categories, dict):
            location_categories = all_categories.get(location, DEFAULT_CATEGORIES.get(location, []))
        else:
            # Backward compatibility
            location_categories = all_categories if isinstance(all_categories, list) else []
        
        # Check each category mapping
        for category, keywords in CATEGORY_MAPPING.items():
            # Only use categories that exist in the current location
            if category not in location_categories:
                continue
            for keyword in keywords:
                if keyword in tags_str:
                    return category
        
        return "Autre"

    def get_zones(self, location: str = STORAGE_FREEZER) -> list[str]:
        """Get list of zones from config for a specific location."""
        all_zones = self.entry.options.get("zones", DEFAULT_ZONES)
        if isinstance(all_zones, dict):
            return all_zones.get(location, DEFAULT_ZONES.get(location, []))
        # Backward compatibility: if zones is still a list, return it
        return all_zones if isinstance(all_zones, list) else []

    def get_categories(self, location: str = STORAGE_FREEZER) -> list[str]:
        """Get list of categories from config for a specific location."""
        all_categories = self.entry.options.get("categories", DEFAULT_CATEGORIES)
        if isinstance(all_categories, dict):
            return all_categories.get(location, DEFAULT_CATEGORIES.get(location, []))
        # Backward compatibility: if categories is still a list, return it
        return all_categories if isinstance(all_categories, list) else []

    async def async_add_product(
        self,
        name: str,
        expiry_date: str,
        location: str = STORAGE_FREEZER,
        quantity: int = 1,
        barcode: str | None = None,
        brand: str | None = None,
        image_url: str | None = None,
        category: str | None = None,
        zone: str | None = None,
    ) -> str:
        """Add a product to the inventory."""
        product_id = str(uuid.uuid4())[:8]
        
        # Default zone is the first one for the specified location
        if zone is None:
            zones = self.get_zones(location)
            zone = zones[0] if zones else "Zone 1"
        
        # Default category is "Autre"
        if category is None:
            category = "Autre"
        
        product = {
            "name": name,
            "expiry_date": expiry_date,
            "location": location,
            "quantity": quantity,
            "category": category,
            "zone": zone,
            "added_date": datetime.now().isoformat(),
        }
        
        if barcode:
            product["barcode"] = barcode
        if brand:
            product["brand"] = brand
        if image_url:
            product["image_url"] = image_url

        self._products[product_id] = product
        await self.async_save_data()
        
        # Fire event
        self.hass.bus.async_fire(
            EVENT_PRODUCT_ADDED,
            {
                "product_id": product_id,
                **product,
            },
        )
        
        # Trigger update
        await self.async_request_refresh()
        
        _LOGGER.info("Added product: %s (ID: %s)", name, product_id)
        return product_id

    async def async_scan_and_add_product(
        self,
        barcode: str,
        expiry_date: str,
        location: str = STORAGE_FREEZER,
        quantity: int = 1,
    ) -> dict[str, Any]:
        """Scan a barcode and add the product to inventory."""
        # Fetch product info from Open Food Facts
        product_info = await self.async_fetch_product_info(barcode)
        
        if product_info:
            name = product_info["name"]
            if product_info.get("brand"):
                name = f"{product_info['brand']} - {name}"
            
            # Déterminer la catégorie depuis Open Food Facts pour le bon emplacement
            categories_tags = product_info.get("categories_tags", [])
            category = self._map_category(categories_tags, location)
            
            product_id = await self.async_add_product(
                name=name,
                expiry_date=expiry_date,
                location=location,
                quantity=quantity,
                barcode=barcode,
                brand=product_info.get("brand"),
                image_url=product_info.get("image_url"),
                category=category,
            )
            
            return {
                "success": True,
                "product_id": product_id,
                "name": name,
                "category": category,
                "info": product_info,
            }
        else:
            # Product not found, create with barcode as name
            product_id = await self.async_add_product(
                name=f"Produit {barcode}",
                expiry_date=expiry_date,
                location=location,
                quantity=quantity,
                barcode=barcode,
                category="Autre",
            )
            
            return {
                "success": True,
                "product_id": product_id,
                "name": f"Produit {barcode}",
                "category": "Autre",
                "info": None,
                "warning": "Produit non trouvé dans Open Food Facts",
            }

    async def async_remove_product(self, product_id: str) -> bool:
        """Remove a product from the inventory."""
        # Normaliser l'ID en string
        product_id = str(product_id)
        
        _LOGGER.debug("Attempting to remove product: %s (type: %s)", product_id, type(product_id))
        _LOGGER.debug("Current product IDs in storage: %s", list(self._products.keys()))
        
        if product_id not in self._products:
            _LOGGER.warning("Product not found: %s. Available IDs: %s", product_id, list(self._products.keys()))
            return False

        product = self._products.pop(product_id)
        await self.async_save_data()
        
        # Fire event
        self.hass.bus.async_fire(
            EVENT_PRODUCT_REMOVED,
            {
                "product_id": product_id,
                "name": product.get("name", "Inconnu"),
            },
        )
        
        # Trigger update
        await self.async_request_refresh()
        
        _LOGGER.info("Removed product: %s", product_id)
        return True

    async def async_update_quantity(
        self, product_id: str, quantity: int
    ) -> bool:
        """Update the quantity of a product."""
        if product_id not in self._products:
            _LOGGER.warning("Product not found: %s", product_id)
            return False

        if quantity <= 0:
            # Remove product if quantity is 0 or less
            return await self.async_remove_product(product_id)

        self._products[product_id]["quantity"] = quantity
        await self.async_save_data()
        await self.async_request_refresh()
        
        _LOGGER.info("Updated quantity for %s: %d", product_id, quantity)
        return True

    async def async_update_product(
        self,
        product_id: str,
        name: str | None = None,
        expiry_date: str | None = None,
        quantity: int | None = None,
        category: str | None = None,
        zone: str | None = None,
    ) -> bool:
        """Update a product's details."""
        if product_id not in self._products:
            _LOGGER.warning("Product not found: %s", product_id)
            return False

        product = self._products[product_id]
        
        if name is not None:
            product["name"] = name
        
        if expiry_date is not None:
            product["expiry_date"] = expiry_date
            # Recalculate days until expiry
            now = dt_util.now().date()
            try:
                expiry = datetime.fromisoformat(expiry_date).date()
                product["days_until_expiry"] = (expiry - now).days
            except ValueError:
                pass
        
        if quantity is not None:
            if quantity <= 0:
                return await self.async_remove_product(product_id)
            product["quantity"] = quantity
        
        if category is not None:
            product["category"] = category
        
        if zone is not None:
            product["zone"] = zone
        
        await self.async_save_data()
        await self.async_request_refresh()
        
        _LOGGER.info("Updated product: %s", product_id)
        return True

    def get_products_by_location(self, location: str) -> list[dict[str, Any]]:
        """Get all products in a specific location."""
        return [
            {"id": pid, **product}
            for pid, product in self._products.items()
            if product.get("location") == location
        ]

    def get_expiring_products(self, days: int = 7) -> list[dict[str, Any]]:
        """Get products expiring within the specified days."""
        now = dt_util.now().date()
        expiring = []

        for product_id, product in self._products.items():
            expiry_str = product.get("expiry_date")
            if not expiry_str:
                continue

            try:
                expiry_date = datetime.fromisoformat(expiry_str).date()
                days_until_expiry = (expiry_date - now).days

                if 0 <= days_until_expiry <= days:
                    expiring.append({
                        "id": product_id,
                        "days_until_expiry": days_until_expiry,
                        **product,
                    })
            except ValueError:
                continue

        return sorted(expiring, key=lambda x: x["days_until_expiry"])

    async def async_add_category(self, name: str, location: str = STORAGE_FREEZER) -> None:
        """Add a new category for a specific location."""
        categories_data = self.entry.options.get("categories", DEFAULT_CATEGORIES)
        
        # Handle migration: if categories is a list, convert to dict
        if isinstance(categories_data, list):
            all_categories = {
                STORAGE_FREEZER: categories_data,
                STORAGE_FRIDGE: list(DEFAULT_CATEGORIES.get(STORAGE_FRIDGE, [])),
                STORAGE_PANTRY: list(DEFAULT_CATEGORIES.get(STORAGE_PANTRY, [])),
            }
        else:
            all_categories = dict(categories_data)
        
        if location not in all_categories:
            all_categories[location] = list(DEFAULT_CATEGORIES.get(location, []))
        
        categories = list(all_categories[location])
        if name not in categories:
            categories.append(name)
            all_categories[location] = categories
            new_data = {**self.entry.options, "categories": all_categories}
            self.hass.config_entries.async_update_entry(self.entry, options=new_data)
            _LOGGER.info("Added category '%s' to location '%s'", name, location)

    async def async_remove_category(self, name: str, location: str = STORAGE_FREEZER) -> None:
        """Remove a category for a specific location. Products with this category will be set to 'Autre'."""
        categories_data = self.entry.options.get("categories", DEFAULT_CATEGORIES)
        
        # Handle migration: if categories is a list, convert to dict
        if isinstance(categories_data, list):
            all_categories = {
                STORAGE_FREEZER: categories_data,
                STORAGE_FRIDGE: list(DEFAULT_CATEGORIES.get(STORAGE_FRIDGE, [])),
                STORAGE_PANTRY: list(DEFAULT_CATEGORIES.get(STORAGE_PANTRY, [])),
            }
        else:
            all_categories = dict(categories_data)
        
        if location not in all_categories:
            return
        
        categories = list(all_categories[location])
        if name in categories:
            categories.remove(name)
            all_categories[location] = categories
            new_data = {**self.entry.options, "categories": all_categories}
            self.hass.config_entries.async_update_entry(self.entry, options=new_data)
            
            # Update products in this location that have this category to 'Autre'
            for product in self._products.values():
                if product.get("location") == location and product.get("category") == name:
                    product["category"] = "Autre"
            await self.async_save_data()
            _LOGGER.info("Removed category '%s' from location '%s'", name, location)

    async def async_rename_category(self, old_name: str, new_name: str, location: str = STORAGE_FREEZER) -> None:
        """Rename a category for a specific location. All products will be updated."""
        categories_data = self.entry.options.get("categories", DEFAULT_CATEGORIES)
        
        # Handle migration: if categories is a list, convert to dict
        if isinstance(categories_data, list):
            all_categories = {
                STORAGE_FREEZER: categories_data,
                STORAGE_FRIDGE: list(DEFAULT_CATEGORIES.get(STORAGE_FRIDGE, [])),
                STORAGE_PANTRY: list(DEFAULT_CATEGORIES.get(STORAGE_PANTRY, [])),
            }
        else:
            all_categories = dict(categories_data)
        
        if location not in all_categories:
            return
        
        categories = list(all_categories[location])
        if old_name in categories:
            idx = categories.index(old_name)
            categories[idx] = new_name
            all_categories[location] = categories
            new_data = {**self.entry.options, "categories": all_categories}
            self.hass.config_entries.async_update_entry(self.entry, options=new_data)
            
            # Update products in this location
            for product in self._products.values():
                if product.get("location") == location and product.get("category") == old_name:
                    product["category"] = new_name
            await self.async_save_data()
            _LOGGER.info("Renamed category '%s' -> '%s' for location '%s'", old_name, new_name, location)

    async def async_add_zone(self, name: str, location: str = STORAGE_FREEZER) -> None:
        """Add a new zone for a specific location."""
        zones_data = self.entry.options.get("zones", DEFAULT_ZONES)
        
        # Handle migration: if zones is a list, convert to dict
        if isinstance(zones_data, list):
            all_zones = {
                STORAGE_FREEZER: zones_data,
                STORAGE_FRIDGE: zones_data[:],
                STORAGE_PANTRY: zones_data[:],
            }
        else:
            all_zones = dict(zones_data)
        
        if location not in all_zones:
            all_zones[location] = list(DEFAULT_ZONES.get(location, []))
        
        zones = list(all_zones[location])
        if name not in zones:
            zones.append(name)
            all_zones[location] = zones
            new_data = {**self.entry.options, "zones": all_zones}
            self.hass.config_entries.async_update_entry(self.entry, options=new_data)
            _LOGGER.info("Added zone '%s' to location '%s'", name, location)

    async def async_remove_zone(self, name: str, location: str = STORAGE_FREEZER) -> None:
        """Remove a zone for a specific location. Products in this zone will be set to first zone."""
        zones_data = self.entry.options.get("zones", DEFAULT_ZONES)
        
        # Handle migration: if zones is a list, convert to dict
        if isinstance(zones_data, list):
            all_zones = {
                STORAGE_FREEZER: zones_data,
                STORAGE_FRIDGE: zones_data[:],
                STORAGE_PANTRY: zones_data[:],
            }
        else:
            all_zones = dict(zones_data)
        
        if location not in all_zones:
            return
        
        zones = list(all_zones[location])
        if name in zones:
            zones.remove(name)
            all_zones[location] = zones
            new_data = {**self.entry.options, "zones": all_zones}
            self.hass.config_entries.async_update_entry(self.entry, options=new_data)
            
            # Update products in this location that have this zone to first zone
            first_zone = zones[0] if zones else "Zone 1"
            for product in self._products.values():
                if product.get("location") == location and product.get("zone") == name:
                    product["zone"] = first_zone
            await self.async_save_data()
            _LOGGER.info("Removed zone '%s' from location '%s'", name, location)

    async def async_rename_zone(self, old_name: str, new_name: str, location: str = STORAGE_FREEZER) -> None:
        """Rename a zone for a specific location. All products will be updated."""
        zones_data = self.entry.options.get("zones", DEFAULT_ZONES)
        
        # Handle migration: if zones is a list, convert to dict
        if isinstance(zones_data, list):
            all_zones = {
                STORAGE_FREEZER: zones_data,
                STORAGE_FRIDGE: zones_data[:],
                STORAGE_PANTRY: zones_data[:],
            }
        else:
            all_zones = dict(zones_data)
        
        if location not in all_zones:
            return
        
        zones = list(all_zones[location])
        if old_name in zones:
            idx = zones.index(old_name)
            zones[idx] = new_name
            all_zones[location] = zones
            new_data = {**self.entry.options, "zones": all_zones}
            self.hass.config_entries.async_update_entry(self.entry, options=new_data)
            
            # Update products in this location
            for product in self._products.values():
                if product.get("location") == location and product.get("zone") == old_name:
                    product["zone"] = new_name
            await self.async_save_data()
            _LOGGER.info("Renamed zone '%s' -> '%s' for location '%s'", old_name, new_name, location)

    async def async_reset_categories(self, location: str = STORAGE_FREEZER) -> None:
        """Reset categories to default values for a specific location."""
        categories_data = self.entry.options.get("categories", DEFAULT_CATEGORIES)
        
        # Handle migration: if categories is a list, convert to dict
        if isinstance(categories_data, list):
            all_categories = {
                STORAGE_FREEZER: categories_data,
                STORAGE_FRIDGE: list(DEFAULT_CATEGORIES.get(STORAGE_FRIDGE, [])),
                STORAGE_PANTRY: list(DEFAULT_CATEGORIES.get(STORAGE_PANTRY, [])),
            }
        else:
            all_categories = dict(categories_data)
        
        all_categories[location] = list(DEFAULT_CATEGORIES.get(location, []))
        new_data = {**self.entry.options, "categories": all_categories}
        self.hass.config_entries.async_update_entry(self.entry, options=new_data)
        _LOGGER.info("Reset categories to default for location '%s'", location)

    async def async_reset_zones(self, location: str = STORAGE_FREEZER) -> None:
        """Reset zones to default values for a specific location."""
        zones_data = self.entry.options.get("zones", DEFAULT_ZONES)
        
        # Handle migration: if zones is a list, convert to dict
        if isinstance(zones_data, list):
            all_zones = {
                STORAGE_FREEZER: zones_data,
                STORAGE_FRIDGE: zones_data[:],
                STORAGE_PANTRY: zones_data[:],
            }
        else:
            all_zones = dict(zones_data)
        
        all_zones[location] = list(DEFAULT_ZONES.get(location, []))
        new_data = {**self.entry.options, "zones": all_zones}
        self.hass.config_entries.async_update_entry(self.entry, options=new_data)
        _LOGGER.info("Reset zones to default for location '%s'", location)
