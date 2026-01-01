# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.8.6] - 2026-01-02

### Corrigé
- **Position des icônes** : Les emojis 🧃 et 🥫 sont maintenant avant le titre au lieu d'après
  - Format correct : "🧃 Gestionnaire d'Inventaire - Réfrigérateur"
  - Format correct : "🥫 Gestionnaire d'Inventaire - Réserve"

## [1.8.5] - 2026-01-02

### Corrigé (CRITIQUE - FIX FINAL)
- **Migration automatique catégories/zones** : Ajout de la migration automatique list → dict
  - **__init__.py** : Migration au démarrage pour les utilisateurs venant des versions < 1.8.0
  - **coordinator.py** : Protection dans toutes les méthodes avec conversion list → dict si nécessaire
  - Les utilisateurs ayant des catégories/zones au format liste (v1.7.x et antérieures) sont maintenant correctement migrés
  - Toutes les méthodes protégées : add_category, remove_category, rename_category, add_zone, remove_zone, rename_zone, reset_categories, reset_zones

- **Icônes emojis** : Correction définitive des icônes 🧃 et 🥫
  - Les emojis sont maintenant correctement encodés en UTF-8
  - Position après le titre au lieu d'avant pour éviter les problèmes d'encodage

### Technique
- La vraie cause du bug : les utilisateurs gardaient le format **liste** des versions < 1.8.0
- Quand `dict(liste)` était appelé, Python essayait de convertir la chaîne en dict → erreur
- Solution à 2 niveaux : migration au démarrage + protection runtime dans toutes les méthodes

## [1.8.4] - 2026-01-02

### Corrigé (CRITIQUE)
- **Erreur services categ/zones persistante** : Correction FINALE du problème "dictionary update sequence element #0 has length 6; 2 is required"
  - Le problème venait de `vol.In(list(STORAGE_LOCATIONS.keys()))` dans les schémas de validation
  - Remplacement par liste explicite : `vol.In([STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY])`
  - Ajout des imports manquants : `STORAGE_FRIDGE` et `STORAGE_PANTRY` dans services.py
  - Correction appliquée à tous les schémas : ADD_CATEGORY, REMOVE_CATEGORY, RENAME_CATEGORY, ADD_ZONE, REMOVE_ZONE, RENAME_ZONE, RESET_CATEGORIES, RESET_ZONES
- **Version footer** : Mise à jour du numéro de version dans home.js (1.8.0 → 1.8.3)

### Technique
- La fonction `list(STORAGE_LOCATIONS.keys())` ne fonctionnait pas correctement avec voluptuous
- Utilisation d'une liste explicite des valeurs valides pour le paramètre `location`

## [1.8.3] - 2026-01-02

### Corrigé
- **Icônes manquantes** : Ajout des icônes 🧃 (réfrigérateur) et 🥫 (réserve) dans les titres des pages
- **Erreur modification catégories/zones** : Correction de l'erreur "dictionary update sequence element #0 has length 9; 2 is required"
  - Tous les appels de services `add_category`, `remove_category`, `rename_category` incluent maintenant le paramètre `location`
  - Tous les appels de services `add_zone`, `remove_zone`, `rename_zone` incluent maintenant le paramètre `location`
  - Les boutons "Réinitialiser" fonctionnent maintenant correctement sur tous les emplacements
  - Correction appliquée aux 3 composants : freezer.js, fridge.js, pantry.js

### Technique
- Les services backend nécessitent le paramètre `location` depuis la v1.8.0, mais le frontend ne le passait pas
- Ajout systématique de `location: 'freezer'|'fridge'|'pantry'` dans tous les appels de gestion de catégories et zones

## [1.8.2] - 2026-01-02

### Documentation
- **Automations par emplacement** : Séparation des exemples d'automations par emplacement dans `automations_example.yaml`
  - 3 automations distinctes avec filtrage par `event_data.location` (freezer, fridge, pantry)
  - Émojis spécifiques pour chaque emplacement (🧊 🧃 🥫)
  - Groupes de notifications séparés pour meilleure organisation

## [1.8.1] - 2026-01-01

### Corrigé
- **Mapping OpenFoodFacts étendu** : Ajout de toutes les catégories manquantes pour réfrigérateur et réserve
  - Ajout des mappings pour "Viande/Charcuterie", "Fromages", "Légumes frais", "Fruits frais"
  - Ajout des mappings pour "Conserves", "Pâtes/Riz/Céréales", "Farines/Sucres", "Huiles/Vinaigres", "Épices/Aromates", "Biscuits/Gâteaux secs", "Produits d'épicerie", "Œufs"
  - Enrichissement des mots-clés existants pour meilleure détection
- **Sensors de produits périmés par emplacement** : Séparation des compteurs de produits périmés
  - Création de `sensor.gestionnaire_d_inventaire_expired_freezer` pour le congélateur
  - Création de `sensor.gestionnaire_d_inventaire_expired_fridge` pour le réfrigérateur
  - Création de `sensor.gestionnaire_d_inventaire_expired_pantry` pour la réserve
  - Chaque emplacement affiche maintenant uniquement ses propres produits périmés
  - Conservation du sensor global `sensor.gestionnaire_d_inventaire_produits_perimes` pour compatibilité

### Modifié
- **Méthode `_map_category()`** : Prend maintenant en compte le `location` pour mapper correctement les catégories par emplacement
- **Composants frontend** : freezer.js, fridge.js et pantry.js utilisent leurs sensors spécifiques

## [1.8.0] - 2026-01-01

### Ajouté
- **Réfrigérateur et Réserve** : Ajout de deux nouvelles zones de stockage
  - 🧃 Réfrigérateur : Gestion dédiée avec catégories adaptées
  - 🥫 Réserve : Gestion de la réserve alimentaire avec catégories spécifiques
- **Catégories par emplacement** : Chaque zone a ses propres catégories personnalisables
  - Congélateur (9 catégories) : Viande, Poisson, Légumes, Fruits, Plats préparés, Pain/Pâtisserie, Glaces/Desserts, Condiments/Sauces, Autre
  - Réfrigérateur (10 catégories) : Viande/Charcuterie, Poisson/Fruits de mer, Produits laitiers, Fromages, Légumes frais, Fruits frais, Boissons, Sauces/Condiments, Plats préparés, Autre
  - Réserve (11 catégories) : Conserves, Pâtes/Riz/Céréales, Farines/Sucres, Huiles/Vinaigres, Épices/Aromates, Biscuits/Gâteaux secs, Boissons, Condiments/Sauces, Produits d'épicerie, Œufs, Autre
- **Zones par emplacement** : Chaque zone a ses propres zones personnalisables (Zone 1/2/3 par défaut)
- **Navigation améliorée** : Page d'accueil avec 3 cartes cliquables pour accéder à chaque emplacement
- **Composants modulaires** : freezer.js, fridge.js, pantry.js pour une meilleure organisation du code

### Modifié
- **Services** : Tous les services de gestion catégories/zones acceptent maintenant un paramètre `location`
- **Backend** : Gestion de 3 inventaires distincts (congélateur, réfrigérateur, réserve)
- **Sensors** : Ajout des sensors dédiés pour réfrigérateur et réserve

### Technique
- Architecture modulaire avec routeur dans panel.js
- Gestion des catégories et zones par emplacement dans le coordinator
- Support complet des 3 emplacements dans tous les services

## [1.7.4] - 2026-01-01

### Corrigé
- **Boutons modales non fonctionnels** : Correction du blocage des clics introduit en v1.7.2
  - Suppression du `stopPropagation()` qui empêchait les boutons de fonctionner
  - Conservation uniquement de la fermeture sur clic backdrop
  - Le véritable fix était déjà dans v1.7.3 (panel.js)
  - Les boutons Annuler, Fermer, Ajouter, etc. fonctionnent maintenant correctement
  - Les modales restent ouvertes et sont totalement fonctionnelles

## [1.7.3] - 2026-01-01

### Corrigé
- **Bug modales (FIX FINAL)** : Correction du véritable problème de fermeture automatique
  - Le problème était dans `panel.js` qui recréait tout le composant à chaque mise à jour de `hass`
  - Ajout d'un flag `_initialized` pour ne faire le rendu qu'une seule fois
  - Les mises à jour de `hass` sont maintenant transmises au composant existant sans le recréer
  - Les modales ne se ferment plus automatiquement après 1-2 secondes
  - Fix confirmé : fonctionne même sans interaction de l'utilisateur

### Technique
- Amélioration du cycle de vie du composant `InventoryManagerPanel`
- Référence au composant actif pour mise à jour incrémentale

## [1.7.2] - 2026-01-01

### Corrigé
- **Bug modales (v2)** : Amélioration de la gestion des événements de clic
  - Utilisation de la phase de capture pour intercepter tous les clics
  - Stop propagation systématique pour empêcher les fermetures intempestives
  - Les modales ne devraient plus se fermer automatiquement

## [1.7.1] - 2026-01-01

### Corrigé
- **Bug modales** : Correction de la fermeture automatique des fenêtres modales après 1-2 secondes
  - Ajout de la gestion de la propagation des événements de clic
  - Les modales restent maintenant ouvertes lors de l'interaction avec le contenu
  - Fermeture possible en cliquant sur le fond ou sur les boutons Annuler/Fermer
  - Fix appliqué sur smartphone et sur le web

## [1.7.0] - 2026-01-01

### Ajouté
- **Page d'accueil** : Nouvelle page principale avec 3 boutons pour choisir l'emplacement
  - 🧊 Congélateur (actif)
  - 🧃 Réfrigérateur (à venir)
  - 🥫 Réserve (à venir)
- **Fichier LICENSE** : Ajout de la licence MIT
- **Architecture modulaire** : Découpage du code en modules
  - `panel.js` : Router principal
  - `home.js` : Page d'accueil
  - `freezer.js` : Gestion du congélateur (ancien panel.js)
- **Bouton retour** : Navigation depuis le congélateur vers la page d'accueil

### Modifié
- Refonte complète de l'architecture frontend
- Interface plus claire avec séparation des emplacements de stockage
- Préparation pour la gestion du réfrigérateur et de la réserve

### Technique
- Code divisé en composants web réutilisables
- Système de navigation par événements personnalisés
- Meilleure organisation du code (réduction de la taille de panel.js)

## [1.6.3] - 2026-01-01

### Ajouté
- **Bouton Réinitialiser** : Ajout d'un bouton 🔄 Réinitialiser dans les modaux de gestion
  - Permet de restaurer les catégories aux 10 valeurs par défaut
  - Permet de restaurer les zones aux 3 valeurs par défaut
  - Confirmation avant réinitialisation pour éviter les erreurs
- 2 nouveaux services : `reset_categories` et `reset_zones`

### Modifié
- Interface des modaux : bouton Réinitialiser à gauche, Fermer à droite

## [1.6.2] - 2026-01-01

### Ajouté
- **Persistance garantie** : Les catégories et zones sont maintenant automatiquement sauvegardées dans la configuration dès l'installation
  - Les listes personnalisées seront préservées lors des mises à jour
  - Les nouvelles installations reçoivent les catégories/zones par défaut sauvegardées
  - Protection contre la perte de personnalisation lors des mises à jour du code

### Technique
- Initialisation de `entry.options["categories"]` et `entry.options["zones"]` au premier démarrage
- Migration automatique pour les installations existantes sans ces options

## [1.6.1] - 2026-01-01

### Corrigé
- **Bug critique** : Erreur `'InventoryCoordinator' object has no attribute '_save_data'` lors de la modification des catégories/zones
  - Corrigé : `_save_data()` remplacé par `async_save_data()` dans toutes les méthodes
- **Layout des boutons** : Les boutons "Gérer catégories" et "Gérer zones" sont maintenant sur la même ligne
- Le bouton "Ajouter un produit" occupe maintenant toute la largeur en dessous

## [1.6.0] - 2026-01-01

### Ajouté
- **Gestion complète des catégories** : Ajouter, supprimer et renommer les catégories
- **Gestion complète des zones** : Ajouter, supprimer et renommer les zones
- Interface de gestion avec boutons "🗂️ Gérer catégories" et "📍 Gérer zones"
- Modaux dédiés pour gérer les catégories et zones
- 6 nouveaux services : `add_category`, `remove_category`, `rename_category`, `add_zone`, `remove_zone`, `rename_zone`

### Modifié
- Les produits sont automatiquement mis à jour lors du renommage
- Suppression d'une catégorie : les produits passent en "Autre"
- Suppression d'une zone : les produits passent à la première zone disponible

## [1.5.1] - 2026-01-01

### Corrigé
- Cache Android : Bump de version pour forcer le rechargement du frontend sur l'application Android Home Assistant
- Les colonnes Catégorie et Zone apparaissent maintenant correctement après mise à jour

## [1.5.0] - 2026-01-01

### Ajouté
- **Catégorisation automatique** des produits (10 catégories françaises)
  - Viande, Poisson, Légumes, Fruits, Produits laitiers
  - Plats préparés, Pain/Pâtisserie, Glaces/Desserts
  - Condiments/Sauces, Autre
- **Zones de stockage** pour organiser le congélateur (Zone 1, 2, 3)
- **Détection automatique de catégorie** depuis Open Food Facts lors du scan
- **Tri par catégorie** et **tri par zone** dans l'interface
- Affichage des colonnes Catégorie et Zone dans le tableau
- Sélecteurs de catégorie et zone dans les modaux d'ajout/édition

### Modifié
- Backend : `coordinator.py` avec méthodes `_map_category()`, `get_categories()`, `get_zones()`
- Services : `add_product` et `update_product` acceptent maintenant `category` et `zone`
- Frontend : Colonnes redimensionnées pour afficher catégorie et zone
- Interface mobile : Catégorie et zone masquées sur petit écran

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
