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
    SERVICE_ADD_PRODUCT,
    SERVICE_REMOVE_PRODUCT,
    SERVICE_UPDATE_QUANTITY,
    SERVICE_UPDATE_PRODUCT,
    SERVICE_LIST_PRODUCTS,
    ATTR_BARCODE,
    ATTR_NAME,
    ATTR_QUANTITY,
    ATTR_EXPIRY_DATE,
    ATTR_LOCATION,
    ATTR_PRODUCT_ID,
    STORAGE_FREEZER,
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
            list(STORAGE_LOCATIONS.keys())
        ),
        vol.Optional(ATTR_QUANTITY, default=1): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
    }
)

ADD_PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_NAME): cv.string,
        vol.Required(ATTR_EXPIRY_DATE): cv.string,
        vol.Optional(ATTR_LOCATION, default=STORAGE_FREEZER): vol.In(
            list(STORAGE_LOCATIONS.keys())
        ),
        vol.Optional(ATTR_QUANTITY, default=1): vol.All(
            vol.Coerce(int), vol.Range(min=1)
        ),
        vol.Optional(ATTR_BARCODE): cv.string,
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
        vol.Optional(ATTR_LOCATION): vol.In(list(STORAGE_LOCATIONS.keys())),
    }
)

UPDATE_PRODUCT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_PRODUCT_ID): cv.string,
        vol.Optional(ATTR_NAME): cv.string,
        vol.Optional(ATTR_EXPIRY_DATE): cv.string,
        vol.Optional(ATTR_QUANTITY): vol.All(vol.Coerce(int), vol.Range(min=1)),
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

    async def handle_add_product(call: ServiceCall) -> ServiceResponse:
        """Handle add product service call."""
        name = call.data[ATTR_NAME]
        expiry_date = call.data[ATTR_EXPIRY_DATE]
        location = call.data.get(ATTR_LOCATION, STORAGE_FREEZER)
        quantity = call.data.get(ATTR_QUANTITY, 1)
        barcode = call.data.get(ATTR_BARCODE)

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
        )

        return {
            "success": success,
            "product_id": product_id,
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

    _LOGGER.info("Inventory Manager services registered")


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload services."""
    hass.services.async_remove(DOMAIN, SERVICE_SCAN_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_ADD_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_REMOVE_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_QUANTITY)
    hass.services.async_remove(DOMAIN, SERVICE_UPDATE_PRODUCT)
    hass.services.async_remove(DOMAIN, SERVICE_LIST_PRODUCTS)
