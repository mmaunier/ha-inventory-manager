# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.4.0] - 2026-01-01

### Ajouté
- **Tri des produits** : Cliquez sur les en-têtes "Produit" ou "Péremption" pour trier la liste
- Indicateurs visuels de tri (▲/▼) sur les colonnes
- Documentation complète dans README.md
- Ce fichier CHANGELOG.md

### Modifié
- Interface utilisateur améliorée avec en-têtes cliquables
- Tri par date de péremption par défaut

## [1.3.12] - 2026-01-01

### Modifié
- Vérification des péremptions toutes les **6 heures** (au lieu de 1h)
- Logique de notification simplifiée :
  - `expired` : produit périmé
  - `expires_today` : périme aujourd'hui
  - `expires_soon` : périme dans 1 à 3 jours

### Ajouté
- Logs de débogage pour le suivi des événements de péremption

## [1.3.11] - 2026-01-01

### Corrigé
- Erreurs de validation Hassfest
- Ajout de `http` et `frontend` dans les dépendances du manifest
- Ajout de `CONFIG_SCHEMA` pour satisfaire la validation

### Modifié
- `iot_class` changé en `local_polling` (plus approprié)

## [1.3.10] - 2026-01-01

### Corrigé
- **Suppression des produits** qui ne fonctionnait pas
- Normalisation de l'ID produit en string avant comparaison
- Attente de la confirmation du serveur avant suppression visuelle

### Ajouté
- Logs de débogage côté frontend et backend

## [1.3.9] - 2026-01-01

### Modifié
- **Fusion des deux boutons d'ajout** : Un seul bouton "➕ Ajouter un produit"
- Le modal unifié permet à la fois le scan et la saisie manuelle
- Interface plus épurée

### Supprimé
- Bouton "Ajouter manuellement" séparé
- Fonctions obsolètes `_openScanModal`, `_scanProduct`

## [1.3.8] - 2026-01-01

### Corrigé
- **Problème de doublons** : Les produits n'apparaissent plus en double après scan
- Suppression complète de la logique des produits temporaires
- Attente de la confirmation serveur avant affichage

## [1.3.7] - 2026-01-01

### Corrigé
- Validation CI GitHub Actions
- Ajout des topics GitHub requis par HACS

## [1.3.6] - 2026-01-01

### Corrigé
- Problème de produits en double après scan (utilisation de `add_product` au lieu de `scan_product`)

## [1.3.5] - 2026-01-01

### Ajouté
- **Modification des produits** : Bouton ✏️ pour éditer nom, date et quantité
- Recherche automatique Open Food Facts avant validation

## [1.3.4] - 2026-01-01

### Corrigé
- Problèmes de responsive sur mobile
- Format de date en JJ/MM/AAAA
- Icône du bouton supprimer

## [1.3.3] - 2026-01-01

### Ajouté
- **Scanner caméra** avec BarcodeDetector API (Chrome/Edge)
- Fallback QuaggaJS pour Android/navigateurs non supportés

## [1.3.0] - 2026-01-01

### Ajouté
- Interface web complète (panel Home Assistant)
- Scan de code-barres via caméra
- Intégration Open Food Facts côté frontend
- Gestion des quantités

## [1.2.0] - 2025-12-31

### Ajouté
- Support HACS
- Configuration via config_flow
- Sensors pour congélateur, réfrigérateur, réserves

## [1.1.0] - 2025-12-31

### Ajouté
- Services : scan_product, add_product, remove_product, update_quantity
- Événements de péremption
- Notifications intelligentes

## [1.0.0] - 2025-12-31

### Ajouté
- Version initiale
- Structure de base de l'intégration
- Stockage JSON des produits
