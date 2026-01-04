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
    ATTR_BARCODE,
    ATTR_BRAND,
    ATTR_CATEGORIES,
    ATTR_CATEGORY,
    ATTR_EXPIRY_DATE,
    ATTR_IMAGE_URL,
    ATTR_LOCATION,
    ATTR_NAME,
    ATTR_PRODUCT_ID,
    ATTR_QUANTITY,
    ATTR_ZONE,
    CATEGORY_MAPPING,
    DEFAULT_CATEGORIES,
    DEFAULT_ZONES,
    DOMAIN,
    EVENT_PRODUCT_ADDED,
    EVENT_PRODUCT_EXPIRING,
    EVENT_PRODUCT_REMOVED,
    EXPIRY_THRESHOLD_NORMAL,
    EXPIRY_THRESHOLD_SOON,
    EXPIRY_THRESHOLD_URGENT,
    OPENFOODFACTS_API_URL,
    SCAN_INTERVAL,
    STORAGE_FILE,
    STORAGE_FREEZER,
    STORAGE_FRIDGE,
    STORAGE_LOCATIONS,
    STORAGE_PANTRY,
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
        self._product_history: list[dict[str, Any]] = []  # Historique des 100 derniers produits ajoutés
        self._last_notification_check: datetime | None = None

    @property
    def products(self) -> dict[str, dict[str, Any]]:
        """Return all products."""
        return self._products

    @property
    def product_history(self) -> list[dict[str, Any]]:
        """Return product history for autocomplete."""
        return self._product_history

    async def async_load_data(self) -> None:
        """Load inventory data from storage."""
        try:
            if self._storage_path.exists():
                data = await self.hass.async_add_executor_job(
                    self._read_storage_file
                )
                self._products = data.get("products", {})
                self._product_history = data.get("product_history", [])
                _LOGGER.info("Loaded %d products and %d history items from storage", len(self._products), len(self._product_history))
            else:
                _LOGGER.info("No existing inventory file, starting fresh")
                self._products = {}
                self._product_history = []
        except Exception as err:
            _LOGGER.error("Error loading inventory data: %s", err)
            self._products = {}
            self._product_history = []

    def _read_storage_file(self) -> dict:
        """Read storage file (blocking)."""
        with open(self._storage_path, "r", encoding="utf-8") as f:
            return json.load(f)

    async def async_save_data(self) -> None:
        """Save inventory data to storage."""
        try:
            data = {
                "products": self._products,
                "product_history": self._product_history,
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
        """Fetch product information from Open Food Facts.
        
        Fast and reliable API for food products (millions of products).
        """
        _LOGGER.info("Searching product for barcode: %s", barcode)
        
        # Open Food Facts (food products)
        result = await self._fetch_from_openfoodfacts(barcode)
        if result:
            result["source"] = "Open Food Facts"
            _LOGGER.info("✓ Found in Open Food Facts: %s", result.get("name", "N/A"))
            return result
        
        _LOGGER.warning("Product not found in Open Food Facts: %s", barcode)
        return None

    async def _fetch_from_openfoodfacts(self, barcode: str) -> dict[str, Any] | None:
        """Fetch product information from Open Food Facts (food products)."""
        url = OPENFOODFACTS_API_URL.format(barcode=barcode)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()
                    
                    if data.get("status") != 1:
                        return None

                    product = data.get("product", {})
                    
                    return {
                        "barcode": barcode,
                        "name": product.get("product_name", product.get("product_name_fr", "")),
                        "brand": product.get("brands", ""),
                        "categories": product.get("categories", ""),
                        "categories_tags": product.get("categories_tags", []),
                        "image_url": product.get("image_url", ""),
                        "quantity_info": product.get("quantity", ""),
                        "nutriscore": product.get("nutriscore_grade", ""),
                    }

        except asyncio.TimeoutError:
            _LOGGER.warning("Open Food Facts: Request timeout (>5s)")
            return None
        except Exception as err:
            _LOGGER.debug("Open Food Facts: Error - %s", err)
            return None

    def _map_category(self, categories_tags: list[str], location: str = STORAGE_FREEZER, product_name: str = "") -> str:
        """Map categories tags or product name to our simplified categories for a specific location."""
        # Get custom categories from config for the specific location
        all_categories = self.entry.options.get("categories", DEFAULT_CATEGORIES)
        if isinstance(all_categories, dict):
            location_categories = all_categories.get(location, DEFAULT_CATEGORIES.get(location, []))
        else:
            # Backward compatibility
            location_categories = all_categories if isinstance(all_categories, list) else []
        
        # Try to match from categories_tags first (for Open Food Facts)
        if categories_tags:
            # Convert tags to lowercase for matching
            tags_lower = [tag.lower() for tag in categories_tags]
            tags_str = " ".join(tags_lower)
            
            # First pass: exact word matching for better precision
            for category in location_categories:
                keywords = CATEGORY_MAPPING.get(category, [])
                for keyword in keywords:
                    # Match whole words or within tag structure (en:keyword)
                    if f":{keyword}" in tags_str or f" {keyword} " in f" {tags_str} " or f"-{keyword}" in tags_str:
                        return category
            
            # Second pass: substring matching (original behavior)
            for category in location_categories:
                keywords = CATEGORY_MAPPING.get(category, [])
                for keyword in keywords:
                    if keyword in tags_str:
                        return category
        
        # If no match from tags, try to detect from product name
        if product_name:
            product_name_lower = product_name.lower()
            
            # Check each category against product name
            for category in location_categories:
                keywords = CATEGORY_MAPPING.get(category, [])
                for keyword in keywords:
                    if keyword in product_name_lower:
                        return category
        
        return "Autre"

    def _add_to_history(self, name: str, category: str, zone: str, location: str) -> None:
        """Add a product to history for autocomplete (keep last 100, avoid duplicates)."""
        # Check if product with same name already exists in history
        existing_idx = None
        for i, item in enumerate(self._product_history):
            if item.get("name", "").lower() == name.lower():
                existing_idx = i
                break
        
        # Remove existing entry to add fresh one at the beginning
        if existing_idx is not None:
            self._product_history.pop(existing_idx)
        
        # Add to beginning of history
        history_item = {
            "name": name,
            "category": category,
            "zone": zone,
            "location": location,
            "added_date": datetime.now().isoformat(),
        }
        self._product_history.insert(0, history_item)
        
        # Keep only last 100
        if len(self._product_history) > 100:
            self._product_history = self._product_history[:100]

    async def async_clear_location(self, location: str) -> int:
        """Clear all products from a specific location. Returns count of deleted products."""
        to_delete = [pid for pid, p in self._products.items() if p.get("location") == location]
        for pid in to_delete:
            del self._products[pid]
        
        await self.async_save_data()
        await self.async_request_refresh()
        
        _LOGGER.info("Cleared %d products from %s", len(to_delete), location)
        return len(to_delete)

    async def async_reset_all(self) -> dict[str, int]:
        """Reset all data: products and history. Returns counts."""
        product_count = len(self._products)
        history_count = len(self._product_history)
        
        self._products = {}
        self._product_history = []
        
        await self.async_save_data()
        await self.async_request_refresh()
        
        _LOGGER.info("Reset all: cleared %d products and %d history items", product_count, history_count)
        return {"products": product_count, "history": history_count}

    def get_export_data(self) -> dict:
        """Get all data for export (products, history, categories, zones)."""
        return {
            "version": "1.15.0",
            "export_date": datetime.now().isoformat(),
            "products": self._products,
            "product_history": self._product_history,
            "categories": self.entry.options.get("categories", DEFAULT_CATEGORIES),
            "zones": self.entry.options.get("zones", DEFAULT_ZONES),
        }

    async def async_import_data(self, data: dict) -> dict:
        """Import data from a backup. Returns import stats."""
        imported = {"products": 0, "history": 0, "categories": 0, "zones": 0}
        
        # Import products - handle both formats:
        # 1. Export format: { "freezer": [...], "fridge": [...], "pantry": [...] }
        # 2. Internal format: { "id1": {...}, "id2": {...}, ... }
        if "products" in data and isinstance(data["products"], dict):
            products_data = data["products"]
            
            # Check if it's export format (keys are location names with arrays)
            if any(key in products_data for key in [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]):
                # Convert from export format to internal format
                new_products = {}
                for location, products_list in products_data.items():
                    if isinstance(products_list, list):
                        for product in products_list:
                            if isinstance(product, dict):
                                # Use existing ID or generate new one
                                product_id = product.get("id") or str(uuid.uuid4())[:8]
                                # Ensure location is set
                                product["location"] = location
                                # Remove days_until_expiry as it's computed
                                product.pop("days_until_expiry", None)
                                new_products[product_id] = product
                self._products = new_products
                imported["products"] = len(new_products)
            else:
                # Already in internal format
                self._products = products_data
                imported["products"] = len(self._products)
        
        # Import history
        if "product_history" in data and isinstance(data["product_history"], list):
            self._product_history = data["product_history"]
            imported["history"] = len(self._product_history)
        
        # Import categories
        if "categories" in data:
            new_options = dict(self.entry.options)
            new_options["categories"] = data["categories"]
            self.hass.config_entries.async_update_entry(self.entry, options=new_options)
            imported["categories"] = sum(len(cats) for cats in data["categories"].values()) if isinstance(data["categories"], dict) else 0
        
        # Import zones
        if "zones" in data:
            new_options = dict(self.entry.options)
            new_options["zones"] = data["zones"]
            self.hass.config_entries.async_update_entry(self.entry, options=new_options)
            imported["zones"] = sum(len(zones) for zones in data["zones"].values()) if isinstance(data["zones"], dict) else 0
        
        await self.async_save_data()
        await self.async_request_refresh()
        
        _LOGGER.info("Imported data: %s", imported)
        return imported

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
        
        # Add to product history for autocomplete (keep last 100)
        self._add_to_history(name, category, zone, location)
        
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
            
            # Déterminer la catégorie depuis les tags ou le nom du produit
            categories_tags = product_info.get("categories_tags", [])
            category = self._map_category(categories_tags, location, product_name=product_info["name"])
            
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
                "source": product_info.get("source", "Unknown"),
                "info": product_info,
            }
        else:
            # Product not found in any database, create with barcode as name
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
                "source": "Manual",
                "info": None,
                "warning": "Produit non trouvé dans les bases de données",
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
        # Garde-fou: impossible de supprimer la catégorie 'Autre'
        if name == "Autre":
            _LOGGER.warning("Cannot remove category 'Autre' - it's the fallback category")
            raise ValueError("Impossible de supprimer la catégorie 'Autre' - elle sert de catégorie par défaut")
        
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
        
        # Garde-fou: toujours garder au moins une catégorie
        if len(categories) <= 1:
            _LOGGER.warning("Cannot remove last category for location '%s'", location)
            raise ValueError("Impossible de supprimer la dernière catégorie")
        
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
        
        # Garde-fou: toujours garder au moins une zone
        if len(zones) <= 1:
            _LOGGER.warning("Cannot remove last zone for location '%s'", location)
            raise ValueError("Impossible de supprimer la dernière zone")
        
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
