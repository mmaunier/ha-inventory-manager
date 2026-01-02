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

# Barcode APIs (cascade search)
OPENFOODFACTS_API_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
UPCITEMDB_API_URL = "https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"
EAN_SEARCH_API_URL = "https://api.ean-search.org/api?token=free&op=barcode-lookup&format=json&ean={barcode}"

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
        "Produits ménagers",
        "Hygiène & Cosmétiques",
        "Papeterie & Fournitures",
        "Médicaments & Santé",
        "Autre",
    ],
}

# Category mapping from Open Food Facts tags to our categories
CATEGORY_MAPPING = {
    # Congélateur
    "Viande": ["meat", "viande", "beef", "pork", "chicken", "poultry", "lamb", "veal", "turkey"],
    "Poisson": ["fish", "poisson", "seafood", "salmon", "tuna", "shrimp", "cod", "haddock", "shellfish"],
    "Légumes": ["vegetable", "legume", "carrot", "tomato", "potato", "onion", "pepper", "broccoli"],
    "Fruits": ["fruit", "berry", "apple", "orange", "banana", "strawberry", "mango", "peach"],
    "Produits laitiers": ["dairy", "lait", "milk", "cream", "butter", "creme"],
    "Plats préparés": ["prepared", "meal", "pizza", "ready", "frozen-meals", "lasagna", "quiche"],
    "Pain/Pâtisserie": ["bread", "pain", "pastry", "cake", "biscuit", "croissant", "brioche"],
    "Glaces/Desserts": ["ice-cream", "glace", "dessert", "sweet", "sorbet", "frozen-dessert"],
    "Condiments/Sauces": ["sauce", "condiment", "dressing", "ketchup", "mustard", "mayonnaise"],
    
    # Réfrigérateur
    "Viande/Charcuterie": ["meat", "viande", "charcuterie", "sausage", "ham", "bacon", "salami", "deli"],
    "Poisson/Fruits de mer": ["fish", "poisson", "seafood", "salmon", "tuna", "shrimp", "crab", "oyster"],
    "Fromages": ["cheese", "fromage", "cheddar", "mozzarella", "parmesan", "brie", "camembert"],
    "Légumes frais": ["vegetable", "legume", "fresh-vegetable", "salad", "lettuce", "cucumber"],
    "Fruits frais": ["fruit", "fresh-fruit", "berries", "citrus", "tropical-fruit"],
    "Boissons": ["beverage", "drink", "boisson", "juice", "soda", "water", "milk"],
    "Sauces/Condiments": ["sauce", "condiment", "dressing", "marinade", "pesto", "aioli"],
    
    # Réserve - Alimentaire
    "Conserves": ["canned", "conserve", "preserved", "tinned", "jarred"],
    "Pâtes/Riz/Céréales": ["pasta", "rice", "cereal", "pates", "riz", "grain", "noodles", "spaghetti"],
    "Farines/Sucres": ["flour", "sugar", "farine", "sucre", "sweetener", "baking"],
    "Huiles/Vinaigres": ["oil", "vinegar", "huile", "vinaigre", "olive-oil", "sunflower"],
    "Épices/Aromates": ["spice", "herb", "epice", "aromate", "pepper", "cumin", "paprika"],
    "Biscuits/Gâteaux secs": ["biscuit", "cookie", "cracker", "wafer", "dry-cake"],
    "Produits d'épicerie": ["grocery", "epicerie", "snack", "dried-food"],
    "Œufs": ["egg", "oeuf", "eggs"],
    
    # Réserve - Produits ménagers
    "Produits ménagers": [
        "detergent", "lessive", "laundry", "bleach", "javel", "cleaner", "nettoyant",
        "dishwashing", "vaisselle", "floor", "sol", "window", "vitre", "disinfectant",
        "désinfectant", "sponge", "éponge", "trash", "poubelle", "bag", "sac"
    ],
    
    # Réserve - Hygiène & Cosmétiques
    "Hygiène & Cosmétiques": [
        "soap", "savon", "shampoo", "shampooing", "gel", "shower", "douche",
        "toothpaste", "dentifrice", "deodorant", "déodorant", "perfume", "parfum",
        "cream", "crème", "lotion", "cosmetic", "cosmétique", "makeup", "maquillage",
        "razor", "rasoir", "tissue", "mouchoir", "cotton", "coton", "hygiene", "hygiène"
    ],
    
    # Réserve - Papeterie
    "Papeterie & Fournitures": [
        "paper", "papier", "pen", "stylo", "pencil", "crayon", "notebook", "cahier",
        "envelope", "enveloppe", "tape", "scotch", "adhesif", "glue", "colle",
        "stapler", "agrafeuse", "folder", "classeur", "label", "étiquette",
        "marker", "marqueur", "scissors", "ciseaux", "clip", "trombone"
    ],
    
    # Réserve - Médicaments
    "Médicaments & Santé": [
        "medicine", "médicament", "pill", "pilule", "tablet", "comprimé",
        "capsule", "syrup", "sirop", "drops", "gouttes", "ointment", "pommade",
        "bandage", "pansement", "gauze", "compresse", "antiseptic", "antiseptique",
        "vitamin", "vitamine", "supplement", "complément", "painkiller", "analgésique",
        "antibiotic", "antibiotique", "prescription", "ordonnance", "pharmacy", "pharmacie"
    ],
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
