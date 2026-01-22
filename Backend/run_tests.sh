#!/bin/bash
# Script pour exécuter tous les tests d'intégration API

echo "========================================"
echo "Tests d'intégration API - RAG System"
echo "========================================"
echo ""

# Activer l'environnement virtuel si disponible
if [ -f "venv/bin/activate" ]; then
    echo "Activation de l'environnement virtuel..."
    source venv/bin/activate
fi

# Aller dans le répertoire Backend
cd "$(dirname "$0")"

echo ""
echo "Exécution des tests d'intégration..."
echo ""

# Exécuter les tests avec pytest
python -m pytest tests/test_api_integration.py -v --tb=short

echo ""
echo "========================================"
echo "Tests terminés"
echo "========================================"

