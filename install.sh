#!/bin/bash
# Script d'installation pour Inventory Manager
# À exécuter depuis le terminal Home Assistant ou via SSH

# Définir le répertoire de destination
CONFIG_DIR="/config"
COMPONENT_DIR="$CONFIG_DIR/custom_components/inventory_manager"

echo "🚀 Installation de Inventory Manager..."

# Créer le dossier si nécessaire
mkdir -p "$COMPONENT_DIR"
mkdir -p "$COMPONENT_DIR/translations"

echo "📁 Dossier créé: $COMPONENT_DIR"

# Télécharger les fichiers depuis GitHub (à adapter avec votre repo)
# Pour l'instant, on affiche les instructions

echo ""
echo "✅ Structure créée !"
echo ""
echo "📝 Prochaines étapes:"
echo "1. Copiez les fichiers Python dans $COMPONENT_DIR"
echo "2. Redémarrez Home Assistant"
echo "3. Ajoutez l'intégration via Paramètres → Intégrations"
echo ""
