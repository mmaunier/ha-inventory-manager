"""Constants for Inventory Manager integration."""
from datetime import timedelta

DOMAIN = "inventory_manager"
PLATFORMS = ["sensor"]

# Storage locations
STORAGE_FREEZER = "freezer"
STORAGE_FRIDGE = "fridge"
STORAGE_PANTRY = "pantry"

STORAGE_LOCATIONS = {
    STORAGE_FREEZER: "Congélateur",
    STORAGE_FRIDGE: "Réfrigérateur",
    STORAGE_PANTRY: "Réserves",
}

# Default storage file
STORAGE_FILE = "inventory_data.json"

# Open Food Facts API
OPENFOODFACTS_API_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

# Notification thresholds (in days)
EXPIRY_THRESHOLD_URGENT = 3  # Rappel d'utilisation le jour même si < 3 jours
EXPIRY_THRESHOLD_SOON = 5    # 1 jour avant si 3-5 jours
EXPIRY_THRESHOLD_NORMAL = 7  # 2 jours avant si >= 7 jours

# Update interval
SCAN_INTERVAL = timedelta(hours=1)

# Services
SERVICE_SCAN_PRODUCT = "scan_product"
SERVICE_ADD_PRODUCT = "add_product"
SERVICE_REMOVE_PRODUCT = "remove_product"
SERVICE_UPDATE_QUANTITY = "update_quantity"
SERVICE_UPDATE_PRODUCT = "update_product"
SERVICE_LIST_PRODUCTS = "list_products"

# Attributes
ATTR_BARCODE = "barcode"
ATTR_NAME = "name"
ATTR_QUANTITY = "quantity"
ATTR_EXPIRY_DATE = "expiry_date"
ATTR_LOCATION = "location"
ATTR_PRODUCT_ID = "product_id"
ATTR_BRAND = "brand"
ATTR_IMAGE_URL = "image_url"
ATTR_CATEGORIES = "categories"
ATTR_ADDED_DATE = "added_date"

# Events
EVENT_PRODUCT_ADDED = "inventory_manager_product_added"
EVENT_PRODUCT_REMOVED = "inventory_manager_product_removed"
EVENT_PRODUCT_EXPIRING = "inventory_manager_product_expiring"
