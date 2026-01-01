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
SERVICE_ADD_CATEGORY = "add_category"
SERVICE_REMOVE_CATEGORY = "remove_category"
SERVICE_RENAME_CATEGORY = "rename_category"
SERVICE_RESET_CATEGORIES = "reset_categories"
SERVICE_ADD_ZONE = "add_zone"
SERVICE_REMOVE_ZONE = "remove_zone"
SERVICE_RENAME_ZONE = "rename_zone"
SERVICE_RESET_ZONES = "reset_zones"

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
ATTR_CATEGORY = "category"
ATTR_ZONE = "zone"
ATTR_ADDED_DATE = "added_date"
ATTR_OLD_NAME = "old_name"
ATTR_NEW_NAME = "new_name"

# Default categories by location (can be customized by user)
DEFAULT_CATEGORIES = {
    STORAGE_FREEZER: [
        "Viande",
        "Poisson",
        "Légumes",
        "Fruits",
        "Plats préparés",
        "Pain/Pâtisserie",
        "Glaces/Desserts",
        "Condiments/Sauces",
        "Autre",
    ],
    STORAGE_FRIDGE: [
        "Viande/Charcuterie",
        "Poisson/Fruits de mer",
        "Produits laitiers",
        "Fromages",
        "Légumes frais",
        "Fruits frais",
        "Boissons",
        "Sauces/Condiments",
        "Plats préparés",
        "Autre",
    ],
    STORAGE_PANTRY: [
        "Conserves",
        "Pâtes/Riz/Céréales",
        "Farines/Sucres",
        "Huiles/Vinaigres",
        "Épices/Aromates",
        "Biscuits/Gâteaux secs",
        "Boissons",
        "Condiments/Sauces",
        "Produits d'épicerie",
        "Œufs",
        "Autre",
    ],
}

# Category mapping from Open Food Facts tags to our categories
CATEGORY_MAPPING = {
    "Viande": ["meat", "viande", "beef", "pork", "chicken", "poultry", "lamb"],
    "Poisson": ["fish", "poisson", "seafood", "salmon", "tuna", "shrimp"],
    "Légumes": ["vegetable", "legume", "carrot", "tomato", "potato"],
    "Fruits": ["fruit", "berry", "apple", "orange", "banana"],
    "Produits laitiers": ["dairy", "lait", "cheese", "yogurt", "milk", "cream"],
    "Plats préparés": ["prepared", "meal", "pizza", "ready", "frozen-meals"],
    "Pain/Pâtisserie": ["bread", "pain", "pastry", "cake", "biscuit"],
    "Glaces/Desserts": ["ice-cream", "glace", "dessert", "sweet"],
    "Condiments/Sauces": ["sauce", "condiment", "dressing", "ketchup"],
}

# Default zones by location (can be customized by user)
DEFAULT_ZONES = {
    STORAGE_FREEZER: ["Zone 1", "Zone 2", "Zone 3"],
    STORAGE_FRIDGE: ["Zone 1", "Zone 2", "Zone 3"],
    STORAGE_PANTRY: ["Zone 1", "Zone 2", "Zone 3"],
}

# Events
EVENT_PRODUCT_ADDED = "inventory_manager_product_added"
EVENT_PRODUCT_REMOVED = "inventory_manager_product_removed"
EVENT_PRODUCT_EXPIRING = "inventory_manager_product_expiring"
