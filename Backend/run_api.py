#!/usr/bin/env python
"""
Script pour démarrer l'API FastAPI.
"""
import uvicorn
import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Vérifier que email_validator est disponible (indicateur que le venv est correct)
try:
    import email_validator
except ImportError:
    venv_python = project_root / "venv" / "Scripts" / "python.exe"
    print("❌ ERREUR: email_validator n'est pas disponible!")
    print(f"   Python actuel: {sys.executable}")
    print("\n   Pour résoudre ce problème:")
    print(f"   1. Activez l'environnement virtuel: .\\venv\\Scripts\\Activate.ps1")
    print(f"   2. Ou lancez directement: .\\venv\\Scripts\\python.exe run_api.py")
    print(f"   3. Ou installez les dépendances: .\\venv\\Scripts\\pip.exe install -r requirement.txt")
    sys.exit(1)

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",  # Utiliser 127.0.0.1 au lieu de 0.0.0.0 pour Windows
        port=8000,
        reload=True,
        reload_dirs=[str(project_root / "api")],
        log_level="info"
    )