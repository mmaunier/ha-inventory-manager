# Inventory Manager - Plugin Home Assistant

## 📦 Gestionnaire d'Inventaire Alimentaire

Cette intégration Home Assistant permet de gérer l'inventaire de votre congélateur (et plus tard réfrigérateur et réserves) avec :
- Scan de code-barres via Open Food Facts
- Gestion des dates de péremption
- Notifications intelligentes

## 🚀 Installation

### Méthode 1 : Installation manuelle

1. Copiez le dossier `custom_components/inventory_manager` dans votre dossier `config/custom_components/` de Home Assistant

2. Redémarrez Home Assistant

3. Allez dans **Paramètres** → **Appareils et services** → **+ Ajouter une intégration**

4. Recherchez "**Inventory Manager**" ou "**Gestionnaire d'Inventaire**"

5. Suivez les instructions de configuration

### Méthode 2 : HACS (Recommandé)

1. Ouvrez **HACS** → **Intégrations** → **⋮** → **Dépôts personnalisés**
2. Ajoutez `https://github.com/mmaunier/ha-inventory-manager` (catégorie: Integration)
3. Cherchez "Inventory Manager" et cliquez **Télécharger**
4. Redémarrez Home Assistant

## 📱 Utilisation

### Services disponibles

#### 1. Scanner un produit (avec code-barres)
```yaml
service: inventory_manager.scan_product
data:
  barcode: "3017620422003"  # Code-barres EAN-13
  expiry_date: "2026-06-15"
  location: "freezer"  # freezer, fridge, ou pantry
  quantity: 1
```

#### 2. Ajouter un produit manuellement
```yaml
service: inventory_manager.add_product
data:
  name: "Pizza 4 fromages"
  expiry_date: "2026-06-15"
  location: "freezer"
  quantity: 2
```

#### 3. Supprimer un produit (1 clic)
```yaml
service: inventory_manager.remove_product
data:
  product_id: "a1b2c3d4"  # ID obtenu via les attributs des capteurs
```

#### 4. Modifier la quantité
```yaml
service: inventory_manager.update_quantity
data:
  product_id: "a1b2c3d4"
  quantity: 3  # 0 pour supprimer
```

#### 5. Lister les produits
```yaml
service: inventory_manager.list_products
data:
  location: "freezer"  # Optionnel, filtre par emplacement
```

### Capteurs créés

| Capteur | Description |
|---------|-------------|
| `sensor.gestionnaire_d_inventaire_total_produits` | Nombre total de produits |
| `sensor.gestionnaire_d_inventaire_congelateur` | Produits dans le congélateur |
| `sensor.gestionnaire_d_inventaire_refrigerateur` | Produits dans le réfrigérateur |
| `sensor.gestionnaire_d_inventaire_reserves` | Produits dans les réserves |
| `sensor.gestionnaire_d_inventaire_produits_perimant_bientot` | Produits expirant sous 7 jours |
| `sensor.gestionnaire_d_inventaire_produits_perimes` | Produits déjà périmés |

### Événements

L'intégration émet les événements suivants :

- `inventory_manager_product_added` - Quand un produit est ajouté
- `inventory_manager_product_removed` - Quand un produit est supprimé  
- `inventory_manager_product_expiring` - Quand un produit approche de la péremption

## 🔔 Automatisations pour les notifications

### Notification de péremption

```yaml
automation:
  - alias: "Notification produit périmant"
    trigger:
      - platform: event
        event_type: inventory_manager_product_expiring
    action:
      - service: notify.mobile_app_votre_telephone
        data:
          title: "⚠️ Produit à consommer"
          message: >
            {% if trigger.event.data.notification_type == 'expired' %}
              🚨 {{ trigger.event.data.name }} est PÉRIMÉ !
            {% elif trigger.event.data.notification_type == 'use_today' %}
              ⚡ {{ trigger.event.data.name }} expire dans {{ trigger.event.data.days_until_expiry }} jour(s) - À utiliser rapidement !
            {% elif trigger.event.data.notification_type == 'expiring_soon' %}
              ⏰ {{ trigger.event.data.name }} expire demain
            {% else %}
              📅 {{ trigger.event.data.name }} expire dans 2 jours
            {% endif %}
          data:
            tag: "expiry_{{ trigger.event.data.product_id }}"
```

## 📲 Scan de code-barres depuis smartphone

### Option 1 : Via l'app Home Assistant Companion

1. Créez un script dans HA :

```yaml
script:
  scan_and_add_product:
    alias: "Scanner et ajouter un produit"
    sequence:
      - service: notify.mobile_app_votre_telephone
        data:
          message: "command_barcode_scanner"
      - wait_for_trigger:
          - platform: event
            event_type: mobile_app_notification_action
        timeout: "00:02:00"
      - service: inventory_manager.scan_product
        data:
          barcode: "{{ wait.trigger.event.data.barcode }}"
          expiry_date: "{{ now().date() + timedelta(days=30) }}"
          location: "freezer"
```

### Option 2 : Interface Web dédiée (à implémenter)

Une page web avec accès caméra utilisant `html5-qrcode` qui appelle l'API HA.

## 🎨 Exemple de carte Lovelace

Voir le fichier `lovelace_example.yaml` pour un exemple de carte complète.

## 📂 Structure des fichiers

```
custom_components/inventory_manager/
├── __init__.py          # Point d'entrée
├── manifest.json        # Métadonnées
├── const.py             # Constantes
├── config_flow.py       # Configuration UI
├── coordinator.py       # Gestion des données
├── sensor.py            # Capteurs
├── services.py          # Services
├── services.yaml        # Définition des services
├── strings.json         # Textes
└── translations/
    ├── fr.json          # Français
    └── en.json          # Anglais
```

## 🗄️ Stockage des données

Les données sont stockées dans `config/inventory_data.json` au format :

```json
{
  "products": {
    "a1b2c3d4": {
      "name": "Nutella",
      "expiry_date": "2026-06-15",
      "location": "freezer",
      "quantity": 1,
      "barcode": "3017620422003",
      "brand": "Ferrero",
      "added_date": "2026-01-01T10:30:00"
    }
  },
  "last_updated": "2026-01-01T10:30:00"
}
```

## ⚙️ Configuration avancée

### Logique des notifications de péremption

| Durée avant péremption | Notification |
|------------------------|--------------|
| < 3 jours | Rappel d'utilisation immédiat |
| 3-5 jours | Notification 1 jour avant |
| ≥ 7 jours | Notification 2 jours avant |

## 🔧 Dépannage

### Le produit n'est pas trouvé dans Open Food Facts

Le produit sera ajouté avec le code-barres comme nom. Vous pouvez :
1. Modifier le nom manuellement dans les attributs
2. Contribuer à Open Food Facts en ajoutant le produit

### Les notifications ne fonctionnent pas

Vérifiez :
1. Que l'option "Notifications de péremption" est activée dans les options
2. Que l'automatisation est bien configurée
3. Que le service de notification est correct

## 📝 Licence

MIT License

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir des issues ou des pull requests.
