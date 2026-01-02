# Instructions de Debug - Problème Réserve

## 1. Vérifier que le fix est chargé

### A. Redémarrer Home Assistant (OBLIGATOIRE)
Le fix dans `services.py` nécessite un redémarrage complet de Home Assistant.

**Dans Home Assistant :**
1. Paramètres → Système → Redémarrer Home Assistant
2. Attendre le redémarrage complet (~1-2 minutes)

## 2. Vérifier les logs Home Assistant

### A. Via l'interface web
1. Paramètres → Système → Journaux
2. Chercher des erreurs avec "inventory_manager"
3. Essayer d'ajouter un produit dans Réserve
4. Rafraîchir les logs et copier les erreurs

### B. Via le terminal (plus complet)
```bash
# Afficher les dernières lignes du log
tail -100 /config/home-assistant.log | grep inventory

# Ou en temps réel
tail -f /config/home-assistant.log | grep -E "(inventory|error|Error)"
```

## 3. Vérifier la console du navigateur

### Étapes :
1. Ouvrir Home Assistant dans le navigateur
2. Appuyer sur **F12** (ou Ctrl+Shift+I)
3. Aller dans l'onglet **Console**
4. Aller dans **Réserve**
5. Essayer d'ajouter un produit
6. Copier toutes les erreurs rouges qui apparaissent

## 4. Vérifier que la version est bien la 1.8.9

### Dans l'interface
1. Ouvrir n'importe quelle page (Congélateur, Réfrigérateur ou Réserve)
2. Vérifier en bas de page : doit afficher "Version 1.8.9 • Inventory Manager"

### Dans manifest.json
```bash
grep version /config/custom_components/inventory_manager/manifest.json
# Doit afficher : "version": "1.8.9"
```

## 5. Test minimal

### Test 1 : Vérifier que le service existe
Dans Outils de développement → Services :
1. Chercher "inventory_manager.add_product"
2. Tester avec :
```yaml
service: inventory_manager.add_product
data:
  name: "Test Réserve"
  expiry_date: "2026-12-31"
  location: "pantry"
  quantity: 1
```
3. Si erreur → copier le message complet

### Test 2 : Vérifier les données
Dans Outils de développement → États :
1. Chercher "sensor.inventory_manager_pantry"
2. Vérifier que le sensor existe
3. Vérifier ses attributs (doit contenir products, categories, zones)

## 6. Informations à me transmettre

Si le problème persiste, envoyez-moi :
- [ ] Version affichée dans le footer (1.8.9 ?)
- [ ] Avez-vous redémarré HA après mise à jour ?
- [ ] Erreurs dans la console navigateur (F12)
- [ ] Erreurs dans les logs HA
- [ ] Résultat du test minimal (service add_product)
- [ ] État du sensor.inventory_manager_pantry

## 7. Réinstallation propre (dernier recours)

Si rien ne fonctionne :
```bash
# Sauvegarder vos données
cp -r /config/.storage/inventory_manager_* ~/backup_inventory/

# Supprimer l'intégration
rm -rf /config/custom_components/inventory_manager

# Redémarrer HA
# Puis réinstaller via HACS (v1.8.9)
```
