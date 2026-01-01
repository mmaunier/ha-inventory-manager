# Inventory Manager - Plugin Home Assistant

[![HACS Badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/mmaunier/ha-inventory-manager)](https://github.com/mmaunier/ha-inventory-manager/releases)
[![License](https://img.shields.io/github/license/mmaunier/ha-inventory-manager)](LICENSE)

## 📦 Gestionnaire d'Inventaire Alimentaire

Cette intégration Home Assistant permet de gérer l'inventaire de votre congélateur avec :
- 📷 **Scan de code-barres** via la caméra du smartphone (Android/iOS)
- 🔍 **Recherche automatique** des produits via Open Food Facts
- 📅 **Gestion des dates de péremption** avec tri par date, nom, catégorie ou zone
- 🗂️ **Catégorisation automatique** des produits (10 catégories)
- 📍 **Zones de stockage** pour organiser votre congélateur (Zone 1, 2, 3)
- 🔔 **Notifications intelligentes** pour les produits qui périment
- 📱 **Interface responsive** optimisée pour mobile

## ✨ Fonctionnalités

- **Scan code-barres** : Utilisez la caméra de votre téléphone pour scanner les produits
- **Open Food Facts** : Récupération automatique du nom, marque et catégorie du produit
- **Catégories automatiques** : 10 catégories (Viande, Poisson, Légumes, Fruits, Produits laitiers, Plats préparés, Pain/Pâtisserie, Glaces/Desserts, Condiments/Sauces, Autre)
- **Zones de stockage** : Organisez votre congélateur en zones (Zone 1, 2, 3)
- **Tri des produits** : Par date de péremption, nom, catégorie ou zone (cliquez sur les en-têtes)
- **Indicateurs visuels** : Couleurs selon l'urgence (🟢 OK, 🟡 Bientôt, 🟠 Urgent, 🔴 Périmé)
- **Notifications** : Alertes automatiques toutes les 6h pour les produits à consommer

## 🚀 Installation

### Via HACS (Recommandé)

1. Ouvrez **HACS** → **Intégrations** → **⋮** → **Dépôts personnalisés**
2. Ajoutez `https://github.com/mmaunier/ha-inventory-manager` (catégorie: Integration)
3. Cherchez "Inventory Manager" et cliquez **Télécharger**
4. Redémarrez Home Assistant
5. Allez dans **Paramètres** → **Appareils et services** → **+ Ajouter une intégration**
6. Recherchez "**Inventory Manager**"

### Installation manuelle

1. Copiez le dossier `custom_components/inventory_manager` dans `config/custom_components/`
2. Redémarrez Home Assistant
3. Ajoutez l'intégration via Paramètres → Appareils et services

## 📱 Utilisation

### Interface Web

Accédez au panel via le menu latéral : **Inventaire Congélateur**

- **➕ Ajouter un produit** : Scannez un code-barres ou saisissez manuellement
- **Tri** : Cliquez sur "Produit" ou "Péremption" pour trier
- **Modifier** : Cliquez sur ✏️ pour éditer un produit
- **Supprimer** : Cliquez sur 🗑️ pour supprimer

### Services disponibles

```yaml
# Scanner un produit (avec code-barres et détection auto de catégorie)
service: inventory_manager.scan_product
data:
  barcode: "3017620422003"
  expiry_date: "2026-06-15"
  location: "freezer"
  quantity: 1

# Ajouter manuellement avec catégorie et zone
service: inventory_manager.add_product
data:
  name: "Pizza 4 fromages"
  expiry_date: "2026-06-15"
  location: "freezer"
  quantity: 2
  category: "Plats préparés"
  zone: "Zone 2"

# Supprimer un produit
service: inventory_manager.remove_product
data:
  product_id: "a1b2c3d4"

# Modifier un produit (y compris catégorie et zone)
service: inventory_manager.update_product
data:
  product_id: "a1b2c3d4"
  name: "Pizza 4 fromages"
  expiry_date: "2026-06-15"
  quantity: 3
  category: "Plats préparés"
  zone: "Zone 1"
```

### Capteurs créés

| Capteur | Description |
|---------|-------------|
| `sensor.gestionnaire_d_inventaire_congelateur` | Produits dans le congélateur |
| `sensor.gestionnaire_d_inventaire_refrigerateur` | Produits dans le réfrigérateur |
| `sensor.gestionnaire_d_inventaire_reserve` | Produits dans la réserve |
| `sensor.gestionnaire_d_inventaire_produits_perimant_bientot` | Produits expirant sous 7 jours (tous emplacements) |
| `sensor.gestionnaire_d_inventaire_produits_perimes` | Produits déjà périmés (tous emplacements) |
| `sensor.gestionnaire_d_inventaire_expired_freezer` | Produits périmés dans le congélateur |
| `sensor.gestionnaire_d_inventaire_expired_fridge` | Produits périmés dans le réfrigérateur |
| `sensor.gestionnaire_d_inventaire_expired_pantry` | Produits périmés dans la réserve |

## 🔔 Notifications de péremption

### Créer une automatisation

L'intégration vérifie les péremptions **toutes les 6 heures** et envoie l'événement `inventory_manager_product_expiring`.

Créez cette automatisation pour recevoir des notifications :

```yaml
alias: "Alerte péremption congélateur"
description: "Notification quand un produit va périmer"
trigger:
  - platform: event
    event_type: inventory_manager_product_expiring
action:
  - service: persistent_notification.create
    data:
      title: >
        {% if trigger.event.data.notification_type == 'expired' %}
        ⛔ Produit périmé !
        {% else %}
        ⚠️ Péremption proche
        {% endif %}
      message: >
        **{{ trigger.event.data.name }}**
        
        {% if trigger.event.data.notification_type == 'expired' %}
        Ce produit est périmé !
        {% elif trigger.event.data.days_until_expiry == 0 %}
        Périme aujourd'hui !
        {% elif trigger.event.data.days_until_expiry == 1 %}
        Périme demain !
        {% else %}
        Périme dans {{ trigger.event.data.days_until_expiry }} jours
        {% endif %}
      notification_id: "inventory_{{ trigger.event.data.product_id }}"
mode: parallel
```

### Types de notifications

| Type | Condition |
|------|-----------|
| `expired` | Produit déjà périmé |
| `expires_today` | Périme aujourd'hui |
| `expires_soon` | Périme dans 1 à 3 jours |

## 📂 Structure des données

Les données sont stockées dans `config/inventory_data.json` :

```json
{
  "products": {
    "a1b2c3d4": {
      "name": "Nutella",
      "expiry_date": "2026-06-15",
      "location": "freezer",
      "quantity": 1,
      "category": "Condiments/Sauces",
      "zone": "Zone 1",
      "barcode": "3017620422003",
      "brand": "Ferrero",
      "added_date": "2026-01-01T10:30:00"
    }
  }
}
```

### Catégories disponibles (v1.5.0+)

| Catégorie | Exemples |
|-----------|----------|
| Viande | Poulet, bœuf, porc... |
| Poisson | Saumon, cabillaud, crevettes... |
| Légumes | Haricots verts, épinards, carottes... |
| Fruits | Framboises, mangue, bananes... |
| Produits laitiers | Yaourts, fromage, beurre... |
| Plats préparés | Pizza, lasagnes, raviolis... |
| Pain/Pâtisserie | Pain, croissants, brioches... |
| Glaces/Desserts | Glaces, sorbets, gâteaux... |
| Condiments/Sauces | Pesto, sauce tomate, herbes... |
| Autre | Produits non classés |

La catégorie est détectée automatiquement depuis Open Food Facts lors du scan.

## 🔧 Dépannage

### Le produit n'est pas trouvé dans Open Food Facts

Le champ nom restera vide. Saisissez le nom manuellement.

### La caméra ne fonctionne pas

- Vérifiez que vous utilisez HTTPS
- Autorisez l'accès à la caméra dans les paramètres du navigateur
- Sur Android, utilisez Chrome ou l'app Home Assistant

### Les notifications ne fonctionnent pas

1. Créez l'automatisation décrite ci-dessus
2. Testez en déclenchant manuellement l'événement dans Outils de développement → Événements

## 📝 Licence

MIT License - Voir [LICENSE](LICENSE)

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir des issues ou des pull requests.
