# Guide de soumission à Home Assistant Brands

## 🎯 Objectif
Ajouter l'icône de votre intégration `inventory_manager` au repository officiel Home Assistant Brands.

## ✅ Prérequis vérifiés
- [x] Repository public : https://github.com/mmaunier/ha-inventory-manager
- [x] icon.png (256×256 PNG) : 11 KB
- [x] icon@2x.png (512×512 PNG) : 20 KB
- [x] Licence MIT dans manifest.json
- [x] Domain dans manifest.json : `inventory_manager`

## 📝 Instructions pas à pas

### 1. Forker le repository Home Assistant Brands

1. Allez sur https://github.com/home-assistant/brands
2. Cliquez sur **Fork** en haut à droite
3. Attendez que le fork se termine

### 2. Créer une nouvelle branche dans votre fork

```bash
# Cloner VOTRE fork (remplacez 'mmaunier' par votre username GitHub)
cd /tmp
git clone https://github.com/mmaunier/brands.git
cd brands

# Créer une branche depuis master
git checkout -b add-inventory-manager
```

### 3. Ajouter vos icônes

```bash
# Créer le dossier pour votre intégration
mkdir -p custom_integrations/inventory_manager

# Copier vos icônes
cp ~/Bureau/Mikael/plugin_homeassistant/custom_components/inventory_manager/icon.png \
   custom_integrations/inventory_manager/

cp ~/Bureau/Mikael/plugin_homeassistant/custom_components/inventory_manager/icon@2x.png \
   custom_integrations/inventory_manager/
```

### 4. Vérifier la structure

```bash
ls -lh custom_integrations/inventory_manager/
# Devrait afficher :
# icon.png (environ 11 KB)
# icon@2x.png (environ 20 KB)
```

### 5. Commit et push

```bash
git add custom_integrations/inventory_manager/
git commit -m "Add Inventory Manager custom integration" -m "Domain: inventory_manager" -m "Repository: https://github.com/mmaunier/ha-inventory-manager"
git push origin add-inventory-manager
```

### 6. Créer la Pull Request

1. Allez sur https://github.com/mmaunier/brands (votre fork)
2. GitHub affichera un bandeau "Compare & pull request" - cliquez dessus
3. **IMPORTANT** : Assurez-vous que :
   - Base repository: `home-assistant/brands`
   - Base branch: `master`
   - Head repository: `mmaunier/brands` (votre fork)
   - Compare branch: `add-inventory-manager`

### 7. Remplir le template de PR

**Titre** :
```
Add Inventory Manager custom integration
```

**Description** :
```markdown
## Integration information

- Domain: `inventory_manager`
- Type: Custom Integration
- Repository: https://github.com/mmaunier/ha-inventory-manager
- Documentation: https://github.com/mmaunier/ha-inventory-manager#readme

## Images added

- [x] icon.png (256×256, 11 KB)
- [x] icon@2x.png (512×512, 20 KB)

## Checklist

- [x] Images are PNG format
- [x] Images are properly compressed
- [x] Images have transparent background
- [x] Images are trimmed (no unnecessary white space)
- [x] Icon is square (1:1 aspect ratio)
- [x] I am the owner/maintainer of this integration
- [x] Integration has MIT license
```

### 8. Attendre la review

Les checks automatiques vont s'exécuter :
- ✅ Validation du format PNG
- ✅ Vérification des dimensions
- ✅ Vérification de la structure

Si tout est vert ✅, un mainteneur reviendra la PR (peut prendre quelques semaines).

## 🔍 Que faire si la PR est refusée ?

- **Images trop grandes** : Compresser davantage avec TinyPNG.com
- **Fond non transparent** : Recréer avec fond transparent
- **Dimensions incorrectes** : Redimensionner à 256×256 et 512×512

## 📌 Après l'acceptation

Une fois merged :
- Votre icône sera disponible sur `https://brands.home-assistant.io/inventory_manager/icon.png`
- HACS affichera automatiquement votre icône personnalisée
- Délai de cache : 24h sur Cloudflare

## ⚡ Commandes rapides (tout en une fois)

```bash
# À exécuter dans /tmp
cd /tmp
git clone https://github.com/mmaunier/brands.git
cd brands
git checkout -b add-inventory-manager
mkdir -p custom_integrations/inventory_manager
cp ~/Bureau/Mikael/plugin_homeassistant/custom_components/inventory_manager/icon*.png \
   custom_integrations/inventory_manager/
git add custom_integrations/inventory_manager/
git commit -m "Add Inventory Manager custom integration" \
           -m "Domain: inventory_manager" \
           -m "Repository: https://github.com/mmaunier/ha-inventory-manager"
git push origin add-inventory-manager
```

Puis créer la PR manuellement sur GitHub.

## 🆘 Ressources

- Documentation Brands : https://github.com/home-assistant/brands#readme
- Exemple de PR acceptée : https://github.com/home-assistant/brands/pulls?q=is%3Apr+is%3Amerged+custom
- Discord HACS : https://discord.gg/apgchf8
