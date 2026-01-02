# Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.10.4] - 2026-01-02

### Corrigé
- **Erreurs 404 dans la console frontend** : Cascade search maintenant gérée côté JavaScript
  - Problème : Le frontend appelait directement Open Food Facts → erreur 404 visible en console
  - Solution : Implémentation de la cascade complète dans pantry.js avec gestion d'erreurs
  - Cascade : Open Food Facts → UPCitemdb → OpenGTINDB (avec try/catch sur chaque API)
  - Affichage de la source du produit trouvé (Open Food Facts, UPCitemdb ou OpenGTINDB)
  - Message clair quand produit non trouvé dans les 3 bases
  - Plus aucune erreur HTTP visible dans la console du navigateur

## [1.10.3] - 2026-01-02

### Corrigé
- **Remplacement de l'API EAN-Search** : Token invalide → Service non fonctionnel
  - Problème : EAN-Search nécessite une inscription payante (token "free" refusé)
  - Solution : Remplacement par **OpenGTINDB** (vraiment gratuit, sans inscription)
  - OpenGTINDB : Base de données européenne/mondiale avec support multilingue
  - Cascade conservée : Open Food Facts → UPCitemdb → OpenGTINDB

### Amélioré
- **Logs détaillés pour cascade search** : Traçabilité complète des requêtes API
  - Préfixe `[CASCADE SEARCH]` pour tous les logs de recherche
  - Indication claire de chaque tentative d'API avec résultats
  - Distinction entre timeout, erreur réseau et produit non trouvé
  - Affichage du nom du produit trouvé dans les logs INFO

## [1.10.2] - 2026-01-02

### Corrigé (CRITIQUE)
- **Détection de catégories Open Food Facts** : Correction d'un bug majeur
  - Problème : Les produits scannés avec Open Food Facts n'étaient pas catégorisés correctement
  - Symptôme : "Farine" dans le nom → Catégorie "Autre" au lieu de "Farines/Sucres"
  - Cause : Le code ne cherchait dans le nom du produit QUE si `categories_tags` était vide
  - Open Food Facts retourne toujours des tags (même génériques) → Le nom n'était jamais analysé
  - Fix : Recherche TOUJOURS dans le nom du produit si les tags n'ont pas donné de résultat
  - Appliqué aux 3 emplacements : Congélateur, Réfrigérateur, Réserve

### Amélioré
- **Mots-clés enrichis** : +100 nouveaux mots-clés pour toutes les catégories
  - **Congélateur** : Ajout variantes FR (poulet/volaille, saumon, brocoli, pomme, etc.)
  - **Réfrigérateur** : Ajout produits FR (jambon, saucisson, comté, salade, etc.)
  - **Réserve** : Ajout pluriels et variantes (farines, pâtes, huiles, etc.)
  - Support accents : œuf/oeuf, pâtes/pates, crème/creme, etc.
  - Meilleure détection produits français

### Exemple de Corrections
**Avant v1.10.2** :
- "Farine de blé" (Open Food Facts) → Catégorie "Autre" ❌
- "Pâtes Barilla" → "Autre" ❌
- "Poulet fermier" → "Autre" ❌

**Après v1.10.2** :
- "Farine de blé" → "Farines/Sucres" ✅
- "Pâtes Barilla" → "Pâtes/Riz/Céréales" ✅
- "Poulet fermier" → "Viande" ✅

### Technique
- `_map_category()` : Logique corrigée en 2 étapes séquentielles
  1. Recherche dans `categories_tags` (Open Food Facts)
  2. **Si aucun match** → Recherche dans le nom du produit (TOUTES les APIs)
  3. Sinon → "Autre"
- CATEGORY_MAPPING : +100 mots-clés ajoutés avec variantes FR

## [1.10.1] - 2026-01-02

### Amélioré
- **Détection de catégories améliorée** : Reconnaissance des produits non-alimentaires
  - Ajout des nouvelles catégories dans `CATEGORY_MAPPING` :
    - **Produits ménagers** : lessive, nettoyants, désinfectants, éponges, etc.
    - **Hygiène & Cosmétiques** : savon, shampoing, crèmes, maquillage, etc.
    - **Papeterie & Fournitures** : stylos, cahiers, scotch, étiquettes, etc.
    - **Médicaments & Santé** : médicaments, vitamines, pansements, etc.
  - Détection basée sur le **nom du produit** (pas seulement les tags)
  - Fonctionne avec UPCitemdb et EAN-Search qui ne fournissent pas de tags
  - Plus de 50 mots-clés ajoutés pour chaque nouvelle catégorie

- **Sécurité et fiabilité**
  - Timeout augmenté : 10s → 15s pour chaque API
  - Gestion robuste des timeouts (déjà en place, améliorée)
  - Si une API ne répond pas, passage automatique à la suivante
  - Logs détaillés pour le débogage

### Technique
- `_map_category()` : Nouvelle logique de détection en 2 étapes
  1. Recherche dans `categories_tags` (Open Food Facts)
  2. Si vide, recherche dans le nom du produit (UPCitemdb/EAN-Search)
- UPCitemdb et EAN-Search convertissent maintenant leur `category` en `categories_tags`
- Timeouts unifiés avec `aiohttp.ClientTimeout(total=15)`

### Exemple
Scan d'un produit "Ariel Lessive" :
- UPCitemdb retourne : `{"category": "Household"}`
- Détection : "lessive" dans le nom → Catégorie : "Produits ménagers" ✅

## [1.10.0] - 2026-01-02

### Ajouté
- **Recherche en cascade sur plusieurs bases de données** : Élargissement de la recherche de codes-barres
  - **Open Food Facts** : Produits alimentaires (déjà en place)
  - **UPCitemdb** : Produits généraux (cosmétiques, ménagers, électronique, etc.)
  - **EAN-Search** : Base européenne généraliste
  - Recherche automatiqueautomatique dans cet ordre jusqu'à trouver le produit
  - Couverture bien plus large pour les produits non-alimentaires de la Réserve

### Modifié
- Backend : `coordinator.async_fetch_product_info()` utilise maintenant 3 APIs
- Chaque résultat indique la source de données utilisée
- Logs améliorés pour le débogage (quelle API a trouvé le produit)

### Technique
- Nouvelles fonctions : `_fetch_from_openfoodfacts()`, `_fetch_from_upcitemdb()`, `_fetch_from_ean_search()`
- Timeouts et gestion d'erreurs robustes pour chaque API
- Format de données unifié entre les différentes sources

### Use Cases
Cette version permet maintenant de scanner :
- Produits alimentaires (Open Food Facts)
- Médicaments avec code-barres (UPCitemdb/EAN-Search)
- Produits ménagers (lessive, nettoyants, etc.)
- Cosmétiques et produits d'hygiène
- Fournitures et papeterie
- Tout produit avec code-barres EAN/UPC

## [1.9.2] - 2026-01-02

### Corrigé
- **Modals d'ajout de produits** : Synchronisation avec les catégories personnalisées
  - Les listes déroulantes de catégories utilisent maintenant les catégories personnalisées de l'utilisateur
  - Avant : catégories hardcodées dans le JavaScript, jamais mises à jour
  - Après : catégories synchronisées automatiquement depuis Home Assistant
  - Les sensors de localisation exposent maintenant `categories` et `zones` dans leurs attributs
  - Fonctionne pour les 3 emplacements : Congélateur, Réfrigérateur, Réserve
  - Lorsque l'utilisateur ajoute/renomme/supprime/réinitialise une catégorie, les modals se mettent à jour automatiquement
  - **Aucun redémarrage nécessaire** : Simple rechargement de page (Ctrl+F5)

### Technique
- Backend : `sensor.py` expose maintenant `coordinator.get_categories()` et `coordinator.get_zones()` dans les attributs
- Frontend : `_syncFromHass()` dans les 3 fichiers JS charge maintenant les catégories/zones depuis le sensor

## [1.9.1] - 2026-01-02

### Corrigé
- **Réinitialisation des catégories Réserve** : Fix du bouton Reset
  - Les catégories par défaut étaient hardcodées dans le JavaScript avec l'ancienne liste
  - Mise à jour de la liste dans `pantry.js` avec les nouvelles catégories :
    - Ajout : Produits ménagers, Hygiène & Cosmétiques, Papeterie & Fournitures, Médicaments & Santé
    - Retrait : Œufs
  - Le bouton "🔄 Réinitialiser" fonctionne maintenant correctement
  - **Aucun redémarrage nécessaire** : Simple rechargement de page (Ctrl+F5)

## [1.9.0] - 2026-01-02

### Ajouté
- **Catégories élargies pour la Réserve** : Support des produits non-alimentaires
  - Nouvelles catégories :
    - Produits ménagers (lessive, liquide vaisselle, nettoyants...)
    - Hygiène & Cosmétiques (savon, shampoing, crèmes...)
    - Papeterie & Fournitures (stylos, cahiers, étiquettes...)
    - Médicaments & Santé (avec dates de péremption)
  - Suppression des catégories périssables non pertinentes pour la réserve (Œufs)
  - Utilisation des zones pour une organisation flexible selon vos besoins

### Modifié
- Catégories par défaut de la Réserve adaptées aux usages mixtes
- Permet maintenant de gérer tout type de produit stocké à long terme

### Use Cases
Cette version permet de gérer :
- Stock de produits d'entretien
- Médicaments avec dates d'expiration
- Fournitures de bureau et papeterie
- Produits d'hygiène et cosmétiques
- Tout produit non-périssable avec traçabilité

## [1.8.10] - 2026-01-02

### Corrigé (CRITIQUE)
- **Bug affichage Réserve** : Correction du nom du sensor dans `pantry.js`
  - Le sensor s'appelle `sensor.gestionnaire_d_inventaire_reserves` (avec un S)
  - Le frontend cherchait `sensor.gestionnaire_d_inventaire_reserve` (sans S)
  - Résultat : Les produits étaient bien ajoutés mais n'apparaissaient jamais dans la liste
  - **Aucun redémarrage nécessaire** : Simple rechargement de page (Ctrl+F5)

- **Liens LICENSE dans README** : Correction des liens brisés
  - Badge licence maintenant pointe vers l'URL GitHub complète
  - Lien footer également mis à jour
  - GitHub détecte maintenant correctement la licence MIT

### Note
- Le fix de la v1.8.9 (schemas de validation) était correct mais incomplet
- Le vrai problème était une faute de frappe dans le nom du sensor frontend

## [1.8.9] - 2026-01-02

### Corrigé (CRITIQUE)
- **Bug ajout produits dans Réserve** : Correction des schémas de validation dans `services.py`
  - Les schémas utilisaient `list(STORAGE_LOCATIONS.keys())` au lieu d'une liste explicite
  - Empêchait l'ajout de produits avec `location: 'pantry'`
  - Fix appliqué aux schémas : `SCAN_PRODUCT_SCHEMA`, `ADD_PRODUCT_SCHEMA`, `LIST_PRODUCTS_SCHEMA`
  - Utilisation de `[STORAGE_FREEZER, STORAGE_FRIDGE, STORAGE_PANTRY]` dans tous les schémas

### Technique
- Ce bug était une régression : le fix de v1.8.4 n'avait pas été appliqué à tous les schémas
- Les produits du congélateur et réfrigérateur fonctionnaient, seule la réserve était affectée

## [1.8.8] - 2026-01-02

### Ajouté
- **Soumission à Home Assistant Brands** : Pull Request créée pour ajouter l'icône officielle
  - Une fois mergée, l'icône personnalisée s'affichera automatiquement dans HACS
  - Icônes soumises : icon.png (256×256) et icon@2x.png (512×512)
  - Lien vers la PR : https://github.com/home-assistant/brands/pull/[numéro]

### Documentation
- Ajout du guide complet de soumission à Brands (`BRANDS_SUBMISSION_GUIDE.md`)
- Clarification sur l'affichage des icônes dans HACS pour les repositories personnalisés

## [1.8.7] - 2026-01-02

### Corrigé
- **Configuration HACS** : Déplacement du fichier `hacs.json` de la racine vers `.github/hacs.json`
  - HACS requiert que `hacs.json` soit dans le dossier `.github/` pour fonctionner correctement
  - L'icône personnalisée `icon.png` à la racine sera maintenant affichée dans l'interface HACS
- **Licence** : Ajout du champ `license: MIT` dans le fichier `manifest.json`
  - GitHub détectera maintenant automatiquement la licence MIT
  - Permet une meilleure conformité avec les standards Home Assistant

### Note sur l'icône HACS
Pour les repositories personnalisés HACS, l'icône provient de :
1. Home Assistant Brands (si l'intégration y est enregistrée)
2. L'icône MDI définie dans le manifest (`mdi:fridge-outline`)
3. Les icônes dans `custom_components/inventory_manager/` (icon.png et icon@2x.png)

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
