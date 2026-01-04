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

# Barcode API
OPENFOODFACTS_API_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

# Notification thresholds (in days)
EXPIRY_THRESHOLD_URGENT = 3  # Rappel d'utilisation le jour même si < 3 jours
EXPIRY_THRESHOLD_SOON = 5    # 1 jour avant si 3-5 jours
EXPIRY_THRESHOLD_NORMAL = 7  # 2 jours avant si >= 7 jours

# Update interval
SCAN_INTERVAL = timedelta(hours=1)

# Services
SERVICE_SCAN_PRODUCT = "scan_product"
SERVICE_LOOKUP_PRODUCT = "lookup_product"
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
SERVICE_EXPORT_DATA = "export_data"
SERVICE_IMPORT_DATA = "import_data"

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
    "Viande": ["meat", "viande", "viandes", "beef", "boeuf", "bœuf", "pork", "porc", "chicken", "poulet", "poultry", "volaille", "lamb", "agneau", "veal", "veau", "turkey", "dinde", "canard", "duck"],
    "Poisson": ["fish", "poisson", "poissons", "seafood", "salmon", "saumon", "tuna", "thon", "shrimp", "crevette", "cod", "cabillaud", "morue", "haddock", "shellfish", "truite", "trout"],
    "Légumes": ["vegetable", "legume", "légume", "légumes", "carrot", "carotte", "tomato", "tomate", "potato", "pomme de terre", "onion", "oignon", "pepper", "poivron", "broccoli", "brocoli", "haricot", "bean"],
    "Fruits": ["fruit", "fruits", "berry", "berries", "baie", "apple", "pomme", "orange", "banana", "banane", "strawberry", "fraise", "mango", "mangue", "peach", "pêche", "poire", "pear"],
    "Produits laitiers": ["dairy", "lait", "laitier", "milk", "cream", "crème", "butter", "beurre", "creme", "yaourt", "yogurt"],
    "Plats préparés": ["prepared", "préparé", "meal", "plat", "pizza", "pizzas", "ready", "frozen-meals", "lasagna", "lasagne", "quiche", "gratin"],
    "Pain/Pâtisserie": ["bread", "pain", "pains", "pastry", "pâtisserie", "patisserie", "cake", "gâteau", "gateau", "biscuit", "croissant", "croissants", "brioche"],
    "Glaces/Desserts": ["ice-cream", "ice cream", "glace", "glaces", "dessert", "desserts", "sweet", "sorbet", "sorbets", "frozen-dessert"],
    "Condiments/Sauces": ["sauce", "sauces", "condiment", "condiments", "dressing", "ketchup", "mustard", "moutarde", "mayonnaise", "mayo"],
    
    # Réfrigérateur
    "Viande/Charcuterie": ["meat", "viande", "viandes", "charcuterie", "sausage", "saucisse", "saucisson", "ham", "jambon", "bacon", "salami", "deli", "pâté", "pate", "rillette"],
    "Poisson/Fruits de mer": ["fish", "poisson", "poissons", "seafood", "salmon", "saumon", "tuna", "thon", "shrimp", "crevette", "crab", "crabe", "oyster", "huître", "moule", "mussel"],
    "Fromages": ["cheese", "fromage", "fromages", "cheddar", "mozzarella", "parmesan", "brie", "camembert", "comté", "comte", "emmental", "roquefort", "chèvre", "chevre"],
    "Légumes frais": ["vegetable", "legume", "légume", "légumes", "fresh-vegetable", "salad", "salade", "lettuce", "laitue", "cucumber", "concombre", "tomate", "tomato", "radis"],
    "Fruits frais": ["fruit", "fruits", "fresh-fruit", "berries", "baies", "citrus", "agrume", "tropical-fruit", "frais", "fresh"],
    "Boissons": ["beverage", "drink", "boisson", "boissons", "juice", "jus", "soda", "water", "eau", "milk", "lait", "bière", "beer"],
    "Sauces/Condiments": ["sauce", "sauces", "condiment", "condiments", "dressing", "marinade", "pesto", "aioli", "aïoli", "ketchup", "moutarde", "mustard"],
    
    # Réserve - Alimentaire
    "Conserves": ["canned", "conserve", "preserved", "tinned", "jarred", "boite", "boîte"],
    "Pâtes/Riz/Céréales": ["pasta", "rice", "cereal", "pates", "pâtes", "riz", "grain", "noodles", "spaghetti", "macaroni", "vermicelle"],
    "Farines/Sucres": ["flour", "sugar", "farine", "farines", "sucre", "sucres", "sweetener", "baking", "levure", "yeast"],
    "Huiles/Vinaigres": ["oil", "vinegar", "huile", "huiles", "vinaigre", "vinaigres", "olive-oil", "sunflower", "colza"],
    "Épices/Aromates": ["spice", "herb", "epice", "épice", "aromate", "pepper", "cumin", "paprika", "thym", "basilic", "sel", "salt", "poivre"],
    "Biscuits/Gâteaux secs": ["biscuit", "biscuits", "cookie", "cookies", "cracker", "crackers", "wafer", "dry-cake", "gâteau", "gateau"],
    "Produits d'épicerie": ["grocery", "epicerie", "épicerie", "snack", "dried-food", "sec", "dry", "spread", "spreads", "pâte à tartiner", "pate a tartiner", "chocolate", "chocolat", "hazelnut", "noisette", "nutella", "jam", "confiture", "marmelade", "honey", "miel"],"Œufs": ["egg", "oeuf", "œuf", "eggs", "oeufs", "œufs"],
    
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
