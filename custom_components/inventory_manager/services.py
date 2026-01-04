"""Services for Inventory Manager integration."""
from __future__ import annotations

import logging
from datetime import datetime

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_SCAN_PRODUCT,
    SERVICE_LOOKUP_PRODUCT,
    SERVICE_ADD_PRODUCT,
    SERVICE_REMOVE_PRODUCT,
    SERVICE_UPDATE_QUANTITY,
    SERVICE_UPDATE_PRODUCT,
    SERVICE_LIST_PRODUCTS,
    SERVICE_ADD_CATEGORY,
    SERVICE_REMOVE_CATEGORY,
    SERVICE_RENAME_CATEGORY,
    SERVICE_RESET_CATEGORIES,
    SERVICE_ADD_ZONE,
    SERVICE_REMOVE_ZONE,
    SERVICE_RENAME_ZONE,
    SERVICE_RESET_ZONES,    SERVICE_EXPORT_DATA,
    SERVICE_IMPORT_DATA,    SERVICE_EXPORT_DATA,
    SERVICE_IMPORT_DATA,
    ATTR_BARCODE,
    ATTR_NAME,
    ATTR_QUANTITY,
    ATTR_EXPIRY_DATE,
    ATTR_LOCATION,
    ATTR_PRODUCT_ID,
    ATTR_CATEGORY,
    ATTR_ZONE,
    ATTR_OLD_NAME,
    ATTR_NEW_NAME,
    STORAGE_FREEZER,
    STORAGE_FRIDGE,
    STORAGE_PANTRY,
    STORAGE_LOCATIONS,
)
from .coordinator import InventoryCoordinator

_LOGGER = logging.getLogger(__name__)

# Service schemas
SCAN_PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BARCODE): cv.string,
        vol.Required(ATTR_EXPIRY_DATE): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
        vol.Optional(ATTR_QUANTITY, default=1): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
    }
)

LOOKUP_PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_BARCODE): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_PANTRY): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
    }
)

ADD_PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): cv.string,
        vol.Required(ATTR_EXPIRY_DATE): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
        vol.Optional(ATTR_QUANTITY, default=1): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
        vol.Optional(ATTR_BARCODE): cv.string,
        vol.Optional(ATTR_CATEGORY): cv.string,
        vol.Optional(ATTR_ZONE): cv.string,
    }
)

REMOVE_PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PRODUCT_ID): cv.string,
    }
)

UPDATE_QUANTITY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PRODUCT_ID): cv.string,
        vol.Required(ATTR_QUANTITY): vol.All(vol.Coerce(int), vol.Range(min=0)),
    }
)

LIST_PRODUCTS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_LOCATION): vol.In([STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]),
    }
)

UPDATE_PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PRODUCT_ID): cv.string,
        vol.Optional(ATTR_NAME): cv.string,
        vol.Optional(ATTR_EXPIRY_DATE): cv.string,
        vol.Optional(ATTR_QUANTITY): vol.All(vol.Coerce(int), vol.Range(min=1)),
        vol.Optional(ATTR_CATEGORY): cv.string,
        vol.Optional(ATTR_ZONE): cv.string,
    }
)

ADD_CATEGORY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
    }
)

REMOVE_CATEGORY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
    }
)

RENAME_CATEGORY_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_OLD_NAME): cv.string,
        vol.Required(ATTR_NEW_NAME): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
    }
)

ADD_ZONE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
    }
)

REMOVE_ZONE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
    }
)

RENAME_ZONE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_OLD_NAME): cv.string,
        vol.Required(ATTR_NEW_NAME): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
    }
)

RESET_CATEGORIES_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
    }
)

RESET_ZONES_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            [STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]
        ),
    }
)


async def async_setup_services(
    hass: HomeAssistant, coordinator: InventoryCoordinator
) -> None:
    """Set up services for Inventory Manager."""

    async def handle_scan_product(call: ServiceCall) -> ServiceResponse:
        """Handle scan product service call."""
        barcode = call.data[ATTR_BARCODE]
        expiry_date = call.data[ATTR_EXPIRY_DATE]
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        quantity = call.data.get(ATTR_QUANTITY, 1)

        # Validate expiry date format
        try:
            datetime.fromisoformat(expiry_date)
        except ValueError:
            # Try to parse common date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    parsed_date = datetime.strptime(expiry_date, fmt)
                    expiry_date = parsed_date.date().isoformat()
                    break
                except ValueError:
                    continue
            else:
                return {
                    "success": False,
                    "error": f"Format de date invalide: {expiry_date}. Utilisez YYYY-MM-DD",
                }

        result = await coordinator.async_scan_and_add_product(
            barcode=barcode,
            expiry_date=expiry_date,
            location=location,
            quantity=quantity,
        )

        return result

    async def handle_lookup_product(call: ServiceCall) -> ServiceResponse:
        """Handle lookup product service call (search only, no add to inventory)."""
        barcode = call.data[ATTR_BARCODE]
        location = call.data.get(ATTR_LOCATION, STORAGE_PANTRY)
        
        # Fetch product info from Open Food Facts
        product_info = await coordinator.async_fetch_product_info(barcode)
        
        if product_info:
            # Map category based on product tags and name
            categories_tags = product_info.get("categories_tags", [])
            mapped_category = coordinator._map_category(
                categories_tags, 
                location, 
                product_name=product_info.get("name", "")
            )
            
            return {
                "success": True,
                "found": True,
                "barcode": barcode,
                "name": product_info.get("name", ""),
                "brand": product_info.get("brand", ""),
                "source": product_info.get("source", "Unknown"),
                "categories": product_info.get("categories", ""),
                "category": mapped_category,
                "image_url": product_info.get("image_url", ""),
            }
        else:
            return {
                "success": True,
                "found": False,
                "barcode": barcode,
                "message": "Produit non trouvé dans les bases de données",
            }

    async def handle_add_product(call: ServiceCall) -> ServiceResponse:
        """Handle add product service call."""
        name = call.data[ATTR_NAME]
        expiry_date = call.data[ATTR_EXPIRY_DATE]
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        quantity = call.data.get(ATTR_QUANTITY, 1)
        barcode = call.data.get(ATTR_BARCODE)
        category = call.data.get(ATTR_CATEGORY)
        zone = call.data.get(ATTR_ZONE)

        # Validate expiry date format
        try:
            datetime.fromisoformat(expiry_date)
        except ValueError:
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                try:
                    parsed_date = datetime.strptime(expiry_date, fmt)
                    expiry_date = parsed_date.date().isoformat()
                    break
                except ValueError:
                    continue
            else:
                return {
                    "success": False,
                    "error": f"Format de date invalide: {expiry_date}. Utilisez YYYY-MM-DD",
                }

        product_id = await coordinator.async_add_product(
            name=name,
            expiry_date=expiry_date,
            location=location,
            quantity=quantity,
            barcode=barcode,
            category=category,
            zone=zone,
        )

        return {
            "success": True,
            "product_id": product_id,
            "name": name,
        }

    async def handle_remove_product(call: ServiceCall) -> ServiceResponse:
        """Handle remove product service call."""
        product_id = call.data[ATTR_PRODUCT_ID]

        success = await coordinator.async_remove_product(product_id)

        return {
            "success": success,
            "product_id": product_id,
        }

    async def handle_update_quantity(call: ServiceCall) -> ServiceResponse:
        """Handle update quantity service call."""
        product_id = call.data[ATTR_PRODUCT_ID]
        quantity = call.data[ATTR_QUANTITY]

        success = await coordinator.async_update_quantity(product_id, quantity)

        return {
            "success": success,
            "product_id": product_id,
            "quantity": quantity,
        }

    async def handle_list_products(call: ServiceCall) -> ServiceResponse:
        """Handle list products service call."""
        location = call.data.get(ATTR_LOCATION)

        if location:
            products = coordinator.get_products_by_location(location)
        else:
            products = [
                {"id": pid, **product}
                for pid, product in coordinator.products.items()
            ]

        return {
            "success": True,
            "count": len(products),
            "products": products,
        }

    async def handle_update_product(call: ServiceCall) -> ServiceResponse:
        """Handle update product service call."""
        product_id = call.data[ATTR_PRODUCT_ID]
        name = call.data.get(ATTR_NAME)
        expiry_date = call.data.get(ATTR_EXPIRY_DATE)
        quantity = call.data.get(ATTR_QUANTITY)
        category = call.data.get(ATTR_CATEGORY)
        zone = call.data.get(ATTR_ZONE)

        # Validate expiry date format if provided
        if expiry_date:
            try:
                datetime.fromisoformat(expiry_date)
            except ValueError:
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]:
                    try:
                        parsed_date = datetime.strptime(expiry_date, fmt)
                        expiry_date = parsed_date.date().isoformat()
                        break
                    except ValueError:
                        continue
                else:
                    return {
                        "success": False,
                        "error": f"Format de date invalide: {expiry_date}. Utilisez YYYY-MM-DD",
                    }

        success = await coordinator.async_update_product(
            product_id=product_id,
            name=name,
            expiry_date=expiry_date,
            quantity=quantity,
            category=category,
            zone=zone,
        )

        return {
            "success": success,
            "product_id": product_id,
        }

    async def handle_add_category(call: ServiceCall) -> ServiceResponse:
        """Handle add category service call."""
        name = call.data[ATTR_NAME]
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        await coordinator.async_add_category(name, location)
        return {
            "success": True,
            "category": name,
            "location": location,
        }

    async def handle_remove_category(call: ServiceCall) -> ServiceResponse:
        """Handle remove category service call."""
        name = call.data[ATTR_NAME]
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        await coordinator.async_remove_category(name, location)
        return {
            "success": True,
            "category": name,
            "location": location,
        }

    async def handle_rename_category(call: ServiceCall) -> ServiceResponse:
        """Handle rename category service call."""
        old_name = call.data[ATTR_OLD_NAME]
        new_name = call.data[ATTR_NEW_NAME]
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        await coordinator.async_rename_category(old_name, new_name, location)
        return {
            "success": True,
            "old_name": old_name,
            "new_name": new_name,
            "location": location,
        }

    async def handle_add_zone(call: ServiceCall) -> ServiceResponse:
        """Handle add zone service call."""
        name = call.data[ATTR_NAME]
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        await coordinator.async_add_zone(name, location)
        return {
            "success": True,
            "zone": name,
            "location": location,
        }

    async def handle_remove_zone(call: ServiceCall) -> ServiceResponse:
        """Handle remove zone service call."""
        name = call.data[ATTR_NAME]
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        await coordinator.async_remove_zone(name, location)
        return {
            "success": True,
            "zone": name,
            "location": location,
        }

    async def handle_rename_zone(call: ServiceCall) -> ServiceResponse:
        """Handle rename zone service call."""
        old_name = call.data[ATTR_OLD_NAME]
        new_name = call.data[ATTR_NEW_NAME]
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        await coordinator.async_rename_zone(old_name, new_name, location)
        return {
            "success": True,
            "old_name": old_name,
            "new_name": new_name,
            "location": location,
        }

    async def handle_reset_categories(call: ServiceCall) -> ServiceResponse:
        """Handle reset categories service call."""
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        await coordinator.async_reset_categories(location)
        return {
            "success": True,
            "location": location,
        }

    async def handle_reset_zones(call: ServiceCall) -> ServiceResponse:
        """Handle reset zones service call."""
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        await coordinator.async_reset_zones(location)
        return {
            "success": True,
        }

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_SCAN_PRODUCT,
        handle_scan_product,
        schema=SCAN_PRODUCT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_LOOKUP_PRODUCT,
        handle_lookup_product,
        schema=LOOKUP_PRODUCT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_PRODUCT,
        handle_add_product,
        schema=ADD_PRODUCT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_PRODUCT,
        handle_remove_product,
        schema=REMOVE_PRODUCT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_QUANTITY,
        handle_update_quantity,
        schema=UPDATE_QUANTITY_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_LIST_PRODUCTS,
        handle_list_products,
        schema=LIST_PRODUCTS_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE_PRODUCT,
        handle_update_product,
        schema=UPDATE_PRODUCT_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_CATEGORY,
        handle_add_category,
        schema=ADD_CATEGORY_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_CATEGORY,
        handle_remove_category,
        schema=REMOVE_CATEGORY_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RENAME_CATEGORY,
        handle_rename_category,
        schema=RENAME_CATEGORY_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_ZONE,
        handle_add_zone,
        schema=ADD_ZONE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_ZONE,
        handle_remove_zone,
        schema=REMOVE_ZONE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RENAME_ZONE,
        handle_rename_zone,
        schema=RENAME_ZONE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_CATEGORIES,
        handle_reset_categories,
        schema=RESET_CATEGORIES_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_ZONES,
        handle_reset_zones,
        schema=RESET_ZONES_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL,
    )

    # Clear location services
    async def handle_clear_freezer(call: ServiceCall) -> ServiceResponse:
        """Handle clear freezer service call."""
        count = await coordinator.async_clear_location(STORAGE_FREEZER)
        return {"success": True, "deleted_count": count, "location": "Congélateur"}

    async def handle_clear_fridge(call: ServiceCall) -> ServiceResponse:
        """Handle clear fridge service call."""
        count = await coordinator.async_clear_location(STORAGE_FRIDGE)
        return {"success": True, "deleted_count": count, "location": "Réfrigérateur"}

    async def handle_clear_pantry(call: ServiceCall) -> ServiceResponse:
        """Handle clear pantry service call."""
        count = await coordinator.async_clear_location(STORAGE_PANTRY)
        return {"success": True, "deleted_count": count, "location": "Réserves"}

    async def handle_reset_all(call: ServiceCall) -> ServiceResponse:
        """Handle reset all service call."""
        result = await coordinator.async_reset_all()
        return {"success": True, **result}

    async def handle_export_data(call: ServiceCall) -> ServiceResponse:
        """Handle export data service call."""
        data = coordinator.get_export_data()
        return {"success": True, "data": data}

    async def handle_import_data(call: ServiceCall) -> ServiceResponse:
        """Handle import data service call."""
        import json
        data_str = call.data.get("data", "{}")
        try:
            data = json.loads(data_str) if isinstance(data_str, str) else data_str
            result = await coordinator.async_import_data(data)
            return {"success": True, **result}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON: {e}"}

    hass.services.async_register(
        DOMAIN,
        "clear_freezer",
        handle_clear_freezer,
        schema=vol.Schema({}),
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        "clear_fridge",
        handle_clear_fridge,
        schema=vol.Schema({}),
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        "clear_pantry",
        handle_clear_pantry,
        schema=vol.Schema({}),
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        "reset_all",
        handle_reset_all,
        schema=vol.Schema({}),
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_DATA,
        handle_export_data,
        schema=vol.Schema({}),
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_IMPORT_DATA,
        handle_import_data,
        schema=vol.Schema({vol.Required("data"): cv.string}),
        supports_response=SupportsResponse.OPTIONAL,
    )

    _LOGGER.info("Inventory Manager services registered")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, SERVICE_SCAN_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_LOOKUP_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_ADD_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_REMOVE_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_QUANTITY)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_LIST_PRODUCTS)
    hass.services.async_remove(DOMAIN, SERVICE_ADD_CATEGORY)
    hass.services.async_remove(DOMAIN, SERVICE_REMOVE_CATEGORY)
    hass.services.async_remove(DOMAIN, SERVICE_RENAME_CATEGORY)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_CATEGORIES)
    hass.services.async_remove(DOMAIN, SERVICE_ADD_ZONE)
    hass.services.async_remove(DOMAIN, SERVICE_REMOVE_ZONE)
    hass.services.async_remove(DOMAIN, SERVICE_RENAME_ZONE)
    hass.services.async_remove(DOMAIN, SERVICE_RESET_ZONES)
    hass.services.async_remove(DOMAIN, "clear_freezer")
    hass.services.async_remove(DOMAIN, "clear_fridge")
    hass.services.async_remove(DOMAIN, "clear_pantry")
    hass.services.async_remove(DOMAIN, "reset_all")
    hass.services.async_remove(DOMAIN, SERVICE_EXPORT_DATA)
    hass.services.async_remove(DOMAIN, SERVICE_IMPORT_DATA)
